from __future__ import annotations

from pathlib import Path

from pysi.plan.capacity_constrained_first_flow import (
    run_japanese_rice_capacity_constrained_first_flow,
    split_lots_by_capacity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
EXPECTED_WEEKLY = {
    "2027-W40": {
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
        "capacity_usage": 80,
        "unused_capacity": 10,
        "shortage": 0,
    },
    "2027-W41": {
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
        "capacity_usage": 90,
        "unused_capacity": 0,
        "shortage": 5,
    },
    "2027-W42": {
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
        "capacity_usage": 90,
        "unused_capacity": 0,
        "shortage": 20,
    },
}
EXPECTED_TOTALS = {
    "requested": 285,
    "capacity": 270,
    "accepted": 260,
    "blocked": 25,
    "capacity_usage": 260,
    "unused_capacity": 10,
    "shortage": 25,
}


def test_split_lots_by_capacity_preserves_order_and_blocks_over_capacity() -> None:
    result = split_lots_by_capacity(["L1", "L2", "L3"], 2)

    assert result["accepted_lot_ids"] == ["L1", "L2"]
    assert result["blocked_lot_ids"] == ["L3"]
    assert result["requested"] == 3
    assert result["accepted"] == 2
    assert result["blocked"] == 1
    assert result["capacity_usage"] == 2
    assert result["unused_capacity"] == 0
    assert result["shortage"] == 1


def test_split_lots_by_capacity_reports_unused_capacity_when_request_is_smaller() -> None:
    result = split_lots_by_capacity(["L1", "L2"], 5)

    assert result["accepted_lot_ids"] == ["L1", "L2"]
    assert result["blocked_lot_ids"] == []
    assert result["requested"] == 2
    assert result["accepted"] == 2
    assert result["blocked"] == 0
    assert result["capacity_usage"] == 2
    assert result["unused_capacity"] == 3
    assert result["shortage"] == 0


def test_japanese_rice_first_flow_runner_marks_isolated_capacity_gate_mode() -> None:
    result = run_japanese_rice_capacity_constrained_first_flow(SCENARIO_ROOT)

    assert result["run_mode"] == "capacity_constrained_first_flow"
    assert result["full_psi_plan"] is False
    assert result["available"] is True


def test_japanese_rice_first_flow_documents_actual_plan_node_demand_lot_source() -> None:
    result = run_japanese_rice_capacity_constrained_first_flow(SCENARIO_ROOT)

    assert result["flow"]["demand_node"] == "MARKET_TOKYO"
    assert result["flow"]["capacity_node"] == "DC_KANTO"
    assert result["flow"]["capacity_type"] == "S"
    assert result["flow"]["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"
    assert result["plan_node_tree_summary"]["demand_attachment"]["node_name"] == "MARKET_TOKYO"
    assert result["plan_node_tree_summary"]["demand_attachment"]["legacy_slot_index"] == 0


def test_japanese_rice_first_flow_weekly_counts_match_dc_kanto_s_capacity_gate() -> None:
    result = run_japanese_rice_capacity_constrained_first_flow(SCENARIO_ROOT)

    assert result["weeks"] == ["2027-W40", "2027-W41", "2027-W42"]
    for week, expected in EXPECTED_WEEKLY.items():
        weekly = result["weekly"][week]
        for key, expected_value in expected.items():
            assert weekly[key] == expected_value


def test_japanese_rice_first_flow_totals_match_expected_gate_result() -> None:
    result = run_japanese_rice_capacity_constrained_first_flow(SCENARIO_ROOT)

    assert result["totals"] == EXPECTED_TOTALS


def test_japanese_rice_first_flow_lot_id_sets_are_consistent_by_week() -> None:
    result = run_japanese_rice_capacity_constrained_first_flow(SCENARIO_ROOT)

    for week, expected in EXPECTED_WEEKLY.items():
        weekly = result["weekly"][week]
        accepted_lot_ids = weekly["accepted_lot_ids"]
        blocked_lot_ids = weekly["blocked_lot_ids"]
        original_demand_lot_ids = weekly["original_demand_lot_ids"]

        assert set(accepted_lot_ids).isdisjoint(blocked_lot_ids)
        assert len(accepted_lot_ids) == expected["accepted"]
        assert len(blocked_lot_ids) == expected["blocked"]
        assert len(accepted_lot_ids) + len(blocked_lot_ids) == expected["requested"]
        assert set(accepted_lot_ids) | set(blocked_lot_ids) == set(original_demand_lot_ids)
        assert accepted_lot_ids + blocked_lot_ids == original_demand_lot_ids
