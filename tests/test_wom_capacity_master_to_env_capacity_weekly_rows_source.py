from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from pysi.capacity.capacity_weekly_rows_source import load_capacity_weekly_rows_to_env

CAPACITY_MASTER_HEADER = (
    "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,"
    "cap_mode,unit,priority,calendar_id,comment"
)


def _write_capacity_master_csv(path: Path, rows: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [CAPACITY_MASTER_HEADER]
    if rows is None:
        rows = [
            (
                "RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,"
                "P,10,hard,lot,1,CAL_STD,test row"
            )
        ]
    lines.extend(rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    return path


def test_explicit_capacity_master_path_loads_rows_to_env(tmp_path: Path) -> None:
    path = _write_capacity_master_csv(
        tmp_path / "capacity_master.csv",
        rows=[
            (
                "RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,"
                "P,10,hard,lot,1,CAL_STD,test row"
            ),
            (
                "RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W41,"
                "P,11,hard,lot,1,CAL_STD,next row"
            ),
        ],
    )
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(env, capacity_master_path=path)

    assert summary["available"] is True
    assert summary["source_kind"] == "capacity_master_csv"
    assert summary["source_path"] == str(path)
    assert summary["row_count"] == 2
    assert summary["attached_to_env"] is True
    assert len(env.capacity_weekly_rows) == 2
    assert env.capacity_weekly_rows_source_kind == "capacity_master_csv"
    assert env.capacity_weekly_rows_source_path == str(path)
    assert env.capacity_weekly_rows_load_summary == summary


def test_scenario_config_capacity_master_path_loads_rows(tmp_path: Path) -> None:
    scenario_root = tmp_path / "scenario"
    path = _write_capacity_master_csv(scenario_root / "masters" / "capacity_master.csv")
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(
        env,
        scenario_root=scenario_root,
        scenario_config={"masters": {"capacity_master": "masters/capacity_master.csv"}},
    )

    assert summary["available"] is True
    assert summary["source_kind"] == "scenario_package_capacity_master"
    assert summary["source_path"] == str(path)
    assert summary["row_count"] == 1
    assert env.capacity_weekly_rows_source_path == str(path)
    assert len(env.capacity_weekly_rows) == 1


def test_default_scenario_root_masters_capacity_master_path_loads_rows(
    tmp_path: Path,
) -> None:
    scenario_root = tmp_path / "scenario"
    path = _write_capacity_master_csv(scenario_root / "masters" / "capacity_master.csv")
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(env, scenario_root=scenario_root)

    assert summary["available"] is True
    assert summary["source_kind"] == "scenario_package_capacity_master"
    assert summary["source_path"] == str(path)
    assert summary["row_count"] == 1
    assert len(env.capacity_weekly_rows) == 1


def test_default_scenario_root_direct_capacity_master_path_loads_rows(
    tmp_path: Path,
) -> None:
    scenario_root = tmp_path / "scenario"
    path = _write_capacity_master_csv(scenario_root / "capacity_master.csv")
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(env, scenario_root=scenario_root)

    assert summary["available"] is True
    assert summary["source_kind"] == "scenario_package_capacity_master"
    assert summary["source_path"] == str(path)
    assert summary["row_count"] == 1
    assert len(env.capacity_weekly_rows) == 1


def test_missing_source_required_false_attaches_only_load_summary(tmp_path: Path) -> None:
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(env, scenario_root=tmp_path / "missing")

    assert summary["available"] is False
    assert summary["source_kind"] == "missing"
    assert summary["source_path"] is None
    assert summary["row_count"] == 0
    assert summary["attached_to_env"] is False
    assert not hasattr(env, "capacity_weekly_rows")
    assert not hasattr(env, "capacity_weekly_rows_source_kind")
    assert not hasattr(env, "capacity_weekly_rows_source_path")
    assert env.capacity_weekly_rows_load_summary == summary


def test_missing_source_required_true_raises_file_not_found(tmp_path: Path) -> None:
    env = SimpleNamespace()

    with pytest.raises(FileNotFoundError):
        load_capacity_weekly_rows_to_env(
            env, scenario_root=tmp_path / "missing", required=True
        )


def test_empty_valid_capacity_master_file_attaches_empty_rows(tmp_path: Path) -> None:
    path = _write_capacity_master_csv(tmp_path / "capacity_master.csv", rows=[])
    env = SimpleNamespace()

    summary = load_capacity_weekly_rows_to_env(env, capacity_master_path=path)

    assert summary["available"] is True
    assert summary["source_path"] == str(path)
    assert summary["row_count"] == 0
    assert summary["attached_to_env"] is True
    assert env.capacity_weekly_rows == []
    assert env.capacity_weekly_rows_load_summary == summary


def test_invalid_capacity_master_schema_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "capacity_master.csv"
    path.write_text(
        "scenario_id,tree_side,node_name,product_name,week,capacity_type,cap_mode,unit\n"
        "RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,hard,lot\n",
        encoding="utf-8",
        newline="",
    )
    env = SimpleNamespace()

    with pytest.raises(ValueError, match="missing required columns"):
        load_capacity_weekly_rows_to_env(env, capacity_master_path=path)
