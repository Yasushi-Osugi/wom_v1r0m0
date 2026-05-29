from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow

REQUIRED_COLUMNS = {
    "scenario_id",
    "tree_side",
    "node_name",
    "product_name",
    "week",
    "capacity_type",
    "capacity_qty",
    "cap_mode",
    "unit",
}


def _parse_capacity_qty(raw_value: Any, *, row_num: int) -> int | float:
    value = str(raw_value if raw_value is not None else "").strip()
    if value == "":
        raise ValueError(f"capacity_qty is required (row {row_num})")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"capacity_qty must be numeric (row {row_num}, value={value!r})") from exc
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _required_str(row: dict[str, str], key: str, row_num: int) -> str:
    value = str(row.get(key, "") or "").strip()
    if value == "":
        raise ValueError(f"{key} is required (row {row_num})")
    return value


def load_capacity_master_csv(path: str | Path) -> list[WeeklyCapacityRow]:
    """Load a capacity_master.csv file into canonical WeeklyCapacityRow objects.

    This loader intentionally stops at the canonical row boundary. It does not
    attach rows to planner/runtime capacity contexts and does not normalize week
    keys; the week string is preserved exactly after CSV whitespace trimming.
    """

    csv_path = Path(path)
    if not csv_path.exists():
        raise ValueError(f"capacity master csv not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("capacity master csv has no header")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"capacity master csv missing required columns: {sorted(missing)}")

        rows: list[WeeklyCapacityRow] = []
        for row_num, row in enumerate(reader, start=2):
            scenario_id = _required_str(row, "scenario_id", row_num)
            tree_side = _required_str(row, "tree_side", row_num)
            node_name = _required_str(row, "node_name", row_num)
            product_name = _required_str(row, "product_name", row_num)
            week = _required_str(row, "week", row_num)
            capacity_type = _required_str(row, "capacity_type", row_num)
            cap_mode = _required_str(row, "cap_mode", row_num)
            unit = _required_str(row, "unit", row_num)
            capacity_qty = _parse_capacity_qty(row.get("capacity_qty"), row_num=row_num)

            rows.append(
                WeeklyCapacityRow(
                    scenario_id=scenario_id,
                    product_id=product_name,
                    capacity_owner_type="node",
                    capacity_owner_id=node_name,
                    week=week,
                    capacity_type=capacity_type,
                    capacity_qty=capacity_qty,
                    cap_mode=cap_mode,
                    unit=unit,
                    source_granularity="weekly",
                    source_id=f"{csv_path.name}:{row_num}",
                    comment=str(row.get("comment", "") or "").strip(),
                    tree_side=tree_side,
                    priority=(str(row.get("priority", "") or "").strip() or None),
                    calendar_id=(str(row.get("calendar_id", "") or "").strip() or None),
                    source_file=str(csv_path),
                )
            )
    return rows
