from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pysi.capacity.capacity_weekly_rows_source import load_capacity_weekly_rows_to_env
from pysi.plan.plan_node_tree_instantiation import (
    LEGACY_PSI_DEMAND_S_INDEX,
    instantiate_japanese_rice_plan_node_tree_and_attach_demand,
)

SCENARIO_ID = "JAPANESE_RICE_VSLICE_001"
PRODUCT_NAME = "JAPANESE_RICE_STANDARD"
TARGET_WEEKS = ("2027-W40", "2027-W41", "2027-W42")
DEMAND_NODE = "MARKET_TOKYO"
CAPACITY_NODE = "DC_KANTO"
CAPACITY_TYPE = "S"
DEMAND_LOT_SOURCE = "MARKET_TOKYO.psi4demand[week][0]"

_TOTAL_FIELDS = (
    "requested",
    "capacity",
    "accepted",
    "blocked",
    "capacity_usage",
    "unused_capacity",
    "shortage",
)


def _integer_capacity_qty(capacity_qty: int | float, *, context: str) -> int:
    if isinstance(capacity_qty, bool):
        raise ValueError(f"capacity quantity must be an integer lot count ({context})")
    if isinstance(capacity_qty, int):
        return capacity_qty
    if isinstance(capacity_qty, float) and capacity_qty.is_integer():
        return int(capacity_qty)
    raise ValueError(f"capacity quantity must be an integer lot count ({context})")


def split_lots_by_capacity(lot_ids: list[str], capacity_qty: int) -> dict[str, Any]:
    """Split lot IDs into FIFO accepted and blocked lists for a capacity gate."""

    capacity = _integer_capacity_qty(capacity_qty, context="split_lots_by_capacity")
    if capacity < 0:
        raise ValueError("capacity quantity must be non-negative")

    requested_lot_ids = list(lot_ids)
    accepted_lot_ids = requested_lot_ids[:capacity]
    blocked_lot_ids = requested_lot_ids[capacity:]
    accepted = len(accepted_lot_ids)
    blocked = len(blocked_lot_ids)

    return {
        "requested": len(requested_lot_ids),
        "capacity": capacity,
        "accepted": accepted,
        "blocked": blocked,
        "capacity_usage": accepted,
        "unused_capacity": max(capacity - accepted, 0),
        "shortage": blocked,
        "accepted_lot_ids": accepted_lot_ids,
        "blocked_lot_ids": blocked_lot_ids,
    }


def compute_capacity_gate_flow_by_week(
    *,
    demand_lots_by_week: dict[str, list[str]],
    capacity_by_week: dict[str, int],
    capacity_node: str,
    demand_node: str,
    capacity_type: str = CAPACITY_TYPE,
) -> dict[str, Any]:
    """Apply one capacity gate to weekly demand lot IDs without planner side effects."""

    weeks = sorted(demand_lots_by_week)
    weekly: dict[str, dict[str, Any]] = {}
    totals = dict.fromkeys(_TOTAL_FIELDS, 0)

    for week in weeks:
        if week not in capacity_by_week:
            raise ValueError(
                f"missing {capacity_node} {capacity_type} capacity for demand week {week}"
            )
        split = split_lots_by_capacity(demand_lots_by_week[week], capacity_by_week[week])
        split["original_demand_lot_ids"] = list(demand_lots_by_week[week])
        weekly[week] = split
        for field in _TOTAL_FIELDS:
            totals[field] += int(split[field])

    return {
        "flow": {
            "capacity_node": capacity_node,
            "demand_node": demand_node,
            "capacity_type": capacity_type,
            "unit": "lot",
            "demand_lot_source": DEMAND_LOT_SOURCE,
        },
        "weeks": weeks,
        "weekly": weekly,
        "totals": totals,
    }


def _capacity_by_week_from_rows(
    rows: list[Any],
    *,
    scenario_id: str,
    product_name: str,
    capacity_node: str,
    capacity_type: str,
    target_weeks: tuple[str, ...],
) -> dict[str, int]:
    capacity_by_week: dict[str, int] = {week: 0 for week in target_weeks}
    for row in rows:
        if row.scenario_id != scenario_id:
            continue
        if row.product_name != product_name:
            continue
        if row.node_name != capacity_node:
            continue
        if row.capacity_type != capacity_type:
            continue
        if row.week not in capacity_by_week:
            continue
        capacity_by_week[row.week] += _integer_capacity_qty(
            row.capacity_qty,
            context=f"{row.node_name}/{row.capacity_type}/{row.week}",
        )
    missing = [week for week, capacity in capacity_by_week.items() if capacity == 0]
    if missing:
        raise ValueError(
            f"missing {capacity_node} {capacity_type} capacity rows for weeks: {missing}"
        )
    return capacity_by_week


def run_japanese_rice_capacity_constrained_first_flow(
    scenario_root: str | Path,
) -> dict[str, Any]:
    """Run the Japanese Rice lot-level first capacity gate diagnostic.

    This is intentionally a vertical-slice diagnostic, not a full PSI planner.
    Demand lots are read from the actual ``MARKET_TOKYO`` ProductPlanNode at
    ``psi4demand[week][0]`` before applying the ``DC_KANTO`` S capacity gate.
    """

    root = Path(scenario_root)
    tree_result = instantiate_japanese_rice_plan_node_tree_and_attach_demand(root)
    market_tokyo = tree_result["market_tokyo"]

    demand_lots_by_week = {
        week: list(market_tokyo.psi4demand[week][LEGACY_PSI_DEMAND_S_INDEX])
        for week in TARGET_WEEKS
    }

    env = SimpleNamespace()
    capacity_summary = load_capacity_weekly_rows_to_env(
        env,
        scenario_root=root,
        required=True,
    )
    capacity_by_week = _capacity_by_week_from_rows(
        env.capacity_weekly_rows,
        scenario_id=SCENARIO_ID,
        product_name=PRODUCT_NAME,
        capacity_node=CAPACITY_NODE,
        capacity_type=CAPACITY_TYPE,
        target_weeks=TARGET_WEEKS,
    )

    gate_flow = compute_capacity_gate_flow_by_week(
        demand_lots_by_week=demand_lots_by_week,
        capacity_by_week=capacity_by_week,
        capacity_node=CAPACITY_NODE,
        demand_node=DEMAND_NODE,
        capacity_type=CAPACITY_TYPE,
    )

    return {
        "scenario_id": SCENARIO_ID,
        "product_name": PRODUCT_NAME,
        "run_mode": "capacity_constrained_first_flow",
        "full_psi_plan": False,
        "available": True,
        "flow": gate_flow["flow"],
        "weeks": list(TARGET_WEEKS),
        "weekly": gate_flow["weekly"],
        "totals": gate_flow["totals"],
        "capacity_source": capacity_summary,
        "plan_node_tree_summary": tree_result["summary"],
        "messages": [
            "Japanese Rice capacity-constrained first flow: actual plan_node tree loaded.",
            "Japanese Rice capacity-constrained first flow: demand lots read from MARKET_TOKYO.psi4demand[week][0].",
            "Japanese Rice capacity-constrained first flow: DC_KANTO S capacity applied.",
            "Japanese Rice capacity-constrained first flow: accepted / blocked lots computed.",
        ],
    }


__all__ = [
    "split_lots_by_capacity",
    "compute_capacity_gate_flow_by_week",
    "run_japanese_rice_capacity_constrained_first_flow",
]
