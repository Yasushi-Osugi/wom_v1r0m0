"""
wom/model/sc_tree.py
====================
WOM Planning Layer — SCTree

Holds the OutBound + InBound PlanNode tree pair for every product.

Tree entry points:
    prod_tree_dict_OT[prod_nm]  →  supply_point PlanNode (OutBound root)
    prod_tree_dict_IN[prod_nm]  →  MOM PlanNode at tier=0 (InBound root)

Hammock model:
                        ┌──────────────────────────────────────┐
    InBound tree        │          OutBound tree               │
    (supply side)       │          (demand side)               │
                        │                                      │
    leaf_in             │   supply_point ──▶ DAD(tier=0) ──▶ leaf_out
      └─ MOM(tier=0) ──▶│   (OT root)        └─▶ DC  ──▶ leaf_out
           └─ tier-1    │                    └─▶ ...
                └─ leaf │
                        └──────────────────────────────────────┘

Traversal rules:
    Backward planning (demand allocation, ideal / CO-free):
        1. walk_postorder(OT root)    leaf_out → DAD → supply_point
        2. Bridge: supply_point demand lots → MOM
        3. walk_preorder(IN root)     MOM → tier-1 → leaf_in

    Forward planning (supply propagation, CO may be generated):
        1. walk_postorder(IN root)    leaf_in → tier-1 → MOM
        2. Bridge: MOM supply lots → supply_point
        3. walk_preorder(OT root)     supply_point → DAD → leaf_out
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, Generator, Iterable, Iterator, List, Optional, Tuple

import pandas as pd

from wom.model.plan_node import (
    PlanNode,
    NODE_TYPE_SUPPLY_POINT,
    NODE_TYPE_DAD,
    NODE_TYPE_LEAF_OUT,
    NODE_TYPE_MOM,
    NODE_TYPE_LEAF_IN,
    S, CO, I, P,
)


# ---------------------------------------------------------------------------
# BridgeTransfer  (data class for supply_point ↔ MOM handoff)
# ---------------------------------------------------------------------------
@dataclass
class BridgeTransfer:
    """
    Records a lot handoff across the supply_point ↔ MOM bridge.
    Used by both backward and forward planning.
    """
    prod_nm:    str
    week:       int
    bucket:     int            # PSI bucket index (S/CO/I/P)
    lot_ids:    List[str]      # lots transferred
    direction:  str            # "backward" | "forward"


# ---------------------------------------------------------------------------
# SCTree
# ---------------------------------------------------------------------------
class SCTree:
    """
    Container for all product-level OutBound / InBound PlanNode trees.

    Attributes
    ----------
    prod_tree_dict_OT : dict[str, PlanNode]
        product_name → OutBound tree root (supply_point node)
    prod_tree_dict_IN : dict[str, PlanNode]
        product_name → InBound tree root (MOM node, tier=0)
    week_labels : list[str]
        Ordered ISO week strings covering the planning horizon,
        e.g. ["2026-W01", ..., "2026-W52"]
    """

    def __init__(self, week_labels: List[str]) -> None:
        if not week_labels:
            raise ValueError("week_labels must not be empty")
        self.week_labels: List[str] = list(week_labels)
        self.prod_tree_dict_OT: Dict[str, PlanNode] = {}
        self.prod_tree_dict_IN: Dict[str, PlanNode] = {}
        # Multi-MOM support: prod_nm → {node_id: PlanNode} for all top-level MOMs
        self._in_roots_dict: Dict[str, Dict[str, PlanNode]] = {}

    # ======================================================================
    # Registration
    # ======================================================================

    def register(
        self,
        prod_nm: str,
        ot_root: PlanNode,
        in_root: PlanNode,
    ) -> None:
        """
        Register an OutBound / InBound tree pair for one product.

        Parameters
        ----------
        prod_nm:
            Product name — key for both dicts.
        ot_root:
            Root of the OutBound PlanNode tree.
            Must be a NODE_TYPE_SUPPLY_POINT node.
        in_root:
            Root of the InBound PlanNode tree.
            Typically a NODE_TYPE_MOM node at tier=0 (Mother Plant).
        """
        if ot_root.node_type != NODE_TYPE_SUPPLY_POINT:
            raise ValueError(
                f"ot_root must be NODE_TYPE_SUPPLY_POINT, got {ot_root.node_type!r}"
            )
        self.prod_tree_dict_OT[prod_nm] = ot_root
        self.prod_tree_dict_IN[prod_nm] = in_root
        # Register as primary entry in multi-MOM dict
        if prod_nm not in self._in_roots_dict:
            self._in_roots_dict[prod_nm] = {}
        self._in_roots_dict[prod_nm][in_root.node_id] = in_root

    def register_extra_mom(self, prod_nm: str, mom_node: PlanNode) -> None:
        """
        Register an additional top-level MOM for multi-factory scenarios.

        The primary MOM (registered via register()) handles lots whose region
        has no explicit lane assignment.  Extra MOMs handle lots explicitly
        routed by LaneTable.

        Parameters
        ----------
        prod_nm:
            Product name (must already be registered via register()).
        mom_node:
            Additional top-level MOM PlanNode to register.
        """
        if prod_nm not in self._in_roots_dict:
            raise KeyError(
                f"Product {prod_nm!r} not yet registered. Call register() first."
            )
        self._in_roots_dict[prod_nm][mom_node.node_id] = mom_node

    # ======================================================================
    # PSI initialisation
    # ======================================================================

    def init_all_psi(self) -> None:
        """
        Call init_psi(week_labels) on every PlanNode in every tree.
        Must be called before any planning operation.
        """
        seen: set = set()
        for node in self._iter_all_nodes_global():
            if id(node) not in seen:
                node.init_psi(self.week_labels)
                seen.add(id(node))

    # ======================================================================
    # Accessors
    # ======================================================================

    @property
    def products(self) -> List[str]:
        """List of registered product names."""
        return list(self.prod_tree_dict_OT.keys())

    def get_ot_root(self, prod_nm: str) -> PlanNode:
        """Return OutBound tree root (supply_point) for the product."""
        try:
            return self.prod_tree_dict_OT[prod_nm]
        except KeyError:
            raise KeyError(f"Product {prod_nm!r} not found in OutBound trees")

    def get_in_root(self, prod_nm: str) -> PlanNode:
        """Return primary InBound tree root (MOM, tier=0) for the product."""
        try:
            return self.prod_tree_dict_IN[prod_nm]
        except KeyError:
            raise KeyError(f"Product {prod_nm!r} not found in InBound trees")

    def get_in_roots(self, prod_nm: str) -> Dict[str, PlanNode]:
        """
        Return all registered top-level MOM nodes for the product.

        Returns
        -------
        dict mapping node_id → PlanNode for every registered MOM root.
        Always contains at least the primary MOM.
        """
        return dict(self._in_roots_dict.get(prod_nm, {
            self.prod_tree_dict_IN[prod_nm].node_id: self.prod_tree_dict_IN[prod_nm]
        }))

    def num_weeks(self) -> int:
        return len(self.week_labels)

    def week_idx(self, week_label: str) -> int:
        return self.week_labels.index(week_label)

    # ======================================================================
    # Planning traversal iterators
    # ======================================================================

    def iter_backward(self, prod_nm: str) -> Iterator[PlanNode]:
        """
        Yield nodes in backward planning order for the product:
            1. OutBound POST-ORDER  (leaf_out → DAD → supply_point)
            2. InBound  PRE-ORDER   (MOM → tier-1 → leaf_in)

        The supply_point itself is yielded at step 1 (end of OT postorder).
        The InBound root (MOM) is yielded at step 2 (start of IN preorder).
        Caller is responsible for the bridge copy at supply_point.
        """
        ot_root = self.get_ot_root(prod_nm)
        in_root = self.get_in_root(prod_nm)
        yield from ot_root.walk_postorder()
        yield from in_root.walk_preorder()

    def iter_forward(self, prod_nm: str) -> Iterator[PlanNode]:
        """
        Yield nodes in forward planning order for the product:
            1. InBound  POST-ORDER  (leaf_in → tier-1 → MOM)
            2. OutBound PRE-ORDER   (supply_point → DAD → leaf_out)

        The InBound root (MOM) is yielded last in step 1.
        Caller is responsible for the bridge copy MOM → supply_point.
        """
        ot_root = self.get_ot_root(prod_nm)
        in_root = self.get_in_root(prod_nm)
        yield from in_root.walk_postorder()
        yield from ot_root.walk_preorder()

    def iter_all_nodes(self, prod_nm: str) -> Iterator[PlanNode]:
        """
        Yield all PlanNodes for one product.
        OT preorder + all IN roots preorder (deduplicating shared nodes).
        Covers multi-MOM scenarios where multiple top-level MOM roots exist.
        """
        seen: set = set()
        in_roots = self.get_in_roots(prod_nm)
        for node in itertools.chain(
            self.get_ot_root(prod_nm).walk_preorder(),
            *(mom.walk_preorder() for mom in in_roots.values()),
        ):
            if id(node) not in seen:
                seen.add(id(node))
                yield node

    # ======================================================================
    # Bridge helpers
    # ======================================================================

    def bridge_backward(
        self,
        prod_nm: str,
        week: int,
        market_priority: Optional[List[str]] = None,
    ) -> BridgeTransfer:
        """
        Backward planning bridge:
        Copy demand lot-IDs from supply_point.psi4demand[week][S]
        into in_root (MOM).psi4demand[week][S].

        In the full original WOM, this step also performs market-priority
        demand allocation across MOM children.  Here we do a direct copy
        (allocation logic lives in the backward planning engine).

        Parameters
        ----------
        prod_nm:
            Product name.
        week:
            Week index.
        market_priority:
            Optional ordered list of region/market names for allocation
            priority (passed through to BridgeTransfer for caller use).

        Returns
        -------
        BridgeTransfer
            Record of the lots transferred.
        """
        sp   = self.get_ot_root(prod_nm)    # supply_point
        mom  = self.get_in_root(prod_nm)    # MOM (InBound root)

        lots = list(sp.psi4demand[week][S])  # copy, not reference
        for lot_id in lots:
            mom.add_lot_demand(week, S, lot_id)

        return BridgeTransfer(
            prod_nm=prod_nm,
            week=week,
            bucket=S,
            lot_ids=lots,
            direction="backward",
        )

    def bridge_forward(
        self,
        prod_nm: str,
        week: int,
    ) -> BridgeTransfer:
        """
        Forward planning bridge:
        Copy supply lot-IDs from MOM.psi4supply[week][P]
        into supply_point.psi4supply[week][P].

        Returns
        -------
        BridgeTransfer
            Record of the lots transferred.
        """
        sp   = self.get_ot_root(prod_nm)
        mom  = self.get_in_root(prod_nm)

        lots = list(mom.psi4supply[week][P])
        for lot_id in lots:
            sp.add_lot_supply(week, P, lot_id)

        return BridgeTransfer(
            prod_nm=prod_nm,
            week=week,
            bucket=P,
            lot_ids=lots,
            direction="forward",
        )

    # ======================================================================
    # Internal helpers
    # ======================================================================

    def _iter_all_nodes_global(self) -> Iterator[PlanNode]:
        """Iterate every node across all products (may yield duplicates)."""
        for prod_nm in self.products:
            yield from self.iter_all_nodes(prod_nm)

    # ======================================================================
    # Summary / debugging
    # ======================================================================

    def summary(self) -> str:
        lines = [
            f"SCTree  weeks={self.num_weeks()}  "
            f"({self.week_labels[0]} … {self.week_labels[-1]})",
            f"  products ({len(self.products)}): {self.products}",
        ]
        for prod_nm in self.products:
            ot_nodes = list(self.get_ot_root(prod_nm).walk_preorder())
            in_nodes = list(self.get_in_root(prod_nm).walk_preorder())
            lines.append(
                f"  [{prod_nm}]  OT nodes={len(ot_nodes)}  "
                f"IN nodes={len(in_nodes)}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"SCTree(products={self.products}, "
            f"weeks={self.num_weeks()})"
        )


# ---------------------------------------------------------------------------
# Demo / test builder
# ---------------------------------------------------------------------------

def build_demo_sc_tree(
    sku_master: "pd.DataFrame",
    week_labels: List[str],
    lt_wks_ot: int = 1,
    lt_wks_in: int = 2,
    cpu_size:  int = 1,
) -> SCTree:
    """
    Build a demo SCTree from an existing WOM sku_master DataFrame.

    Hammock structure per product (sku_id):
        OutBound (3 levels):
            supply_point  (OT root, tier=0 relative to SP)
              └─ region_DC (DAD, tier=0, one per region)
                   └─ sales_leaf (leaf_out, tier=1, one per sku×region)

        InBound (3 levels):
            mother_plant  (MOM, tier=0, IN root)
              └─ tier1_supplier (MOM, tier=1, one per sku)
                   └─ raw_material (leaf_in, tier=2)

    Parameters
    ----------
    sku_master:
        DataFrame with columns: sku_id, sku_name, region, lead_time_wks
    week_labels:
        ISO week strings for the planning horizon.
    lt_wks_ot, lt_wks_in:
        Default OutBound / InBound lead times (weeks) if not in master.
    cpu_size:
        Common Planning Unit lot size (shared across all nodes).

    Returns
    -------
    SCTree
        Fully wired tree with init_psi() already called.
    """
    from wom.data.schema import Cols

    tree = SCTree(week_labels)
    skus = sku_master[Cols.SKU_ID].unique().tolist()

    for sku_id in skus:
        sku_rows = sku_master[sku_master[Cols.SKU_ID] == sku_id]
        regions  = sku_rows[Cols.REGION].tolist()

        # -- OutBound tree -------------------------------------------------
        sp = PlanNode(
            node_id   = f"SP:{sku_id}",
            node_name = f"Supply Point [{sku_id}]",
            product   = sku_id,
            side      = "outbound",
            node_type = NODE_TYPE_SUPPLY_POINT,
            tier      = 0,
            lt_wks    = 0,
            cpu_size  = cpu_size,
        )

        for region in regions:
            lt = int(
                sku_rows.loc[sku_rows[Cols.REGION] == region, Cols.LT_WKS]
                .values[0]
            ) if Cols.LT_WKS in sku_rows.columns else lt_wks_ot

            dad = PlanNode(
                node_id   = f"OUT:DC:{region}:{sku_id}",
                node_name = f"DC {region} [{sku_id}]",
                product   = sku_id,
                side      = "outbound",
                node_type = NODE_TYPE_DAD,
                tier      = 0,
                lt_wks    = max(lt, 1),
                cpu_size  = cpu_size,
            )
            leaf_out = PlanNode(
                node_id   = f"OUT:Sales:{region}:{sku_id}",
                node_name = f"Sales {region} [{sku_id}]",
                product   = sku_id,
                side      = "outbound",
                node_type = NODE_TYPE_LEAF_OUT,
                tier      = 1,
                lt_wks    = 1,
                cpu_size  = cpu_size,
            )
            dad.add_child(leaf_out)
            sp.add_child(dad)

        # -- InBound tree --------------------------------------------------
        mom = PlanNode(
            node_id   = f"IN:MFG:{sku_id}",
            node_name = f"Mother Plant [{sku_id}]",
            product   = sku_id,
            side      = "inbound",
            node_type = NODE_TYPE_MOM,
            tier      = 0,
            lt_wks    = lt_wks_in,
            cpu_size  = cpu_size,
        )
        tier1 = PlanNode(
            node_id   = f"IN:T1:{sku_id}",
            node_name = f"Tier-1 Supplier [{sku_id}]",
            product   = sku_id,
            side      = "inbound",
            node_type = NODE_TYPE_MOM,
            tier      = 1,
            lt_wks    = lt_wks_in,
            cpu_size  = cpu_size,
        )
        raw_mat = PlanNode(
            node_id   = f"IN:RAW:{sku_id}",
            node_name = f"Raw Material [{sku_id}]",
            product   = sku_id,
            side      = "inbound",
            node_type = NODE_TYPE_LEAF_IN,
            tier      = 2,
            lt_wks    = 1,
            cpu_size  = cpu_size,
        )
        tier1.add_child(raw_mat)
        mom.add_child(tier1)

        # -- Register & initialise -----------------------------------------
        tree.register(sku_id, ot_root=sp, in_root=mom)

    tree.init_all_psi()
    return tree
