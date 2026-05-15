from __future__ import annotations

from pathlib import Path

from pysi.cases.japanese_rice import (
    adapt_rice_case_to_executable,
    build_default_rice_case_dataset,
    run_weekly_psi_simulation,
    summarize_costs,
    summarize_kpis,
)
from pysi.runners.run_japanese_rice_case_smoke import run_smoke


def test_rice_case_smoke_mvp(tmp_path: Path) -> None:
    dataset = build_default_rice_case_dataset()
    assert len(dataset.weeks) == 52

    plan = adapt_rice_case_to_executable(dataset)
    assert sum(plan.weekly_supply_qty.values()) == 100.0
    assert len(plan.weekly_demand_qty) == 52
    assert all(v == 1.6 for v in plan.weekly_demand_qty.values())

    weekly = run_weekly_psi_simulation(plan)
    assert all(x.I >= 0 for x in weekly)

    w39 = next(x for x in weekly if x.week == "2026-W39")
    w40 = next(x for x in weekly if x.week == "2026-W40")
    assert w40.I > w39.I

    total_shipped = sum(x.S for x in weekly)
    assert total_shipped > 0

    costs = summarize_costs(plan, weekly)
    assert "total_revenue" in costs
    assert "total_storage_cost" in costs
    assert "gross_profit" in costs

    kpis = summarize_kpis(plan, weekly, costs)
    assert "fill_rate" in kpis
    assert "peak_inventory_qty" in kpis

    result = run_smoke(output_dir=tmp_path / "japanese_rice")
    out_dir = result["output_dir"]
    assert (out_dir / "rice_psi_summary.csv").exists()
    assert (out_dir / "rice_cost_summary.csv").exists()
    assert (out_dir / "rice_kpi_summary.csv").exists()
