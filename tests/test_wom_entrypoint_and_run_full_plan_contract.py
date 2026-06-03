from __future__ import annotations

import csv
import json
from pathlib import Path

from pysi.runners.run_full_plan import (
    CONTRACT_VERSION,
    FullPlanResult,
    WomRunConfig,
    main,
    run_full_plan,
    write_full_plan_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
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


def _config(output_dir: Path | str = "outputs/run_full_plan") -> WomRunConfig:
    return WomRunConfig(
        scenario_root=str(SCENARIO_ROOT),
        scenario_id="japanese_rice_vslice_001",
        run_id="test_run_full_plan_v0r1",
        output_dir=str(output_dir),
    )


def test_dataclass_contract_defaults_are_stable() -> None:
    config = _config()
    result = run_full_plan(config)

    assert WomRunConfig is not None
    assert FullPlanResult is not None
    assert result.contract_version == CONTRACT_VERSION
    assert result.contract_version == "wom_full_plan_result_v0r1"
    assert result.run_mode == "diagnostic_smoke_bridge"
    assert result.full_psi_plan is False


def test_run_full_plan_bridges_japanese_rice_runner_contract() -> None:
    result = run_full_plan(_config())

    assert result.status == "success"
    for key, expected in EXPECTED_TOTALS.items():
        assert result.capacity_result_summary["totals"][key] == expected
    assert "actual_plan_node_tree" in result.runtime_model_summary
    assert result.runtime_model_summary["inbound_node_count"] == 5
    assert result.runtime_model_summary["outbound_node_count"] == 5
    assert result.runtime_model_summary["market_node"] == "MARKET_TOKYO"


def test_output_export_writes_stable_json_and_capacity_gate_csv(tmp_path: Path) -> None:
    result = write_full_plan_outputs(
        run_full_plan(_config(tmp_path)), output_dir=tmp_path
    )
    run_dir = tmp_path / "test_run_full_plan_v0r1"
    json_path = run_dir / "full_plan_result.json"
    csv_path = run_dir / "visual_capacity_gate_weekly.csv"

    assert json_path.exists()
    assert csv_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "wom_full_plan_result_v0r1"
    assert payload["run_mode"] == "diagnostic_smoke_bridge"
    assert payload["full_psi_plan"] is False
    assert payload["output_paths"]["full_plan_result_json"] == str(json_path)
    assert payload["output_paths"]["visual_capacity_gate_weekly_csv"] == str(csv_path)

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert [row["week"] for row in rows] == list(EXPECTED_WEEKLY)
    for row in rows:
        expected = EXPECTED_WEEKLY[row["week"]]
        assert int(row["requested"]) == expected["requested"]
        assert int(row["capacity"]) == expected["capacity"]
        assert int(row["accepted"]) == expected["accepted"]
        assert int(row["blocked"]) == expected["blocked"]


def test_cli_summary_smoke_prints_bridge_totals(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "--scenario-root",
            str(SCENARIO_ROOT),
            "--scenario-id",
            "japanese_rice_vslice_001",
            "--run-id",
            "cli_summary_test_run_full_plan_v0r1",
            "--output-dir",
            str(tmp_path),
            "--format",
            "summary",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "WOM Run Full Plan" in output
    assert "diagnostic_smoke_bridge" in output
    assert "DC_KANTO" in output
    assert "accepted" in output
    assert "blocked" in output
    assert "260" in output
    assert "25" in output


def test_cli_json_smoke_prints_parseable_contract(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "--scenario-root",
            str(SCENARIO_ROOT),
            "--scenario-id",
            "japanese_rice_vslice_001",
            "--run-id",
            "cli_json_test_run_full_plan_v0r1",
            "--output-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["contract_version"] == "wom_full_plan_result_v0r1"
    assert "capacity_result_summary" in payload
    assert "output_paths" in payload


def test_missing_scenario_root_returns_failed_result_and_nonzero_cli(
    tmp_path: Path, capsys
) -> None:
    missing_root = tmp_path / "missing_scenario_root"
    result = run_full_plan(
        WomRunConfig(
            scenario_root=str(missing_root),
            scenario_id="missing",
            run_id="missing_run",
            output_dir=str(tmp_path),
        )
    )

    assert result.status == "failed"
    assert "scenario_root does not exist" in result.diagnostics[0]

    exit_code = main(
        [
            "--scenario-root",
            str(missing_root),
            "--scenario-id",
            "missing",
            "--run-id",
            "missing_run",
            "--output-dir",
            str(tmp_path),
            "--format",
            "summary",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code != 0
    assert "failed" in output
    assert "scenario_root does not exist" in output
