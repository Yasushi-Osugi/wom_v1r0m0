"""
wom/engine/sc_tree_builder.py
==============================
Phase B — Multi-tier SCTree builder from CSV master.

Reads a sc_tree_master.csv that describes an arbitrary-depth supply chain
tree (ported from original WOM pysi/network/tree.py  create_tree_set_attribute).

CSV schema (required)
---------------------
    node_name    : str   — unique name within this product (e.g. "Foxconn_CN")
    parent_node  : str   — parent's node_name; empty / NaN means this is a root
    product_name : str   — SKU / product key (matches demand_forecast sku_id)
    node_type    : str   — supply_point | dad | leaf_out | mom | leaf_in
    side         : str   — outbound | inbound
    lt_wks       : int   — lead time in weeks

CSV schema (optional)
---------------------
    cpu_size     : int   — lot size (default 1)
    region       : str   — geographic region; REQUIRED on leaf_out nodes for
                           demand-lot assignment to work (e.g. "AMER")

Tree topology rules
-------------------
OutBound (demand side):
    supply_point  ← OT root (no parent, side=outbound, node_type=supply_point)
      └─ dad(s)   ← distribution centres, warehouses
           └─ leaf_out(s)  ← sales channels; MUST have region

InBound (supply side):
    mom  ← IN root (no parent, side=inbound, node_type=mom)
      └─ mom(s)   ← tier-1, tier-2 suppliers / factories
           └─ leaf_in(s)  ← raw material / component sources

Backward planning order (demand → supply):
    OT postorder → bridge SP→MOM → IN preorder

Forward planning order (supply → demand):
    IN postorder → bridge MOM→SP → OT preorder

Compatibility
-------------
The built SCTree is identical in interface to build_demo_sc_tree() output.
BackwardPlanner, ForwardPlanner, assign_demand_lots_from_dict, and all
downstream KPI engines work unchanged.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from wom.model.plan_node import (
    PlanNode,
    NODE_TYPE_SUPPLY_POINT,
    NODE_TYPE_DAD,
    NODE_TYPE_LEAF_OUT,
    NODE_TYPE_MOM,
    NODE_TYPE_LEAF_IN,
)
from wom.model.sc_tree import SCTree


# ──────────────────────────────────────────────────────────────────────────
# Required / optional columns
# ──────────────────────────────────────────────────────────────────────────

REQUIRED_COLS = {"node_name", "parent_node", "product_name",
                 "node_type", "side", "lt_wks"}


def _is_sc_tree_master(df: pd.DataFrame) -> bool:
    """Return True if df looks like a sc_tree_master (has parent_node column)."""
    return "parent_node" in df.columns and "node_type" in df.columns


# ──────────────────────────────────────────────────────────────────────────
# Node-id builders  (must match _infer_region_from_node convention in
# wom/model/lot_generator.py so demand-lot assignment works correctly)
# ──────────────────────────────────────────────────────────────────────────

def _make_node_id(
    node_type: str,
    side: str,
    node_name: str,
    region: str,
    prod_nm: str,
) -> str:
    """
    Build a node_id that is parseable by lot_generator._infer_region_from_node.

    Convention (from lot_generator.py):
        OT leaf_out :  "OUT:<anything>:<region>:<prod_nm>"
                       →  parts[0]=="OUT", len>=4, region=parts[2]
        All other   :  "OUT:<type>:<name>:<prod_nm>"  or
                       "IN:<type>:<name>:<prod_nm>"
    """
    safe_name = node_name.replace(":", "_")
    safe_prod = prod_nm.replace(":", "_")
    safe_region = region.replace(":", "_") if region else "NA"

    if side == "outbound" and node_type == NODE_TYPE_LEAF_OUT:
        # Must be "OUT:X:REGION:PROD" so parts[2] == region
        return f"OUT:leaf_out:{safe_region}:{safe_prod}"

    prefix = "OUT" if side == "outbound" else "IN"
    return f"{prefix}:{node_type}:{safe_name}:{safe_prod}"


# ──────────────────────────────────────────────────────────────────────────
# Main builder
# ──────────────────────────────────────────────────────────────────────────

def build_sc_tree_from_master(
    df: pd.DataFrame,
    week_labels: List[str],
) -> SCTree:
    """
    Build an arbitrary-depth SCTree from a sc_tree_master DataFrame.

    Parameters
    ----------
    df:
        DataFrame loaded from sc_tree_master.csv.
        Required columns: node_name, parent_node, product_name,
                          node_type, side, lt_wks
        Optional columns: cpu_size, region
    week_labels:
        Ordered ISO week strings for the planning horizon.

    Returns
    -------
    SCTree
        Fully wired and init_psi() called, ready for BackwardPlanner.

    Raises
    ------
    ValueError
        If required columns are missing, or if a product has no supply_point
        or no inbound MOM root.
    """
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(
            f"sc_tree_master is missing required columns: {missing}"
        )

    tree = SCTree(week_labels)

    for prod_nm in df["product_name"].unique():
        prod_df = df[df["product_name"] == prod_nm].copy()
        _build_product_tree(tree, prod_nm, prod_df)

    tree.init_all_psi()
    return tree


def _build_product_tree(
    tree: SCTree,
    prod_nm: str,
    prod_df: pd.DataFrame,
) -> None:
    """Build and register OT + IN trees for one product."""

    nodes: Dict[str, PlanNode] = {}

    # ── Step 1: Create all PlanNode objects ──────────────────────────────
    for _, row in prod_df.iterrows():
        node_name = str(row["node_name"]).strip()
        node_type = str(row["node_type"]).strip()
        side      = str(row["side"]).strip()
        lt_wks    = int(row.get("lt_wks", 1) or 1)
        cpu_size  = int(row.get("cpu_size", 1) or 1)
        region    = str(row.get("region", "") or "").strip()

        node_id = _make_node_id(node_type, side, node_name, region, prod_nm)

        pnode = PlanNode(
            node_id   = node_id,
            node_name = node_name,
            product   = prod_nm,
            side      = side,
            node_type = node_type,
            tier      = 0,       # calculated in Step 3
            lt_wks    = lt_wks,
            cpu_size  = cpu_size,
        )
        nodes[node_name] = pnode

    # ── Step 2: Wire parent → child ──────────────────────────────────────
    for _, row in prod_df.iterrows():
        node_name   = str(row["node_name"]).strip()
        parent_name = str(row.get("parent_node", "") or "").strip()
        if parent_name and parent_name in nodes:
            nodes[parent_name].add_child(nodes[node_name])

    # ── Step 3: Compute tier depth (0 = tree root, increases toward leaf) ─
    for node in nodes.values():
        depth = 0
        n = node
        while n.parent is not None:
            depth += 1
            n = n.parent
        node.tier = depth

    # ── Step 4: Identify OT root (supply_point) and IN root (top MOM) ────
    ot_roots = [
        n for n in nodes.values()
        if n.node_type == NODE_TYPE_SUPPLY_POINT and n.parent is None
    ]
    in_roots = [
        n for n in nodes.values()
        if n.node_type == NODE_TYPE_MOM and n.parent is None
    ]

    if not ot_roots:
        raise ValueError(
            f"Product {prod_nm!r}: no 'supply_point' root found. "
            f"Add a row with node_type='supply_point', parent_node='' "
            f"on the outbound side."
        )
    if not in_roots:
        raise ValueError(
            f"Product {prod_nm!r}: no 'mom' root found. "
            f"Add a row with node_type='mom', parent_node='' "
            f"on the inbound side."
        )
    if len(ot_roots) > 1:
        raise ValueError(
            f"Product {prod_nm!r}: multiple supply_point roots found: "
            f"{[n.node_name for n in ot_roots]}"
        )
    # Multiple top-level MOM roots are allowed for multi-factory scenarios
    # (Production Allocation Policy).  The first MOM (lowest node_id
    # alphabetically, for determinism) is registered as the primary.
    # Additional MOMs are registered via register_extra_mom() and will be
    # routed to by LaneTable during BackwardPlanner Phase 2.
    in_roots_sorted = sorted(in_roots, key=lambda n: n.node_id)
    primary_in_root = in_roots_sorted[0]

    tree.register(prod_nm, ot_root=ot_roots[0], in_root=primary_in_root)

    for extra_mom in in_roots_sorted[1:]:
        tree.register_extra_mom(prod_nm, extra_mom)
        print(f"[SCTreeBuilder] {prod_nm}: extra MOM root registered: {extra_mom.node_id}")


# ──────────────────────────────────────────────────────────────────────────
# Introspection helper
# ──────────────────────────────────────────────────────────────────────────

def print_sc_tree_structure(tree: SCTree) -> None:
    """Print a human-readable tree structure for debugging."""
    for prod_nm in tree.products:
        print(f"\n{'='*60}")
        print(f"Product: {prod_nm}")
        print("  OutBound:")
        _print_node(tree.get_ot_root(prod_nm), indent=4)
        print("  InBound:")
        for mom in tree.get_in_roots(prod_nm).values():
            _print_node(mom, indent=4)


def _print_node(node: PlanNode, indent: int = 0) -> None:
    pad = " " * indent
    print(f"{pad}[{node.node_type}] {node.node_name}  "
          f"(tier={node.tier}, lt={node.lt_wks}w, id={node.node_id})")
    for child in node.children:
        _print_node(child, indent + 4)
