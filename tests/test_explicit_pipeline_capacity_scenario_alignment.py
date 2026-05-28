from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    build_explicit_pipeline_capacity_scenario_alignment_diagnostic,
    classify_week_key_domain,
)


class _Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []


def _forward_week_map(product="PACKAGED_RICE_STANDARD", node="MILL_EAST", week="2027-W40"):
    return {product: {node: {"P": {week: 5}}}}


def test_classify_week_key_domain_cases():
    assert classify_week_key_domain([]) == "empty"
    assert classify_week_key_domain([0, 1]) == "integer_index"
    assert classify_week_key_domain(["0", "1"]) == "integer_string_index"
    assert classify_week_key_domain(["2027-W40", "2027-W41"]) == "label_week"
    assert classify_week_key_domain(["2027-10-04"]) == "date"
    assert classify_week_key_domain([0, "2027-W40"]) == "mixed"


def test_product_mismatch_diagnostic():
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="IPHONE_NM_2028_BASE",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(),
    )

    assert diag["forward_capacity"]["selected_product_present"] is False
    assert diag["alignment"]["product_alignment"] in {"mismatch", "partial_match"}
    assert any("not present in forward capacity context" in m for m in diag["messages"])


def test_product_match_diagnostic():
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(),
    )

    assert diag["forward_capacity"]["selected_product_present"] is True


def test_node_mismatch_diagnostic():
    root = _Node("supply_point", children=[_Node("MOM_final_assy_ASIA")])
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(node="MILL_EAST"),
        outbound_root=root,
    )

    assert diag["runtime_tree"]["capacity_node_match_count"] == 0
    assert diag["alignment"]["node_alignment"] == "mismatch"


def test_node_partial_match_diagnostic():
    root = _Node("supply_point", children=[_Node("MILL_EAST")])
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(node="MILL_EAST"),
        outbound_root=root,
    )

    assert diag["alignment"]["node_alignment"] in {"aligned", "partial_match"}


def test_week_domain_mismatch_diagnostic():
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(week="2027-W40"),
        consumer_forward_week_domain="integer_index",
    )

    assert diag["alignment"]["week_domain_alignment"] == "mismatch"


def test_shape_mismatch_diagnostic():
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=_forward_week_map(),
        consumer_forward_capacity_shape_version="product_node_type_week_list_v0",
    )

    assert diag["alignment"]["shape_alignment"] == "mismatch"


def test_list_indexed_forward_capacity_shape_diagnostic():
    forward = {"P1": {"N1": {"P": [1, 2, 3]}}}
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="P1",
        backward_weekly_capability=None,
        forward_weekly_capacity=forward,
        consumer_forward_capacity_shape_version="product_node_type_week_list_v0",
    )

    assert diag["forward_capacity"]["shape_version"] == "product_node_type_week_list_v0"
    assert diag["alignment"]["shape_alignment"] == "aligned"


def test_backward_capability_diagnostic():
    backward = {"MILL_EAST": {"PACKAGED_RICE_STANDARD": {"2027-W40": 5}}}
    diag = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=backward,
        forward_weekly_capacity=None,
    )

    assert diag["backward_capability"]["available"] is True
    assert diag["backward_capability"]["shape_version"] == "node_product_week_map_v1"
