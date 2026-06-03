from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from pysi.gui.wom_run_full_plan_graph_panel_adapter import (
    extract_run_full_plan_graph_panel_model_from_output_dir,
)
from pysi.runners.run_full_plan import (
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
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
EXPECTED_TOTALS = {
    "Requested": 285,
    "Capacity": 270,
    "Accepted": 260,
    "Blocked": 25,
}


def _run_full_plan_model(tmp_path: Path) -> dict:
    config = WomRunConfig(
        scenario_root=str(SCENARIO_ROOT),
        scenario_id="japanese_rice_vslice_001",
        run_id="viewer_vertical_slice_test_v0r1",
        output_dir=str(tmp_path),
    )
    result = write_full_plan_outputs(run_full_plan(config), output_dir=tmp_path)
    return extract_run_full_plan_graph_panel_model_from_output_dir(
        tmp_path / result.run_id
    )


def test_viewer_module_import_is_safe_and_exports_public_helpers() -> None:
    module = importlib.import_module("pysi.gui.wom_run_full_plan_result_viewer")

    assert module.build_viewer_title is not None
    assert module.format_capacity_gate_weekly_table_rows is not None
    assert module.build_totals_display_rows is not None
    assert module.launch_run_full_plan_result_viewer is not None
    assert module.main is not None


def test_build_viewer_title_handles_available_and_unavailable_models(
    tmp_path: Path,
) -> None:
    from pysi.gui.wom_run_full_plan_result_viewer import build_viewer_title

    model = _run_full_plan_model(tmp_path)
    title = build_viewer_title(model)

    assert "WOM Run Full Plan Result Viewer" in title
    assert "japanese_rice_vslice_001" in title

    unavailable_title = build_viewer_title(
        {
            "available": False,
            "status": "unavailable",
            "reason": "missing full_plan_result.json",
        }
    )
    assert "WOM Run Full Plan Result Viewer" in unavailable_title
    assert "unavailable" in unavailable_title


def test_format_capacity_gate_weekly_table_rows_preserves_bridge_values(
    tmp_path: Path,
) -> None:
    from pysi.gui.wom_run_full_plan_result_viewer import (
        format_capacity_gate_weekly_table_rows,
    )

    model = _run_full_plan_model(tmp_path)
    rows = format_capacity_gate_weekly_table_rows(model)

    assert len(rows) == 3
    for row in rows:
        expected = EXPECTED_WEEKLY[row["week"]]
        assert row["requested"] == expected["requested"]
        assert row["capacity"] == expected["capacity"]
        assert row["accepted"] == expected["accepted"]
        assert row["blocked"] == expected["blocked"]
    assert rows[0]["capacity_usage_pct"] == 88.88888888888889
    assert rows[0]["blocked_pct"] == 0
    assert rows[1]["capacity_usage_pct"] == 100
    assert rows[1]["blocked_pct"] == 5.263157894736842
    assert rows[2]["capacity_usage_pct"] == 100
    assert rows[2]["blocked_pct"] == 18.181818181818183


def test_build_totals_display_rows_contains_expected_totals(tmp_path: Path) -> None:
    from pysi.gui.wom_run_full_plan_result_viewer import build_totals_display_rows

    model = _run_full_plan_model(tmp_path)
    rows = build_totals_display_rows(model)
    totals_by_label = {row["label"]: row["value"] for row in rows}

    assert totals_by_label == EXPECTED_TOTALS


def test_summary_text_preserves_diagnostic_truthfulness_note(tmp_path: Path) -> None:
    model = _run_full_plan_model(tmp_path)
    summary_text = model["summary_text"]

    assert "diagnostic_smoke_bridge" in summary_text
    assert "Full PSI plan: False" in summary_text
    assert "final full PSI planning is not yet executed" in summary_text


def test_unavailable_model_formatting_is_safe() -> None:
    from pysi.gui.wom_run_full_plan_result_viewer import (
        build_totals_display_rows,
        build_viewer_title,
        format_capacity_gate_weekly_table_rows,
    )

    model = {
        "available": False,
        "status": "unavailable",
        "reason": "missing full_plan_result.json",
        "rows": [],
        "totals": {},
    }

    assert "WOM Run Full Plan Result Viewer" in build_viewer_title(model)
    assert format_capacity_gate_weekly_table_rows(model) == []
    assert build_totals_display_rows(model) == []


def test_viewer_module_has_explicit_main_guard() -> None:
    import pysi.gui.wom_run_full_plan_result_viewer as viewer

    source = inspect.getsource(viewer)

    assert 'if __name__ == "__main__":' in source
