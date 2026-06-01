from __future__ import annotations

import importlib
from pathlib import Path

from pysi.gui.japanese_rice_first_runner_view import (
    build_japanese_rice_weekly_capacity_gate_rows,
    extract_japanese_rice_first_runner_gui_model,
    format_japanese_rice_gui_summary_text,
)
from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"

EXPECTED_WEEKLY_ROWS = [
    {"week": "2027-W40", "requested": 80, "capacity": 90, "accepted": 80, "blocked": 0},
    {"week": "2027-W41", "requested": 95, "capacity": 90, "accepted": 90, "blocked": 5},
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
    },
]
EXPECTED_TOTALS = {
    "requested": 285,
    "capacity": 270,
    "accepted": 260,
    "blocked": 25,
}


def _result() -> dict:
    return run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)


def test_module_import_smoke_does_not_open_gui_window() -> None:
    module = importlib.import_module("pysi.gui.japanese_rice_first_runner_view")

    assert hasattr(module, "extract_japanese_rice_first_runner_gui_model")
    assert hasattr(module, "build_japanese_rice_weekly_capacity_gate_rows")
    assert hasattr(module, "format_japanese_rice_gui_summary_text")
    assert hasattr(module, "_create_scrollable_frame")
    assert hasattr(module, "_launch_model_window")


def test_gui_model_extraction_reports_runner_identity() -> None:
    model = extract_japanese_rice_first_runner_gui_model(_result())

    assert model["available"] is True
    assert model["scenario_id"] == "JAPANESE_RICE_VSLICE_001"
    assert model["product_name"] == "JAPANESE_RICE_STANDARD"
    assert model["contract_version"] == "japanese_rice_first_runner_output_v0r1"
    assert model["runner_mode"] == "diagnostic_first_psi_smoke"
    assert model["full_psi_plan"] is False


def test_gui_summary_text_uses_cli_summary_lines() -> None:
    result = _result()
    model = extract_japanese_rice_first_runner_gui_model(result)

    assert format_japanese_rice_gui_summary_text(result) == "\n".join(
        result["cli_summary_lines"]
    )
    assert "WOM Japanese Rice first PSI smoke" in model["summary_text"]
    assert "MARKET_TOKYO.psi4demand[week][0]" in model["summary_text"]
    assert "DC_KANTO S capacity gate" in model["summary_text"]
    assert "accepted=260" in model["summary_text"]
    assert "blocked=25" in model["summary_text"]


def test_weekly_capacity_gate_rows_follow_demo_summary_week_order() -> None:
    result = _result()
    model = extract_japanese_rice_first_runner_gui_model(result)

    assert build_japanese_rice_weekly_capacity_gate_rows(result) == EXPECTED_WEEKLY_ROWS
    assert model["weekly_rows"] == EXPECTED_WEEKLY_ROWS
    assert len(model["weekly_rows"]) == 3


def test_gui_model_totals_and_management_message() -> None:
    model = extract_japanese_rice_first_runner_gui_model(_result())

    assert model["totals"] == EXPECTED_TOTALS
    assert (
        model["management_message"]
        == "DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon."
    )


def test_unavailable_model_behavior_is_safe_for_display_code() -> None:
    model = extract_japanese_rice_first_runner_gui_model(
        {"available": False, "messages": ["x"]}
    )

    assert model["available"] is False
    assert model["weekly_rows"] == []
    assert "could not be run" in model["summary_text"] or model["error"]


def test_weekly_rows_fall_back_to_sorted_weekly_keys_when_weeks_are_missing() -> None:
    result = _result()
    result["demo_summary"] = dict(result["demo_summary"])
    result["demo_summary"].pop("weeks")

    assert build_japanese_rice_weekly_capacity_gate_rows(result) == EXPECTED_WEEKLY_ROWS
