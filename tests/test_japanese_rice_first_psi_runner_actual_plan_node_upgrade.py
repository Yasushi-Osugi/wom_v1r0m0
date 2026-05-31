from __future__ import annotations

from pathlib import Path

from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
EXPECTED_WEEKLY_DEMAND = {
    "2027-W40": 80,
    "2027-W41": 95,
    "2027-W42": 110,
}
EXPECTED_WEEKLY_GATE = {
    "2027-W40": {"accepted": 80, "blocked": 0},
    "2027-W41": {"accepted": 90, "blocked": 5},
    "2027-W42": {"accepted": 90, "blocked": 20},
}


def _result() -> dict:
    return run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)


def test_runner_remains_diagnostic_first_psi_smoke() -> None:
    result = _result()

    assert result["run_mode"] == "diagnostic_first_psi_smoke"
    assert result["full_psi_plan"] is False


def test_existing_master_counts_remain_available() -> None:
    result = _result()

    assert result["masters"] == {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    }


def test_actual_plan_node_tree_section_reports_market_tokyo_s_slot_counts() -> None:
    result = _result()
    actual_tree = result["actual_plan_node_tree"]

    assert actual_tree["available"] is True
    assert actual_tree["product_name"] == "JAPANESE_RICE_STANDARD"
    assert actual_tree["inbound_node_count"] == 5
    assert actual_tree["outbound_node_count"] == 5
    assert actual_tree["demand_node"] == "MARKET_TOKYO"
    assert actual_tree["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"
    assert actual_tree["weekly_s_slot_counts"] == EXPECTED_WEEKLY_DEMAND


def test_capacity_constrained_first_flow_section_reports_dc_kanto_gate() -> None:
    result = _result()
    first_flow = result["capacity_constrained_first_flow"]

    assert first_flow["available"] is True
    assert first_flow["run_mode"] == "capacity_constrained_first_flow"
    assert first_flow["full_psi_plan"] is False
    assert first_flow["capacity_node"] == "DC_KANTO"
    assert first_flow["demand_node"] == "MARKET_TOKYO"
    assert first_flow["capacity_type"] == "S"
    assert first_flow["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"


def test_capacity_constrained_first_flow_weekly_accepted_and_blocked_counts() -> None:
    result = _result()
    weekly = result["capacity_constrained_first_flow"]["weekly"]

    for week, expected in EXPECTED_WEEKLY_GATE.items():
        assert weekly[week]["accepted"] == expected["accepted"]
        assert weekly[week]["blocked"] == expected["blocked"]


def test_capacity_constrained_first_flow_totals_are_visible() -> None:
    result = _result()
    totals = result["capacity_constrained_first_flow"]["totals"]

    assert totals["requested"] == 285
    assert totals["capacity"] == 270
    assert totals["accepted"] == 260
    assert totals["blocked"] == 25


def test_upgrade_messages_are_deterministic() -> None:
    result = _result()
    messages_text = "\n".join(result["messages"])

    assert "actual ProductPlanNode tree instantiated" in messages_text
    assert "MARKET_TOKYO.psi4demand[week][0] verified" in messages_text
    assert "DC_KANTO capacity-constrained first flow attached" in messages_text
