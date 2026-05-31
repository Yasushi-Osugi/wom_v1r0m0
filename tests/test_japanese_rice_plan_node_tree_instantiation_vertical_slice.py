from __future__ import annotations

from pathlib import Path

from pysi.demand.demand_lot_generator import generate_demand_anchored_lots
from pysi.demand.demand_master_loader import load_weekly_demand_master_csv
from pysi.network.network_master_loader import load_network_master_package
from pysi.plan.plan_node_tree_instantiation import (
    LEGACY_PSI_DEMAND_S_INDEX,
    ProductPlanNode,
    attach_demand_lots_to_actual_plan_node_psi4demand,
    ensure_psi_week_slots,
    instantiate_japanese_rice_plan_node_tree_and_attach_demand,
    instantiate_product_plan_node_trees,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
SCENARIO_ID = "JAPANESE_RICE_VSLICE_001"
PRODUCT_NAME = "JAPANESE_RICE_STANDARD"
EXPECTED_WEEKLY_LOT_COUNTS = {
    "2027-W40": 80,
    "2027-W41": 95,
    "2027-W42": 110,
}
INBOUND_PATH = [
    "supply_side_root",
    "supply_point",
    "RICE_MILL_A",
    "FARM_REGION_A",
    "Procurement_Center",
]
OUTBOUND_PATH = [
    "demand_side_root",
    "supply_point",
    "DC_KANTO",
    "MARKET_TOKYO",
    "Global_Sales_Office",
]


def _trees():
    package = load_network_master_package(SCENARIO_ROOT)
    return instantiate_product_plan_node_trees(
        scenario_id=SCENARIO_ID,
        product_name=PRODUCT_NAME,
        nodes=package["nodes"],
        edges=package["edges"],
    )


def _assert_object_path(root: ProductPlanNode, path: list[str]) -> None:
    current = root
    assert current.node_name == path[0]
    assert current.parent is None
    for expected_child_name in path[1:]:
        matching_children = [
            child for child in current.children if child.node_name == expected_child_name
        ]
        assert len(matching_children) == 1
        child = matching_children[0]
        assert child.parent is current
        current = child


def test_instantiates_inbound_and_outbound_product_specific_plan_node_trees() -> None:
    trees = _trees()

    assert trees["inbound"]["root"].node_name == "supply_side_root"
    assert trees["outbound"]["root"].node_name == "demand_side_root"
    assert trees["summary"]["inbound_node_count"] == 5
    assert trees["summary"]["outbound_node_count"] == 5
    assert set(trees["inbound"]["nodes"]) == set(INBOUND_PATH)
    assert set(trees["outbound"]["nodes"]) == set(OUTBOUND_PATH)
    assert all(node.product_name == PRODUCT_NAME for node in trees["inbound"]["nodes"].values())
    assert all(node.product_name == PRODUCT_NAME for node in trees["outbound"]["nodes"].values())


def test_inbound_parent_children_links_follow_actual_plan_node_objects() -> None:
    trees = _trees()

    _assert_object_path(trees["inbound"]["root"], INBOUND_PATH)


def test_outbound_parent_children_links_follow_actual_plan_node_objects() -> None:
    trees = _trees()

    _assert_object_path(trees["outbound"]["root"], OUTBOUND_PATH)


def test_node_character_and_partner_key_are_preserved_for_mom_and_dad() -> None:
    trees = _trees()
    rice_mill = trees["inbound"]["nodes"]["RICE_MILL_A"]
    kanto_dc = trees["outbound"]["nodes"]["DC_KANTO"]

    assert rice_mill.node_character == "MOM"
    assert rice_mill.is_mom is True
    assert rice_mill.partner_key == "RICE_CORE"
    assert kanto_dc.node_character == "DAD"
    assert kanto_dc.is_dad is True
    assert kanto_dc.partner_key == "RICE_CORE"


def test_supply_point_instances_are_tree_side_specific_plan_nodes() -> None:
    trees = _trees()
    inbound_supply_point = trees["inbound"]["nodes"]["supply_point"]
    outbound_supply_point = trees["outbound"]["nodes"]["supply_point"]

    assert inbound_supply_point.tree_side == "inbound"
    assert outbound_supply_point.tree_side == "outbound"
    assert inbound_supply_point is not outbound_supply_point
    assert inbound_supply_point.identity_key == (
        SCENARIO_ID,
        PRODUCT_NAME,
        "inbound",
        "supply_point",
    )
    assert outbound_supply_point.identity_key == (
        SCENARIO_ID,
        PRODUCT_NAME,
        "outbound",
        "supply_point",
    )


def test_market_tokyo_exists_as_actual_outbound_demand_leaf_plan_node() -> None:
    trees = _trees()
    market_tokyo = trees["outbound"]["nodes"]["MARKET_TOKYO"]

    assert market_tokyo.node_character == "MARKET_LEAF"
    assert market_tokyo.is_market_leaf is True
    assert market_tokyo.is_leaf is True
    assert market_tokyo.children[0].node_name == "Global_Sales_Office"


def test_attaches_demand_lots_to_actual_market_tokyo_plan_node_psi4demand() -> None:
    trees = _trees()
    demand_rows = load_weekly_demand_master_csv(
        SCENARIO_ROOT / "masters" / "demand_master.csv"
    )
    lots = generate_demand_anchored_lots(demand_rows)
    market_tokyo = trees["outbound"]["nodes"]["MARKET_TOKYO"]

    summary = attach_demand_lots_to_actual_plan_node_psi4demand(market_tokyo, lots)

    assert len(lots) == 285
    assert summary == {
        "attached": True,
        "node_name": "MARKET_TOKYO",
        "product_name": PRODUCT_NAME,
        "tree_side": "outbound",
        "total_lots": 285,
        "weekly_lot_counts": EXPECTED_WEEKLY_LOT_COUNTS,
        "psi_slot": "S",
        "legacy_slot_index": 0,
    }
    for week, expected_count in EXPECTED_WEEKLY_LOT_COUNTS.items():
        assert len(market_tokyo.psi4demand[week][LEGACY_PSI_DEMAND_S_INDEX]) == expected_count
    all_attached_lot_ids = [
        lot_id
        for week in EXPECTED_WEEKLY_LOT_COUNTS
        for lot_id in market_tokyo.psi4demand[week][LEGACY_PSI_DEMAND_S_INDEX]
    ]
    assert len(all_attached_lot_ids) == 285
    assert len(set(all_attached_lot_ids)) == 285


def test_legacy_psi_slot_index_zero_is_s_and_other_slots_remain_lists() -> None:
    trees = _trees()
    market_tokyo = trees["outbound"]["nodes"]["MARKET_TOKYO"]
    s_slot_lot_id = "LOT_IN_LEGACY_S_SLOT"

    slots = ensure_psi_week_slots(market_tokyo, "2027-W40", psi_attr="psi4demand")
    slots[0].append(s_slot_lot_id)

    assert len(market_tokyo.psi4demand["2027-W40"]) == 4
    assert market_tokyo.psi4demand["2027-W40"][0] is slots[0]
    assert market_tokyo.psi4demand["2027-W40"][0] == [s_slot_lot_id]
    assert market_tokyo.psi4demand["2027-W40"][1] == []
    assert market_tokyo.psi4demand["2027-W40"][2] == []
    assert market_tokyo.psi4demand["2027-W40"][3] == []
    assert all(isinstance(slot, list) for slot in market_tokyo.psi4demand["2027-W40"])


def test_capacity_nodes_align_with_instantiated_plan_node_trees() -> None:
    trees = _trees()

    assert "FARM_REGION_A" in trees["inbound"]["nodes"]
    assert "RICE_MILL_A" in trees["inbound"]["nodes"]
    assert "DC_KANTO" in trees["outbound"]["nodes"]


def test_japanese_rice_convenience_helper_instantiates_and_attaches_demand() -> None:
    result = instantiate_japanese_rice_plan_node_tree_and_attach_demand(SCENARIO_ROOT)
    market_tokyo = result["market_tokyo"]

    assert result["summary"]["inbound_node_count"] == 5
    assert result["summary"]["outbound_node_count"] == 5
    assert result["summary"]["total_lots"] == 285
    assert (
        result["summary"]["demand_attachment"]["weekly_lot_counts"]
        == EXPECTED_WEEKLY_LOT_COUNTS
    )
    assert len(market_tokyo.psi4demand["2027-W40"][0]) == 80
    assert len(market_tokyo.psi4demand["2027-W41"][0]) == 95
    assert len(market_tokyo.psi4demand["2027-W42"][0]) == 110
