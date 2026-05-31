from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from pysi.demand.demand_lot_generator import (
    DemandAnchoredLot,
    generate_demand_anchored_lots,
)
from pysi.demand.demand_master_loader import load_weekly_demand_master_csv
from pysi.network.network_master_loader import (
    NetworkEdgeRow,
    NetworkNodeRow,
    derive_tree_depths,
    load_network_master_package,
)

LEGACY_PSI_DEMAND_SLOT_NAMES = ("S", "CO", "I", "P")
LEGACY_PSI_DEMAND_S_INDEX = 0


@dataclass
class ProductPlanNode:
    """Runtime product-specific planning-layer node for vertical-slice PSI seeding.

    A planning node is intentionally identified by scenario, product, tree side,
    and node name.  This lets the inbound and outbound ``supply_point`` rows
    become distinct runtime objects even though they share the same master node
    name and canonical node character.
    """

    scenario_id: str
    product_name: str
    tree_side: str
    node_name: str
    node_character: str
    node_role: str | None = None
    parent: "ProductPlanNode | None" = None
    children: list["ProductPlanNode"] = field(default_factory=list)
    partner_key: str | None = None
    position_group: str | None = None
    depth: int | None = None
    is_root: bool = False
    is_leaf: bool = False
    is_mom: bool = False
    is_dad: bool = False
    is_supply_point: bool = False
    is_supplier_leaf: bool = False
    is_market_leaf: bool = False
    is_procurement_center: bool = False
    is_global_sales_office: bool = False
    psi4demand: dict[str, list[list[str]]] = field(default_factory=dict)
    psi4supply: dict[str, list[list[str]]] = field(default_factory=dict)

    @property
    def identity_key(self) -> tuple[str, str, str, str]:
        return (self.scenario_id, self.product_name, self.tree_side, self.node_name)


def _node_row_matches_side(row: NetworkNodeRow, tree_side: str) -> bool:
    return row.tree_side == tree_side or row.tree_side == "both"


def _node_rows_by_name_for_side(
    nodes: Iterable[NetworkNodeRow],
    *,
    scenario_id: str,
    product_name: str,
    tree_side: str,
) -> dict[str, NetworkNodeRow]:
    rows_by_name: dict[str, NetworkNodeRow] = {}
    for row in nodes:
        if row.scenario_id != scenario_id or row.product_name != product_name:
            continue
        if not _node_row_matches_side(row, tree_side):
            continue
        if row.node_name in rows_by_name:
            raise ValueError(
                "duplicate network node row for product plan tree side: "
                f"{scenario_id}/{product_name}/{tree_side}/{row.node_name}"
            )
        rows_by_name[row.node_name] = row
    return rows_by_name


def _edge_rows_for_side(
    edges: Iterable[NetworkEdgeRow],
    *,
    scenario_id: str,
    product_name: str,
    tree_side: str,
) -> list[NetworkEdgeRow]:
    return [
        edge
        for edge in edges
        if edge.scenario_id == scenario_id
        and edge.product_name == product_name
        and edge.tree_side == tree_side
    ]


def _find_tree_root(node_rows: dict[str, NetworkNodeRow], edge_rows: list[NetworkEdgeRow]) -> str:
    root_candidates = [row.node_name for row in node_rows.values() if row.is_root]
    if len(root_candidates) == 1:
        return root_candidates[0]
    if len(root_candidates) > 1:
        raise ValueError(f"multiple root node rows found: {sorted(root_candidates)}")

    child_names = {edge.child_node for edge in edge_rows}
    derived_roots = sorted({edge.parent_node for edge in edge_rows} - child_names)
    if len(derived_roots) != 1:
        raise ValueError(f"could not derive a unique root from edges: {derived_roots}")
    return derived_roots[0]


def _make_product_plan_node(
    row: NetworkNodeRow,
    *,
    scenario_id: str,
    product_name: str,
    tree_side: str,
    depth: int | None,
) -> ProductPlanNode:
    return ProductPlanNode(
        scenario_id=scenario_id,
        product_name=product_name,
        tree_side=tree_side,
        node_name=row.node_name,
        node_character=row.node_character,
        node_role=row.node_role,
        partner_key=row.partner_key,
        position_group=row.position_group,
        depth=depth,
        is_root=row.is_root,
        is_leaf=row.is_leaf,
        is_mom=row.is_mom,
        is_dad=row.is_dad,
        is_supply_point=row.is_supply_point,
        is_supplier_leaf=row.is_supplier_leaf,
        is_market_leaf=row.is_market_leaf,
        is_procurement_center=row.is_procurement_center,
        is_global_sales_office=row.is_global_sales_office,
    )


def _instantiate_tree_side(
    *,
    scenario_id: str,
    product_name: str,
    tree_side: str,
    nodes: list[NetworkNodeRow],
    edges: list[NetworkEdgeRow],
) -> dict[str, Any]:
    edge_rows = _edge_rows_for_side(
        edges, scenario_id=scenario_id, product_name=product_name, tree_side=tree_side
    )
    node_rows = _node_rows_by_name_for_side(
        nodes, scenario_id=scenario_id, product_name=product_name, tree_side=tree_side
    )
    if not edge_rows:
        raise ValueError(f"no network edges found for {scenario_id}/{product_name}/{tree_side}")

    edge_node_names = {edge.parent_node for edge in edge_rows} | {
        edge.child_node for edge in edge_rows
    }
    missing_nodes = sorted(edge_node_names - set(node_rows))
    if missing_nodes:
        raise ValueError(
            f"network edges reference missing node_master rows for {tree_side}: {missing_nodes}"
        )

    root_node_name = _find_tree_root(node_rows, edge_rows)
    depths = derive_tree_depths(edge_rows, root_node=root_node_name, tree_side=tree_side)
    unreachable_nodes = sorted(edge_node_names - set(depths))
    if unreachable_nodes:
        raise ValueError(f"nodes are not reachable from {root_node_name}: {unreachable_nodes}")

    plan_nodes = {
        node_name: _make_product_plan_node(
            node_rows[node_name],
            scenario_id=scenario_id,
            product_name=product_name,
            tree_side=tree_side,
            depth=depths.get(node_name),
        )
        for node_name in sorted(edge_node_names, key=lambda name: (depths.get(name, 10_000), name))
    }

    children_by_parent: dict[str, list[NetworkEdgeRow]] = defaultdict(list)
    for edge in edge_rows:
        children_by_parent[edge.parent_node].append(edge)
    for parent_name, child_edges in children_by_parent.items():
        parent = plan_nodes[parent_name]
        for edge in sorted(child_edges, key=lambda item: (item.priority or 0, item.child_node)):
            child = plan_nodes[edge.child_node]
            if child.parent is not None:
                raise ValueError(
                    f"node has multiple parents in {tree_side} tree: {child.node_name}"
                )
            child.parent = parent
            parent.children.append(child)

    return {
        "root": plan_nodes[root_node_name],
        "nodes": plan_nodes,
        "tree_side": tree_side,
        "root_node_name": root_node_name,
        "node_count": len(plan_nodes),
    }


def instantiate_product_plan_node_trees(
    *,
    scenario_id: str,
    product_name: str,
    nodes: list[NetworkNodeRow],
    edges: list[NetworkEdgeRow],
) -> dict[str, Any]:
    """Instantiate inbound and outbound product-specific plan_node trees."""

    inbound = _instantiate_tree_side(
        scenario_id=scenario_id,
        product_name=product_name,
        tree_side="inbound",
        nodes=nodes,
        edges=edges,
    )
    outbound = _instantiate_tree_side(
        scenario_id=scenario_id,
        product_name=product_name,
        tree_side="outbound",
        nodes=nodes,
        edges=edges,
    )
    return {
        "scenario_id": scenario_id,
        "product_name": product_name,
        "inbound": inbound,
        "outbound": outbound,
        "summary": {
            "scenario_id": scenario_id,
            "product_name": product_name,
            "inbound_node_count": inbound["node_count"],
            "outbound_node_count": outbound["node_count"],
        },
    }


def ensure_psi_week_slots(
    plan_node: ProductPlanNode,
    week: str,
    *,
    psi_attr: str = "psi4demand",
) -> list[list[str]]:
    """Ensure a legacy four-slot PSI week bucket and return it.

    The list order is ``[S, CO, I, P]``; slot index ``0`` is the legacy demand
    ``S`` slot used by this vertical slice.
    """

    psi = getattr(plan_node, psi_attr)
    slots = psi.get(week)
    if slots is None:
        slots = [[], [], [], []]
        psi[week] = slots
    if not isinstance(slots, list):
        raise TypeError(f"{psi_attr}[{week!r}] must be a legacy PSI slot list")
    while len(slots) < len(LEGACY_PSI_DEMAND_SLOT_NAMES):
        slots.append([])
    if len(slots) != len(LEGACY_PSI_DEMAND_SLOT_NAMES):
        raise ValueError(
            f"{psi_attr}[{week!r}] must have exactly 4 legacy PSI slots, got {len(slots)}"
        )
    for index, slot in enumerate(slots):
        if not isinstance(slot, list):
            raise TypeError(f"{psi_attr}[{week!r}][{index}] must be a list")
    return slots


def _lot_anchor_node(lot: DemandAnchoredLot) -> str:
    return lot.anchor_node or lot.demand_node


def attach_demand_lots_to_actual_plan_node_psi4demand(
    plan_node: ProductPlanNode,
    lots: list[DemandAnchoredLot],
) -> dict[str, Any]:
    """Attach matching demand lot IDs to an actual outbound plan_node S slot."""

    matching_lots = [
        lot
        for lot in lots
        if lot.scenario_id == plan_node.scenario_id
        and lot.product_name == plan_node.product_name
        and lot.anchor_tree_side == plan_node.tree_side
        and _lot_anchor_node(lot) == plan_node.node_name
    ]

    weekly_lot_counts: dict[str, int] = {}
    for lot in matching_lots:
        slots = ensure_psi_week_slots(plan_node, lot.week, psi_attr="psi4demand")
        slots[LEGACY_PSI_DEMAND_S_INDEX].append(lot.lot_id)
        weekly_lot_counts[lot.week] = weekly_lot_counts.get(lot.week, 0) + 1

    return {
        "attached": bool(matching_lots),
        "node_name": plan_node.node_name,
        "product_name": plan_node.product_name,
        "tree_side": plan_node.tree_side,
        "total_lots": len(matching_lots),
        "weekly_lot_counts": dict(sorted(weekly_lot_counts.items())),
        "psi_slot": LEGACY_PSI_DEMAND_SLOT_NAMES[LEGACY_PSI_DEMAND_S_INDEX],
        "legacy_slot_index": LEGACY_PSI_DEMAND_S_INDEX,
    }


def _find_market_leaf(
    outbound_nodes: dict[str, ProductPlanNode], node_name: str
) -> ProductPlanNode:
    plan_node = outbound_nodes[node_name]
    if not plan_node.is_market_leaf:
        raise ValueError(f"{node_name} is not marked as an outbound market leaf")
    return plan_node


def _collect_tree_node_names(root: ProductPlanNode) -> list[str]:
    names: list[str] = []
    queue: deque[ProductPlanNode] = deque([root])
    while queue:
        node = queue.popleft()
        names.append(node.node_name)
        queue.extend(node.children)
    return names


def instantiate_japanese_rice_plan_node_tree_and_attach_demand(
    scenario_root: str | Path,
) -> dict[str, Any]:
    """Load Japanese Rice masters, instantiate plan_node trees, and attach demand."""

    root = Path(scenario_root)
    network_package = load_network_master_package(root)
    trees = instantiate_product_plan_node_trees(
        scenario_id="JAPANESE_RICE_VSLICE_001",
        product_name="JAPANESE_RICE_STANDARD",
        nodes=network_package["nodes"],
        edges=network_package["edges"],
    )
    demand_rows = load_weekly_demand_master_csv(root / "masters" / "demand_master.csv")
    lots = generate_demand_anchored_lots(demand_rows)
    market_tokyo = _find_market_leaf(trees["outbound"]["nodes"], "MARKET_TOKYO")
    attach_summary = attach_demand_lots_to_actual_plan_node_psi4demand(market_tokyo, lots)
    return {
        "trees": trees,
        "lots": lots,
        "market_tokyo": market_tokyo,
        "attach_summary": attach_summary,
        "summary": {
            **trees["summary"],
            "total_lots": len(lots),
            "inbound_tree_node_names": _collect_tree_node_names(trees["inbound"]["root"]),
            "outbound_tree_node_names": _collect_tree_node_names(trees["outbound"]["root"]),
            "demand_attachment": attach_summary,
        },
    }
