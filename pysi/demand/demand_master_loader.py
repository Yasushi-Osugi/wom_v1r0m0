from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "scenario_id",
    "demand_node",
    "product_name",
    "week",
    "demand_qty",
    "unit",
    "source_granularity",
    "priority",
    "calendar_id",
    "comment",
}


@dataclass(frozen=True)
class WeeklyDemandRow:
    """Canonical weekly demand row for WOM demand-source entrance slices."""

    scenario_id: str
    demand_node: str
    product_id: str
    week: str
    demand_qty: int | float
    unit: str = "lot"
    source_granularity: str = "weekly"
    priority: int | None = None
    calendar_id: str | None = None
    comment: str | None = None
    source_id: str | None = None
    source_file: str | None = None

    @property
    def node_name(self) -> str:
        return self.demand_node

    @property
    def product_name(self) -> str:
        return self.product_id


def _parse_demand_qty(raw_value: Any, *, row_num: int) -> int | float:
    value = str(raw_value if raw_value is not None else "").strip()
    if value == "":
        raise ValueError(f"demand_qty is required (row {row_num})")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"demand_qty must be numeric (row {row_num}, value={value!r})") from exc
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _parse_priority(raw_value: Any) -> int | None:
    value = str(raw_value if raw_value is not None else "").strip()
    if value == "":
        return None
    return int(value)


def _required_str(row: dict[str, str], key: str, row_num: int) -> str:
    value = str(row.get(key, "") or "").strip()
    if value == "":
        raise ValueError(f"{key} is required (row {row_num})")
    return value


def load_weekly_demand_master_csv(path: str | Path) -> list[WeeklyDemandRow]:
    """Load weekly demand_master.csv rows without changing week bucket strings.

    This loader is intentionally narrow: it creates canonical weekly demand rows
    only. It does not read legacy S_month_data.csv files, perform monthly-to-
    weekly allocation, mutate planner nodes, or run PSI planning behavior.
    """

    csv_path = Path(path)
    if not csv_path.exists():
        raise ValueError(f"weekly demand master csv not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("weekly demand master csv has no header")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"weekly demand master csv missing required columns: {sorted(missing)}")

        rows: list[WeeklyDemandRow] = []
        for row_num, row in enumerate(reader, start=2):
            scenario_id = _required_str(row, "scenario_id", row_num)
            demand_node = _required_str(row, "demand_node", row_num)
            product_name = _required_str(row, "product_name", row_num)
            week = _required_str(row, "week", row_num)
            unit = _required_str(row, "unit", row_num)
            source_granularity = _required_str(row, "source_granularity", row_num)
            demand_qty = _parse_demand_qty(row.get("demand_qty"), row_num=row_num)

            rows.append(
                WeeklyDemandRow(
                    scenario_id=scenario_id,
                    demand_node=demand_node,
                    product_id=product_name,
                    week=week,
                    demand_qty=demand_qty,
                    unit=unit,
                    source_granularity=source_granularity,
                    priority=_parse_priority(row.get("priority")),
                    calendar_id=(str(row.get("calendar_id", "") or "").strip() or None),
                    comment=(str(row.get("comment", "") or "").strip() or None),
                    source_id=f"{csv_path.name}:{row_num}",
                    source_file=str(csv_path),
                )
            )
    return rows
