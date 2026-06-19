"""
wom/engine/backward_planner.py
================================
WOM Backward Planning Engine (Step 4)

Backward planning = Demand Allocation in ideal / unconstrained state.
CO (Carry Over) is NEVER generated here.

─────────────────────────────────────────────────────────────────────────────
Algorithm
─────────────────────────────────────────────────────────────────────────────

Phase 1 — OutBound POST-ORDER (leaf_out → DAD → supply_point)
    For each node (children before parent):
        psi4demand[w][P] = psi4demand[w][S]          (ideal: receive = ship)
        parent.psi4demand[w - node.lt_wks][S] +=     (parent ships lt_wks earlier)
            node.psi4demand[w][S]

    lt_wks on each node = transit time for goods to arrive FROM parent TO this node.
    So "parent must ship in week  w - node.lt_wks"  for this node to have goods in week w.

Phase 2 — Bridge  (supply_point → MOM, week by week)
    MOM.psi4demand[w][S] +=  supply_point.psi4demand[w][S]   for all w
    (Full WOM: market-priority allocation happens here.
     BackwardPlanner v1: 1-to-1 copy, allocation deferred to future step.)

Phase 3 — InBound PRE-ORDER (MOM → tier-1 → leaf_in)
    For each node (parent before children):
        psi4demand[w][P] = psi4demand[w][S]          (ideal: receive = ship)
        for each child:
            child.psi4demand[w - child.lt_wks][S] += (child ships lt_wks earlier)
                node.psi4demand[w][S]

    InBound lt_wks on child = transit time from child (supplier) to parent (MOM).
    So "child must ship in week  w - child.lt_wks"  for parent to have goods in week w.

─────────────────────────────────────────────────────────────────────────────
Lot-ID handling
─────────────────────────────────────────────────────────────────────────────

Lots that fall outside the planning horizon  (offset week < 0)  are
accumulated in BackwardPlanResult.past_due_lots — they represent demand
that would require procurement action BEFORE the planning horizon begins.

─────────────────────────────────────────────────────────────────────────────
v1r0m2: Holiday Calendar closure-week skip
─────────────────────────────────────────────────────────────────────────────

When HolidayCalendarPlugin runs on_pre_plan it writes
    config["explicit_closures"] = {node_name: set(week_idx)}
BackwardPlanner reads this via __init__(config=...) and uses _offset_week()
to skip closed weeks when stepping back by lt_wks, adding extra offset for
each closed week found in the range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from wom.model.plan_node import PlanNode, S, CO, I, P
from wom.model.sc_tree   import SCTree
from wom.engine.lane_assignment import LaneTable


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class BackwardPlanResult:
    """
    Summary of one backward planning pass for a single product.
    """
    prod_nm: str

    # Total lot-propagation events recorded
    ot_propagations: int = 0   # OutBound phase lot moves
    bridge_lots:     int = 0   # Lots transferred at supply_point -> MOM bridge
    in_propagations: int = 0   # InBound phase lot moves

    # Lots that fell before the planning horizon (offset week < 0)
    # key = (node_id, lot_id)
    past_due_lots: List[Tuple[str, str, int]] = field(default_factory=list)
    # (node_id, lot_id, original_week)

    # Per-node demand summary  node_id -> {week_label: {S, P} qty}
    node_summary: Dict[str, Dict[str, Dict[str, int]]] = field(
        default_factory=dict
    )

    def record_past_due(self, node_id: str, lot_id: str, week: int) -> None:
        self.past_due_lots.append((node_id, lot_id, week))

    def __str__(self) -> str:
        return (
            f"BackwardPlanResult[{self.prod_nm}]  "
            f"OT={self.ot_propagations}  bridge={self.bridge_lots}  "
            f"IN={self.in_propagations}  past_due={len(self.past_due_lots)}"
        )


# ---------------------------------------------------------------------------
# BackwardPlanner
# ---------------------------------------------------------------------------

class BackwardPlanner:
    """
    Runs the backward planning pass for one or all products in an SCTree.

    Usage
    -----
        planner = BackwardPlanner(sc_tree)
        result  = planner.run("SKU-A")

        # or for all products:
        results = planner.run_all()
    """

    def __init__(self, sc_tree: SCTree,
                 lane_table: Optional[LaneTable] = None,
                 config: Optional[dict] = None) -> None:
        self.sc_tree    = sc_tree
        self.lane_table = lane_table or LaneTable.empty()
        # v1r0m2: explicit_closures from HolidayCalendarPlugin via config
        # Structure: {node_name: set(week_idx)} — weeks that are supply-closed.
        # BackwardPlanner uses this to skip closed weeks during LT offset calc.
        cfg = config or {}
        self._explicit_closures: Dict[str, set] = cfg.get("explicit_closures", {})

    # ======================================================================
    # Public API
    # ======================================================================

    def run(self, prod_nm: str) -> BackwardPlanResult:
        """
        Execute the full backward planning pass for one product.

        Parameters
        ----------
        prod_nm:
            Product name (key in sc_tree.prod_tree_dict_OT/IN).

        Returns
        -------
        BackwardPlanResult
        """
        result = BackwardPlanResult(prod_nm=prod_nm)
        n_weeks = self.sc_tree.num_weeks()

        ot_root = self.sc_tree.get_ot_root(prod_nm)
        in_root = self.sc_tree.get_in_root(prod_nm)

        # -- Phase 1: OutBound POST-ORDER ----------------------------------
        for node in ot_root.walk_postorder():
            self._ot_propagate(node, n_weeks, result)

        # -- Phase 2: Bridge supply_point -> MOM (with Lane Assignment) ---
        in_roots = self.sc_tree.get_in_roots(prod_nm)  # {node_id: PlanNode}
        primary_mom = self.sc_tree.get_in_root(prod_nm)

        if self.lane_table.is_empty() or len(in_roots) == 1:
            # No lane table or single MOM -> original 1:1 bridge
            for w in range(n_weeks):
                transfer = self.sc_tree.bridge_backward(prod_nm, w)
                result.bridge_lots += len(transfer.lot_ids)
        else:
            # Multi-MOM: route each lot to its assigned MOM via LaneTable
            lot_leaf_index = self._build_lot_leaf_index(ot_root)
            for w in range(n_weeks):
                for lot_id in list(ot_root.psi4demand[w][S]):
                    # Resolve destination MOM: leaf_node_name first, region fallback
                    leaf      = lot_leaf_index.get(lot_id)
                    leaf_name = leaf.node_name if leaf else ""
                    # PlanNode has no .region attribute; extract from lot_id
                    # lot_id format: "{sku_id}:{region}:{week}:{seq}"
                    _parts = lot_id.split(":")
                    region = _parts[1] if len(_parts) >= 3 else ""
                    mom_id     = self.lane_table.resolve(prod_nm, leaf_name, region)
                    target_mom = in_roots.get(mom_id, primary_mom)
                    target_mom.add_lot_demand(w, S, lot_id)
                    result.bridge_lots += 1

        # -- Phase 3: InBound PRE-ORDER (all MOM roots) -------------------
        for mom_node in in_roots.values():
            for node in mom_node.walk_preorder():
                self._in_propagate(node, n_weeks, result)

        # -- Build node summary -------------------------------------------
        for node in self.sc_tree.iter_all_nodes(prod_nm):
            self._record_summary(node, result)

        return result

    def run_all(self) -> Dict[str, BackwardPlanResult]:
        """Run backward planning for every product in the SCTree."""
        return {
            prod_nm: self.run(prod_nm)
            for prod_nm in self.sc_tree.products
        }

    # ======================================================================
    # v1r0m2: LT offset with closure-week skip
    # ======================================================================

    def _offset_week(self, week: int, lt_wks: int, node_name: str) -> int:
        """
        Compute the upstream week index by stepping back lt_wks weeks,
        skipping any explicitly-closed weeks for the given node.

        Example: lt=2, week=10, closure_weeks={9} for node_name
            → step back from 10: skip 9 (closed), count 8, count 7 → return 7

        If node_name has no closures, this is equivalent to week - lt_wks.
        """
        closure_set = self._explicit_closures.get(node_name, set())
        if not closure_set:
            return week - lt_wks

        remaining = lt_wks
        w = week - 1
        while remaining > 0 and w >= -(lt_wks * 2 + len(closure_set)):
            if w not in closure_set:
                remaining -= 1
            w -= 1
        return w + 1  # w was decremented one extra at loop exit

    # ======================================================================
    # Phase 1: OutBound propagation  (POST-ORDER)
    # ======================================================================

    def _ot_propagate(
        self,
        node:    PlanNode,
        n_weeks: int,
        result:  BackwardPlanResult,
    ) -> None:
        """
        For each lot in node.S[w]:
          1. Copy lot to node.P[w]            (ideal: receive = ship)
          2. Add lot to parent.S[w - lt_wks]  (parent ships lt_wks earlier)
        """
        for w in range(n_weeks):
            # Iterate over a snapshot (list copy) because parent.S may be
            # extended by earlier iterations in the same pass.
            for lot_id in list(node.psi4demand[w][S]):
                # -- P = S  (ideal backward) --------------------------------
                node.psi4demand[w][P].append(lot_id)

                # -- Propagate to parent ------------------------------------
                if node.parent is None:
                    # supply_point: no further parent on OT side
                    continue

                # v1r0m2: skip closure weeks of the parent node when stepping back
                # ss_wks adds safety stock buffer on top of lead time
                parent_w = self._offset_week(w, node.lt_wks + node.ss_wks, node.parent.node_name)
                if parent_w < 0:
                    result.record_past_due(node.node_id, lot_id, w)
                elif parent_w < n_weeks:
                    node.parent.psi4demand[parent_w][S].append(lot_id)
                    result.ot_propagations += 1

    # ======================================================================
    # Phase 3: InBound propagation  (PRE-ORDER)
    # ======================================================================

    def _in_propagate(
        self,
        node:    PlanNode,
        n_weeks: int,
        result:  BackwardPlanResult,
    ) -> None:
        """
        For each lot in node.S[w]:
          1. Copy lot to node.P[w]                  (ideal: receive = ship)
          2. For each child:
             child.S[w - child.lt_wks] += lot       (child ships lt_wks earlier)

        v1r0m2: Capacity envelope (JIT weekly synchronization)
        -------------------------------------------------------
        When node.cap_hard(w) > 0, only the first cap_hard(w) lots are
        propagated to children (suppliers).  This models the MOM node as a
        capacity pacemaker: suppliers receive exactly the capped supply order,
        not the raw unconstrained market demand.

        Effect: a step-function cap_hard at Foxconn_CN (3→2→1→0 shifts)
        propagates backward through the entire InBound tree, so TSMC_TW,
        Buffer_Wafer_TW, and SiliconWafer_TW all synchronize to the same
        stepped production rhythm (JIT "drum-buffer-rope" behaviour).

        Nodes with cap_hard(w) == 0.0 (unlimited) are unaffected.
        """
        for w in range(n_weeks):
            all_lots = list(node.psi4demand[w][S])

            # -- P = S  (record full demand signal) -------------------------
            for lot_id in all_lots:
                node.psi4demand[w][P].append(lot_id)

            # -- Capacity envelope: clip propagation at cap_hard(w) ---------
            cap_w = node.cap_hard(w)
            propagate_lots = all_lots[:int(cap_w)] if cap_w > 0 else all_lots

            # -- Propagate (capped) lots to each child (supplier) -----------
            for lot_id in propagate_lots:
                for child in node.children:
                    # v1r0m2: skip closure weeks; ss_wks adds safety-stock offset
                    child_w = self._offset_week(w, child.lt_wks + child.ss_wks, child.node_name)
                    if child_w < 0:
                        result.record_past_due(child.node_id, lot_id, w)
                    elif child_w < n_weeks:
                        child.psi4demand[child_w][S].append(lot_id)
                        result.in_propagations += 1

    # ======================================================================
    # Multi-MOM lane routing helper
    # ======================================================================

    def _build_lot_leaf_index(self, ot_root: PlanNode) -> dict:
        """
        Build lot_id -> leaf_out PlanNode index for multi-MOM lane routing.

        Traverses the OT tree; for every leaf node (no children) records
        which lot_ids appear in psi4demand[w][S].  After Phase 1 OT
        propagation, each lot originated from exactly one leaf_out node.

        Used by run() Phase 2 to look up the leaf_out node for each lot
        arriving at supply_point, so its node_name can be passed to
        LaneTable.resolve() for exact-channel matching.
        """
        index: dict = {}
        for node in ot_root.walk_preorder():
            if not node.children:          # leaf_out nodes have no children
                for w_psi in node.psi4demand:
                    for lot_id in w_psi[S]:
                        index[lot_id] = node
        return index

    # ======================================================================
    # Summary helper
    # ======================================================================

    @staticmethod
    def _record_summary(
        node:   PlanNode,
        result: BackwardPlanResult,
    ) -> None:
        if not node.week_labels:
            return
        summary: Dict[str, Dict[str, int]] = {}
        for w, wk_label in enumerate(node.week_labels):
            s_qty = node.qty_demand(w, S)
            p_qty = node.qty_demand(w, P)
            i_qty = node.qty_demand(w, I)
            if s_qty or p_qty:
                summary[wk_label] = {"S": s_qty, "P": p_qty, "I": i_qty}
        if summary:
            result.node_summary[node.node_id] = summary
