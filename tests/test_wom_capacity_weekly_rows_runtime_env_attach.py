from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow
from pysi.plan.explicit_pipeline_capacity_context import (
    attach_capacity_runtime_contexts_to_env_from_weekly_rows,
)


def row(
    product_id: str = "PACKAGED_RICE_STANDARD",
    node_id: str = "MILL_EAST",
    capacity_type: str = "P",
    week: Any = "2027-W40",
    qty: int | float = 5,
) -> WeeklyCapacityRow:
    return WeeklyCapacityRow(
        scenario_id="RICE_AS_IS",
        product_id=product_id,
        capacity_owner_type="node",
        capacity_owner_id=node_id,
        week=week,
        capacity_type=capacity_type,
        capacity_qty=qty,
        cap_mode="hard",
        unit="lot",
        source_granularity="weekly",
    )


def test_attaches_forward_capacity_context_from_weekly_rows() -> None:
    env = SimpleNamespace()

    attach_capacity_runtime_contexts_to_env_from_weekly_rows(
        env,
        [row(week="2027-W40", qty=5), row(week="2027-W41", qty=7)],
    )

    assert env.explicit_pipeline_forward_weekly_capacity == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 5,
                    "2027-W41": 7,
                }
            }
        }
    }


def test_attaches_backward_capacity_context_to_safe_canonical_side_attribute() -> None:
    env = SimpleNamespace(explicit_pipeline_backward_weekly_capability={"existing": "kept"})

    summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, [row()])

    assert env.explicit_pipeline_backward_weekly_capability == {"existing": "kept"}
    assert env.explicit_pipeline_backward_weekly_capability_from_weekly_rows == {
        "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}}
    }
    assert summary["backward_consumer_attribute_replaced"] is False
    assert summary["backward_canonical_attribute_attached"] is True


def test_attaches_source_rows_and_summary() -> None:
    env = SimpleNamespace()
    rows = [row(qty=5), row(qty=6)]

    summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows)

    assert env.capacity_weekly_rows == rows
    assert env.capacity_weekly_rows is not rows
    assert env.capacity_runtime_attachment_summary == summary


def test_summary_contains_diagnostic_counts_and_shape_names() -> None:
    env = SimpleNamespace()

    summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(
        env,
        [
            row(week="2027-W40", qty=5),
            row(week="2027-W41", qty=6),
            row(product_id="BROWN_RICE_PREMIUM", capacity_type="S", week="2027-W41", qty=7),
        ],
    )

    assert summary["available"] is True
    assert summary["input_row_count"] == 3
    assert summary["attached_forward"] is True
    assert summary["attached_backward"] is True
    assert summary["forward_shape"] == "product_node_type_week_qty_v1"
    assert summary["backward_shape"] == "product_node_type_week_qty_v1"
    assert summary["forward_product_count"] == 2
    assert summary["backward_product_count"] == 2
    assert summary["node_count"] == 1
    assert summary["capacity_type_count"] == 2
    assert summary["week_key_count"] == 2
    assert summary["week_key_domain"] == "preserve"
    assert summary["messages"] == []


def test_empty_rows_do_not_crash_and_attach_empty_contexts_when_requested() -> None:
    env = SimpleNamespace()

    summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, [])

    assert env.explicit_pipeline_forward_weekly_capacity == {}
    assert env.explicit_pipeline_backward_weekly_capability_from_weekly_rows == {}
    assert env.capacity_weekly_rows == []
    assert summary["available"] is False
    assert summary["input_row_count"] == 0
    assert summary["attached_forward"] is True
    assert summary["attached_backward"] is True
    assert summary["messages"] == ["No WeeklyCapacityRow rows provided."]


def test_switch_flags_control_attachments_without_suppressing_returned_summary() -> None:
    env = SimpleNamespace()

    summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(
        env,
        [row()],
        attach_forward=False,
        attach_backward=False,
        attach_rows=False,
        attach_summary=False,
    )

    assert not hasattr(env, "explicit_pipeline_forward_weekly_capacity")
    assert not hasattr(env, "explicit_pipeline_backward_weekly_capability_from_weekly_rows")
    assert not hasattr(env, "capacity_weekly_rows")
    assert not hasattr(env, "capacity_runtime_attachment_summary")
    assert summary["available"] is True
    assert summary["attached_forward"] is False
    assert summary["attached_backward"] is False
    assert summary["attached_rows"] is False
    assert summary["forward_shape"] == "not_attached"
    assert summary["backward_shape"] == "not_attached"
    assert summary["week_key_domain"] == "preserve"
