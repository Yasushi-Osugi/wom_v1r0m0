from __future__ import annotations

from typing import Any

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow
from pysi.plan.explicit_pipeline_capacity_context import weekly_capacity_rows_to_explicit_forward_capacity


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


def test_happy_path_builds_product_node_capacity_type_week_capacity_context():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(week="2027-W40", qty=5),
            row(week="2027-W41", qty=6),
        ]
    )

    assert got == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 5,
                    "2027-W41": 6,
                }
            }
        }
    }


def test_product_separation():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(product_id="PACKAGED_RICE_STANDARD", qty=5),
            row(product_id="BROWN_RICE_PREMIUM", qty=7),
        ]
    )

    assert got == {
        "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}},
        "BROWN_RICE_PREMIUM": {"MILL_EAST": {"P": {"2027-W40": 7}}},
    }


def test_node_separation():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(node_id="MILL_EAST", qty=5),
            row(node_id="MILL_WEST", qty=7),
        ]
    )

    assert got == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {"P": {"2027-W40": 5}},
            "MILL_WEST": {"P": {"2027-W40": 7}},
        }
    }


def test_capacity_type_separation():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(capacity_type="P", qty=5),
            row(capacity_type="S", qty=7),
        ]
    )

    assert got == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {"2027-W40": 5},
                "S": {"2027-W40": 7},
            }
        }
    }


def test_duplicate_product_node_capacity_type_week_rows_are_summed():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(qty=5),
            row(qty=3),
            row(week="2027-W41", qty=2.5),
            row(week="2027-W41", qty=1),
        ]
    )

    assert got == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 8,
                    "2027-W41": 3.5,
                }
            }
        }
    }


def test_week_keys_are_preserved_without_normalization():
    got = weekly_capacity_rows_to_explicit_forward_capacity(
        [
            row(week="2027-W40", qty=5),
            row(week=0, qty=6),
        ]
    )

    assert got["PACKAGED_RICE_STANDARD"]["MILL_EAST"]["P"] == {
        "2027-W40": 5,
        0: 6,
    }


def test_empty_input_returns_empty_dict():
    assert weekly_capacity_rows_to_explicit_forward_capacity([]) == {}
