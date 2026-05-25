# Codex Request: Implement Explicit Pipeline Management Cockpit KPI Demo Flag Preset Helper Phase 1

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design memo has already been added:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset.md
```

Please read this design memo first.

The Explicit Pipeline Management Cockpit KPI UI MVP has already been implemented and merged into `main`.

The UI now exists and opens correctly from the WOM GUI:

```text
Explicit KPI View
    ├─ Summary
    │   └─ KPI Cards
    ├─ Graphs
    │   └─ Canvas Charts
    ├─ Top Issues
    ├─ Replan Candidates
    ├─ Health
    ├─ Assumptions / Exports
    └─ Messages
```

However, normal `python -m main` execution currently opens the Explicit KPI View with unavailable reporting data:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

This is expected because the explicit pipeline reporting stack is protected by default-off feature flags.

This request implements **Phase 1** only:

```text
pure demo flag preset helper + tests
```

This request does **not** wire the helper into the GUI yet.

GUI checkbox / toggle integration will be a separate Phase 2 request.

---

## 2. Main Objective

Add a pure helper that applies the Explicit KPI demo / reporting flags to an `env` object.

Target new module:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Target test file:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Also update package exports if appropriate:

```text
pysi/reporting/__init__.py
```

Main function to implement:

```python
def apply_explicit_pipeline_kpi_demo_flags(
    env: Any,
    *,
    include_exports: bool = False,
    cost_kpi_context: dict[str, Any] | None = None,
) -> dict[str, bool]:
    ...
```

The helper should set the required display flags and return a deterministic flag map.

---

## 3. Important Constraints

Please follow these constraints strictly:

```text
1. Do not modify pysi/gui/cockpit_tk.py.
2. Do not add GUI checkbox / toggle in this request.
3. Do not add GUI buttons.
4. Do not add menu entries.
5. Do not run planning.
6. Do not run Run Full Plan.
7. Do not run the explicit pipeline.
8. Do not run the reporting stack helper.
9. Do not trigger exports.
10. Do not execute ReplanCommand.
11. Do not implement automatic replanning.
12. Do not implement OR optimization.
13. Do not implement database persistence.
14. Do not implement Knowledge Continuity persistence.
15. Do not modify reporting builders/exporters.
16. Do not modify Cost / KPI enrichment logic.
17. Do not modify cockpit rendering logic.
18. Do not add matplotlib or new dependencies.
```

This request is only for:

```text
pure demo flag preset helper + unit tests
```

The safety rule remains:

```text
Prepare the ignition switch.
Do not start the engine.
```

---

## 4. Files to Modify / Add

Please add:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Please update if appropriate:

```text
pysi/reporting/__init__.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/*
pysi/core/*
```

unless a tiny export-surface compatibility issue is absolutely unavoidable.

---

## 5. Required Display Flags

The helper should enable these required display flags:

```text
enable_explicit_bridge_capacity_pipeline
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
```

Set each to:

```python
True
```

These flags are needed so that, when the existing planning flow is run later, the explicit pipeline and reporting artifacts can be attached to `env` and shown in the Explicit KPI View.

The helper itself must not run the planning flow.

---

## 6. Optional Export Flags

Export flags should remain optional.

When:

```python
include_exports=False
```

the helper should not enable export behavior.

Recommended behavior:

```text
set export flags to False explicitly
```

for deterministic behavior.

Export flags:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

When:

```python
include_exports=True
```

set these export flags to:

```python
True
```

Reason:

```text
GUI display does not require file exports.
Export generation may create files and should remain explicit.
```

Default must be:

```python
include_exports=False
```

---

## 7. Cost / KPI Context Behavior

The helper supports an optional `cost_kpi_context`.

If:

```python
cost_kpi_context is not None
```

then attach it to:

```python
env.explicit_bridge_capacity_cost_kpi_context
```

If:

```python
cost_kpi_context is None
```

then do not overwrite an existing:

```python
env.explicit_bridge_capacity_cost_kpi_context
```

This preserves any existing scenario context.

---

## 8. Helper Return Value

The helper should return a stable dictionary containing all seven flag names and their applied boolean values.

When `include_exports=False`, expected return map:

```python
{
    "enable_explicit_bridge_capacity_pipeline": True,
    "enable_explicit_bridge_capacity_report": True,
    "enable_explicit_bridge_capacity_issue_candidates": True,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi": True,
    "enable_explicit_bridge_capacity_report_export": False,
    "enable_explicit_bridge_capacity_issue_candidate_export": False,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export": False,
}
```

When `include_exports=True`, expected return map:

```python
{
    "enable_explicit_bridge_capacity_pipeline": True,
    "enable_explicit_bridge_capacity_report": True,
    "enable_explicit_bridge_capacity_issue_candidates": True,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi": True,
    "enable_explicit_bridge_capacity_report_export": True,
    "enable_explicit_bridge_capacity_issue_candidate_export": True,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export": True,
}
```

The order does not have to matter semantically, but a deterministic literal order is preferred.

---

## 9. Env Compatibility

The helper should work with any simple object that supports `setattr`.

Tests should use:

```python
from types import SimpleNamespace
```

Example:

```python
env = SimpleNamespace()
applied = apply_explicit_pipeline_kpi_demo_flags(env)
```

After the call:

```python
env.enable_explicit_bridge_capacity_pipeline is True
env.enable_explicit_bridge_capacity_report is True
...
```

---

## 10. Recommended Module Structure

Recommended implementation style:

```python
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


def apply_explicit_pipeline_kpi_demo_flags(
    env: Any,
    *,
    include_exports: bool = False,
    cost_kpi_context: dict[str, Any] | None = None,
) -> dict[str, bool]:
    ...
```

Keep the helper small and explicit.

---

## 11. Package Export

If consistent with existing package style, update:

```text
pysi/reporting/__init__.py
```

to expose:

```python
apply_explicit_pipeline_kpi_demo_flags
```

Do not break existing exports.

---

## 12. Tests to Add

Add focused unit tests:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Suggested tests:

### 12.1 Required flags enabled

```text
apply_explicit_pipeline_kpi_demo_flags(env)
```

Verify:

```text
all display flags are True
all export flags are False
return map matches expected
```

### 12.2 Export flags enabled when requested

```text
apply_explicit_pipeline_kpi_demo_flags(env, include_exports=True)
```

Verify:

```text
all display flags are True
all export flags are True
return map matches expected
```

### 12.3 Existing cost context preserved by default

Input:

```python
env.explicit_bridge_capacity_cost_kpi_context = {"scenario": "existing"}
```

Call:

```python
apply_explicit_pipeline_kpi_demo_flags(env)
```

Verify:

```text
context remains {"scenario": "existing"}
```

### 12.4 Provided cost context attached

Call:

```python
apply_explicit_pipeline_kpi_demo_flags(
    env,
    cost_kpi_context={"scenario": "demo"},
)
```

Verify:

```text
env.explicit_bridge_capacity_cost_kpi_context == {"scenario": "demo"}
```

### 12.5 Helper is execution-free

This can be implicit.

Do not import or call planning / reporting execution modules in this helper.

Test can verify only flags/context are attached.

---

## 13. Tests to Run

Please run:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Then run related cockpit / reporting tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_canvas_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_button_integration.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Then run key regression tests if time allows:

```bat
python -m pytest tests/test_explicit_pipeline_issue_candidate_cost_kpi_export.py
python -m pytest tests/test_explicit_pipeline_issue_candidate_cost_kpi.py
python -m pytest tests/test_explicit_pipeline_issue_candidate_export.py
python -m pytest tests/test_explicit_pipeline_issue_candidates.py
python -m pytest tests/test_explicit_pipeline_capacity_report_export.py
python -m pytest tests/test_explicit_pipeline_capacity_report_attachment.py
python -m pytest tests/test_explicit_pipeline_capacity_reporting.py
python -m pytest tests/test_run_full_plan_explicit_pipeline_insertion.py
python -m pytest tests/test_explicit_bridge_capacity_pipeline_feature_flag.py
python -m pytest tests/test_explicit_bridge_capacity_pipeline.py
python -m pytest tests/test_e2e_bridge_forward_capacity_smoke.py
python -m pytest tests/test_weekly_forward_push_with_capacity.py
python -m pytest tests/test_demand_to_supply_execution_bridge.py
python -m pytest tests/test_capacity_aware_inbound_backward_planning.py
python -m pytest tests/test_japanese_rice_case_smoke.py
```

Optional:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If optional tests are not run, state so clearly.

If Tk tests are skipped because Tk is unavailable, state so clearly.

---

## 14. Completion Criteria

This request is complete when:

```text
[OK] pysi/reporting/explicit_pipeline_kpi_demo_flags.py exists
[OK] apply_explicit_pipeline_kpi_demo_flags(env) exists
[OK] required display flags are enabled
[OK] export flags are False by default
[OK] export flags are True when include_exports=True
[OK] existing cost_kpi_context is preserved by default
[OK] provided cost_kpi_context is attached
[OK] deterministic return map is provided
[OK] tests/test_explicit_pipeline_kpi_demo_flags.py exists
[OK] focused tests pass
[OK] existing cockpit/reporting tests pass
[OK] no GUI modification is made
[OK] no planning execution is added
[OK] no export execution is added
[OK] no ReplanCommand execution is added
```

---

## 15. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Main implementation approach
3. Helper function signature
4. Display flags enabled
5. Export flag behavior
6. Cost / KPI context behavior
7. Return map behavior
8. Safety boundaries preserved
9. Test commands executed
10. Test results
11. Any skipped tests and why
12. Limitations / follow-up
```

Please do not proceed into:

```text
cockpit_tk.py GUI wiring
GUI checkbox / toggle
Run Full Plan integration
view message changes
planning execution
export execution
reporting stack execution
ReplanCommand execution
Knowledge Continuity persistence
waterfall / heatmap / drilldown
```

This request is only for:

```text
Explicit Pipeline Management Cockpit KPI Demo Flag Preset Helper Phase 1
```

The GUI wiring belongs to Phase 2.
