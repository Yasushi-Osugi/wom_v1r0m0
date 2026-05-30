from __future__ import annotations

from pathlib import Path
from typing import Any

from pysi.capacity.capacity_master_loader import load_capacity_master_csv


def _missing_summary() -> dict[str, Any]:
    return {
        "available": False,
        "source_kind": "missing",
        "source_path": None,
        "row_count": 0,
        "attached_to_env": False,
        "messages": ["Capacity weekly rows source: no capacity master source found."],
    }


def _scenario_config_capacity_master_path(
    scenario_root: Path | None, scenario_config: dict[str, Any] | None
) -> Path | None:
    if not isinstance(scenario_config, dict):
        return None

    masters = scenario_config.get("masters")
    if not isinstance(masters, dict):
        return None

    configured_path = masters.get("capacity_master")
    if not configured_path:
        return None

    path = Path(configured_path)
    if path.is_absolute():
        return path
    if scenario_root is None:
        return None
    return scenario_root / path


def _resolve_capacity_master_source(
    *,
    capacity_master_path: str | Path | None,
    scenario_root: str | Path | None,
    scenario_config: dict[str, Any] | None,
) -> tuple[str, Path] | tuple[str, None]:
    root = Path(scenario_root) if scenario_root is not None else None

    if capacity_master_path is not None:
        path = Path(capacity_master_path)
        if path.exists():
            return "capacity_master_csv", path
        return "missing", None

    configured_path = _scenario_config_capacity_master_path(root, scenario_config)
    if configured_path is not None and configured_path.exists():
        return "scenario_package_capacity_master", configured_path

    if root is not None:
        masters_path = root / "masters" / "capacity_master.csv"
        if masters_path.exists():
            return "scenario_package_capacity_master", masters_path

        direct_path = root / "capacity_master.csv"
        if direct_path.exists():
            return "scenario_package_capacity_master", direct_path

    return "missing", None


def load_capacity_weekly_rows_to_env(
    env: Any,
    *,
    capacity_master_path: str | Path | None = None,
    scenario_root: str | Path | None = None,
    scenario_config: dict[str, Any] | None = None,
    required: bool = False,
) -> dict[str, Any]:
    """Load canonical capacity master rows into ``env.capacity_weekly_rows``.

    Source resolution is intentionally narrow and deterministic:

    1. explicit ``capacity_master_path``
    2. ``scenario_config["masters"]["capacity_master"]`` relative to ``scenario_root``
    3. ``scenario_root / "masters" / "capacity_master.csv"``
    4. ``scenario_root / "capacity_master.csv"``

    CSV parsing and validation are delegated to ``load_capacity_master_csv``.
    Week keys are preserved by that canonical loader without normalization.
    """

    source_kind, source_path = _resolve_capacity_master_source(
        capacity_master_path=capacity_master_path,
        scenario_root=scenario_root,
        scenario_config=scenario_config,
    )

    if source_path is None:
        summary = _missing_summary()
        env.capacity_weekly_rows_load_summary = summary
        if required:
            raise FileNotFoundError(
                "Capacity weekly rows source: no capacity master source found."
            )
        return summary

    rows = load_capacity_master_csv(source_path)
    summary = {
        "available": True,
        "source_kind": source_kind,
        "source_path": str(source_path),
        "row_count": len(rows),
        "attached_to_env": True,
        "messages": [
            f"Capacity weekly rows source: loaded {len(rows)} rows from {source_path.name}."
        ],
    }

    env.capacity_weekly_rows = rows
    env.capacity_weekly_rows_source_kind = source_kind
    env.capacity_weekly_rows_source_path = str(source_path)
    env.capacity_weekly_rows_load_summary = summary
    return summary


__all__ = ["load_capacity_weekly_rows_to_env"]
