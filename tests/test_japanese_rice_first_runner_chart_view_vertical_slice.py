from __future__ import annotations

import importlib
from pathlib import Path

from pysi.gui.japanese_rice_first_runner_view import (
    build_japanese_rice_capacity_gate_chart_dataset,
    build_japanese_rice_capacity_gate_chart_series,
    extract_japanese_rice_first_runner_gui_model,
)
from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"


def _dataset() -> dict:
    result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
    model = extract_japanese_rice_first_runner_gui_model(result)
    return build_japanese_rice_capacity_gate_chart_dataset(model)


def test_capacity_gate_chart_series_returns_week_and_lot_arrays() -> None:
    dataset = _dataset()

    series = build_japanese_rice_capacity_gate_chart_series(dataset)

    assert series["title"] == "Japanese Rice DC_KANTO capacity gate"
    assert series["unit"] == "lot"
    assert series["x_key"] == "week"
    assert series["weeks"] == ["2027-W40", "2027-W41", "2027-W42"]
    assert series["series"]["requested"] == [80, 95, 110]
    assert series["series"]["capacity"] == [90, 90, 90]
    assert series["series"]["accepted"] == [80, 90, 90]
    assert series["series"]["blocked"] == [0, 5, 20]


def test_capacity_gate_chart_series_is_safe_for_empty_rows() -> None:
    dataset = {
        "title": "Japanese Rice DC_KANTO capacity gate",
        "unit": "lot",
        "x_key": "week",
        "series": ["requested", "capacity", "accepted", "blocked"],
        "rows": [],
        "totals": {},
        "chart_hint": "line_or_grouped_bar",
    }

    series = build_japanese_rice_capacity_gate_chart_series(dataset)

    assert series["weeks"] == []
    assert series["series"]["requested"] == []
    assert series["series"]["capacity"] == []
    assert series["series"]["accepted"] == []
    assert series["series"]["blocked"] == []


def test_japanese_rice_first_runner_view_import_is_safe() -> None:
    module = importlib.import_module("pysi.gui.japanese_rice_first_runner_view")

    assert module.__name__ == "pysi.gui.japanese_rice_first_runner_view"
    assert hasattr(module, "build_japanese_rice_capacity_gate_chart_series")
