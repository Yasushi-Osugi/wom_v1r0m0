from types import SimpleNamespace

from pysi.reporting.explicit_pipeline_kpi_demo_flags import apply_explicit_pipeline_kpi_demo_flags
from pysi.reporting.explicit_pipeline_kpi_demo_flags import get_missing_explicit_pipeline_demo_ctx_keys


def _expected_map(include_exports: bool) -> dict[str, bool]:
    return {
        "enable_explicit_bridge_capacity_pipeline": True,
        "enable_explicit_bridge_capacity_report": True,
        "enable_explicit_bridge_capacity_issue_candidates": True,
        "enable_explicit_bridge_capacity_issue_candidate_cost_kpi": True,
        "enable_explicit_bridge_capacity_report_export": include_exports,
        "enable_explicit_bridge_capacity_issue_candidate_export": include_exports,
        "enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export": include_exports,
    }


def test_required_flags_enabled_export_flags_disabled_by_default():
    env = SimpleNamespace()

    applied = apply_explicit_pipeline_kpi_demo_flags(env)

    assert applied == _expected_map(include_exports=False)
    for name, value in applied.items():
        assert getattr(env, name) is value


def test_export_flags_enabled_when_requested():
    env = SimpleNamespace()

    applied = apply_explicit_pipeline_kpi_demo_flags(env, include_exports=True)

    assert applied == _expected_map(include_exports=True)
    for name, value in applied.items():
        assert getattr(env, name) is value


def test_existing_cost_context_preserved_by_default():
    existing = {"scenario": "existing"}
    env = SimpleNamespace(explicit_bridge_capacity_cost_kpi_context=existing)

    apply_explicit_pipeline_kpi_demo_flags(env)

    assert env.explicit_bridge_capacity_cost_kpi_context == existing


def test_provided_cost_context_attached():
    env = SimpleNamespace(explicit_bridge_capacity_cost_kpi_context={"scenario": "existing"})

    apply_explicit_pipeline_kpi_demo_flags(env, cost_kpi_context={"scenario": "demo"})

    assert env.explicit_bridge_capacity_cost_kpi_context == {"scenario": "demo"}


def test_missing_ctx_detection_reports_backward_weekly_capability():
    env = SimpleNamespace()

    missing = get_missing_explicit_pipeline_demo_ctx_keys(env)

    assert "explicit_pipeline_backward_weekly_capability" in missing


def test_missing_ctx_detection_empty_when_backward_weekly_capability_present():
    env = SimpleNamespace(
        explicit_pipeline_backward_weekly_capability={"MOM": {"W01": 100}}
    )

    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
