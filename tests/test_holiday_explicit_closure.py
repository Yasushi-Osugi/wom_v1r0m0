import csv

import pytest

from wom.engine.backward_planner import BackwardPlanner
from wom.engine.forward_planner import ForwardPlanner
from wom.engine.holiday_calendar_plugin import HolidayCalendarPlugin
from wom.engine.plan_copy import copy_demand_to_supply
from wom.model.plan_node import (
    PlanNode,
    S,
    CO,
    P,
    NODE_TYPE_LEAF_IN,
    NODE_TYPE_MOM,
    NODE_TYPE_SUPPLY_POINT,
)
from wom.model.sc_tree import SCTree


WEEKS = [f"2027-W{week:02d}" for week in range(1, 9)]
SKU = "Soy_Sauce"


def _node(node_id, node_name, node_type, side, lt_wks=0):
    return PlanNode(
        node_id=node_id,
        node_name=node_name,
        product=SKU,
        side=side,
        node_type=node_type,
        tier=0,
        lt_wks=lt_wks,
        transit_lt_wks=0,
    )


def _tree(with_upstream=True):
    sp = _node("SP", "SP_Soy", NODE_TYPE_SUPPLY_POINT, "outbound")
    bottling = _node("MOM:B", "Bottling_Noda", NODE_TYPE_MOM, "inbound")
    brewing = materials = None
    if with_upstream:
        brewing = _node("MOM:BR", "Brewing_Noda", NODE_TYPE_MOM, "inbound", 1)
        materials = _node(
            "IN:MAT", "Materials_JP", NODE_TYPE_LEAF_IN, "inbound", 1)
        bottling.add_child(brewing)
        brewing.add_child(materials)
    tree = SCTree(WEEKS)
    tree.register(SKU, sp, bottling)
    tree.init_all_psi()
    return tree, sp, bottling, brewing, materials


def _forward_tree():
    tree, sp, bottling, _, _ = _tree(with_upstream=False)
    materials = _node(
        "IN:MAT", "Materials_JP", NODE_TYPE_LEAF_IN, "inbound")
    bottling.add_child(materials)
    materials.init_psi(WEEKS)
    materials.plan_mode = "push_sub"
    return tree, sp, bottling, materials


@pytest.mark.parametrize("value", ["0", "1500"])
def test_plugin_registers_closure_independently_of_value(tmp_path, value):
    tree, _, bottling, _, _ = _tree()
    bottling.set_capacity(3, cap_hard=77)
    path = tmp_path / "holiday_calendar.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "holiday_id", "holiday_name", "start_week", "end_week",
            "node_name", "effect", "value",
        ])
        writer.writeheader()
        writer.writerow({
            "holiday_id": "GW", "holiday_name": "Golden Week",
            "start_week": WEEKS[3], "end_week": WEEKS[3],
            "node_name": "Bottling_Noda", "effect": "supply_closure",
            "value": value,
        })

    config = {"holiday_cal_path": str(path)}
    HolidayCalendarPlugin().on_pre_plan(tree, WEEKS, config)

    assert config["explicit_closures"]["Bottling_Noda"] == {3}
    assert bottling.cap_hard(3) == 77


def test_zero_without_closure_remains_unconstrained():
    tree, sp, bottling, _, _ = _tree(with_upstream=False)
    lots = ["DAL-1", "DAL-2"]
    sp.psi4demand[4][S] = list(lots)

    BackwardPlanner(tree, config={"explicit_closures": {}}).run(SKU)

    assert bottling.psi4demand[4][S] == lots
    assert bottling.psi4demand[4][P] == lots


def test_mom_closure_moves_same_lots_earlier_and_clears_closed_week():
    tree, sp, bottling, _, _ = _tree(with_upstream=False)
    lots = ["DAL-A", "DAL-B"]
    sp.psi4demand[5][S] = list(lots)

    BackwardPlanner(
        tree, config={"explicit_closures": {"Bottling_Noda": {5}}}
    ).run(SKU)

    assert bottling.psi4demand[5][S] == []
    assert bottling.psi4demand[5][P] == []
    assert bottling.psi4demand[4][S] == lots
    assert bottling.psi4demand[4][P] == lots
    assert bottling.psi4demand[5][CO] == lots


def test_consecutive_closures_carry_to_nearest_open_week_without_duplicates():
    tree, sp, bottling, _, _ = _tree(with_upstream=False)
    lots = ["DAL-A", "DAL-B"]
    sp.psi4demand[5][S] = list(lots)

    BackwardPlanner(
        tree, config={"explicit_closures": {"Bottling_Noda": {4, 5}}}
    ).run(SKU)

    assert bottling.psi4demand[4][P] == []
    assert bottling.psi4demand[5][P] == []
    assert bottling.psi4demand[3][P] == lots
    assert len(set(bottling.psi4demand[3][P])) == len(lots)


def test_mom_adjustment_precedes_upstream_propagation():
    tree, sp, bottling, brewing, materials = _tree()
    lots = ["DAL-A", "DAL-B"]
    sp.psi4demand[6][S] = list(lots)

    BackwardPlanner(
        tree, config={"explicit_closures": {"Bottling_Noda": {6}}}
    ).run(SKU)

    assert bottling.psi4demand[6][P] == []
    assert bottling.psi4demand[5][P] == lots
    assert brewing.psi4demand[4][S] == lots
    assert materials.psi4demand[3][S] == lots
    assert lots[0] not in brewing.psi4demand[5][S]


def test_forward_blocks_closed_mom_and_defers_same_lot_ids():
    tree, sp, bottling, materials = _forward_tree()
    lots = ["DAL-A", "DAL-B"]
    materials.psi4supply[4][P] = list(lots)
    bottling.psi4supply[4][S] = list(lots)

    result = ForwardPlanner(
        tree, explicit_closures={"Bottling_Noda": {4}}
    ).run(SKU)

    assert bottling.psi4supply[4][P] == []
    assert sp.psi4supply[4][P] == []
    assert bottling.psi4supply[5][P] == lots
    assert bottling.psi4supply[5][CO] == lots
    assert sp.psi4supply[5][P] == lots
    assert result.cap_hard_sealed == len(lots)


def test_empty_closure_map_preserves_forward_flow():
    tree, sp, bottling, materials = _forward_tree()
    lots = ["DAL-A", "DAL-B"]
    materials.psi4supply[4][P] = list(lots)
    bottling.psi4supply[4][S] = list(lots)

    result = ForwardPlanner(tree, explicit_closures={}).run(SKU)

    assert bottling.psi4supply[4][P] == lots
    assert sp.psi4supply[4][P] == lots
    assert result.bridge_lots == len(lots)


def test_leaf_in_post_backward_closure_moves_once():
    tree, _, _, _, materials = _tree()
    lots = ["DAL-A", "DAL-B"]
    materials.psi4demand[4][P] = list(lots)
    plugin = HolidayCalendarPlugin()
    plugin._rules = [{
        "effect": "supply_closure",
        "node_name": "Materials_JP",
        "week_idxs": [4],
    }]

    plugin.on_post_backward(
        tree, SKU, WEEKS, {"explicit_closures": {"Materials_JP": {4}}})

    assert materials.psi4demand[4][P] == []
    assert materials.psi4demand[3][P] == lots
    assert len(set(materials.psi4demand[3][P])) == len(lots)
