from types import SimpleNamespace

import pytest

from pysi.plan.weekly_forward_push_with_capacity import weekly_forward_push_with_capacity
from pysi.reporting.explicit_pipeline_capacity_report import build_explicit_pipeline_capacity_report
from pysi.reporting.explicit_pipeline_issue_candidates import build_explicit_pipeline_issue_candidates
from pysi.gui.explicit_pipeline_management_cockpit_view import build_explicit_pipeline_kpi_graph_view_model


class _Node:
    def __init__(self, name: str, psi4supply, children=None):
        self.name = name
        self.psi4supply = psi4supply
        self.children = children or []


def _single_week_supply_node(node_name="N1"):
    return _Node(node_name, psi4supply=[[[], [], [], ["L1"]]])


def test_forward_capacity_product_week_dict_shape_raises_key_error_today():
    root = _single_week_supply_node()
    weekly_capacity = {
        "P1": {
            "N1": {
                "P": {
                    "2027-W40": 0,
                }
            }
        }
    }

    with pytest.raises(KeyError):
        weekly_forward_push_with_capacity(root=root, product="P1", weekly_capacity=weekly_capacity)


def test_issue_lineage_warning_count_is_planning_plus_management():
    pipeline_result = SimpleNamespace(
        product_name="IPHONE_NM_2028_BASE",
        blocked_lot_ids=["L1", "L2"],
        overflow_i_lot_ids=[],
        backlog_lot_ids=[],
        shifted_lot_ids=[],
        missing_lot_ids=[],
        non_list_bucket_errors=[],
        non_string_lot_errors=[],
        capacity_usage=[],
        capacity_violations=[],
        replan_commands=[],
        message="",
    )
    report = build_explicit_pipeline_capacity_report(pipeline_result)
    bundle = build_explicit_pipeline_issue_candidates(report)

    assert report.summary["lot_exception_record_count"] == 2
    assert bundle.summary["planning_issue_candidate_count"] == 2
    assert bundle.summary["management_issue_candidate_count"] == 2
    assert bundle.summary["warning_count"] == 4


def test_weekly_graph_shows_unavailable_when_top_issues_have_no_week():
    vm = {
        "available": True,
        "issue_summary": {"error_count": 0, "warning_count": 1, "info_count": 0},
        "top_impact_issues": [{"issue_type": "blocked_lot", "node": "N1", "week": "", "estimated_total_business_impact": 0.0}],
        "executive_kpi_summary": {
            "estimated_lost_sales_value_total": 0.0,
            "estimated_margin_impact_total": 0.0,
            "estimated_inventory_cost_impact_total": 0.0,
            "estimated_capacity_cost_impact_total": 0.0,
            "estimated_service_penalty_total": 0.0,
        },
        "messages": [],
    }

    graph = build_explicit_pipeline_kpi_graph_view_model(vm)

    assert graph["weekly_issue_counts"] == []
    assert graph["impact_composition"]
