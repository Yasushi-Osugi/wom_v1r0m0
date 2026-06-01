from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from pysi.gui.japanese_rice_first_runner_view import (
    build_capacity_gate_scenario_comparison,
    build_capacity_override_chart_dataset,
    build_japanese_rice_capacity_gate_chart_dataset,
    extract_japanese_rice_first_runner_gui_model,
    format_capacity_gate_scenario_comparison_text,
)
from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"

EXPECTED_VARIANT_ROWS = [
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 100,
        "accepted": 80,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 20,
        "capacity_usage_ratio": 0.8,
        "blocked_ratio": 0.0,
        "capacity_usage_pct": 80.0,
        "blocked_pct": 0.0,
    },
    {
        "week": "2027-W41",
        "requested": 95,
        "capacity": 100,
        "accepted": 95,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 5,
        "capacity_usage_ratio": 0.95,
        "blocked_ratio": 0.0,
        "capacity_usage_pct": 95.0,
        "blocked_pct": 0.0,
    },
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 100,
        "accepted": 100,
        "blocked": 10,
        "shortage": 10,
        "unused_capacity": 0,
        "capacity_usage_ratio": 1.0,
        "blocked_ratio": 10 / 110,
        "capacity_usage_pct": 100.0,
        "blocked_pct": (10 / 110) * 100,
    },
]


def _base_dataset() -> dict:
    result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
    model = extract_japanese_rice_first_runner_gui_model(result)
    return build_japanese_rice_capacity_gate_chart_dataset(model)


def _variant_dataset() -> dict:
    return build_capacity_override_chart_dataset(
        _base_dataset(),
        capacity_value=100,
        scenario_label="Capacity-up",
    )


def test_capacity_override_dataset_recalculates_capacity_up_rows_and_totals() -> None:
    variant_dataset = _variant_dataset()

    assert (
        variant_dataset["title"] == "Japanese Rice DC_KANTO capacity gate - Capacity-up"
    )
    assert variant_dataset["scenario_label"] == "Capacity-up"
    assert variant_dataset["capacity_override"] == 100
    assert variant_dataset["unit"] == "lot"
    assert variant_dataset["x_key"] == "week"
    assert variant_dataset["series"] == ["requested", "capacity", "accepted", "blocked"]
    assert variant_dataset["chart_hint"] == "line_or_grouped_bar"

    assert len(variant_dataset["rows"]) == 3
    for row, expected in zip(
        variant_dataset["rows"], EXPECTED_VARIANT_ROWS, strict=True
    ):
        assert row["week"] == expected["week"]
        assert row["requested"] == expected["requested"]
        assert row["capacity"] == expected["capacity"]
        assert row["accepted"] == expected["accepted"]
        assert row["blocked"] == expected["blocked"]
        assert row["shortage"] == expected["shortage"]
        assert row["unused_capacity"] == expected["unused_capacity"]
        assert isinstance(row["capacity_usage_ratio"], (int, float))
        assert isinstance(row["blocked_ratio"], (int, float))
        assert isinstance(row["capacity_usage_pct"], (int, float))
        assert isinstance(row["blocked_pct"], (int, float))
        assert row["capacity_usage_ratio"] == pytest.approx(
            expected["capacity_usage_ratio"]
        )
        assert row["blocked_ratio"] == pytest.approx(expected["blocked_ratio"])
        assert row["capacity_usage_pct"] == pytest.approx(
            expected["capacity_usage_pct"]
        )
        assert row["blocked_pct"] == pytest.approx(expected["blocked_pct"])

    totals = variant_dataset["totals"]
    assert totals["requested"] == 285
    assert totals["capacity"] == 300
    assert totals["accepted"] == 275
    assert totals["blocked"] == 10
    assert totals["shortage"] == 10
    assert totals["unused_capacity"] == 25
    assert isinstance(totals["capacity_usage_ratio"], (int, float))
    assert isinstance(totals["blocked_ratio"], (int, float))
    assert totals["capacity_usage_ratio"] == pytest.approx(275 / 300)
    assert totals["blocked_ratio"] == pytest.approx(10 / 285)


def test_capacity_gate_scenario_comparison_totals_and_weekly_deltas() -> None:
    comparison = build_capacity_gate_scenario_comparison(
        _base_dataset(), _variant_dataset()
    )

    assert comparison["title"] == "Japanese Rice DC_KANTO capacity scenario comparison"
    assert comparison["base_label"] == "Base"
    assert comparison["variant_label"] == "Capacity-up"

    totals = comparison["totals"]
    assert totals["base"]["requested"] == 285
    assert totals["base"]["capacity"] == 270
    assert totals["base"]["accepted"] == 260
    assert totals["base"]["blocked"] == 25
    assert totals["variant"]["requested"] == 285
    assert totals["variant"]["capacity"] == 300
    assert totals["variant"]["accepted"] == 275
    assert totals["variant"]["blocked"] == 10
    assert totals["delta"]["capacity"] == 30
    assert totals["delta"]["accepted"] == 15
    assert totals["delta"]["blocked"] == -15
    assert totals["blocked_reduction"] == 15
    assert totals["blocked_reduction_ratio"] == pytest.approx(0.6)
    assert totals["blocked_reduction_pct"] == pytest.approx(60.0)

    rows_by_week = {row["week"]: row for row in comparison["rows"]}
    assert rows_by_week["2027-W40"]["base_requested"] == 80
    assert rows_by_week["2027-W40"]["base_capacity"] == 90
    assert rows_by_week["2027-W40"]["base_accepted"] == 80
    assert rows_by_week["2027-W40"]["base_blocked"] == 0
    assert rows_by_week["2027-W40"]["variant_requested"] == 80
    assert rows_by_week["2027-W40"]["variant_capacity"] == 100
    assert rows_by_week["2027-W40"]["variant_accepted"] == 80
    assert rows_by_week["2027-W40"]["variant_blocked"] == 0
    assert rows_by_week["2027-W40"]["delta_capacity"] == 10
    assert rows_by_week["2027-W40"]["delta_accepted"] == 0
    assert rows_by_week["2027-W40"]["delta_blocked"] == 0
    assert rows_by_week["2027-W41"]["delta_accepted"] == 5
    assert rows_by_week["2027-W41"]["delta_blocked"] == -5
    assert rows_by_week["2027-W42"]["delta_accepted"] == 10
    assert rows_by_week["2027-W42"]["delta_blocked"] == -10


def test_capacity_gate_scenario_comparison_summary_text_includes_management_values() -> (
    None
):
    comparison = build_capacity_gate_scenario_comparison(
        _base_dataset(), _variant_dataset()
    )

    text = format_capacity_gate_scenario_comparison_text(comparison)

    assert "Base" in text
    assert "Capacity-up" in text
    assert "DC_KANTO" in text
    assert "90" in text
    assert "100" in text
    assert "25 -> 10" in text
    assert "15 lots" in text
    assert "60.0%" in text
    assert "260 -> 275" in text


def test_capacity_gate_scenario_comparison_is_safe_for_empty_datasets() -> None:
    comparison = build_capacity_gate_scenario_comparison(
        {"rows": [], "totals": {}},
        {"rows": [], "totals": {}},
    )

    assert comparison["rows"] == []
    assert comparison["totals"]["base"] == {
        "requested": 0,
        "capacity": 0,
        "accepted": 0,
        "blocked": 0,
    }
    assert comparison["totals"]["variant"] == {
        "requested": 0,
        "capacity": 0,
        "accepted": 0,
        "blocked": 0,
    }
    assert comparison["totals"]["delta"] == {
        "capacity": 0,
        "accepted": 0,
        "blocked": 0,
    }
    assert comparison["totals"]["blocked_reduction"] == 0
    assert comparison["totals"]["blocked_reduction_ratio"] == 0
    assert comparison["totals"]["blocked_reduction_pct"] == 0


def test_importing_runner_view_module_does_not_open_gui_window() -> None:
    module = importlib.import_module("pysi.gui.japanese_rice_first_runner_view")

    assert hasattr(module, "build_capacity_override_chart_dataset")
    assert hasattr(module, "build_capacity_gate_scenario_comparison")
    assert hasattr(module, "format_capacity_gate_scenario_comparison_text")
