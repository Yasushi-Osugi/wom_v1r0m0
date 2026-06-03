from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

NUMERIC_CAPACITY_GATE_FIELDS = {
    "requested",
    "capacity",
    "accepted",
    "blocked",
    "shortage",
    "unused_capacity",
    "capacity_usage_ratio",
    "blocked_ratio",
    "capacity_usage_pct",
    "blocked_pct",
}
CHART_SERIES_KEYS = ["requested", "capacity", "accepted", "blocked"]
DATASET_ROW_KEYS = [
    "week",
    "requested",
    "capacity",
    "accepted",
    "blocked",
    "shortage",
    "unused_capacity",
    "capacity_usage_ratio",
    "blocked_ratio",
    "capacity_usage_pct",
    "blocked_pct",
]


def load_full_plan_result_json(path: str | Path) -> dict:
    """Load a Run Full Plan JSON result without hiding loader failures."""

    result_path = Path(path)
    with result_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"full_plan_result.json must contain an object: {result_path}")
    return payload


def _convert_csv_value(key: str, value: str | None) -> Any:
    if key not in NUMERIC_CAPACITY_GATE_FIELDS:
        return "" if value is None else value
    if value is None or value == "":
        return 0
    try:
        number = float(value)
    except ValueError:
        return value
    if number.is_integer():
        return int(number)
    return number


def load_visual_capacity_gate_weekly_csv(path: str | Path) -> list[dict]:
    """Load the capacity-gate CSV while preserving row order and numeric values."""

    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            {key: _convert_csv_value(key, value) for key, value in row.items()}
            for row in reader
        ]


def _sum_numeric(rows: list[dict], key: str) -> int | float:
    total: int | float = 0
    for row in rows:
        value = row.get(key, 0)
        if isinstance(value, (int, float)):
            total += value
    return total


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _capacity_totals(rows: list[dict]) -> dict[str, int | float]:
    requested = _sum_numeric(rows, "requested")
    capacity = _sum_numeric(rows, "capacity")
    accepted = _sum_numeric(rows, "accepted")
    blocked = _sum_numeric(rows, "blocked")
    shortage = _sum_numeric(rows, "shortage")
    unused_capacity = _sum_numeric(rows, "unused_capacity")
    capacity_usage_ratio = _ratio(accepted, capacity)
    blocked_ratio = _ratio(blocked, requested)
    return {
        "requested": requested,
        "capacity": capacity,
        "accepted": accepted,
        "blocked": blocked,
        "shortage": shortage,
        "unused_capacity": unused_capacity,
        "capacity_usage_ratio": capacity_usage_ratio,
        "blocked_ratio": blocked_ratio,
        "capacity_usage_pct": capacity_usage_ratio * 100,
        "blocked_pct": blocked_ratio * 100,
    }


def _unavailable_model(reason: str, diagnostics: list[Any] | None = None) -> dict:
    return {
        "available": False,
        "status": "unavailable",
        "reason": reason,
        "rows": [],
        "totals": {},
        "summary_text": f"WOM Run Full Plan graph panel unavailable: {reason}",
        "messages": [],
        "diagnostics": diagnostics or [reason],
    }


def extract_run_full_plan_capacity_gate_graph_model(
    *,
    full_plan_result: dict,
    capacity_gate_rows: list[dict],
) -> dict:
    """Build a graph-panel model from Run Full Plan JSON and capacity CSV rows."""

    if not capacity_gate_rows:
        return _unavailable_model(
            "visual_capacity_gate_weekly.csv contains no capacity gate rows",
            diagnostics=list(full_plan_result.get("diagnostics", []))
            + ["empty capacity gate rows"],
        )

    first_row = capacity_gate_rows[0]
    capacity_summary = full_plan_result.get("capacity_result_summary", {})
    totals = _capacity_totals(capacity_gate_rows)
    messages = list(full_plan_result.get("messages", []))
    management_message = (
        "This result is generated through diagnostic_smoke_bridge; final full PSI "
        "planning is not yet executed."
    )

    model = {
        "available": True,
        "contract_version": full_plan_result.get("contract_version"),
        "run_id": full_plan_result.get("run_id", first_row.get("run_id", "")),
        "scenario_id": full_plan_result.get(
            "scenario_id", first_row.get("scenario_id", "")
        ),
        "scenario_root": full_plan_result.get("scenario_root", ""),
        "run_mode": full_plan_result.get("run_mode", ""),
        "full_psi_plan": full_plan_result.get("full_psi_plan"),
        "status": full_plan_result.get("status", ""),
        "product_name": first_row.get("product_name", ""),
        "node_name": first_row.get(
            "node_name", capacity_summary.get("capacity_node", "")
        ),
        "capacity_type": first_row.get(
            "capacity_type", capacity_summary.get("capacity_type", "")
        ),
        "rows": capacity_gate_rows,
        "totals": totals,
        "summary_text": "",
        "messages": messages,
        "diagnostics": list(full_plan_result.get("diagnostics", [])),
        "management_message": management_message,
    }
    model["summary_text"] = format_run_full_plan_graph_panel_summary_text(model)
    return model


def extract_run_full_plan_graph_panel_model_from_output_dir(
    output_dir: str | Path,
) -> dict:
    """Load Run Full Plan outputs from a run directory into a graph-panel model."""

    run_dir = Path(output_dir)
    json_path = run_dir / "full_plan_result.json"
    csv_path = run_dir / "visual_capacity_gate_weekly.csv"
    try:
        full_plan_result = load_full_plan_result_json(json_path)
        capacity_gate_rows = load_visual_capacity_gate_weekly_csv(csv_path)
        return extract_run_full_plan_capacity_gate_graph_model(
            full_plan_result=full_plan_result,
            capacity_gate_rows=capacity_gate_rows,
        )
    except FileNotFoundError as exc:
        return _unavailable_model(
            f"missing Run Full Plan output file: {exc.filename}",
            diagnostics=[str(exc)],
        )
    except (json.JSONDecodeError, ValueError, csv.Error) as exc:
        return _unavailable_model(
            f"invalid Run Full Plan output file: {exc}",
            diagnostics=[repr(exc)],
        )


def build_run_full_plan_capacity_gate_chart_dataset(model: dict) -> dict:
    """Build a chart-dataset contract from a graph-panel model."""

    rows = [
        {key: row.get(key, 0 if key != "week" else "") for key in DATASET_ROW_KEYS}
        for row in model.get("rows", [])
    ]
    return {
        "title": "WOM Run Full Plan Capacity Gate",
        "unit": "lot",
        "x_key": "week",
        "series": list(CHART_SERIES_KEYS),
        "rows": rows,
        "totals": dict(model.get("totals", {})),
        "chart_hint": "line_or_grouped_bar",
    }


def build_run_full_plan_capacity_gate_chart_series(dataset: dict) -> dict:
    """Transform chart-dataset rows into chart-ready series arrays."""

    rows = dataset.get("rows", [])
    x_key = dataset.get("x_key", "week")
    series_keys = dataset.get("series", CHART_SERIES_KEYS)
    return {
        "weeks": [row.get(x_key, "") for row in rows],
        "series": {key: [row.get(key, 0) for row in rows] for key in series_keys},
    }


def format_run_full_plan_graph_panel_summary_text(model: dict) -> str:
    """Format stable graph-panel summary text for headless tests or GUI display."""

    if not model.get("available", False):
        return model.get(
            "summary_text",
            f"WOM Run Full Plan graph panel unavailable: {model.get('reason', '')}",
        )

    totals = model.get("totals", {})
    run_mode = model.get("run_mode")
    lines = [
        "WOM Run Full Plan",
        f"Scenario: {model.get('scenario_id')}",
        f"Run mode: {run_mode}",
        f"Full PSI plan: {model.get('full_psi_plan')}",
        f"Status: {model.get('status')}",
        "",
        f"Capacity gate: {model.get('node_name')} {model.get('capacity_type')}",
        f"Requested: {totals.get('requested')}",
        f"Capacity: {totals.get('capacity')}",
        f"Accepted: {totals.get('accepted')}",
        f"Blocked: {totals.get('blocked')}",
        "",
        (
            f"This result is generated through {run_mode}; final full PSI planning "
            "is not yet executed."
        ),
    ]
    return "\n".join(lines)


__all__ = [
    "load_full_plan_result_json",
    "load_visual_capacity_gate_weekly_csv",
    "extract_run_full_plan_capacity_gate_graph_model",
    "extract_run_full_plan_graph_panel_model_from_output_dir",
    "build_run_full_plan_capacity_gate_chart_dataset",
    "build_run_full_plan_capacity_gate_chart_series",
    "format_run_full_plan_graph_panel_summary_text",
]
