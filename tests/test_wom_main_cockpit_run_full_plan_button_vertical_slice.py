from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pysi.runners.run_full_plan import DEFAULT_RUN_MODE, DEFAULT_SCENARIO_ID


def test_helper_import_is_gui_safe() -> None:
    import pysi.gui.wom_main_cockpit_run_full_plan_viewer_action as action

    assert action.DEFAULT_COCKPIT_VIEWER_SCENARIO_ROOT.endswith(
        "japanese_rice_vslice_001"
    )


def test_cockpit_viewer_run_id_uses_expected_prefix_and_timestamp() -> None:
    from pysi.gui.wom_main_cockpit_run_full_plan_viewer_action import (
        make_cockpit_viewer_run_id,
    )

    run_id = make_cockpit_viewer_run_id(datetime(2026, 6, 3, 17, 35, 0))

    assert run_id == "cockpit_viewer_20260603_173500"
    timestamp = run_id.removeprefix("cockpit_viewer_")
    assert len(timestamp) == len("YYYYMMDD_HHMMSS")
    assert timestamp.replace("_", "").isdigit()


def test_cockpit_viewer_config_builder_preserves_contract_defaults() -> None:
    from pysi.gui.wom_main_cockpit_run_full_plan_viewer_action import (
        build_cockpit_viewer_run_config,
    )

    config = build_cockpit_viewer_run_config(
        scenario_root="examples/scenarios/japanese_rice_vslice_001",
        scenario_id="japanese_rice_vslice_001",
        run_id="cockpit_viewer_20260603_173500",
    )

    assert config.scenario_root == "examples/scenarios/japanese_rice_vslice_001"
    assert config.scenario_id == DEFAULT_SCENARIO_ID
    assert config.run_id == "cockpit_viewer_20260603_173500"
    assert config.output_dir == "outputs/run_full_plan"
    assert config.run_mode == DEFAULT_RUN_MODE


def test_main_cockpit_source_preserves_legacy_button_and_adds_viewer_button() -> None:
    source = Path("pysi/gui/cockpit_tk.py").read_text(encoding="utf-8")

    assert 'text="Run Full Plan"' in source
    assert "command=self.run_full_plan" in source
    assert 'text="Run Full Plan → Viewer"' in source
    assert "command=self.on_run_full_plan_viewer_clicked" in source


def test_existing_run_full_plan_and_viewer_contract_symbols_remain_available() -> None:
    import pysi.gui.wom_run_full_plan_result_viewer as viewer
    import pysi.runners.run_full_plan as runner

    assert callable(runner.run_full_plan)
    assert callable(runner.write_full_plan_outputs)
    assert callable(viewer.launch_run_full_plan_result_viewer)


def test_cockpit_viewer_action_calls_standard_output_path(
    monkeypatch, tmp_path
) -> None:
    import pysi.gui.wom_main_cockpit_run_full_plan_viewer_action as action
    from pysi.runners.run_full_plan import FullPlanResult, WomRunConfig

    calls: list[tuple[str, object]] = []

    def fake_run_full_plan(config: WomRunConfig) -> FullPlanResult:
        calls.append(("run_full_plan", config))
        return FullPlanResult(
            contract_version="wom_full_plan_result_v0r1",
            run_id=config.run_id,
            scenario_id=config.scenario_id,
            scenario_root=config.scenario_root,
            run_mode=config.run_mode,
            full_psi_plan=False,
            status="success",
            master_load_summary={},
            runtime_model_summary={},
            capacity_result_summary={},
            visualization_datasets={},
            output_paths={},
            diagnostics=[],
            messages=[],
        )

    def fake_write_full_plan_outputs(result: FullPlanResult, *, output_dir: str):
        calls.append(("write_full_plan_outputs", (result.run_id, output_dir)))
        run_dir = Path(output_dir) / result.run_id
        run_dir.mkdir(parents=True)
        result.output_paths["run_dir"] = str(run_dir)
        return result

    def fake_launch_run_full_plan_result_viewer(run_dir: str | Path) -> int:
        calls.append(("launch_run_full_plan_result_viewer", Path(run_dir)))
        return 0

    monkeypatch.setattr(action, "run_full_plan", fake_run_full_plan)
    monkeypatch.setattr(action, "write_full_plan_outputs", fake_write_full_plan_outputs)
    monkeypatch.setattr(
        "pysi.gui.wom_run_full_plan_result_viewer.launch_run_full_plan_result_viewer",
        fake_launch_run_full_plan_result_viewer,
    )

    config = action.build_cockpit_viewer_run_config(
        scenario_root="examples/scenarios/japanese_rice_vslice_001",
        run_id="cockpit_viewer_20260603_173500",
        output_dir=str(tmp_path),
    )

    assert action.run_full_plan_and_open_viewer(config) == 0
    assert calls == [
        ("run_full_plan", config),
        ("write_full_plan_outputs", ("cockpit_viewer_20260603_173500", str(tmp_path))),
        (
            "launch_run_full_plan_result_viewer",
            tmp_path / "cockpit_viewer_20260603_173500",
        ),
    ]
