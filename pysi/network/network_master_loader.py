from __future__ import annotations

import csv
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NODE_REQUIRED_COLUMNS = {
    "scenario_id",
    "node_name",
    "display_name",
    "node_character",
    "node_role",
    "tree_side",
    "product_name",
    "is_root",
    "is_supply_point",
    "is_mom",
    "is_dad",
    "is_leaf",
    "is_supplier_leaf",
    "is_market_leaf",
    "is_procurement_center",
    "is_global_sales_office",
    "position_group",
    "partner_key",
    "e2e_stage",
    "priority",
    "comment",
}

EDGE_REQUIRED_COLUMNS = {
    "scenario_id",
    "product_name",
    "tree_side",
    "parent_node",
    "child_node",
    "edge_type",
    "edge_role",
    "leadtime",
    "process_capa",
    "transport_capacity_qty",
    "unit",
    "priority",
    "calendar_id",
    "comment",
}


@dataclass(frozen=True)
class NetworkNodeRow:
    """Canonical node_master.csv row for the WOM E2E hammock network slice."""

    scenario_id: str
    node_name: str
    display_name: str
    node_character: str
    node_role: str
    tree_side: str
    product_id: str
    is_root: bool = False
    is_supply_point: bool = False
    is_mom: bool = False
    is_dad: bool = False
    is_leaf: bool = False
    is_supplier_leaf: bool = False
    is_market_leaf: bool = False
    is_procurement_center: bool = False
    is_global_sales_office: bool = False
    position_group: str | None = None
    partner_key: str | None = None
    e2e_stage: int | None = None
    priority: int | None = None
    comment: str | None = None

    @property
    def product_name(self) -> str:
        return self.product_id


@dataclass(frozen=True)
class NetworkEdgeRow:
    """Canonical network_master.csv parent-child relationship row."""

    scenario_id: str
    product_id: str
    tree_side: str
    parent_node: str
    child_node: str
    edge_type: str
    edge_role: str
    leadtime: int
    process_capa: int | float | None = None
    transport_capacity_qty: int | float | None = None
    unit: str = "lot"
    priority: int | None = None
    calendar_id: str | None = None
    comment: str | None = None

    @property
    def product_name(self) -> str:
        return self.product_id


def _required_str(row: dict[str, str], key: str, row_num: int) -> str:
    value = str(row.get(key, "") or "").strip()
    if value == "":
        raise ValueError(f"{key} is required (row {row_num})")
    return value


def _optional_str(row: dict[str, str], key: str) -> str | None:
    value = str(row.get(key, "") or "").strip()
    return value or None


def _parse_bool(raw_value: Any, *, row_num: int, key: str) -> bool:
    value = str(raw_value if raw_value is not None else "").strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no", ""}:
        return False
    raise ValueError(f"{key} must be boolean-like (row {row_num}, value={value!r})")


def _parse_optional_int(raw_value: Any, *, row_num: int, key: str) -> int | None:
    value = str(raw_value if raw_value is not None else "").strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer (row {row_num}, value={value!r})") from exc


def _parse_required_int(raw_value: Any, *, row_num: int, key: str) -> int:
    parsed = _parse_optional_int(raw_value, row_num=row_num, key=key)
    if parsed is None:
        raise ValueError(f"{key} is required (row {row_num})")
    return parsed


def _parse_optional_number(raw_value: Any, *, row_num: int, key: str) -> int | float | None:
    value = str(raw_value if raw_value is not None else "").strip()
    if value == "":
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be numeric (row {row_num}, value={value!r})") from exc
    if parsed.is_integer():
        return int(parsed)
    return parsed


def load_network_node_master_csv(path: str | Path) -> list[NetworkNodeRow]:
    """Load node_master.csv rows without mutating planner or GUI state.

    MOM/DAD roles are determined from node_character semantics. The boolean
    columns are preserved, but arbitrary node names such as RICE_MILL_A and
    DC_KANTO do not need MOM/DAD prefixes to be recognized as those roles.
    """

    csv_path = Path(path)
    if not csv_path.exists():
        raise ValueError(f"network node master csv not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("network node master csv has no header")

        missing = NODE_REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"network node master csv missing required columns: {sorted(missing)}")

        rows: list[NetworkNodeRow] = []
        for row_num, row in enumerate(reader, start=2):
            node_character = _required_str(row, "node_character", row_num)
            rows.append(
                NetworkNodeRow(
                    scenario_id=_required_str(row, "scenario_id", row_num),
                    node_name=_required_str(row, "node_name", row_num),
                    display_name=_required_str(row, "display_name", row_num),
                    node_character=node_character,
                    node_role=_required_str(row, "node_role", row_num),
                    tree_side=_required_str(row, "tree_side", row_num),
                    product_id=_required_str(row, "product_name", row_num),
                    is_root=_parse_bool(row.get("is_root"), row_num=row_num, key="is_root"),
                    is_supply_point=(
                        _parse_bool(row.get("is_supply_point"), row_num=row_num, key="is_supply_point")
                        or node_character == "SUPPLY_POINT"
                    ),
                    is_mom=(
                        _parse_bool(row.get("is_mom"), row_num=row_num, key="is_mom")
                        or node_character == "MOM"
                    ),
                    is_dad=(
                        _parse_bool(row.get("is_dad"), row_num=row_num, key="is_dad")
                        or node_character == "DAD"
                    ),
                    is_leaf=_parse_bool(row.get("is_leaf"), row_num=row_num, key="is_leaf"),
                    is_supplier_leaf=(
                        _parse_bool(row.get("is_supplier_leaf"), row_num=row_num, key="is_supplier_leaf")
                        or node_character == "SUPPLIER_LEAF"
                    ),
                    is_market_leaf=(
                        _parse_bool(row.get("is_market_leaf"), row_num=row_num, key="is_market_leaf")
                        or node_character == "MARKET_LEAF"
                    ),
                    is_procurement_center=(
                        _parse_bool(
                            row.get("is_procurement_center"),
                            row_num=row_num,
                            key="is_procurement_center",
                        )
                        or node_character == "PROCUREMENT_CENTER"
                    ),
                    is_global_sales_office=(
                        _parse_bool(
                            row.get("is_global_sales_office"),
                            row_num=row_num,
                            key="is_global_sales_office",
                        )
                        or node_character == "GLOBAL_SALES_OFFICE"
                    ),
                    position_group=_optional_str(row, "position_group"),
                    partner_key=_optional_str(row, "partner_key"),
                    e2e_stage=_parse_optional_int(row.get("e2e_stage"), row_num=row_num, key="e2e_stage"),
                    priority=_parse_optional_int(row.get("priority"), row_num=row_num, key="priority"),
                    comment=_optional_str(row, "comment"),
                )
            )
    return rows


def load_network_edge_master_csv(path: str | Path) -> list[NetworkEdgeRow]:
    """Load network_master.csv parent-child rows without building a PySI tree."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise ValueError(f"network edge master csv not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("network edge master csv has no header")

        missing = EDGE_REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"network edge master csv missing required columns: {sorted(missing)}")

        rows: list[NetworkEdgeRow] = []
        for row_num, row in enumerate(reader, start=2):
            rows.append(
                NetworkEdgeRow(
                    scenario_id=_required_str(row, "scenario_id", row_num),
                    product_id=_required_str(row, "product_name", row_num),
                    tree_side=_required_str(row, "tree_side", row_num),
                    parent_node=_required_str(row, "parent_node", row_num),
                    child_node=_required_str(row, "child_node", row_num),
                    edge_type=_required_str(row, "edge_type", row_num),
                    edge_role=_required_str(row, "edge_role", row_num),
                    leadtime=_parse_required_int(row.get("leadtime"), row_num=row_num, key="leadtime"),
                    process_capa=_parse_optional_number(
                        row.get("process_capa"), row_num=row_num, key="process_capa"
                    ),
                    transport_capacity_qty=_parse_optional_number(
                        row.get("transport_capacity_qty"),
                        row_num=row_num,
                        key="transport_capacity_qty",
                    ),
                    unit=_required_str(row, "unit", row_num),
                    priority=_parse_optional_int(row.get("priority"), row_num=row_num, key="priority"),
                    calendar_id=_optional_str(row, "calendar_id"),
                    comment=_optional_str(row, "comment"),
                )
            )
    return rows


def load_network_master_package(scenario_root: str | Path) -> dict[str, Any]:
    """Load a scenario's network master package as pure data rows and summary."""

    root = Path(scenario_root)
    node_path = root / "masters" / "node_master.csv"
    edge_path = root / "masters" / "network_master.csv"
    nodes = load_network_node_master_csv(node_path)
    edges = load_network_edge_master_csv(edge_path)
    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_master_path": str(node_path),
            "network_master_path": str(edge_path),
            "tree_sides": sorted({edge.tree_side for edge in edges}),
        },
    }


def find_node(nodes: list[NetworkNodeRow], node_name: str) -> NetworkNodeRow | None:
    for node in nodes:
        if node.node_name == node_name:
            return node
    return None


def edges_by_tree_side(edges: list[NetworkEdgeRow], tree_side: str) -> list[NetworkEdgeRow]:
    return [edge for edge in edges if edge.tree_side == tree_side]


def has_path(edges: list[NetworkEdgeRow], path: list[str], tree_side: str) -> bool:
    if len(path) < 2:
        return True
    edge_pairs = {
        (edge.parent_node, edge.child_node)
        for edge in edges_by_tree_side(edges, tree_side)
    }
    return all((parent, child) in edge_pairs for parent, child in zip(path, path[1:]))


def derive_tree_depths(
    edges: list[NetworkEdgeRow], root_node: str, tree_side: str
) -> dict[str, int]:
    """Derive default layout depths from parent-child tree structure using BFS."""

    adjacency: dict[str, list[str]] = {}
    for edge in edges_by_tree_side(edges, tree_side):
        adjacency.setdefault(edge.parent_node, []).append(edge.child_node)

    depths = {root_node: 0}
    queue: deque[str] = deque([root_node])
    while queue:
        parent = queue.popleft()
        for child in adjacency.get(parent, []):
            if child in depths:
                continue
            depths[child] = depths[parent] + 1
            queue.append(child)
    return depths
