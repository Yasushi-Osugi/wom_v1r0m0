from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow
from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    apply_capacity_runtime_attachment_preflight,
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


def test_preflight_skips_safely_when_capacity_weekly_rows_missing() -> None:
    env = SimpleNamespace()

    result = apply_capacity_runtime_attachment_preflight(env)

    assert result["applied"] is False
    assert result["reason"] == "capacity_weekly_rows_missing"
    assert result["row_source"] == "missing"
    assert result["input_row_count"] == 0
    assert result["attachment_summary"] is None
    assert result["runtime_attachment"]["available"] is False
    assert result["runtime_attachment"]["reason"] == "missing_capacity_runtime_attachment_summary"
    assert (
        "Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing."
        in result["messages"]
    )
    assert not hasattr(env, "explicit_pipeline_forward_weekly_capacity")


def test_preflight_applies_when_capacity_weekly_rows_exist() -> None:
    env = SimpleNamespace(
        capacity_weekly_rows=[row(week="2027-W40", qty=5), row(week="2027-W41", qty=7)]
    )

    result = apply_capacity_runtime_attachment_preflight(env)

    assert result["applied"] is True
    assert result["reason"] is None
    assert result["row_source"] == "env.capacity_weekly_rows"
    assert result["input_row_count"] == 2
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
    assert hasattr(env, "explicit_pipeline_backward_weekly_capability_from_weekly_rows")
    assert hasattr(env, "capacity_runtime_attachment_summary")
    assert result["attachment_summary"] is env.capacity_runtime_attachment_summary
    assert result["runtime_attachment"]["summary_available"] is True
    assert "Capacity runtime attachment: summary available." in result["messages"]


def test_preflight_applies_empty_capacity_weekly_rows_as_available_source() -> None:
    env = SimpleNamespace(capacity_weekly_rows=[])

    result = apply_capacity_runtime_attachment_preflight(env)

    assert result["applied"] is True
    assert result["input_row_count"] == 0
    assert env.explicit_pipeline_forward_weekly_capacity == {}
    assert env.explicit_pipeline_backward_weekly_capability_from_weekly_rows == {}
    assert result["attachment_summary"]["available"] is False
    assert result["attachment_summary"]["input_row_count"] == 0
    assert "No WeeklyCapacityRow rows provided." in result["messages"]


def test_preflight_appends_to_external_messages_list() -> None:
    env = SimpleNamespace(capacity_weekly_rows=[row()])
    messages: list[str] = []

    result = apply_capacity_runtime_attachment_preflight(env, messages=messages)

    assert messages == result["messages"]
    assert "Capacity runtime attachment: summary available." in messages


def test_preflight_is_idempotent_for_repeated_calls() -> None:
    env = SimpleNamespace(capacity_weekly_rows=[row(week="2027-W40", qty=5)])

    first = apply_capacity_runtime_attachment_preflight(env)
    first_forward = env.explicit_pipeline_forward_weekly_capacity.copy()
    first_backward = env.explicit_pipeline_backward_weekly_capability_from_weekly_rows.copy()
    first_summary = dict(env.capacity_runtime_attachment_summary)

    second = apply_capacity_runtime_attachment_preflight(env)

    assert first["applied"] is True
    assert second["applied"] is True
    assert env.explicit_pipeline_forward_weekly_capacity == first_forward
    assert env.explicit_pipeline_backward_weekly_capability_from_weekly_rows == first_backward
    assert env.capacity_runtime_attachment_summary == first_summary
    assert second["runtime_attachment"]["summary_available"] is True
