from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

from pysi.plan.explicit_pipeline_capacity_context import (
    load_explicit_pipeline_backward_weekly_capability_csv,
    maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
)
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    get_missing_explicit_pipeline_demo_ctx_keys,
)


def test_sample_csv_exists_and_loads_non_empty_context() -> None:
    path = Path("data/explicit_pipeline_backward_weekly_capability.csv")
    assert path.exists()

    context = load_explicit_pipeline_backward_weekly_capability_csv(path)

    assert context == {
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }


def test_sample_csv_attach_helper_attaches_context_and_clears_guard_key() -> None:
    env = SimpleNamespace()

    result = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)

    assert result["file_exists"] is True
    assert result["attached"] is True
    assert result["reason"] == ""
    assert result["record_count"] == 2
    assert result["node_count"] == 1
    assert result["product_count"] == 1

    assert env.explicit_pipeline_backward_weekly_capability == {
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == [
        "explicit_pipeline_forward_weekly_capacity"
    ]


def test_sample_csv_rows_use_base_scenario_for_gui_default_filter() -> None:
    path = Path("data/explicit_pipeline_backward_weekly_capability.csv")

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert all(row["scenario"] == "base" for row in rows)
