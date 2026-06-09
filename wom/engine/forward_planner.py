"""
wom/engine/forward_planner.py
==============================
WOM Forward Planning Engine (Step 6)

Operates on psi4supply (psi4demand is never modified here).
Generates CO when supply falls short of demand.
Applies capacity constraints (Step 7 CapHard/CapSoft).
Respects PUSH/PULL mode flags (Step 8).

plan_mode handling
------------------
"pull"     : normal PSI roll-forward (demand-constrained shipment)
"push"     : decoupling node (MOM) — normal PSI; holds buffer inventory
"push_sub" : InBound pass-through — ship ALL available supply upward;
             no demand-side gate; I always = 0 at these nodes

Algorithm
---------
Preparation
    Clear psi4supply[w][P] on derived nodes (rebuilt during forward pass).
    Source P kept: leaf_in (push or pull), supply_point (filled by bridge).

Phase 1 — InBound POST-ORDER (leaf_in -> tier-1 -> MOM)
    Step 0a: CapHard seal P[w]; excess -> CO[w+1]
    Step 0b: CapSoft check (flag only)
    PSI:
        push_sub: s_plan = available (ship everything upward)
        others  : normal CO+S demand calculation

Phase 2 — Bridge MOM -> supply_point
    SP.psi4supply[w][P] = list(MOM.psi4supply[w][S])

Phase 3 — OutBound PRE-ORDER (supply_point -> DAD -> leaf_out)
    Same capacity + PSI logic as Phase 1 (all OT nodes are "pull").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from wom.model.plan_node import PlanNode, S, CO, I, P, NODE_TYPE_LEAF_IN
from wom.model.sc_tree   import SCTree
from wom.model.lot_generator import LotIDGenerator


@dataclass
class ForwardPlanResult:
    prod_nm:        str
    ot_processed:   int = 0
    in_processed:   int = 0
    bridge_lots:    int = 0
    co_generated:   int = 0
    shortfall_weeks: List[tuple] = field(default_factory=list)

    # Step 7
    cap_hard_sealed: int = 0
    cap_hard_events: List[tuple] = field(default_factory=list)
    cap_soft_violations: List[tuple] = field(default_factory=list)

    def record_shortfall(self, node_id, week_label, count):
        self.shortfall_weeks.append((node_id, week_label, count))
        self.co_generated += count

    def record_cap_hard_sealed(self, node_id, week_label, count):
        self.cap_hard_events.append((node_id, week_label, count))
        self.cap_hard_sealed += count
        self.co_generated    += count

    def record_cap_soft_violation(self, node_id, week_label, over_by):
        self.cap_soft_violations.append((node_id, week_label, over_by))

    def __str__(self):
        return (
            f"ForwardPlanResult[{self.prod_nm}]  "
            f"IN={self.in_processed}  OT={self.ot_processed}  "
            f"bridge={self.bridge_lots}  CO={self.co_generated}  "
            f"cap_hard_sealed={self.cap_hard_sealed}  "
            f"cap_soft_violations={len(self.cap_soft_violations)}"
        )


class ForwardPlanner:
    """
    Runs the forward planning pass for one or all products in an SCTree.

    Usage:
        fp     = ForwardPlanner(sc_tree)
        result = fp.run("SKU-A")
        results = fp.run_all()

    opening_inv: {node_id: [lot_id, ...]} — pre-horizon inventory seed.
    """

    def __init__(
        self,
        sc_tree:     SCTree,
        opening_inv: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.sc_tree     = sc_tree
        self.opening_inv = opening_inv or {}

    def run(self, prod_nm: str) -> ForwardPlanResult:
        result  = ForwardPlanResult(prod_nm=prod_nm)
        n_weeks = self.sc_tree.num_weeks()

        ot_root = self.sc_tree.get_ot_root(prod_nm)
        in_root = self.sc_tree.get_in_root(prod_nm)

        self._clear_derived_p(in_root, ot_root, n_weeks)

        # Phase 1: InBound POST-ORDER
        for node in in_root.walk_postorder():
            opening = list(self.opening_inv.get(node.node_id, []))
            self._process_node(node, n_weeks, result, opening_lots=opening)
            result.in_processed += 1
            if node.parent is not None:
                self._propagate_to_parent(node, n_weeks)

        # Phase 2: Bridge MOM -> supply_point
        for w in range(n_weeks):
            mom_s = list(in_root.psi4supply[w][S])
            ot_root.psi4supply[w][P] = mom_s
            result.bridge_lots += len(mom_s)

        # Phase 3: OutBound PRE-ORDER
        for node in ot_root.walk_preorder():
            opening = list(self.opening_inv.get(node.node_id, []))
            self._process_node(node, n_weeks, result, opening_lots=opening)
            result.ot_processed += 1
            for child in node.children:
                self._propagate_to_child(node, child, n_weeks)

        return result

    def run_all(self) -> Dict[str, ForwardPlanResult]:
        return {p: self.run(p) for p in self.sc_tree.products}

    # ------------------------------------------------------------------
    # Preparation
    # ------------------------------------------------------------------

    def _clear_derived_p(self, in_root, ot_root, n_weeks):
        """
        Clear P on derived nodes (rebuilt by forward propagation).
        Source nodes whose P is KEPT:
            leaf_in  — external supply (PULL demand or PUSH schedule)
            supply_point — P filled by bridge in Phase 2
        """
        for node in in_root.walk_preorder():
            if node.node_type != NODE_TYPE_LEAF_IN:
                for w in range(n_weeks):
                    node.psi4supply[w][P] = []

        for node in ot_root.walk_preorder():
            if node is not ot_root:
                for w in range(n_weeks):
                    node.psi4supply[w][P] = []

    # ------------------------------------------------------------------
    # Core node processing
    # ------------------------------------------------------------------

    def _process_node(self, node, n_weeks, result, opening_lots):
        """
        Compute psi4supply[I] and handle CO for one node across all weeks.

        Step 0a  CapHard sealing: P[w] truncated to cap_hard; excess -> CO[w+1]
        Step 0b  CapSoft check: flag if P[w] > cap_soft (no movement)

        PSI formula (normal / PULL):
            available = I[w-1] + P[w]               (CO is demand, not supply)
            total_demand = CO[w] + S_plan[w]
            Case 1: avail >= total  -> S=S_plan, I=surplus
            Case 2: avail >= CO     -> S=remaining, CO[w+1]+=shortfall_S
            Case 3: avail < CO      -> S=available, CO[w+1]+=all_remaining

        PSI formula (push_sub — InBound pass-through):
            s_plan = available          (ship ALL supply upward)
            -> always Case 1, I=0, no CO generated
        """
        prev_inv_lots: List[str] = list(opening_lots)
        is_push_sub = (node.plan_mode == "push_sub")

        for w in range(n_weeks):
            wk_label = node.week_labels[w] if node.week_labels else str(w)

            # Step 0a: CapHard sealing
            ch = node.cap_hard(w)
            if ch > 0 and len(node.psi4supply[w][P]) > int(ch):
                excess = node.psi4supply[w][P][int(ch):]
                node.psi4supply[w][P] = node.psi4supply[w][P][:int(ch)]
                if w + 1 < n_weeks:
                    node.psi4supply[w + 1][CO].extend(excess)
                result.record_cap_hard_sealed(node.node_id, wk_label, len(excess))

            # Step 0b: CapSoft check
            cs = node.cap_soft(w)
            if cs > 0 and len(node.psi4supply[w][P]) > int(cs):
                result.record_cap_soft_violation(
                    node.node_id, wk_label,
                    len(node.psi4supply[w][P]) - int(cs),
                )

            # Supply side
            p_lots    = list(node.psi4supply[w][P])
            available = prev_inv_lots + p_lots

            # Demand side
            if is_push_sub:
                # PUSH sub-node: ship ALL available supply upward.
                # No demand gate; inventory stays at zero.
                node.psi4supply[w][S] = list(available)
                node.psi4supply[w][I] = []
                prev_inv_lots         = []
                continue

            co_lots      = list(node.psi4supply[w][CO])
            s_plan       = list(node.psi4supply[w][S])
            total_demand = co_lots + s_plan

            avail_cnt = len(available)
            total_cnt = len(total_demand)
            co_cnt    = len(co_lots)

            node.psi4supply[w][CO] = []

            if avail_cnt >= total_cnt:
                node.psi4supply[w][S] = s_plan
                node.psi4supply[w][I] = available[total_cnt:]
                prev_inv_lots         = node.psi4supply[w][I]

            elif avail_cnt >= co_cnt:
                remaining = available[co_cnt:]
                shortfall = s_plan[len(remaining):]
                node.psi4supply[w][S] = remaining
                node.psi4supply[w][I] = []
                prev_inv_lots         = []
                if shortfall and (w + 1) < n_weeks:
                    node.psi4supply[w + 1][CO].extend(shortfall)
                if shortfall:
                    result.record_shortfall(node.node_id, wk_label, len(shortfall))

            else:
                unfulfilled = total_demand[avail_cnt:]
                node.psi4supply[w][S] = available if available else []
                node.psi4supply[w][I] = []
                prev_inv_lots         = []
                if unfulfilled and (w + 1) < n_weeks:
                    node.psi4supply[w + 1][CO].extend(unfulfilled)
                if unfulfilled:
                    result.record_shortfall(node.node_id, wk_label, len(unfulfilled))

    # ------------------------------------------------------------------
    # Supply propagation helpers
    # ------------------------------------------------------------------

    def _propagate_to_parent(self, node, n_weeks):
        """InBound: child S[w] -> parent P[w + node.lt_wks]."""
        parent = node.parent
        if parent is None:
            return
        for w in range(n_weeks):
            confirmed_s = node.psi4supply[w][S]
            if not confirmed_s:
                continue
            target_w = w + node.lt_wks
            if 0 <= target_w < n_weeks:
                parent.psi4supply[target_w][P].extend(confirmed_s)

    def _propagate_to_child(self, parent, child, n_weeks):
        """
        OutBound: parent S[w] -> child P[w + child.lt_wks].
        Region-filters lots when parent has multiple children.
        """
        child_region = _infer_region_from_node_id(child.node_id)

        for w in range(n_weeks):
            confirmed_s = parent.psi4supply[w][S]
            if not confirmed_s:
                continue

            if child_region and len(parent.children) > 1:
                matched = [
                    lot for lot in confirmed_s
                    if _lot_region(lot) == child_region
                ]
            else:
                matched = list(confirmed_s)

            if not matched:
                continue
            target_w = w + child.lt_wks
            if 0 <= target_w < n_weeks:
                child.psi4supply[target_w][P].extend(matched)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _lot_region(lot_id):
    """Extract region from lot ID: {sku}:{region}:{week}:{seq}"""
    try:
        parts = lot_id.rsplit(":", 1)
        prefix = parts[0].rsplit(":", 1)
        sku_region = prefix[0].split(":", 1)
        return sku_region[1]
    except (ValueError, IndexError):
        return None


def _infer_region_from_node_id(node_id):
    """Extract region from node_id: OUT:Sales:{region}:{sku}"""
    parts = node_id.split(":")
    if len(parts) >= 4 and parts[0] in ("OUT", "IN"):
        return parts[2]
    return None
