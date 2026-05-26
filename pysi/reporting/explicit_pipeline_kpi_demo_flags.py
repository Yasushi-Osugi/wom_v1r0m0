from __future__ import annotations

from typing import Any

_DISPLAY_FLAGS = (
    "enable_explicit_bridge_capacity_pipeline",
    "enable_explicit_bridge_capacity_report",
    "enable_explicit_bridge_capacity_issue_candidates",
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi",
)

_EXPORT_FLAGS = (
    "enable_explicit_bridge_capacity_report_export",
    "enable_explicit_bridge_capacity_issue_candidate_export",
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export",
)

_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
)


def apply_explicit_pipeline_kpi_demo_flags(
    env: Any,
    *,
    include_exports: bool = False,
    cost_kpi_context: dict[str, Any] | None = None,
) -> dict[str, bool]:
    """Apply explicit pipeline KPI demo/reporting flags to ``env``.

    This helper only sets feature flags and optional context. It does not execute
    planning, reporting, or export routines.
    """

    applied: dict[str, bool] = {}

    for flag_name in _DISPLAY_FLAGS:
        setattr(env, flag_name, True)
        applied[flag_name] = True

    for flag_name in _EXPORT_FLAGS:
        flag_value = include_exports
        setattr(env, flag_name, flag_value)
        applied[flag_name] = flag_value

    if cost_kpi_context is not None:
        env.explicit_bridge_capacity_cost_kpi_context = cost_kpi_context

    return applied


def get_missing_explicit_pipeline_demo_ctx_keys(env: Any) -> list[str]:
    """Return required explicit pipeline ctx keys that are missing on ``env``.

    A key is considered missing when the attribute does not exist or the value is
    ``None``.
    """

    missing: list[str] = []
    for key in _REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS:
        if not hasattr(env, key) or getattr(env, key) is None:
            missing.append(key)
    return missing
