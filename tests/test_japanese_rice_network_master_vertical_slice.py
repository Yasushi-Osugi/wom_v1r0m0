from __future__ import annotations

from pathlib import Path

from pysi.network import (
    derive_tree_depths,
    find_node,
    has_path,
    load_network_edge_master_csv,
    load_network_master_package,
    load_network_node_master_csv,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
NODE_MASTER_PATH = SCENARIO_ROOT / "masters" / "node_master.csv"
NETWORK_MASTER_PATH = SCENARIO_ROOT / "masters" / "network_master.csv"
EXPECTED_PRODUCT = "JAPANESE_RICE_STANDARD"
EXPECTED_CAPACITY_NODES = {"FARM_REGION_A", "RICE_MILL_A", "DC_KANTO"}
EXPECTED_DEMAND_NODE = "MARKET_TOKYO"
INBOUND_HAMMOCK_PATH = [
    "supply_side_root",
    "supply_point",
    "RICE_MILL_A",
    "FARM_REGION_A",
    "Procurement_Center",
]
OUTBOUND_HAMMOCK_PATH = [
    "demand_side_root",
    "supply_point",
    "DC_KANTO",
    "MARKET_TOKYO",
    "Global_Sales_Office",
]


def _loaded_nodes():
    return load_network_node_master_csv(NODE_MASTER_PATH)


def _loaded_edges():
    return load_network_edge_master_csv(NETWORK_MASTER_PATH)


def _node_by_name(node_name: str):
    node = find_node(_loaded_nodes(), node_name)
    assert node is not None
    return node


def test_japanese_rice_network_master_files_exist_and_load_expected_counts() -> None:
    assert NODE_MASTER_PATH.exists()
    assert NETWORK_MASTER_PATH.exists()

    nodes = _loaded_nodes()
    edges = _loaded_edges()
    package = load_network_master_package(SCENARIO_ROOT)

    assert len(nodes) == 9
    assert len(edges) == 8
    assert package["summary"]["node_count"] == 9
    assert package["summary"]["edge_count"] == 8
    assert {node.product_name for node in nodes} == {EXPECTED_PRODUCT}
    assert {edge.product_name for edge in edges} == {EXPECTED_PRODUCT}


def test_node_characters_are_loaded_as_canonical_wom_roles() -> None:
    assert _node_by_name("supply_point").node_character == "SUPPLY_POINT"
    assert _node_by_name("RICE_MILL_A").node_character == "MOM"
    assert _node_by_name("DC_KANTO").node_character == "DAD"
    assert _node_by_name("FARM_REGION_A").node_character == "SUPPLIER_LEAF"
    assert _node_by_name("MARKET_TOKYO").node_character == "MARKET_LEAF"
    assert find_node(_loaded_nodes(), "Procurement_Center") is not None
    assert find_node(_loaded_nodes(), "Global_Sales_Office") is not None


def test_mom_and_dad_are_detected_from_node_character_without_name_prefixes() -> None:
    rice_mill = _node_by_name("RICE_MILL_A")
    kanto_dc = _node_by_name("DC_KANTO")

    assert not rice_mill.node_name.startswith("MOM")
    assert not kanto_dc.node_name.startswith("DAD")
    assert rice_mill.node_character == "MOM"
    assert kanto_dc.node_character == "DAD"
    assert rice_mill.is_mom is True
    assert kanto_dc.is_dad is True


def test_partner_key_aligns_japanese_rice_mom_and_dad_pair() -> None:
    nodes = _loaded_nodes()
    rice_mill = find_node(nodes, "RICE_MILL_A")
    kanto_dc = find_node(nodes, "DC_KANTO")
    assert rice_mill is not None
    assert kanto_dc is not None

    assert rice_mill.partner_key == "RICE_CORE"
    assert kanto_dc.partner_key == "RICE_CORE"
    assert any(
        node.node_character == "MOM" and node.partner_key == "RICE_CORE" for node in nodes
    )
    assert any(
        node.node_character == "DAD" and node.partner_key == "RICE_CORE" for node in nodes
    )


def test_inbound_hammock_path_exists_from_parent_child_tree_edges() -> None:
    assert has_path(_loaded_edges(), INBOUND_HAMMOCK_PATH, tree_side="inbound")


def test_outbound_hammock_path_exists_from_parent_child_tree_edges() -> None:
    assert has_path(_loaded_edges(), OUTBOUND_HAMMOCK_PATH, tree_side="outbound")


def test_market_tokyo_is_outbound_final_demand_leaf() -> None:
    market_tokyo = _node_by_name("MARKET_TOKYO")

    assert market_tokyo.is_leaf is True
    assert market_tokyo.is_market_leaf is True
    assert market_tokyo.tree_side == "outbound"


def test_capacity_and_demand_nodes_align_with_network_node_master() -> None:
    node_names = {node.node_name for node in _loaded_nodes()}

    assert EXPECTED_CAPACITY_NODES <= node_names
    assert EXPECTED_DEMAND_NODE in node_names


def test_default_layout_depths_are_derived_from_parent_child_tree_structure() -> None:
    edges = _loaded_edges()

    inbound_depths = derive_tree_depths(
        edges, root_node="supply_side_root", tree_side="inbound"
    )
    outbound_depths = derive_tree_depths(
        edges, root_node="demand_side_root", tree_side="outbound"
    )

    assert inbound_depths == {
        "supply_side_root": 0,
        "supply_point": 1,
        "RICE_MILL_A": 2,
        "FARM_REGION_A": 3,
        "Procurement_Center": 4,
    }
    assert outbound_depths == {
        "demand_side_root": 0,
        "supply_point": 1,
        "DC_KANTO": 2,
        "MARKET_TOKYO": 3,
        "Global_Sales_Office": 4,
    }


def test_position_group_and_e2e_stage_are_optional_layout_hints() -> None:
    rice_mill = _node_by_name("RICE_MILL_A")
    kanto_dc = _node_by_name("DC_KANTO")

    assert rice_mill.position_group == "RICE_CORE"
    assert kanto_dc.position_group == "RICE_CORE"
    assert rice_mill.e2e_stage is None
    assert kanto_dc.e2e_stage is None
    assert derive_tree_depths(
        _loaded_edges(), root_node="supply_side_root", tree_side="inbound"
    )["RICE_MILL_A"] == 2
    assert derive_tree_depths(
        _loaded_edges(), root_node="demand_side_root", tree_side="outbound"
    )["DC_KANTO"] == 2
