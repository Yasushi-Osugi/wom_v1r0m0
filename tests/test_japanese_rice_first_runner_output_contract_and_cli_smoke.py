from __future__ import annotations

import json
from pathlib import Path

from pysi.runners.run_japanese_rice_first_psi_vslice import (
    CONTRACT_VERSION,
    main,
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
EXPECTED_MASTER_COUNTS = {
    "capacity_rows": 9,
    "demand_rows": 3,
    "demand_lots": 285,
    "network_nodes": 9,
    "network_edges": 8,
}
EXPECTED_WEEKLY_S_SLOT_COUNTS = {
    "2027-W40": 80,
    "2027-W41": 95,
    "2027-W42": 110,
}
EXPECTED_WEEKLY_GATE = {
    "2027-W40": {
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
    },
    "2027-W41": {
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
    },
    "2027-W42": {
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
    },
}
EXPECTED_TOTALS = {
    "requested": 285,
    "capacity": 270,
    "accepted": 260,
    "blocked": 25,
}


def _result() -> dict:
    return run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)


def test_runner_exposes_contract_version() -> None:
    result = _result()

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["contract_version"] == "japanese_rice_first_runner_output_v0r1"


def test_demo_summary_exposes_runner_identity_and_mode() -> None:
    result = _result()
    demo_summary = result["demo_summary"]

    assert demo_summary["scenario_id"] == "JAPANESE_RICE_VSLICE_001"
    assert demo_summary["product_name"] == "JAPANESE_RICE_STANDARD"
    assert demo_summary["runner_mode"] == "diagnostic_first_psi_smoke"
    assert demo_summary["full_psi_plan"] is False
    assert result["run_mode"] == "diagnostic_first_psi_smoke"
    assert result["full_psi_plan"] is False


def test_demo_summary_master_counts_are_stable() -> None:
    result = _result()

    assert result["demo_summary"]["master_counts"] == EXPECTED_MASTER_COUNTS


def test_demo_summary_plan_node_summary_reports_market_tokyo_s_slot_counts() -> None:
    result = _result()
    plan_node_summary = result["demo_summary"]["plan_node_summary"]

    assert plan_node_summary["inbound_node_count"] == 5
    assert plan_node_summary["outbound_node_count"] == 5
    assert plan_node_summary["demand_node"] == "MARKET_TOKYO"
    assert plan_node_summary["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"
    assert plan_node_summary["weekly_s_slot_counts"] == EXPECTED_WEEKLY_S_SLOT_COUNTS


def test_demo_summary_capacity_gate_summary_reports_dc_kanto_weekly_split() -> None:
    result = _result()
    gate_summary = result["demo_summary"]["capacity_gate_summary"]

    assert gate_summary["capacity_node"] == "DC_KANTO"
    assert gate_summary["capacity_type"] == "S"
    assert gate_summary["unit"] == "lot"
    assert gate_summary["weekly"] == EXPECTED_WEEKLY_GATE


def test_demo_summary_capacity_gate_summary_reports_totals() -> None:
    result = _result()

    assert result["demo_summary"]["capacity_gate_summary"]["totals"] == EXPECTED_TOTALS


def test_cli_summary_lines_are_human_readable_and_stable() -> None:
    result = _result()
    cli_summary_lines = result["cli_summary_lines"]
    joined = "\n".join(cli_summary_lines)

    assert isinstance(cli_summary_lines, list)
    assert "WOM Japanese Rice first PSI smoke" in joined
    assert "MARKET_TOKYO.psi4demand[week][0]" in joined
    assert "DC_KANTO S capacity gate" in joined
    assert "accepted=260" in joined
    assert "blocked=25" in joined


def test_cli_main_summary_format_prints_summary_only(capsys) -> None:
    exit_code = main(["--scenario-root", str(SCENARIO_ROOT), "--format", "summary"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "WOM Japanese Rice first PSI smoke" in output
    assert "DC_KANTO S capacity gate" in output
    assert "accepted=260" in output
    assert "contract_version" not in output


def test_cli_main_json_format_prints_full_contract(capsys) -> None:
    exit_code = main(["--scenario-root", str(SCENARIO_ROOT), "--format", "json"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["contract_version"] == "japanese_rice_first_runner_output_v0r1"
    assert payload["demo_summary"]["capacity_gate_summary"]["totals"] == EXPECTED_TOTALS
    assert "cli_summary_lines" in payload
