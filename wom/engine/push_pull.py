"""
wom/engine/push_pull.py
=======================
WOM Step 8 — PUSH / PULL Buffer Stock Switching

Overview
--------
PULL (default): demand-driven. psi4supply[P] at leaf_in is set by backward
demand propagation. Production = what demand needs.

PUSH: supply-driven. psi4supply[P] at leaf_in is set by a PUSH production
schedule (fixed weekly qty or buffer-replenishment formula), independent of
downstream demand. The entire InBound sub-chain below the decoupling node
acts as a pass-through pipeline — each node ships ALL available supply upward
so that the decoupling node (MOM) accumulates buffer inventory.

plan_mode values
----------------
"pull"     : default, demand-driven (OutBound + PULL InBound nodes)
"push"     : decoupling node (MOM) — receives push supply, ships to demand,
             holds buffer inventory
"push_sub" : InBound nodes BELOW the decoupling node — ship ALL available
             supply upward (no demand-side gate)

Execution order (per planning cycle)
-------------------------------------
    Step 4  BackwardPlanner.run()          fills psi4demand (demand truth)
    Step 5  copy_demand_to_supply()        psi4supply <- copy of psi4demand
    Step 8  PushProductionPlanner.setup()  overwrite leaf_in P + mark modes
    Step 6  ForwardPlanner.run()           propagates from leaf_in forward

PushProductionPlanner.setup() MUST run between Step 5 and Step 6.

PUSH production modes
---------------------
Mode 1 - Fixed quantity  (push_qty_per_week > 0):
    leaf_in.psi4supply[w][P] = push_qty_per_week lots for every week w.

Mode 2 - Replenishment-to-buffer  (push_qty_per_week == 0):
    Simulate rolling inventory at MOM:
        I[0]    = buffer_lots  (start at full buffer)
        push[w] = max(buffer_lots - I_prev + demand_w, 0)
        I[w]    = max(I_prev + push[w] - demand_w, 0)

Region-proportional lot assignment
------------------------------------
PUSH lots must carry region tags to route correctly through SP -> DAD in
ForwardPlanner._propagate_to_child. Distribution uses TOTAL regional demand
ratio (sum across all weeks) so every production week is tagged correctly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from wom.model.plan_node import (
    PlanNode, S, CO, I, P,
    NODE_TYPE_LEAF_IN, NODE_TYPE_LEAF_OUT, NODE_TYPE_MOM,
)
from wom.model.sc_tree      import SCTree
from wom.model.lot_generator import LotIDGenerator

# plan_mode constants
PULL_MODE     = "pull"
PUSH_MODE     = "push"
PUSH_SUB_MODE = "push_sub"


@dataclass
class PushConfig:
    """
    PUSH production configuration for one decoupling node.

    node_id           : node_id of the decoupling node (MOM/InBound root)
    push_qty_per_week : fixed lots/week (0 = replenishment mode)
    buffer_lots       : target buffer inventory (replenishment + initial fill)
    sku_id            : SKU for lot-ID generation (inferred from node_id if empty)
    mode_only         : True = set plan_mode flags ONLY; do NOT overwrite leaf_in
                        P-schedule.  Use when another plugin (e.g. HarvestBatch)
                        has already placed the production schedule.
    """
    node_id:           str
    push_qty_per_week: int  = 0
    buffer_lots:       int  = 0
    sku_id:            str  = ""
    mode_only:         bool = False

    def is_fixed_mode(self) -> bool:
        return self.push_qty_per_week > 0

    def effective_sku(self) -> str:
        if self.sku_id:
            return self.sku_id
        parts = self.node_id.split(":")
        return parts[-1] if len(parts) >= 3 else self.node_id


@dataclass
class PushSetupResult:
    prod_nm:         str
    mode:            str  = "fixed"
    push_lots_total: int  = 0
    push_events:     List[Tuple[str, str, int]] = field(default_factory=list)

    def record(self, node_id: str, week_label: str, qty: int) -> None:
        self.push_events.append((node_id, week_label, qty))
        self.push_lots_total += qty

    def __str__(self) -> str:
        return (
            f"PushSetupResult[{self.prod_nm}]  mode={self.mode}  "
            f"push_lots={self.push_lots_total}  events={len(self.push_events)}"
        )


class PushProductionPlanner:
    """
    Overwrites psi4supply[P] on leaf_in nodes with PUSH lots and sets
    plan_mode flags on the InBound subtree.

    Run AFTER copy_demand_to_supply, BEFORE ForwardPlanner.run.
    """

    def __init__(
        self,
        sc_tree:       SCTree,
        lot_generator: Optional[LotIDGenerator] = None,
    ) -> None:
        self.sc_tree       = sc_tree
        self.lot_generator = lot_generator or LotIDGenerator()

    def setup(self, prod_nm: str, config: PushConfig) -> PushSetupResult:
        """
        Apply PUSH production to the InBound subtree of the decoupling node.

        1. Locate + mark the decoupling node (plan_mode="push").
        2. Mark all InBound nodes BELOW it as plan_mode="push_sub".
           ForwardPlanner._process_node treats push_sub nodes as pass-through
           (ship ALL available supply upward, no demand gate).
        3. Compute push quantities per week.
        4. Compute total regional demand ratio for lot tagging.
        5. Generate + assign lots to each leaf_in.
        """
        n_weeks = self.sc_tree.num_weeks()
        result  = PushSetupResult(
            prod_nm = prod_nm,
            mode    = "fixed" if config.is_fixed_mode() else "replenishment",
        )

        # 1. Locate decoupling node
        decoupling_node = self._find_node(prod_nm, config.node_id)
        if decoupling_node is None:
            raise ValueError(
                f"Decoupling node {config.node_id!r} not found for {prod_nm!r}"
            )

        # 2. Set plan_mode flags
        decoupling_node.is_decoupling = True
        decoupling_node.plan_mode     = PUSH_MODE
        for node in decoupling_node.walk_preorder():
            if node is not decoupling_node:
                node.plan_mode = PUSH_SUB_MODE   # pass-through pipeline

        # 3. Compute push quantities
        push_qtys = self._compute_push_quantities(
            decoupling_node, config, n_weeks
        )

        # 4. Total regional distribution (long-run proportions, week-agnostic)
        region_totals = self._compute_region_totals(prod_nm, n_weeks)

        # 5. Find leaf_in nodes and assign lots
        leaf_in_nodes = [
            node for node in decoupling_node.walk_preorder()
            if node.node_type == NODE_TYPE_LEAF_IN
        ]
        if not leaf_in_nodes:
            raise ValueError(
                f"No leaf_in nodes under {config.node_id!r}"
            )

        # mode_only: plan_mode flags already set; skip P-schedule overwrite
        if config.mode_only:
            return result

        sku_id   = config.effective_sku()
        n_leaves = len(leaf_in_nodes)

        for w in range(n_weeks):
            total_qty = push_qtys[w]
            wk_label  = self.sc_tree.week_labels[w]
            if total_qty <= 0:
                continue

            base, remainder = divmod(total_qty, n_leaves)

            for leaf_idx, leaf_node in enumerate(leaf_in_nodes):
                leaf_qty = base + (1 if leaf_idx < remainder else 0)
                if leaf_qty <= 0:
                    continue

                lots = self._generate_regional_lots(
                    sku_id, wk_label, leaf_qty, region_totals
                )
                leaf_node.psi4supply[w][P] = lots
                result.record(leaf_node.node_id, wk_label, len(lots))

        return result

    def setup_all(
        self,
        push_configs: Dict[str, PushConfig],
    ) -> Dict[str, PushSetupResult]:
        return {
            prod_nm: self.setup(prod_nm, cfg)
            for prod_nm, cfg in push_configs.items()
        }

    # ------------------------------------------------------------------
    # Push quantity calculation
    # ------------------------------------------------------------------

    def _compute_push_quantities(
        self,
        decoupling_node: PlanNode,
        config:          PushConfig,
        n_weeks:         int,
    ) -> List[int]:
        if config.is_fixed_mode():
            return [config.push_qty_per_week] * n_weeks
        return self._replenishment_schedule(
            decoupling_node, config.buffer_lots, n_weeks
        )

    def _replenishment_schedule(
        self,
        mom:         PlanNode,
        buffer_lots: int,
        n_weeks:     int,
    ) -> List[int]:
        """
        Order-up-to replenishment at MOM.
        push[w] = max(buffer_lots - I_prev + demand_w, 0)
        I[w]    = max(I_prev + push[w] - demand_w, 0)
        """
        schedule: List[int] = []
        I_prev = buffer_lots

        for w in range(n_weeks):
            demand_w = len(mom.psi4demand[w][S])
            deficit  = max(buffer_lots - I_prev + demand_w, 0)
            push_w   = deficit
            I_w      = max(I_prev + push_w - demand_w, 0)

            schedule.append(push_w)
            I_prev = I_w

        return schedule

    # ------------------------------------------------------------------
    # Regional distribution helpers
    # ------------------------------------------------------------------

    def _compute_region_totals(
        self,
        prod_nm: str,
        n_weeks: int,
    ) -> Dict[str, int]:
        """
        Return {region: total_demand_lots} summed across ALL weeks.
        PUSH uses long-run regional proportions so lots are tagged correctly
        for every production week (decoupled from week-specific demand).
        """
        ot_root       = self.sc_tree.get_ot_root(prod_nm)
        region_totals: Dict[str, int] = {}

        for node in ot_root.walk_preorder():
            if node.node_type != NODE_TYPE_LEAF_OUT:
                continue
            region = _extract_region_from_node_id(node.node_id)
            if not region:
                continue
            total_qty = sum(len(node.psi4demand[w][S]) for w in range(n_weeks))
            region_totals[region] = region_totals.get(region, 0) + total_qty

        return region_totals

    def _generate_regional_lots(
        self,
        sku_id:     str,
        wk_label:   str,
        total_qty:  int,
        region_map: Dict[str, int],
    ) -> List[str]:
        """
        Generate total_qty lots distributed across regions proportionally.
        Falls back to region "PUSH" if no demand data exists.
        """
        if not region_map or sum(region_map.values()) == 0:
            return self.lot_generator.generate(
                sku_id, "PUSH", wk_label, total_qty
            )

        regions      = list(region_map.keys())
        total_demand = sum(region_map.values())
        lots: List[str] = []
        remaining = total_qty

        for idx, region in enumerate(regions):
            if idx == len(regions) - 1:
                count = remaining
            else:
                fraction = region_map[region] / total_demand
                count    = max(round(total_qty * fraction), 0)
                remaining -= count

            if count > 0:
                lots += self.lot_generator.generate(
                    sku_id, region, wk_label, count
                )

        return lots

    # ------------------------------------------------------------------
    # Node lookup
    # ------------------------------------------------------------------

    def _find_node(
        self,
        prod_nm: str,
        node_id: str,
    ) -> Optional[PlanNode]:
        for node in self.sc_tree.iter_all_nodes(prod_nm):
            if node.node_id == node_id:
                return node
        return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def mark_pull_mode(sc_tree: SCTree, prod_nm: str, node_id: str) -> None:
    """
    Switch a node and its InBound subtree back to PULL mode.
    Does NOT modify psi4supply — caller must re-run Steps 5+6.
    """
    for node in sc_tree.iter_all_nodes(prod_nm):
        if node.node_id == node_id:
            node.is_decoupling = False
            node.plan_mode     = PULL_MODE
            for child in node.walk_preorder():
                if child is not node:
                    child.plan_mode = PULL_MODE
            return
    raise ValueError(f"Node {node_id!r} not found for product {prod_nm!r}")


def get_push_pull_summary(sc_tree: SCTree, prod_nm: str) -> List[dict]:
    """Return plan_mode / is_decoupling status for all nodes."""
    return [
        {
            "node_id":       node.node_id,
            "side":          node.side,
            "node_type":     node.node_type,
            "plan_mode":     node.plan_mode,
            "is_decoupling": node.is_decoupling,
        }
        for node in sc_tree.iter_all_nodes(prod_nm)
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_region_from_node_id(node_id: str) -> Optional[str]:
    parts = node_id.split(":")
    if len(parts) >= 4 and parts[0] in ("OUT", "IN"):
        return parts[2]
    return None
