from __future__ import annotations

from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pysi.capacity.capacity_weekly_rows_source import load_capacity_weekly_rows_to_env
from pysi.demand import (
    attach_demand_lots_to_leaf_plan_node_psi4demand,
    generate_demand_anchored_lots,
    load_weekly_demand_master_csv,
)
from pysi.network import find_node, has_path, load_network_master_package
from pysi.plan.capacity_constrained_first_flow import (
    run_japanese_rice_capacity_constrained_first_flow,
)
from pysi.plan.plan_node_tree_instantiation import (
    LEGACY_PSI_DEMAND_S_INDEX,
    instantiate_japanese_rice_plan_node_tree_and_attach_demand,
)
from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    apply_capacity_runtime_attachment_preflight,
)

SCENARIO_ID = "JAPANESE_RICE_VSLICE_001"
PRODUCT_NAME = "JAPANESE_RICE_STANDARD"
EXPECTED_WEEKS = ["2027-W40", "2027-W41", "2027-W42"]
DEMAND_NODE = "MARKET_TOKYO"
MOM_NODE = "RICE_MILL_A"
DAD_NODE = "DC_KANTO"
SUPPLY_SOURCE_NODE = "FARM_REGION_A"
SUPPLY_POINT_NODE = "supply_point"
PARTNER_KEY = "RICE_CORE"

INBOUND_HAMMOCK_PATH = [
    "supply_side_root",
    SUPPLY_POINT_NODE,
    MOM_NODE,
    SUPPLY_SOURCE_NODE,
    "Procurement_Center",
]
OUTBOUND_HAMMOCK_PATH = [
    "demand_side_root",
    SUPPLY_POINT_NODE,
    DAD_NODE,
    DEMAND_NODE,
    "Global_Sales_Office",
]

BALANCE_CAPACITY_SLOTS = {
    DAD_NODE: "S",
    MOM_NODE: "P",
    SUPPLY_SOURCE_NODE: "P",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _capacity_by_node_type_week(
    capacity_rows: list[Any],
) -> dict[tuple[str, str, str], int | float]:
    lookup: dict[tuple[str, str, str], int | float] = {}
    for row in capacity_rows:
        if row.product_name != PRODUCT_NAME:
            continue
        lookup[(row.node_name, row.capacity_type, row.week)] = row.capacity_qty
    return lookup


def _compute_weekly_balance(
    *,
    weekly_lot_counts: dict[str, int],
    capacity_rows: list[Any],
) -> dict[str, dict[str, dict[str, int | float]]]:
    capacity_lookup = _capacity_by_node_type_week(capacity_rows)
    balance: dict[str, dict[str, dict[str, int | float]]] = {}

    for node_name, capacity_type in BALANCE_CAPACITY_SLOTS.items():
        node_balance: dict[str, dict[str, int | float]] = {}
        for week in EXPECTED_WEEKS:
            demand = weekly_lot_counts[week]
            capacity = capacity_lookup[(node_name, capacity_type, week)]
            week_balance = capacity - demand
            node_balance[week] = {
                "demand": demand,
                "capacity": capacity,
                "balance": week_balance,
                "shortage": max(0, -week_balance),
            }
        balance[node_name] = node_balance

    return balance


def _extract_capacity_context_summary(preflight_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_attachment_applied": preflight_result.get("applied") is True,
        "input_row_count": preflight_result.get("input_row_count", 0),
        "row_source": preflight_result.get("row_source"),
    }


def _build_actual_plan_node_tree_diagnostic(
    scenario_root: Path,
) -> dict[str, Any]:
    tree_result = instantiate_japanese_rice_plan_node_tree_and_attach_demand(scenario_root)
    summary = tree_result["summary"]
    market_tokyo = tree_result["market_tokyo"]
    weekly_s_slot_counts = {
        week: len(market_tokyo.psi4demand[week][LEGACY_PSI_DEMAND_S_INDEX])
        for week in EXPECTED_WEEKS
    }

    return {
        "available": True,
        "product_name": PRODUCT_NAME,
        "inbound_node_count": summary["inbound_node_count"],
        "outbound_node_count": summary["outbound_node_count"],
        "demand_node": DEMAND_NODE,
        "demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]",
        "weekly_s_slot_counts": weekly_s_slot_counts,
    }


def _build_capacity_constrained_first_flow_diagnostic(
    scenario_root: Path,
) -> dict[str, Any]:
    flow_result = run_japanese_rice_capacity_constrained_first_flow(scenario_root)
    flow = flow_result["flow"]

    return {
        "available": flow_result["available"],
        "run_mode": flow_result["run_mode"],
        "full_psi_plan": flow_result["full_psi_plan"],
        "capacity_node": flow["capacity_node"],
        "demand_node": flow["demand_node"],
        "capacity_type": flow["capacity_type"],
        "demand_lot_source": flow["demand_lot_source"],
        "weeks": flow_result["weeks"],
        "weekly": flow_result["weekly"],
        "totals": flow_result["totals"],
    }


def run_japanese_rice_first_psi_vslice(scenario_root: str | Path) -> dict[str, Any]:
    """Run the Japanese Rice diagnostic-first PSI smoke vertical slice.

    This runner intentionally stops at an integration diagnostic boundary. It
    loads the Japanese Rice capacity, demand, and network masters, attaches the
    already-supported compatibility structures, verifies cross-master alignment,
    and computes a same-week demand-vs-capacity balance. It does not perform a
    full WOM PSI plan, lead-time propagation, inventory carry-over, backlog, or
    optimization.
    """

    root = Path(scenario_root)

    network_package = load_network_master_package(root)
    nodes = network_package["nodes"]
    edges = network_package["edges"]

    demand_rows = load_weekly_demand_master_csv(root / "masters" / "demand_master.csv")
    demand_lots = generate_demand_anchored_lots(demand_rows)
    leaf_compatibility = attach_demand_lots_to_leaf_plan_node_psi4demand(demand_lots)

    env = SimpleNamespace(product_selected=PRODUCT_NAME)
    load_capacity_weekly_rows_to_env(env, scenario_root=root, required=True)
    capacity_preflight = apply_capacity_runtime_attachment_preflight(env)
    capacity_rows = list(env.capacity_weekly_rows)

    node_names = {node.node_name for node in nodes}
    _require(
        DEMAND_NODE in node_names,
        f"demand node is missing from network: {DEMAND_NODE}",
    )
    for node_name in (SUPPLY_SOURCE_NODE, MOM_NODE, DAD_NODE):
        _require(node_name in node_names, f"capacity node is missing from network: {node_name}")

    _require(
        {row.scenario_id for row in demand_rows} == {SCENARIO_ID},
        "unexpected demand scenario_id",
    )
    _require(
        {row.product_name for row in demand_rows} == {PRODUCT_NAME},
        "unexpected demand product",
    )
    _require(
        {row.scenario_id for row in capacity_rows} == {SCENARIO_ID},
        "unexpected capacity scenario_id",
    )
    _require(
        {row.product_name for row in capacity_rows} == {PRODUCT_NAME},
        "unexpected capacity product",
    )
    _require(
        {node.scenario_id for node in nodes} == {SCENARIO_ID},
        "unexpected network node scenario_id",
    )
    _require(
        {edge.scenario_id for edge in edges} == {SCENARIO_ID},
        "unexpected network edge scenario_id",
    )
    _require(
        {node.product_name for node in nodes} == {PRODUCT_NAME},
        "unexpected network node product",
    )
    _require(
        {edge.product_name for edge in edges} == {PRODUCT_NAME},
        "unexpected network edge product",
    )

    supply_point = find_node(nodes, SUPPLY_POINT_NODE)
    mom_node = find_node(nodes, MOM_NODE)
    dad_node = find_node(nodes, DAD_NODE)
    market_leaf = find_node(nodes, DEMAND_NODE)
    supply_source = find_node(nodes, SUPPLY_SOURCE_NODE)
    _require(
        supply_point is not None and supply_point.node_character == "SUPPLY_POINT",
        "invalid supply point role",
    )
    _require(
        mom_node is not None and mom_node.node_character == "MOM",
        "invalid MOM role",
    )
    _require(
        dad_node is not None and dad_node.node_character == "DAD",
        "invalid DAD role",
    )
    _require(
        market_leaf is not None and market_leaf.node_character == "MARKET_LEAF",
        "invalid market leaf role",
    )
    _require(
        supply_source is not None and supply_source.node_character == "SUPPLIER_LEAF",
        "invalid supplier leaf role",
    )
    _require(mom_node.partner_key == PARTNER_KEY, "unexpected MOM partner_key")
    _require(dad_node.partner_key == PARTNER_KEY, "unexpected DAD partner_key")

    inbound_path_exists = has_path(edges, INBOUND_HAMMOCK_PATH, tree_side="inbound")
    outbound_path_exists = has_path(edges, OUTBOUND_HAMMOCK_PATH, tree_side="outbound")
    _require(inbound_path_exists, "inbound hammock path is missing")
    _require(outbound_path_exists, "outbound hammock path is missing")

    weekly_lot_counts = dict(Counter(lot.demand_week for lot in demand_lots))
    weekly_lot_counts = {week: weekly_lot_counts.get(week, 0) for week in EXPECTED_WEEKS}
    leaf_plan_node = leaf_compatibility[PRODUCT_NAME][DEMAND_NODE]
    psi4demand_counts = {
        week: len(leaf_plan_node["psi4demand"][week]["S"])
        for week in EXPECTED_WEEKS
    }
    _require(
        psi4demand_counts == weekly_lot_counts,
        "demand lot compatibility attachment mismatch",
    )

    balance = _compute_weekly_balance(
        weekly_lot_counts=weekly_lot_counts,
        capacity_rows=capacity_rows,
    )
    actual_plan_node_tree = _build_actual_plan_node_tree_diagnostic(root)
    capacity_constrained_first_flow = _build_capacity_constrained_first_flow_diagnostic(root)

    return {
        "scenario_id": SCENARIO_ID,
        "product_name": PRODUCT_NAME,
        "available": True,
        "run_mode": "diagnostic_first_psi_smoke",
        "full_psi_plan": False,
        "masters": {
            "capacity_rows": len(capacity_rows),
            "demand_rows": len(demand_rows),
            "demand_lots": len(demand_lots),
            "network_nodes": network_package["summary"]["node_count"],
            "network_edges": network_package["summary"]["edge_count"],
        },
        "weeks": list(EXPECTED_WEEKS),
        "demand": {
            "node": DEMAND_NODE,
            "weekly_lot_counts": weekly_lot_counts,
            "total_lots": len(demand_lots),
            "leaf_plan_node_psi4demand_counts": psi4demand_counts,
            "leaf_plan_node_compatibility": leaf_plan_node,
        },
        "network": {
            "inbound_path_exists": inbound_path_exists,
            "outbound_path_exists": outbound_path_exists,
            "mom_node": MOM_NODE,
            "dad_node": DAD_NODE,
            "partner_key": PARTNER_KEY,
            "market_leaf": DEMAND_NODE,
            "supply_point": SUPPLY_POINT_NODE,
            "supply_source": SUPPLY_SOURCE_NODE,
        },
        "capacity": _extract_capacity_context_summary(capacity_preflight),
        "actual_plan_node_tree": actual_plan_node_tree,
        "capacity_constrained_first_flow": capacity_constrained_first_flow,
        "balance": balance,
        "most_restrictive_node": DAD_NODE,
        "messages": [
            "Japanese Rice first PSI vertical slice: masters loaded.",
            "Japanese Rice first PSI vertical slice: demand lots attached to MARKET_TOKYO leaf.",
            "Japanese Rice first PSI vertical slice: capacity runtime context attached.",
            "Japanese Rice first PSI vertical slice: network hammock paths verified.",
            "Japanese Rice first PSI vertical slice: simple weekly balance computed.",
            "Japanese Rice first PSI vertical slice: actual ProductPlanNode tree instantiated.",
            "Japanese Rice first PSI vertical slice: MARKET_TOKYO.psi4demand[week][0] verified.",
            "Japanese Rice first PSI vertical slice: DC_KANTO capacity-constrained first flow attached.",
        ],
    }


__all__ = ["run_japanese_rice_first_psi_vslice"]
