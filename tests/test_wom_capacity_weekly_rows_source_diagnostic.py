from __future__ import annotations

from types import SimpleNamespace

from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    build_capacity_weekly_rows_source_diagnostic,
    build_explicit_pipeline_capacity_scenario_alignment_diagnostic,
)


def _source_summary(**overrides):
    summary = {
        "available": True,
        "source_kind": "scenario_package_capacity_master",
        "source_path": "/tmp/scenario/masters/capacity_master.csv",
        "row_count": 2,
        "attached_to_env": True,
        "messages": [
            "Capacity weekly rows source: loaded 2 rows from capacity_master.csv."
        ],
    }
    summary.update(overrides)
    return summary


def _runtime_summary(**overrides):
    summary = {
        "available": True,
        "input_row_count": 2,
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


def test_missing_summary_reports_missing_reason() -> None:
    env = SimpleNamespace()

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["available"] is False
    assert diagnostic["summary_available"] is False
    assert diagnostic["reason"] == "missing_capacity_weekly_rows_load_summary"
    assert "Capacity weekly rows source: load summary missing." in diagnostic["messages"]


def test_loaded_non_empty_source_reports_consistent_env_rows() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(),
        capacity_weekly_rows=[object(), object()],
        capacity_weekly_rows_source_kind="scenario_package_capacity_master",
        capacity_weekly_rows_source_path="/tmp/scenario/masters/capacity_master.csv",
    )

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["available"] is True
    assert diagnostic["summary_available"] is True
    assert diagnostic["env_rows_present"] is True
    assert diagnostic["env_row_count"] == 2
    assert diagnostic["row_count_matches_env"] is True
    assert diagnostic["source_kind_matches_env"] is True
    assert diagnostic["source_path_matches_env"] is True
    assert "Capacity weekly rows source: load summary available." in diagnostic["messages"]
    assert "Capacity weekly rows source: loaded 2 rows." in diagnostic["messages"]


def test_object_style_load_summary_is_supported() -> None:
    summary = SimpleNamespace(
        available=True,
        source_kind="capacity_master_csv",
        source_path="/tmp/capacity_master.csv",
        row_count=1,
        attached_to_env=True,
        messages=["object summary message"],
    )
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=summary,
        capacity_weekly_rows=[object()],
        capacity_weekly_rows_source_kind="capacity_master_csv",
        capacity_weekly_rows_source_path="/tmp/capacity_master.csv",
    )

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["available"] is True
    assert diagnostic["row_count"] == 1
    assert diagnostic["row_count_matches_env"] is True
    assert "object summary message" in diagnostic["messages"]


def test_missing_source_summary_reports_source_missing_reason() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(
            available=False,
            source_kind="missing",
            source_path=None,
            row_count=0,
            attached_to_env=False,
            messages=["Capacity weekly rows source: no capacity master source found."],
        )
    )

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["available"] is False
    assert diagnostic["summary_available"] is True
    assert diagnostic["source_kind"] == "missing"
    assert diagnostic["source_path"] is None
    assert diagnostic["row_count"] == 0
    assert diagnostic["attached_to_env"] is False
    assert diagnostic["env_rows_present"] is False
    assert diagnostic["env_row_count"] == 0
    assert diagnostic["reason"] == "capacity_weekly_rows_source_missing"
    assert (
        "Capacity weekly rows source: no capacity master source found."
        in diagnostic["messages"]
    )


def test_empty_valid_source_reports_zero_rows_as_loaded() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(row_count=0),
        capacity_weekly_rows=[],
        capacity_weekly_rows_source_kind="scenario_package_capacity_master",
        capacity_weekly_rows_source_path="/tmp/scenario/masters/capacity_master.csv",
    )

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["available"] is True
    assert diagnostic["env_rows_present"] is True
    assert diagnostic["env_row_count"] == 0
    assert diagnostic["row_count_matches_env"] is True
    assert "Capacity weekly rows source: loaded 0 rows." in diagnostic["messages"]


def test_manual_rows_without_summary_reports_rows_present_without_load_summary() -> None:
    env = SimpleNamespace(capacity_weekly_rows=[object(), object(), object()])

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["summary_available"] is False
    assert diagnostic["env_rows_present"] is True
    assert diagnostic["env_row_count"] == 3
    assert (
        "Capacity weekly rows source: env.capacity_weekly_rows present without load summary."
        in diagnostic["messages"]
    )


def test_row_count_mismatch_reports_warning_message() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(row_count=3),
        capacity_weekly_rows=[object(), object()],
        capacity_weekly_rows_source_kind="scenario_package_capacity_master",
        capacity_weekly_rows_source_path="/tmp/scenario/masters/capacity_master.csv",
    )

    diagnostic = build_capacity_weekly_rows_source_diagnostic(env)

    assert diagnostic["row_count_matches_env"] is False
    assert (
        "Capacity weekly rows source: summary row_count differs from env row count."
        in diagnostic["messages"]
    )
    assert (
        "Capacity weekly rows source: summary row_count differs from env row count."
        in diagnostic["warnings"]
    )


def test_integration_adds_capacity_weekly_rows_source_key() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(),
        capacity_weekly_rows=[object(), object()],
        capacity_weekly_rows_source_kind="scenario_package_capacity_master",
        capacity_weekly_rows_source_path="/tmp/scenario/masters/capacity_master.csv",
    )

    diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=None,
        env=env,
    )

    assert "capacity_weekly_rows_source" in diagnostic
    assert diagnostic["capacity_weekly_rows_source"]["available"] is True


def test_source_messages_precede_runtime_attachment_messages() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows_load_summary=_source_summary(),
        capacity_weekly_rows=[object(), object()],
        capacity_weekly_rows_source_kind="scenario_package_capacity_master",
        capacity_weekly_rows_source_path="/tmp/scenario/masters/capacity_master.csv",
        capacity_runtime_attachment_summary=_runtime_summary(),
        explicit_pipeline_forward_weekly_capacity={
            "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 1}}}
        },
        explicit_pipeline_backward_weekly_capability_from_weekly_rows={
            "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 1}}}
        },
    )

    diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product="PACKAGED_RICE_STANDARD",
        backward_weekly_capability=None,
        forward_weekly_capacity=None,
        env=env,
    )

    messages = diagnostic["messages"]
    source_index = messages.index("Capacity weekly rows source: load summary available.")
    runtime_index = messages.index("Capacity runtime attachment: summary available.")
    assert source_index < runtime_index
