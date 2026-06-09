"""
wom/engine/hammock_layout.py
============================
Attribute-driven E2E Hammock Layout for SCTree PlanNodes.

Ported conceptually from original PySI make_E2E_positions(), but
uses PlanNode.side / node_type / tier attributes instead of
MOM/DAD naming conventions.

Layout axes
-----------
X axis  =  distance from supply_point (bridge)
  supply_point        →  x = 0       (centre)
  OutBound dad/leaf   →  x = +tier   (rightward)
  InBound  mom/leaf   →  x = -(tier+1) (leftward)
  sales_office        →  x = max_ot_depth + 1
  procurement_office  →  x = -(max_in_depth + 2)

Y axis  =  peer position at each X level, centred on 0
  Nodes at the same X level are spaced by Y_SPACING.
  Order is depth-first pre-order within each product.

Virtual nodes
-------------
  "procurement_office"  : left terminus (InBound supply source)
  "sales_office"        : right terminus (OutBound demand sink)

For multi-product trees, products are stacked vertically:
  product index p  →  y_offset = p * PRODUCT_GAP
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from wom.model.plan_node import (
    PlanNode,
    NODE_TYPE_SUPPLY_POINT,
    NODE_TYPE_DAD,
    NODE_TYPE_LEAF_OUT,
    NODE_TYPE_MOM,
    NODE_TYPE_LEAF_IN,
)
from wom.model.sc_tree import SCTree


# ── Layout constants ──────────────────────────────────────────────────────

Y_SPACING    = 1.8   # vertical gap between peer nodes at same X level
PRODUCT_GAP  = 0.0   # vertical gap between products (0 = overlay, >0 = stack)
X_SPACING    = 1.0   # horizontal unit between depth levels

# ── Colour mapping by node_type ───────────────────────────────────────────

NODE_COLOUR = {
    NODE_TYPE_SUPPLY_POINT: "#FFEB3B",   # yellow  – bridge / supply_point
    NODE_TYPE_MOM:          "#66BB6A",   # green   – InBound production nodes
    NODE_TYPE_LEAF_IN:      "#26A69A",   # teal    – InBound leaf (raw material)
    NODE_TYPE_DAD:          "#42A5F5",   # blue    – OutBound DC / warehouse
    NODE_TYPE_LEAF_OUT:     "#AB47BC",   # purple  – OutBound leaf (market)
    "virtual":              "#FF9800",   # orange  – procurement/sales office
}

NODE_SIZE = {
    NODE_TYPE_SUPPLY_POINT: 2400,
    NODE_TYPE_MOM:          1600,
    NODE_TYPE_LEAF_IN:      1200,
    NODE_TYPE_DAD:          1600,
    NODE_TYPE_LEAF_OUT:     1200,
    "virtual":              1000,
}


# ──────────────────────────────────────────────────────────────────────────
# Position computation
# ──────────────────────────────────────────────────────────────────────────

def compute_hammock_positions(
    sc_tree: SCTree,
    prod_nm: Optional[str] = None,
    y_spacing: float = Y_SPACING,
    x_spacing: float = X_SPACING,
) -> Dict[str, Tuple[float, float]]:
    """
    Compute (x, y) layout positions for all nodes of one product.

    Parameters
    ----------
    sc_tree   : built SCTree (init_psi already called)
    prod_nm   : product name; if None, uses sc_tree.products[0]
    y_spacing : vertical gap between peer nodes
    x_spacing : not used in current layout (x = tier index)

    Returns
    -------
    dict  node_id  →  (x, y)
    Also includes virtual IDs "procurement_office" and "sales_office".
    """
    if prod_nm is None:
        prod_nm = sc_tree.products[0]

    # ── Collect all nodes by x-level ──────────────────────────────────
    # x_level → ordered list of (node_id, PlanNode | None)
    x_buckets: Dict[int, List[Tuple[str, Optional[PlanNode]]]] = defaultdict(list)

    # supply_point → x = 0
    sp = sc_tree.get_ot_root(prod_nm)
    x_buckets[0].append((sp.node_id, sp))

    # OutBound nodes (dad, leaf_out) → x = +tier (tier starts at 1 for SP's children)
    for node in sp.walk_preorder():
        if node is sp:
            continue   # already added
        x = node.tier  # tier=1 for dad, tier=2 for leaf_out, etc.
        x_buckets[x].append((node.node_id, node))

    # InBound nodes (mom, leaf_in) → x = -(tier+1)
    in_root = sc_tree.get_in_root(prod_nm)
    for node in in_root.walk_preorder():
        x = -(node.tier + 1)   # in_root(tier=0)→x=-1, tier1→x=-2, ...
        x_buckets[x].append((node.node_id, node))

    # Virtual: find depth extents
    max_ot = max(
        (n.tier for n in sp.walk_preorder() if n is not sp),
        default=1
    )
    max_in = max(
        (n.tier for n in in_root.walk_preorder()),
        default=0
    )
    x_buckets[max_ot + 1].append(("sales_office", None))
    x_buckets[-(max_in + 2)].append(("procurement_office", None))

    # ── Assign y positions ─────────────────────────────────────────────
    positions: Dict[str, Tuple[float, float]] = {}
    for x_level, bucket in x_buckets.items():
        n = len(bucket)
        for i, (node_id, _node) in enumerate(bucket):
            y = (i - (n - 1) / 2) * y_spacing
            positions[node_id] = (float(x_level) * x_spacing, y)

    return positions


def compute_hammock_positions_all(
    sc_tree: SCTree,
    y_spacing: float = Y_SPACING,
    x_spacing: float = X_SPACING,
    product_gap: float = PRODUCT_GAP,
) -> Dict[str, Tuple[float, float]]:
    """
    Compute positions for ALL products.
    Products are separated vertically by product_gap * max_y_extent.
    """
    all_pos: Dict[str, Tuple[float, float]] = {}
    y_offset = 0.0

    for p_idx, prod_nm in enumerate(sc_tree.products):
        prod_pos = compute_hammock_positions(sc_tree, prod_nm,
                                            y_spacing=y_spacing,
                                            x_spacing=x_spacing)
        # Shift y by offset and add product suffix to virtual node IDs
        for node_id, (x, y) in prod_pos.items():
            if node_id in ("sales_office", "procurement_office"):
                uid = f"{node_id}_{prod_nm}"
            else:
                uid = node_id
            all_pos[uid] = (x, y + y_offset)

        # Advance y_offset for next product
        if prod_pos:
            ys = [v[1] for v in prod_pos.values()]
            y_offset += (max(ys) - min(ys) + y_spacing) + product_gap

    return all_pos


# ──────────────────────────────────────────────────────────────────────────
# Graph builder  (NetworkX DiGraph)
# ──────────────────────────────────────────────────────────────────────────

def build_hammock_graph(sc_tree: SCTree, prod_nm: Optional[str] = None):
    """
    Build a NetworkX DiGraph in hammock E2E layout for one product.

    Returns
    -------
    G    : nx.DiGraph  with node attributes { kind, node_type, node_obj }
    pos  : dict  node_id → (x, y)
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx is required: pip install networkx")

    if prod_nm is None:
        prod_nm = sc_tree.products[0]

    G   = nx.DiGraph()
    pos = compute_hammock_positions(sc_tree, prod_nm)

    sp      = sc_tree.get_ot_root(prod_nm)
    in_root = sc_tree.get_in_root(prod_nm)

    # ── Add nodes ─────────────────────────────────────────────────────
    # supply_point
    G.add_node(sp.node_id,
               kind=sp.node_type, node_type=sp.node_type,
               node_obj=sp, label=sp.node_name)

    # OutBound
    for node in sp.walk_preorder():
        if node is sp:
            continue
        G.add_node(node.node_id,
                   kind=node.node_type, node_type=node.node_type,
                   node_obj=node, label=node.node_name)

    # InBound
    for node in in_root.walk_preorder():
        G.add_node(node.node_id,
                   kind=node.node_type, node_type=node.node_type,
                   node_obj=node, label=node.node_name)

    # Virtual terminals
    max_ot = max((n.tier for n in sp.walk_preorder() if n is not sp), default=1)
    max_in = max((n.tier for n in in_root.walk_preorder()), default=0)

    G.add_node("sales_office",
               kind="virtual", node_type="virtual",
               node_obj=None, label="sales\noffice")
    G.add_node("procurement_office",
               kind="virtual", node_type="virtual",
               node_obj=None, label="procurement\noffice")

    # ── Add edges ──────────────────────────────────────────────────────
    # OutBound: parent → child (supply_point is root)
    _add_edges_preorder(G, sp)

    # InBound: parent → child (in_root is root)
    _add_edges_preorder(G, in_root)

    # Bridge: in_root → supply_point
    G.add_edge(in_root.node_id, sp.node_id)

    # Virtual terminals
    for node in sp.walk_preorder():
        if node.node_type == NODE_TYPE_LEAF_OUT:
            G.add_edge(node.node_id, "sales_office")

    for node in in_root.walk_preorder():
        if node.node_type == NODE_TYPE_LEAF_IN:
            G.add_edge("procurement_office", node.node_id)

    return G, pos


def _add_edges_preorder(G, root: PlanNode) -> None:
    """Add parent→child edges for the tree rooted at `root`."""
    for node in root.walk_preorder():
        for child in node.children:
            G.add_edge(node.node_id, child.node_id)


# ──────────────────────────────────────────────────────────────────────────
# Colour / size helpers
# ──────────────────────────────────────────────────────────────────────────

def node_colour(node_type: str, is_selected: bool = False,
                highlight_colour: str = "#FFFF00") -> str:
    if is_selected:
        return highlight_colour
    return NODE_COLOUR.get(node_type, "#607D8B")


def node_size(node_type: str, is_selected: bool = False) -> int:
    if is_selected:
        return 3000
    return NODE_SIZE.get(node_type, 1400)
