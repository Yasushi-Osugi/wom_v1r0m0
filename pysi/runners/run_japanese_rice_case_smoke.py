from __future__ import annotations

import csv
from pathlib import Path

from pysi.cases.japanese_rice import (
    PRODUCT_ID,
    adapt_rice_case_to_executable,
    build_default_rice_case_dataset,
    run_weekly_psi_simulation,
    summarize_costs,
    summarize_kpis,
)


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_smoke(output_dir: Path | None = None) -> dict[str, object]:
    dataset = build_default_rice_case_dataset()
    plan = adapt_rice_case_to_executable(dataset)
    weekly = run_weekly_psi_simulation(plan)
    costs = summarize_costs(plan, weekly)
    kpis = summarize_kpis(plan, weekly, costs)

    out_dir = output_dir or Path("outputs/japanese_rice")

    psi_rows = [
        {
            "scenario_id": dataset.scenario_id,
            "week": w.week,
            "product_id": PRODUCT_ID,
            "P": w.P,
            "S": w.S,
            "I": w.I,
            "storage_capacity": w.storage_capacity,
            "storage_utilization": w.storage_utilization,
            "milling_capacity": plan.milling_capacity,
            "transport_capacity": plan.transport_capacity,
        }
        for w in weekly
    ]
    _write_csv(
        out_dir / "rice_psi_summary.csv",
        psi_rows,
        [
            "scenario_id",
            "week",
            "product_id",
            "P",
            "S",
            "I",
            "storage_capacity",
            "storage_utilization",
            "milling_capacity",
            "transport_capacity",
        ],
    )

    cost_rows = [
        {
            "scenario_id": dataset.scenario_id,
            "metric": metric,
            "value": value,
            "currency": "JPY",
            "comment": "MVP simplified assumption",
        }
        for metric, value in costs.items()
    ]
    _write_csv(
        out_dir / "rice_cost_summary.csv",
        cost_rows,
        ["scenario_id", "metric", "value", "currency", "comment"],
    )

    kpi_rows = [
        {
            "scenario_id": dataset.scenario_id,
            "kpi_id": kpi,
            "value": value,
            "unit": "ratio" if "rate" in kpi or "margin" in kpi or "utilization" in kpi else "lot",
            "comment": "MVP KPI",
        }
        for kpi, value in kpis.items()
    ]
    _write_csv(
        out_dir / "rice_kpi_summary.csv",
        kpi_rows,
        ["scenario_id", "kpi_id", "value", "unit", "comment"],
    )

    return {"dataset": dataset, "plan": plan, "weekly": weekly, "costs": costs, "kpis": kpis, "output_dir": out_dir}


def main() -> None:
    result = run_smoke()
    dataset = result["dataset"]
    weekly = result["weekly"]
    costs = result["costs"]
    kpis = result["kpis"]

    print("=== Japanese Rice Case smoke ===")
    print(f"scenario: {dataset.scenario_id}")
    print(f"product: {PRODUCT_ID}")
    print(f"horizon: {dataset.weeks[0]}..{dataset.weeks[-1]}\n")
    print("supply:")
    print(f"  total harvest supply: {kpis['total_supply_qty']:.1f} lots")
    print("  harvest weeks: W40-W44\n")
    print("demand:")
    print(f"  total annual demand: {kpis['total_demand_qty']:.1f} lots")
    print("  weekly demand: 1.6 lots\n")
    print("PSI:")
    print(f"  peak inventory: {kpis['peak_inventory_qty']:.1f} lots")
    print(f"  ending inventory: {kpis['ending_inventory_qty']:.1f} lots")
    print(f"  total shipped/sold: {kpis['total_shipped_qty']:.1f} lots\n")
    print("capacity:")
    print(f"  storage capacity: {dataset.storage_capacity:.0f} lots")
    print(f"  peak storage utilization: {kpis['peak_storage_utilization'] * 100:.1f}%")
    print(f"  milling capacity: {dataset.milling_capacity:.1f} lots/week")
    print(f"  transport capacity: {dataset.transport_capacity:.1f} lots/week\n")
    print("money:")
    print(f"  total revenue: {costs['total_revenue']:.0f} JPY")
    print(f"  total purchase cost: {costs['total_purchase_cost']:.0f} JPY")
    print(f"  total storage cost: {costs['total_storage_cost']:.0f} JPY")
    print(f"  total gross profit: {costs['gross_profit']:.0f} JPY\n")
    print("KPI:")
    print(f"  fill rate: {kpis['fill_rate'] * 100:.1f}%")
    avg_inventory = sum(x.I for x in weekly) / len(weekly)
    turns = (kpis['total_shipped_qty'] / avg_inventory) if avg_inventory > 0 else 0.0
    print(f"  inventory turnover proxy: {turns:.3f}")


if __name__ == "__main__":
    main()
