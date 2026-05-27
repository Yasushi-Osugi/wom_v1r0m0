from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

from pysi.plan.explicit_pipeline_capacity_context import (
    load_explicit_pipeline_forward_weekly_capacity_csv,
    maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
    maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv,
)
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    get_missing_explicit_pipeline_demo_ctx_keys,
)


def test_forward_capacity_sample_csv_exists_and_loads_non_empty_context() -> None:
    path = Path("data/explicit_pipeline_forward_weekly_capacity.csv")
    assert path.exists()

    context = load_explicit_pipeline_forward_weekly_capacity_csv(path)

    assert context == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 5,
                    "2027-W41": 6,
                }
            }
        }
    }


def test_forward_capacity_sample_csv_attach_helper_attaches_context() -> None:
    env = SimpleNamespace()

    result = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env)

    assert result["file_exists"] is True
    assert result["attached"] is True
    assert result["reason"] == ""
    assert result["record_count"] == 2
    assert result["product_count"] == 1
    assert result["node_count"] == 1
    assert result["capacity_type_count"] == 1

    assert env.explicit_pipeline_forward_weekly_capacity == {
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 5,
                    "2027-W41": 6,
                }
            }
        }
    }


def test_forward_capacity_sample_csv_rows_use_base_scenario_for_gui_default_filter() -> None:
    path = Path("data/explicit_pipeline_forward_weekly_capacity.csv")

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["scenario"] for row in rows} == {"base"}


def test_backward_and_forward_sample_csvs_clear_explicit_kpi_ctx_guard() -> None:
    env = SimpleNamespace()

    backward = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)
    forward = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env)

    assert backward["attached"] is True
    assert forward["attached"] is True
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
