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


def _result() -> dict:
    return run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)


def test_runner_loads_capacity_demand_and_network_masters() -> None:
    result = _result()

    assert result["available"] is True
    assert result["masters"] == {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    }


def test_demand_lots_attach_to_market_tokyo_leaf_compatibility_shape() -> None:
    result = _result()

    assert result["demand"]["node"] == "MARKET_TOKYO"
    assert result["demand"]["weekly_lot_counts"] == EXPECTED_WEEKLY_DEMAND
    assert result["demand"]["total_lots"] == 285
    assert result["demand"]["leaf_plan_node_psi4demand_counts"] == EXPECTED_WEEKLY_DEMAND

    psi4demand = result["demand"]["leaf_plan_node_compatibility"]["psi4demand"]
    assert len(psi4demand["2027-W40"]["S"]) == 80
    assert len(psi4demand["2027-W41"]["S"]) == 95
    assert len(psi4demand["2027-W42"]["S"]) == 110


def test_capacity_runtime_attachment_preflight_is_applied() -> None:
    result = _result()

    assert result["capacity"]["runtime_attachment_applied"] is True
    assert result["capacity"]["input_row_count"] == 9
    assert result["capacity"]["row_source"] == "env.capacity_weekly_rows"


def test_network_hammock_paths_and_partner_alignment_are_verified() -> None:
    result = _result()

    assert result["network"]["inbound_path_exists"] is True
    assert result["network"]["outbound_path_exists"] is True
    assert result["network"]["mom_node"] == "RICE_MILL_A"
    assert result["network"]["dad_node"] == "DC_KANTO"
    assert result["network"]["partner_key"] == "RICE_CORE"
    assert result["network"]["market_leaf"] == "MARKET_TOKYO"
    assert result["network"]["supply_point"] == "supply_point"


def test_simple_balance_for_dc_kanto() -> None:
    result = _result()

    assert result["balance"]["DC_KANTO"] == {
        "2027-W40": {"demand": 80, "capacity": 90, "balance": 10, "shortage": 0},
        "2027-W41": {"demand": 95, "capacity": 90, "balance": -5, "shortage": 5},
        "2027-W42": {"demand": 110, "capacity": 90, "balance": -20, "shortage": 20},
    }


def test_simple_balance_for_rice_mill_a() -> None:
    result = _result()

    assert result["balance"]["RICE_MILL_A"] == {
        "2027-W40": {"demand": 80, "capacity": 100, "balance": 20, "shortage": 0},
        "2027-W41": {"demand": 95, "capacity": 100, "balance": 5, "shortage": 0},
        "2027-W42": {"demand": 110, "capacity": 100, "balance": -10, "shortage": 10},
    }


def test_simple_balance_for_farm_region_a() -> None:
    result = _result()

    assert result["balance"]["FARM_REGION_A"] == {
        "2027-W40": {"demand": 80, "capacity": 120, "balance": 40, "shortage": 0},
        "2027-W41": {"demand": 95, "capacity": 120, "balance": 25, "shortage": 0},
        "2027-W42": {"demand": 110, "capacity": 120, "balance": 10, "shortage": 0},
    }


def test_messages_are_deterministic() -> None:
    result = _result()
    messages_text = "\n".join(result["messages"])

    assert "masters loaded" in messages_text
    assert "demand lots attached" in messages_text
    assert "capacity runtime context attached" in messages_text
    assert "network hammock paths verified" in messages_text
    assert "simple weekly balance computed" in messages_text


def test_result_marks_diagnostic_first_smoke_not_full_psi() -> None:
    result = _result()

    assert result["run_mode"] == "diagnostic_first_psi_smoke"
    assert result["full_psi_plan"] is False
