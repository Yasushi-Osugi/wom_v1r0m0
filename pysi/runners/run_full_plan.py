from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "wom_full_plan_result_v0r1"
DEFAULT_RUN_MODE = "diagnostic_smoke_bridge"
DEFAULT_SCENARIO_ID = "japanese_rice_vslice_001"
DEFAULT_OUTPUT_DIR = "outputs/run_full_plan"
CAPACITY_GATE_DATASET_KEY = "capacity_gate_weekly"
CAPACITY_GATE_CSV_COLUMNS = [
    "scenario_id",
    "run_id",
    "product_name",
    "node_name",
    "capacity_type",
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


@dataclass(frozen=True)
class WomRunConfig:
    scenario_root: str
    scenario_id: str = DEFAULT_SCENARIO_ID
    run_id: str = ""
    run_mode: str = DEFAULT_RUN_MODE
    output_dir: str = DEFAULT_OUTPUT_DIR
    enable_capacity: bool = True
    enable_visualization_export: bool = True
    debug: bool = False


@dataclass
class FullPlanResult:
    contract_version: str
    run_id: str
    scenario_id: str
    scenario_root: str
    run_mode: str
    full_psi_plan: bool
    status: str
    master_load_summary: dict[str, Any]
    runtime_model_summary: dict[str, Any]
    capacity_result_summary: dict[str, Any]
    visualization_datasets: dict[str, Any]
    output_paths: dict[str, str]
    diagnostics: list[Any]
    messages: list[str]


def _effective_run_id(config: WomRunConfig) -> str:
    if config.run_id:
        return config.run_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_scenario_id = config.scenario_id.replace("/", "_").replace(" ", "_")
    return f"{safe_scenario_id}_{timestamp}"


def _failed_result(config: WomRunConfig, message: str) -> FullPlanResult:
    return FullPlanResult(
        contract_version=CONTRACT_VERSION,
        run_id=_effective_run_id(config),
        scenario_id=config.scenario_id,
        scenario_root=str(config.scenario_root),
        run_mode=config.run_mode,
        full_psi_plan=False,
        status="failed",
        master_load_summary={},
        runtime_model_summary={},
        capacity_result_summary={},
        visualization_datasets={},
        output_paths={},
        diagnostics=[message],
        messages=[message],
    )


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _capacity_gate_rows(
    *,
    scenario_id: str,
    run_id: str,
    product_name: str,
    capacity_node: str,
    capacity_type: str,
    weekly: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for week in sorted(weekly):
        row = weekly[week]
        requested = row["requested"]
        capacity = row["capacity"]
        accepted = row["accepted"]
        blocked = row["blocked"]
        shortage = max(0, requested - capacity)
        unused_capacity = max(0, capacity - accepted)
        capacity_usage_ratio = _ratio(accepted, capacity)
        blocked_ratio = _ratio(blocked, requested)
        rows.append(
            {
                "scenario_id": scenario_id,
                "run_id": run_id,
                "product_name": product_name,
                "node_name": capacity_node,
                "capacity_type": capacity_type,
                "week": week,
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
        )
    return rows


def _totals_with_derived_values(totals: dict[str, Any]) -> dict[str, Any]:
    requested = totals.get("requested", 0)
    capacity = totals.get("capacity", 0)
    accepted = totals.get("accepted", 0)
    blocked = totals.get("blocked", 0)
    shortage = max(0, requested - capacity)
    unused_capacity = max(0, capacity - accepted)
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


def _bridge_japanese_rice_result(
    *, config: WomRunConfig, run_id: str, source_result: dict[str, Any]
) -> FullPlanResult:
    demo_summary = source_result.get("demo_summary", {})
    master_counts = demo_summary.get("master_counts", source_result.get("masters", {}))
    plan_node_summary = demo_summary.get(
        "plan_node_summary", source_result.get("actual_plan_node_tree", {})
    )
    gate_summary = demo_summary.get(
        "capacity_gate_summary",
        source_result.get("capacity_constrained_first_flow", {}),
    )
    weekly = gate_summary.get("weekly", {})
    totals = gate_summary.get("totals", {})
    product_name = demo_summary.get(
        "product_name", source_result.get("product_name", "")
    )
    capacity_node = gate_summary.get("capacity_node", "")
    capacity_type = gate_summary.get("capacity_type", "")
    capacity_rows = _capacity_gate_rows(
        scenario_id=config.scenario_id,
        run_id=run_id,
        product_name=product_name,
        capacity_node=capacity_node,
        capacity_type=capacity_type,
        weekly=weekly,
    )

    master_load_summary = {
        "network": source_result.get("network", {}),
        "demand": {
            key: value
            for key, value in source_result.get("demand", {}).items()
            if key != "leaf_plan_node_compatibility"
        },
        "capacity": source_result.get("capacity", {}),
        "master_counts": dict(master_counts),
    }
    runtime_model_summary = {
        "actual_plan_node_tree": source_result.get("actual_plan_node_tree", {}),
        "inbound_node_count": plan_node_summary.get("inbound_node_count"),
        "outbound_node_count": plan_node_summary.get("outbound_node_count"),
        "market_node": plan_node_summary.get("demand_node"),
        "market_tokyo_weekly_s_slot_counts": plan_node_summary.get(
            "weekly_s_slot_counts", {}
        ),
        "demand_lot_source": plan_node_summary.get("demand_lot_source"),
    }
    capacity_result_summary = {
        "capacity_node": capacity_node,
        "capacity_type": capacity_type,
        "unit": gate_summary.get("unit"),
        "weekly": weekly,
        "totals": _totals_with_derived_values(totals),
    }
    visualization_datasets = {
        CAPACITY_GATE_DATASET_KEY: {
            "rows": capacity_rows,
            "path": "",
        }
    }
    messages = list(source_result.get("cli_summary_lines", []))
    messages.append(
        "WOM Run Full Plan uses diagnostic_smoke_bridge; full PSI planning is not executed."
    )

    return FullPlanResult(
        contract_version=CONTRACT_VERSION,
        run_id=run_id,
        scenario_id=config.scenario_id,
        scenario_root=str(config.scenario_root),
        run_mode=DEFAULT_RUN_MODE,
        full_psi_plan=False,
        status="success",
        master_load_summary=master_load_summary,
        runtime_model_summary=runtime_model_summary,
        capacity_result_summary=capacity_result_summary,
        visualization_datasets=visualization_datasets,
        output_paths={},
        diagnostics=[
            {
                "bridge_source_contract_version": source_result.get("contract_version"),
                "bridge_source_run_mode": source_result.get("run_mode"),
                "bridge_source_full_psi_plan": source_result.get("full_psi_plan"),
            }
        ],
        messages=messages,
    )


def run_full_plan(config: WomRunConfig) -> FullPlanResult:
    """Run the first minimal WOM Run Full Plan bridge contract."""

    run_id = _effective_run_id(config)
    scenario_root = Path(config.scenario_root)
    if not scenario_root.exists():
        return _failed_result(config, f"scenario_root does not exist: {scenario_root}")

    try:
        from pysi.runners.run_japanese_rice_first_psi_vslice import (
            run_japanese_rice_first_psi_vslice,
        )
    except Exception as exc:  # pragma: no cover - defensive bridge guard
        return _failed_result(config, f"Japanese Rice bridge unavailable: {exc}")

    try:
        source_result = run_japanese_rice_first_psi_vslice(scenario_root)
    except Exception as exc:
        return _failed_result(config, f"Japanese Rice bridge failed: {exc}")

    if not source_result.get("available", False):
        return _failed_result(
            config, "Japanese Rice bridge returned unavailable result."
        )

    return _bridge_japanese_rice_result(
        config=config, run_id=run_id, source_result=source_result
    )


def full_plan_result_to_dict(result: FullPlanResult) -> dict[str, Any]:
    return asdict(result)


def write_full_plan_outputs(
    result: FullPlanResult, *, output_dir: str | Path
) -> FullPlanResult:
    run_dir = Path(output_dir) / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    full_plan_json_path = run_dir / "full_plan_result.json"
    capacity_csv_path = run_dir / "visual_capacity_gate_weekly.csv"

    result.output_paths = {
        "run_dir": str(run_dir),
        "full_plan_result_json": str(full_plan_json_path),
        "visual_capacity_gate_weekly_csv": str(capacity_csv_path),
    }
    if CAPACITY_GATE_DATASET_KEY in result.visualization_datasets:
        result.visualization_datasets[CAPACITY_GATE_DATASET_KEY]["path"] = str(
            capacity_csv_path
        )

    rows = result.visualization_datasets.get(CAPACITY_GATE_DATASET_KEY, {}).get(
        "rows", []
    )
    with capacity_csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CAPACITY_GATE_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: row.get(column, "") for column in writer.fieldnames}
            )

    with full_plan_json_path.open("w", encoding="utf-8") as file:
        json.dump(full_plan_result_to_dict(result), file, indent=2, sort_keys=True)
        file.write("\n")

    return result


def format_full_plan_summary(result: FullPlanResult) -> list[str]:
    gate = result.capacity_result_summary
    totals = gate.get("totals", {})
    lines = [
        "WOM Run Full Plan",
        f"contract_version: {result.contract_version}",
        f"run_mode: {result.run_mode}",
        f"full_psi_plan: {result.full_psi_plan}",
        f"scenario_id: {result.scenario_id}",
        f"status: {result.status}",
    ]
    if gate:
        lines.extend(
            [
                f"capacity gate: {gate.get('capacity_node')} {gate.get('capacity_type')}",
                f"requested: {totals.get('requested')}",
                f"capacity: {totals.get('capacity')}",
                f"accepted: {totals.get('accepted')}",
                f"blocked: {totals.get('blocked')}",
            ]
        )
    if result.output_paths:
        lines.extend(
            [
                "outputs:",
                "  full_plan_result.json",
                "  visual_capacity_gate_weekly.csv",
            ]
        )
    return lines


def _json_default(value: Any) -> Any:
    if hasattr(value, "__dict__"):
        return vars(value)
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the WOM Full Plan bridge.")
    parser.add_argument("--scenario-root", required=True, help="Path to scenario root.")
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args(argv)

    config = WomRunConfig(
        scenario_root=args.scenario_root,
        scenario_id=args.scenario_id,
        run_id=args.run_id,
        output_dir=args.output_dir,
    )
    result = run_full_plan(config)
    if result.status == "success":
        result = write_full_plan_outputs(result, output_dir=config.output_dir)

    if args.format == "json":
        print(
            json.dumps(
                full_plan_result_to_dict(result),
                default=_json_default,
                sort_keys=True,
            )
        )
    else:
        print("\n".join(format_full_plan_summary(result)))
        if result.status != "success" and result.diagnostics:
            print(f"error: {result.diagnostics[0]}")

    return 0 if result.status == "success" else 1


__all__ = [
    "CONTRACT_VERSION",
    "FullPlanResult",
    "WomRunConfig",
    "format_full_plan_summary",
    "full_plan_result_to_dict",
    "main",
    "run_full_plan",
    "write_full_plan_outputs",
]


if __name__ == "__main__":
    raise SystemExit(main())
