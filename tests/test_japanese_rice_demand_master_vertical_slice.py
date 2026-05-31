from __future__ import annotations

from collections import Counter
from pathlib import Path

from pysi.demand import (
    attach_demand_lots_to_leaf_plan_node_psi4demand,
    generate_demand_anchored_lots,
    load_weekly_demand_master_csv,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
DEMAND_MASTER_PATH = SCENARIO_ROOT / "masters" / "demand_master.csv"
EXPECTED_PRODUCT = "JAPANESE_RICE_STANDARD"
EXPECTED_DEMAND_NODE = "MARKET_TOKYO"
EXPECTED_WEEKS = ["2027-W40", "2027-W41", "2027-W42"]
EXPECTED_DEMAND_BY_WEEK = {
    "2027-W40": 80,
    "2027-W41": 95,
    "2027-W42": 110,
}
EXPECTED_TOTAL_DEMAND = 285


def _loaded_rows():
    return load_weekly_demand_master_csv(DEMAND_MASTER_PATH)


def _generated_lots():
    return generate_demand_anchored_lots(_loaded_rows())


def test_japanese_rice_demand_master_file_exists_and_loads_three_weekly_rows() -> None:
    assert DEMAND_MASTER_PATH.exists()

    rows = _loaded_rows()

    assert len(rows) == 3
    assert sum(row.demand_qty for row in rows) == EXPECTED_TOTAL_DEMAND


def test_loaded_rows_preserve_product_leaf_demand_node_weeks_and_quantities() -> None:
    rows = _loaded_rows()

    assert {row.product_id for row in rows} == {EXPECTED_PRODUCT}
    assert {row.product_name for row in rows} == {EXPECTED_PRODUCT}
    assert {row.demand_node for row in rows} == {EXPECTED_DEMAND_NODE}
    assert {row.node_name for row in rows} == {EXPECTED_DEMAND_NODE}
    assert [row.week for row in rows] == EXPECTED_WEEKS
    assert {row.week: row.demand_qty for row in rows} == EXPECTED_DEMAND_BY_WEEK
    assert {row.source_granularity for row in rows} == {"weekly"}


def test_demand_anchored_lot_generation_is_deterministic_and_unique() -> None:
    first_run = _generated_lots()
    second_run = _generated_lots()

    assert len(first_run) == EXPECTED_TOTAL_DEMAND
    assert len({lot.lot_id for lot in first_run}) == EXPECTED_TOTAL_DEMAND
    assert first_run[0].lot_id == second_run[0].lot_id
    assert first_run[-1].lot_id == second_run[-1].lot_id
    assert first_run[0].lot_id == (
        "JAPANESE_RICE_VSLICE_001|MARKET_TOKYO|JAPANESE_RICE_STANDARD|2027-W40|000001"
    )
    assert first_run[-1].lot_id == (
        "JAPANESE_RICE_VSLICE_001|MARKET_TOKYO|JAPANESE_RICE_STANDARD|2027-W42|000110"
    )


def test_weekly_lot_counts_match_weekly_demand_quantities() -> None:
    counts = Counter(lot.demand_week for lot in _generated_lots())

    assert counts == EXPECTED_DEMAND_BY_WEEK


def test_leaf_plan_node_psi4demand_s_slot_attachment_by_product_and_leaf() -> None:
    psi4demand_by_product_leaf = attach_demand_lots_to_leaf_plan_node_psi4demand(
        _generated_lots()
    )

    assert set(psi4demand_by_product_leaf) == {EXPECTED_PRODUCT}
    assert set(psi4demand_by_product_leaf[EXPECTED_PRODUCT]) == {EXPECTED_DEMAND_NODE}

    leaf_plan_node = psi4demand_by_product_leaf[EXPECTED_PRODUCT][EXPECTED_DEMAND_NODE]
    psi4demand = leaf_plan_node["psi4demand"]
    assert len(psi4demand["2027-W40"]["S"]) == 80
    assert len(psi4demand["2027-W41"]["S"]) == 95
    assert len(psi4demand["2027-W42"]["S"]) == 110


def test_s_slot_output_is_legacy_bridge_to_outbound_leaf_plan_node_psi4demand() -> None:
    """Bridge: outbound leaf plan_node.psi4demand[w][0:"S"] = list[lot_ID]."""

    bridge = attach_demand_lots_to_leaf_plan_node_psi4demand(_generated_lots())
    leaf_plan_node = bridge[EXPECTED_PRODUCT][EXPECTED_DEMAND_NODE]

    assert "psi4demand" in leaf_plan_node
    assert leaf_plan_node["psi4demand"]["2027-W40"]["S"][0].endswith("|000001")
    assert all(
        lot_id.startswith(
            "JAPANESE_RICE_VSLICE_001|MARKET_TOKYO|JAPANESE_RICE_STANDARD|"
        )
        for week in EXPECTED_WEEKS
        for lot_id in leaf_plan_node["psi4demand"][week]["S"]
    )


def test_demand_anchored_lots_carry_outbound_leaf_plan_node_anchor_semantics() -> None:
    lots = _generated_lots()

    assert {lot.anchor_tree_side for lot in lots} == {"outbound"}
    assert {lot.anchor_node for lot in lots} == {EXPECTED_DEMAND_NODE}
    assert {lot.target_psi_layer for lot in lots} == {"demand"}
    assert {lot.target_psi_slot for lot in lots} == {"S"}
