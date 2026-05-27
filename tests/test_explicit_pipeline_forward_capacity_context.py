from __future__ import annotations

from types import SimpleNamespace

import pytest

from pysi.plan.explicit_pipeline_capacity_context import attach_explicit_pipeline_backward_weekly_capability_to_env
from pysi.plan.explicit_pipeline_capacity_context import attach_explicit_pipeline_forward_weekly_capacity_to_env
from pysi.plan.explicit_pipeline_capacity_context import build_explicit_pipeline_forward_weekly_capacity
from pysi.plan.explicit_pipeline_capacity_context import load_explicit_pipeline_forward_weekly_capacity_csv
from pysi.plan.explicit_pipeline_capacity_context import maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv
from pysi.reporting.explicit_pipeline_kpi_demo_flags import get_missing_explicit_pipeline_demo_ctx_keys


def test_build_product_first_context():
    got = build_explicit_pipeline_forward_weekly_capacity(
        [
            {
                "scenario": "base",
                "product": "PACKAGED_RICE_STANDARD",
                "node": "MILL_EAST",
                "capacity_type": "P",
                "week": "2027-W40",
                "capacity_lots": 5,
                "unit": "lot",
            },
            {
                "scenario": "base",
                "product": "PACKAGED_RICE_STANDARD",
                "node": "MILL_EAST",
                "capacity_type": "P",
                "week": "2027-W41",
                "capacity_lots": 6,
                "unit": "lot",
            },
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


def test_scenario_filtering_default_and_none_behavior():
    rows = [
        {"scenario": "base", "product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 1},
        {"scenario": "constrained", "product": "P1", "node": "N1", "capacity_type": "P", "week": "W2", "capacity_lots": 2},
        {"scenario": "", "product": "P1", "node": "N1", "capacity_type": "P", "week": "W3", "capacity_lots": 3},
    ]

    assert build_explicit_pipeline_forward_weekly_capacity(rows) == {"P1": {"N1": {"P": {"W1": 1, "W3": 3}}}}
    assert build_explicit_pipeline_forward_weekly_capacity(rows, scenario="constrained") == {
        "P1": {"N1": {"P": {"W2": 2}}}
    }
    assert build_explicit_pipeline_forward_weekly_capacity(rows, scenario=None) == {
        "P1": {"N1": {"P": {"W1": 1, "W2": 2, "W3": 3}}}
    }


def test_capacity_type_normalization_aliases():
    rows = [
        {"product": "P1", "node": "N1", "capacity_type": "production", "week": "W1", "capacity_lots": 1},
        {"product": "P1", "node": "N1", "capacity_type": "processing", "week": "W2", "capacity_lots": 2},
        {"product": "P1", "node": "N1", "capacity_type": "shipping", "week": "W3", "capacity_lots": 3},
        {"product": "P1", "node": "N1", "capacity_type": "sales", "week": "W4", "capacity_lots": 4},
        {"product": "P1", "node": "N1", "capacity_type": "inventory", "week": "W5", "capacity_lots": 5},
        {"product": "P1", "node": "N1", "capacity_type": "storage", "week": "W6", "capacity_lots": 6},
    ]

    got = build_explicit_pipeline_forward_weekly_capacity(rows)

    assert got == {
        "P1": {
            "N1": {
                "P": {"W1": 1, "W2": 2},
                "S": {"W3": 3, "W4": 4},
                "I": {"W5": 5, "W6": 6},
            }
        }
    }


def test_invalid_rows_skipped_non_strict():
    rows = [
        {"product": "", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 1},
        {"product": "P1", "node": "", "capacity_type": "P", "week": "W1", "capacity_lots": 1},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "", "capacity_lots": 1},
        {"product": "P1", "node": "N1", "capacity_type": "", "week": "W1", "capacity_lots": 1},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": "abc"},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": -1},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 5.5},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 1, "unit": "kg"},
        {"product": "P1", "node": "N1", "capacity_type": "unknown", "week": "W1", "capacity_lots": 1},
        {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W2", "capacity_lots": 2},
    ]

    assert build_explicit_pipeline_forward_weekly_capacity(rows, strict=False) == {"P1": {"N1": {"P": {"W2": 2}}}}


def test_invalid_rows_raise_strict():
    with pytest.raises(ValueError):
        build_explicit_pipeline_forward_weekly_capacity(
            [{"product": "P1", "node": "N1", "capacity_type": "unknown", "week": "W1", "capacity_lots": 1}],
            strict=True,
        )


def test_duplicate_last_valid_row_wins():
    got = build_explicit_pipeline_forward_weekly_capacity(
        [
            {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 1},
            {"product": "P1", "node": "N1", "capacity_type": "P", "week": "W1", "capacity_lots": 9},
        ]
    )

    assert got == {"P1": {"N1": {"P": {"W1": 9}}}}


def test_loader_reads_csv(tmp_path):
    csv_path = tmp_path / "forward.csv"
    csv_path.write_text(
        "scenario,product,node,capacity_type,week,capacity_lots,unit\n"
        "base,P1,N1,production,2027-W40,5,lot\n",
        encoding="utf-8",
    )

    got = load_explicit_pipeline_forward_weekly_capacity_csv(csv_path)

    assert got == {"P1": {"N1": {"P": {"2027-W40": 5}}}}


def test_attach_helper_sets_env_key():
    env = SimpleNamespace()
    context = {"P1": {"N1": {"P": {"W1": 1}}}}

    attached = attach_explicit_pipeline_forward_weekly_capacity_to_env(env, context)

    assert attached is env
    assert env.explicit_pipeline_forward_weekly_capacity == context


def test_maybe_attach_missing_file(tmp_path):
    env = SimpleNamespace()
    missing_path = tmp_path / "missing.csv"

    result = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env, missing_path)

    assert result["attached"] is False
    assert result["reason"] == "file_missing"
    assert not hasattr(env, "explicit_pipeline_forward_weekly_capacity")
    assert env.explicit_pipeline_forward_weekly_capacity_attach_result == result
    assert env.explicit_pipeline_forward_weekly_capacity_attached is False


def test_maybe_attach_valid_file(tmp_path):
    env = SimpleNamespace()
    csv_path = tmp_path / "forward.csv"
    csv_path.write_text(
        "scenario,product,node,capacity_type,week,capacity_lots,unit\n"
        "base,P1,N1,production,W1,1,lot\n"
        "base,P1,N1,sales,W1,3,lot\n"
        "base,P1,N1,production,W2,2,lot\n"
        "base,P1,N2,production,W1,4,lot\n",
        encoding="utf-8",
    )

    result = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env, csv_path)

    assert result["attached"] is True
    assert result["reason"] == ""
    assert result["record_count"] == 4
    assert result["product_count"] == 1
    assert result["node_count"] == 2
    assert result["capacity_type_count"] == 3
    assert env.explicit_pipeline_forward_weekly_capacity == {
        "P1": {
            "N1": {"P": {"W1": 1, "W2": 2}, "S": {"W1": 3}},
            "N2": {"P": {"W1": 4}},
        }
    }


def test_failed_attach_preserves_existing_context(tmp_path):
    env = SimpleNamespace(explicit_pipeline_forward_weekly_capacity={"EX": {"N": {"P": {"W": 1}}}})
    missing_path = tmp_path / "missing.csv"

    result = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env, missing_path)

    assert result["attached"] is False
    assert env.explicit_pipeline_forward_weekly_capacity == {"EX": {"N": {"P": {"W": 1}}}}


def test_guard_clears_when_backward_and_forward_present():
    env = SimpleNamespace()

    attach_explicit_pipeline_backward_weekly_capability_to_env(env, {"MOM_A": {"P1": {"202601": 100}}})
    attach_explicit_pipeline_forward_weekly_capacity_to_env(env, {"P1": {"N1": {"P": {"W1": 1}}}})

    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
