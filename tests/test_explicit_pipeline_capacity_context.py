from __future__ import annotations

from types import SimpleNamespace

import pytest

from pysi.plan.explicit_pipeline_capacity_context import attach_explicit_pipeline_backward_weekly_capability_to_env
from pysi.plan.explicit_pipeline_capacity_context import build_explicit_pipeline_backward_weekly_capability
from pysi.plan.explicit_pipeline_capacity_context import load_explicit_pipeline_backward_weekly_capability_csv
from pysi.reporting.explicit_pipeline_kpi_demo_flags import get_missing_explicit_pipeline_demo_ctx_keys


def test_build_simple_nested_context():
    got = build_explicit_pipeline_backward_weekly_capability(
        [
            {
                "node": "MOM_A",
                "product": "P1",
                "week": "202601",
                "capability_lots": "100",
            }
        ]
    )

    assert got == {"MOM_A": {"P1": {"202601": 100}}}


def test_scenario_filtering_and_none_includes_all():
    rows = [
        {"scenario": "base", "node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "100"},
        {"scenario": "constrained", "node": "MOM_A", "product": "P1", "week": "202602", "capability_lots": "80"},
    ]

    base_only = build_explicit_pipeline_backward_weekly_capability(rows, scenario="base")
    all_rows = build_explicit_pipeline_backward_weekly_capability(rows, scenario=None)

    assert base_only == {"MOM_A": {"P1": {"202601": 100}}}
    assert all_rows == {"MOM_A": {"P1": {"202601": 100, "202602": 80}}}


def test_blank_scenario_defaults_to_base():
    got = build_explicit_pipeline_backward_weekly_capability(
        [
            {
                "scenario": "",
                "node": "MOM_A",
                "product": "P1",
                "week": "202601",
                "capability_lots": "100",
            }
        ],
        scenario="base",
    )

    assert got == {"MOM_A": {"P1": {"202601": 100}}}


def test_duplicate_last_row_wins():
    got = build_explicit_pipeline_backward_weekly_capability(
        [
            {"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "100"},
            {"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "120"},
        ]
    )

    assert got == {"MOM_A": {"P1": {"202601": 120}}}


def test_invalid_numeric_skipped_in_non_strict():
    got = build_explicit_pipeline_backward_weekly_capability(
        [
            {"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "abc"},
            {"node": "MOM_A", "product": "P1", "week": "202602", "capability_lots": "100"},
        ],
        strict=False,
    )

    assert got == {"MOM_A": {"P1": {"202602": 100}}}


def test_invalid_numeric_raises_in_strict():
    with pytest.raises(ValueError, match="invalid capability_lots"):
        build_explicit_pipeline_backward_weekly_capability(
            [{"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "abc"}],
            strict=True,
        )


def test_negative_capability_handling():
    non_strict = build_explicit_pipeline_backward_weekly_capability(
        [{"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "-1"}],
        strict=False,
    )
    assert non_strict == {}

    with pytest.raises(ValueError, match="negative capability_lots"):
        build_explicit_pipeline_backward_weekly_capability(
            [{"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "-1"}],
            strict=True,
        )


def test_unsupported_unit_handling():
    non_strict = build_explicit_pipeline_backward_weekly_capability(
        [
            {
                "node": "MOM_A",
                "product": "P1",
                "week": "202601",
                "capability_lots": "100",
                "unit": "piece",
            }
        ],
        strict=False,
    )
    assert non_strict == {}

    with pytest.raises(ValueError, match="unsupported unit"):
        build_explicit_pipeline_backward_weekly_capability(
            [
                {
                    "node": "MOM_A",
                    "product": "P1",
                    "week": "202601",
                    "capability_lots": "100",
                    "unit": "piece",
                }
            ],
            strict=True,
        )


def test_csv_loader(tmp_path):
    csv_path = tmp_path / "capability.csv"
    csv_path.write_text(
        "scenario,node,product,week,capability_lots,capability_type,unit,source,note\n"
        "base,MOM_A,P1,202601,100,output,lot,manual,ok\n",
        encoding="utf-8",
    )

    got = load_explicit_pipeline_backward_weekly_capability_csv(csv_path)

    assert got == {"MOM_A": {"P1": {"202601": 100}}}


def test_env_attach_clears_existing_guard_missing_key():
    env = SimpleNamespace()

    assert "explicit_pipeline_backward_weekly_capability" in get_missing_explicit_pipeline_demo_ctx_keys(env)

    context = {"MOM_A": {"P1": {"202601": 100}}}
    attached = attach_explicit_pipeline_backward_weekly_capability_to_env(env, context)

    assert attached is env
    assert env.explicit_pipeline_backward_weekly_capability == context
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
