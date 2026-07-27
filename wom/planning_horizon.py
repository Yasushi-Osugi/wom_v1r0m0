"""Planning/reporting horizon configuration for model-folder workflows."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Optional


def iso_week_date(value: str) -> date:
    try:
        year, week = str(value).strip().split("-W")
        return date.fromisocalendar(int(year), int(week), 1)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid ISO week: {value!r}") from exc


def iso_weeks(start_week: str, count: int) -> list[str]:
    if int(count) <= 0:
        raise ValueError("week count must be > 0")
    start = iso_week_date(start_week)
    return [
        f"{d.isocalendar().year}-W{d.isocalendar().week:02d}"
        for d in (start + timedelta(weeks=i) for i in range(int(count)))
    ]


@dataclass(frozen=True)
class PlanningHorizon:
    planning_start_week: str
    planning_weeks: int
    reporting_start_week: str
    reporting_weeks: int
    source: str = "model-config"

    def __post_init__(self) -> None:
        planning = iso_weeks(self.planning_start_week, self.planning_weeks)
        reporting = iso_weeks(self.reporting_start_week, self.reporting_weeks)
        if iso_week_date(self.reporting_start_week) < iso_week_date(self.planning_start_week):
            raise ValueError("reporting_start_week must not precede planning_start_week")
        if reporting[-1] not in planning:
            raise ValueError("reporting horizon must be inside planning horizon")

    @property
    def planning_week_labels(self) -> list[str]:
        return iso_weeks(self.planning_start_week, self.planning_weeks)

    @property
    def reporting_week_labels(self) -> list[str]:
        return iso_weeks(self.reporting_start_week, self.reporting_weeks)


def load_planning_horizon(path: str | Path) -> PlanningHorizon:
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1:
        raise ValueError("planning_horizon.csv must contain exactly one config row")
    row = rows[0]
    required = {"planning_start_week", "planning_weeks",
                "reporting_start_week", "reporting_weeks"}
    missing = required - set(row)
    if missing:
        raise ValueError(f"planning_horizon.csv missing columns: {sorted(missing)}")
    return PlanningHorizon(
        row["planning_start_week"].strip(), int(row["planning_weeks"]),
        row["reporting_start_week"].strip(), int(row["reporting_weeks"]))


def autodetect_horizon(demand_weeks: Iterable[str]) -> Optional[PlanningHorizon]:
    weeks = sorted({str(w).strip() for w in demand_weeks if str(w).strip()})
    if not weeks:
        return None
    return PlanningHorizon(weeks[0], len(weeks), weeks[0], len(weeks),
                           source="demand-autodetect")


def ppc_horizons(
    planning_week_labels: Iterable[str],
    reporting_start_week: str,
    reporting_weeks: int,
) -> tuple[list[str], list[str]]:
    """Return separate valuation and standard-reporting week lists for PPC."""
    planning = list(planning_week_labels)
    reporting = iso_weeks(reporting_start_week, reporting_weeks)
    if not planning:
        raise ValueError("PPC Planning Horizon must not be empty")
    if not set(reporting).issubset(planning):
        raise ValueError("PPC Reporting Horizon must be inside Planning Horizon")
    return planning, reporting
