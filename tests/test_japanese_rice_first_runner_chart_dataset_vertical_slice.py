from __future__ import annotations

from pathlib import Path

import pytest

from pysi.gui.japanese_rice_first_runner_view import (
    build_japanese_rice_capacity_gate_chart_dataset,
    extract_japanese_rice_first_runner_gui_model,
)
from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"

EXPECTED_ROW_VALUES = [
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 10,
        "capacity_usage_ratio": 80 / 90,
        "blocked_ratio": 0.0,
        "capacity_usage_pct": (80 / 90) * 100,
        "blocked_pct": 0.0,
    },
    {
        "week": "2027-W41",
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
        "shortage": 5,
        "unused_capacity": 0,
        "capacity_usage_ratio": 1.0,
        "blocked_ratio": 5 / 95,
        "capacity_usage_pct": 100.0,
        "blocked_pct": (5 / 95) * 100,
    },
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
        "shortage": 20,
        "unused_capacity": 0,
        "capacity_usage_ratio": 1.0,
        "blocked_ratio": 20 / 110,
        "capacity_usage_pct": 100.0,
        "blocked_pct": (20 / 110) * 100,
    },
]


def _dataset() -> dict:
    result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
    model = extract_japanese_rice_first_runner_gui_model(result)
    return build_japanese_rice_capacity_gate_chart_dataset(model)


def test_capacity_gate_chart_dataset_metadata_exists() -> None:
    dataset = _dataset()

    assert dataset["title"] == "Japanese Rice DC_KANTO capacity gate"
    assert dataset["unit"] == "lot"
    assert dataset["x_key"] == "week"
    assert dataset["chart_hint"] == "line_or_grouped_bar"
    assert dataset["series"] == ["requested", "capacity", "accepted", "blocked"]


def test_capacity_gate_chart_dataset_rows_include_original_and_derived_values() -> None:
    dataset = _dataset()

    assert len(dataset["rows"]) == 3
    for row, expected in zip(dataset["rows"], EXPECTED_ROW_VALUES, strict=True):
        assert row["week"] == expected["week"]
        assert row["requested"] == expected["requested"]
        assert row["capacity"] == expected["capacity"]
        assert row["accepted"] == expected["accepted"]
        assert row["blocked"] == expected["blocked"]
        assert row["shortage"] == expected["shortage"]
        assert row["unused_capacity"] == expected["unused_capacity"]


def test_capacity_gate_chart_dataset_rows_include_derived_ratios_and_percentages() -> None:
    dataset = _dataset()

    for row, expected in zip(dataset["rows"], EXPECTED_ROW_VALUES, strict=True):
        assert row["capacity_usage_ratio"] == pytest.approx(
            expected["capacity_usage_ratio"]
        )
        assert row["blocked_ratio"] == pytest.approx(expected["blocked_ratio"])
        assert row["capacity_usage_pct"] == pytest.approx(
            expected["capacity_usage_pct"]
        )
        assert row["blocked_pct"] == pytest.approx(expected["blocked_pct"])


def test_capacity_gate_chart_dataset_totals_include_original_and_derived_values() -> None:
    dataset = _dataset()
    totals = dataset["totals"]

    assert totals["requested"] == 285
    assert totals["capacity"] == 270
    assert totals["accepted"] == 260
    assert totals["blocked"] == 25
    assert totals["shortage"] == 25
    assert totals["unused_capacity"] == 10
    assert totals["capacity_usage_ratio"] == pytest.approx(260 / 270)
    assert totals["blocked_ratio"] == pytest.approx(25 / 285)
    assert totals["capacity_usage_pct"] == pytest.approx((260 / 270) * 100)
    assert totals["blocked_pct"] == pytest.approx((25 / 285) * 100)


def test_capacity_gate_chart_dataset_is_safe_for_zero_capacity() -> None:
    dataset = build_japanese_rice_capacity_gate_chart_dataset(
        {
            "weekly_rows": [
                {
                    "week": "W0",
                    "requested": 10,
                    "capacity": 0,
                    "accepted": 0,
                    "blocked": 10,
                }
            ],
            "totals": {"requested": 10, "capacity": 0, "accepted": 0, "blocked": 10},
        }
    )
    row = dataset["rows"][0]
    totals = dataset["totals"]

    assert row["capacity_usage_ratio"] == 0
    assert row["blocked_ratio"] == pytest.approx(1.0)
    assert row["capacity_usage_pct"] == 0
    assert row["blocked_pct"] == pytest.approx(100.0)
    assert totals["capacity_usage_ratio"] == 0
    assert totals["blocked_ratio"] == pytest.approx(1.0)
    assert totals["capacity_usage_pct"] == 0
    assert totals["blocked_pct"] == pytest.approx(100.0)


def test_capacity_gate_chart_dataset_is_safe_for_empty_input() -> None:
    dataset = build_japanese_rice_capacity_gate_chart_dataset(
        {"weekly_rows": [], "totals": {}}
    )

    assert dataset["rows"] == []
    assert dataset["totals"] == {
        "requested": 0,
        "capacity": 0,
        "accepted": 0,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 0,
        "capacity_usage_ratio": 0,
        "blocked_ratio": 0,
        "capacity_usage_pct": 0,
        "blocked_pct": 0,
    }
