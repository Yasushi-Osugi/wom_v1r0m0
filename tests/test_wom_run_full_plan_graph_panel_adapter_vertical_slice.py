from __future__ import annotations

import shutil
from pathlib import Path

from pysi.gui.wom_run_full_plan_graph_panel_adapter import (
    build_run_full_plan_capacity_gate_chart_dataset,
    build_run_full_plan_capacity_gate_chart_series,
    extract_run_full_plan_capacity_gate_graph_model,
    extract_run_full_plan_graph_panel_model_from_output_dir,
    format_run_full_plan_graph_panel_summary_text,
    load_full_plan_result_json,
    load_visual_capacity_gate_weekly_csv,
)
from pysi.runners.run_full_plan import (
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
RUN_ID = "test_graph_adapter_v0r1"
EXPECTED_TOTALS = {
    "requested": 285,
    "capacity": 270,
    "accepted": 260,
    "blocked": 25,
}
EXPECTED_WEEKLY = {
    "2027-W40": {"requested": 80, "capacity": 90, "accepted": 80, "blocked": 0},
    "2027-W41": {"requested": 95, "capacity": 90, "accepted": 90, "blocked": 5},
    "2027-W42": {
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
    },
}


def _write_run_full_plan_outputs(tmp_path: Path) -> Path:
    config = WomRunConfig(
        scenario_root=str(SCENARIO_ROOT),
        scenario_id="japanese_rice_vslice_001",
        run_id=RUN_ID,
        output_dir=str(tmp_path),
    )
    result = run_full_plan(config)
    write_full_plan_outputs(result, output_dir=str(tmp_path))
    return tmp_path / RUN_ID


def _load_model(run_dir: Path) -> dict:
    full_plan_result = load_full_plan_result_json(run_dir / "full_plan_result.json")
    capacity_gate_rows = load_visual_capacity_gate_weekly_csv(
        run_dir / "visual_capacity_gate_weekly.csv"
    )
    return extract_run_full_plan_capacity_gate_graph_model(
        full_plan_result=full_plan_result,
        capacity_gate_rows=capacity_gate_rows,
    )


def test_adapter_imports_without_opening_gui_window() -> None:
    import pysi.gui.wom_run_full_plan_graph_panel_adapter as adapter

    assert adapter is not None


def test_load_full_plan_result_json_and_visual_capacity_gate_csv(
    tmp_path: Path,
) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)

    full_plan_result = load_full_plan_result_json(run_dir / "full_plan_result.json")
    capacity_gate_rows = load_visual_capacity_gate_weekly_csv(
        run_dir / "visual_capacity_gate_weekly.csv"
    )

    assert full_plan_result["contract_version"] == "wom_full_plan_result_v0r1"
    assert len(capacity_gate_rows) == 3
    assert capacity_gate_rows[0]["week"] == "2027-W40"
    assert capacity_gate_rows[0]["requested"] == 80


def test_extract_available_graph_model_from_bridge_outputs(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)

    model = _load_model(run_dir)

    assert model["available"] is True
    assert model["contract_version"] == "wom_full_plan_result_v0r1"
    assert model["run_mode"] == "diagnostic_smoke_bridge"
    assert model["full_psi_plan"] is False
    assert model["status"] == "success"
    assert model["scenario_id"] == "japanese_rice_vslice_001"
    assert model["node_name"] == "DC_KANTO"
    assert model["capacity_type"] == "S"
    for key, expected in EXPECTED_TOTALS.items():
        assert model["totals"][key] == expected


def test_preserves_weekly_capacity_gate_rows(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    model = _load_model(run_dir)

    rows_by_week = {row["week"]: row for row in model["rows"]}

    assert list(rows_by_week) == ["2027-W40", "2027-W41", "2027-W42"]
    for week, expected_values in EXPECTED_WEEKLY.items():
        for key, expected in expected_values.items():
            assert rows_by_week[week][key] == expected


def test_build_capacity_gate_chart_dataset(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    model = _load_model(run_dir)

    dataset = build_run_full_plan_capacity_gate_chart_dataset(model)

    assert dataset["title"] == "WOM Run Full Plan Capacity Gate"
    assert dataset["unit"] == "lot"
    assert dataset["x_key"] == "week"
    assert dataset["chart_hint"] == "line_or_grouped_bar"
    assert dataset["series"] == ["requested", "capacity", "accepted", "blocked"]
    for key, expected in EXPECTED_TOTALS.items():
        assert dataset["totals"][key] == expected
    assert dataset["rows"][1]["week"] == "2027-W41"
    assert dataset["rows"][1]["blocked"] == 5


def test_build_capacity_gate_chart_series(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    model = _load_model(run_dir)
    dataset = build_run_full_plan_capacity_gate_chart_dataset(model)

    series = build_run_full_plan_capacity_gate_chart_series(dataset)

    assert series["weeks"] == ["2027-W40", "2027-W41", "2027-W42"]
    assert series["series"]["requested"] == [80, 95, 110]
    assert series["series"]["capacity"] == [90, 90, 90]
    assert series["series"]["accepted"] == [80, 90, 90]
    assert series["series"]["blocked"] == [0, 5, 20]


def test_summary_text_includes_truthfulness_note(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    model = _load_model(run_dir)

    summary_text = format_run_full_plan_graph_panel_summary_text(model)

    assert "WOM Run Full Plan" in summary_text
    assert "diagnostic_smoke_bridge" in summary_text
    assert "Full PSI plan: False" in summary_text
    assert "DC_KANTO S" in summary_text
    assert "Requested: 285" in summary_text
    assert "Accepted: 260" in summary_text
    assert "Blocked: 25" in summary_text
    assert "final full PSI planning is not yet executed" in summary_text


def test_missing_output_dir_returns_safe_unavailable_model(tmp_path: Path) -> None:
    model = extract_run_full_plan_graph_panel_model_from_output_dir(
        tmp_path / "missing"
    )

    assert model["available"] is False
    assert model["status"] == "unavailable"
    assert model["rows"] == []
    assert model["totals"] == {}
    assert model["reason"]


def test_missing_csv_returns_safe_unavailable_model(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    missing_csv_dir = tmp_path / "missing_csv"
    missing_csv_dir.mkdir()
    shutil.copyfile(
        run_dir / "full_plan_result.json", missing_csv_dir / "full_plan_result.json"
    )

    model = extract_run_full_plan_graph_panel_model_from_output_dir(missing_csv_dir)

    assert model["available"] is False
    assert model["status"] == "unavailable"
    assert model["rows"] == []
    assert model["totals"] == {}
    assert model["reason"]


def test_missing_json_returns_safe_unavailable_model(tmp_path: Path) -> None:
    run_dir = _write_run_full_plan_outputs(tmp_path)
    missing_json_dir = tmp_path / "missing_json"
    missing_json_dir.mkdir()
    shutil.copyfile(
        run_dir / "visual_capacity_gate_weekly.csv",
        missing_json_dir / "visual_capacity_gate_weekly.csv",
    )

    model = extract_run_full_plan_graph_panel_model_from_output_dir(missing_json_dir)

    assert model["available"] is False
    assert model["status"] == "unavailable"
    assert model["rows"] == []
    assert model["totals"] == {}
    assert model["reason"]


def test_empty_rows_do_not_crash_lower_level_extractor() -> None:
    model = extract_run_full_plan_capacity_gate_graph_model(
        full_plan_result={
            "contract_version": "wom_full_plan_result_v0r1",
            "run_mode": "diagnostic_smoke_bridge",
            "status": "success",
        },
        capacity_gate_rows=[],
    )

    assert model["available"] is False
    assert model["status"] == "unavailable"
    assert model["rows"] == []
    assert model["totals"] == {}
