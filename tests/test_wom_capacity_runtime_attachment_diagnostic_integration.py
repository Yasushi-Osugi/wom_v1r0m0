from __future__ import annotations

from types import SimpleNamespace

from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env,
    build_capacity_runtime_attachment_diagnostic,
)


def _summary(**overrides):
    summary = {
        "available": True,
        "input_row_count": 1,
        "attached_rows": True,
        "attached_forward": True,
        "attached_backward": True,
        "forward_shape": "product_node_type_week_qty_v1",
        "backward_shape": "product_node_type_week_qty_v1",
        "week_key_domain": "preserve",
        "backward_consumer_attribute_replaced": False,
        "backward_canonical_attribute_attached": True,
        "messages": [],
    }
    summary.update(overrides)
    return summary


def test_runtime_attachment_summary_available_reports_attached_contexts() -> None:
    env = SimpleNamespace(
        capacity_runtime_attachment_summary=_summary(),
        explicit_pipeline_forward_weekly_capacity={"P1": {"N1": {"P": {"2027-W40": 1}}}},
        explicit_pipeline_backward_weekly_capability_from_weekly_rows={
            "P1": {"N1": {"P": {"2027-W40": 1}}}
        },
        capacity_weekly_rows=[object()],
    )

    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    assert diagnostic["available"] is True
    assert diagnostic["summary_available"] is True
    assert diagnostic["consistency"]["summary_matches_env"] is True
    assert diagnostic["week_key_domain"] == "preserve"
    assert diagnostic["shape"]["forward_shape_from_summary"] == "product_node_type_week_qty_v1"
    assert "Capacity runtime attachment: summary available." in diagnostic["messages"]
    assert "Capacity runtime attachment: forward context attached." in diagnostic["messages"]
    assert (
        "Capacity runtime attachment: backward canonical side context attached."
        in diagnostic["messages"]
    )
    assert "Capacity runtime attachment: week keys preserved." in diagnostic["messages"]
    assert "Capacity runtime attachment: shape = product_node_type_week_qty_v1." in diagnostic[
        "messages"
    ]


def test_runtime_attachment_summary_missing_reports_reason() -> None:
    env = SimpleNamespace()

    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    assert diagnostic["available"] is False
    assert diagnostic["summary_available"] is False
    assert diagnostic["reason"] == "missing_capacity_runtime_attachment_summary"
    assert diagnostic["messages"] == ["Capacity runtime attachment: summary missing."]


def test_forward_inconsistency_reports_missing_despite_summary() -> None:
    env = SimpleNamespace(
        capacity_runtime_attachment_summary=_summary(attached_forward=True),
        explicit_pipeline_backward_weekly_capability_from_weekly_rows={},
        capacity_weekly_rows=[],
    )

    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    assert diagnostic["consistency"]["forward_env_attribute_present"] is False
    assert diagnostic["consistency"]["summary_matches_env"] is False
    assert (
        "Capacity runtime attachment: forward context missing despite summary."
        in diagnostic["messages"]
    )
    assert (
        "Capacity runtime attachment: forward context missing despite summary."
        in diagnostic["warnings"]
    )


def test_backward_canonical_inconsistency_reports_missing_despite_summary() -> None:
    env = SimpleNamespace(
        capacity_runtime_attachment_summary=_summary(
            backward_canonical_attribute_attached=True
        ),
        explicit_pipeline_forward_weekly_capacity={},
        capacity_weekly_rows=[],
    )

    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    assert diagnostic["consistency"]["backward_canonical_env_attribute_present"] is False
    assert diagnostic["consistency"]["summary_matches_env"] is False
    assert (
        "Capacity runtime attachment: backward canonical side context missing despite summary."
        in diagnostic["messages"]
    )


def test_backward_consumer_facing_not_replaced_is_visible() -> None:
    env = SimpleNamespace(
        capacity_runtime_attachment_summary=_summary(
            backward_consumer_attribute_replaced=False,
            backward_canonical_attribute_attached=True,
        ),
        explicit_pipeline_forward_weekly_capacity={},
        explicit_pipeline_backward_weekly_capability_from_weekly_rows={},
        capacity_weekly_rows=[],
    )

    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    assert diagnostic["shape"]["backward_consumer_attribute_replaced"] is False
    assert (
        "Capacity runtime attachment: backward consumer-facing capability was not replaced."
        in diagnostic["messages"]
    )


def test_capacity_scenario_alignment_diagnostic_includes_runtime_attachment_messages() -> None:
    env = SimpleNamespace(
        product_selected="P1",
        capacity_runtime_attachment_summary=_summary(),
        explicit_pipeline_forward_weekly_capacity={"P1": {"N1": {"P": {"2027-W40": 1}}}},
        explicit_pipeline_backward_weekly_capability_from_weekly_rows={
            "P1": {"N1": {"P": {"2027-W40": 1}}}
        },
        capacity_weekly_rows=[object()],
    )

    diagnostic = attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(
        env
    )

    assert "runtime_attachment" in diagnostic
    assert diagnostic["runtime_attachment"]["available"] is True
    assert "Capacity runtime attachment: summary available." in diagnostic["messages"]
