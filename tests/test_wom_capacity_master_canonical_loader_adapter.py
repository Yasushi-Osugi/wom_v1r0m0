from __future__ import annotations

import pytest

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow
from pysi.capacity.capacity_master_loader import load_capacity_master_csv


def _write_csv(tmp_path, text: str):
    path = tmp_path / "capacity_master.csv"
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_capacity_master_loader_happy_path_returns_weekly_capacity_rows(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot,1,JP_445,weekly milling capacity",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W41,P,6,hard,lot,1,JP_445,next week capacity",
            ]
        ),
    )

    rows = load_capacity_master_csv(path)

    assert len(rows) == 2
    assert all(isinstance(row, WeeklyCapacityRow) for row in rows)
    assert rows[0].scenario_id == "RICE_AS_IS"
    assert rows[0].tree_side == "IN"
    assert rows[0].product_id == "PACKAGED_RICE_STANDARD"
    assert rows[0].product_name == "PACKAGED_RICE_STANDARD"
    assert rows[0].capacity_owner_type == "node"
    assert rows[0].capacity_owner_id == "MILL_EAST"
    assert rows[0].node_name == "MILL_EAST"
    assert rows[0].week == "2027-W40"
    assert rows[0].capacity_type == "P"
    assert rows[0].capacity_qty == 5
    assert rows[0].cap_mode == "hard"
    assert rows[0].unit == "lot"
    assert rows[0].priority == "1"
    assert rows[0].calendar_id == "JP_445"
    assert rows[0].comment == "weekly milling capacity"
    assert rows[0].source_granularity == "weekly"
    assert rows[0].source_file == str(path)
    assert rows[0].source_id == "capacity_master.csv:2"
    assert rows[1].source_id == "capacity_master.csv:3"


def test_capacity_master_loader_missing_required_columns_raises_value_error(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,cap_mode,unit",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,hard,lot",
            ]
        ),
    )

    with pytest.raises(ValueError, match="missing required columns") as exc_info:
        load_capacity_master_csv(path)

    assert "capacity_qty" in str(exc_info.value)


def test_capacity_master_loader_invalid_capacity_qty_raises_value_error(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,abc,hard,lot",
            ]
        ),
    )

    with pytest.raises(ValueError, match="capacity_qty"):
        load_capacity_master_csv(path)


def test_capacity_master_loader_optional_columns_absent_uses_safe_defaults(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot",
            ]
        ),
    )

    rows = load_capacity_master_csv(path)

    assert len(rows) == 1
    assert rows[0].priority is None
    assert rows[0].calendar_id is None
    assert rows[0].comment == ""


def test_capacity_master_loader_preserves_week_keys_without_normalization(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,0,P,6,hard,lot",
            ]
        ),
    )

    rows = load_capacity_master_csv(path)

    assert [row.week for row in rows] == ["2027-W40", "0"]


def test_capacity_master_loader_preserves_duplicate_rows(tmp_path):
    path = _write_csv(
        tmp_path,
        "\n".join(
            [
                "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot",
                "RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot",
            ]
        ),
    )

    rows = load_capacity_master_csv(path)

    assert len(rows) == 2
    assert [row.source_id for row in rows] == ["capacity_master.csv:2", "capacity_master.csv:3"]
