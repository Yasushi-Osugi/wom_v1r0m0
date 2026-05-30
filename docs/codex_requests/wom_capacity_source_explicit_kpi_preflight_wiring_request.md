# Codex Request: WOM Capacity Source Explicit KPI Preflight Wiring

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_source_explicit_kpi_preflight_wiring_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please wire the completed capacity source helper into the existing Explicit KPI preflight flow.

Use the existing helper:

```python
load_capacity_weekly_rows_to_env(...)
```

and call it before the existing runtime attachment preflight helper:

```python
apply_capacity_runtime_attachment_preflight(...)
```

The intended flow is:

```text
Explicit KPI preflight
    ↓
load_capacity_weekly_rows_to_env(...), if a capacity source hint exists
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_preflight_result
    ↓
existing capacity scenario alignment diagnostic
```

This request is intentionally narrow.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change blocked lot behavior.

Do not change data CSV files.

Do not normalize week keys.

Do not change GUI layout.

Do not implement scenario runner integration.

Do not implement legacy PySI V0R8 adapter dispatch.

---

## 2. Why This Request Exists

The capacity row source helper is already implemented:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

The Explicit KPI preflight runtime attachment path is also already implemented:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
runtime attachment diagnostic
```

The remaining missing connection is:

```text
Explicit KPI preflight
    ↓
source helper
    ↓
runtime attachment preflight
```

This request connects those two already completed pieces.

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
```

Also inspect these implementation and test files:

```text
pysi/capacity/capacity_weekly_rows_source.py
pysi/gui/cockpit_tk.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Reuse the existing helpers:

```python
load_capacity_weekly_rows_to_env(...)
apply_capacity_runtime_attachment_preflight(...)
```

Do not duplicate their logic.

---

## 4. Implementation Scope

### Required

Wire source loading into the existing Explicit KPI preflight flow.

Likely file:

```text
pysi/gui/cockpit_tk.py
```

Likely area:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

or a nearby helper added in the previous Explicit KPI runtime preflight wiring.

Recommended new helper method:

```python
_maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight(
    self,
    *,
    messages: list[str],
) -> dict | None:
    ...
```

This helper should:

```text
inspect available source hints from self/env
call load_capacity_weekly_rows_to_env(..., required=False) only when a source hint exists
append load summary messages into the supplied messages list
return the load summary
```

Then `_maybe_apply_explicit_kpi_demo_flags` should call it before:

```text
_maybe_apply_capacity_runtime_attachment_preflight(...)
```

---

## 5. Explicit Non-Scope

Do not implement:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
data CSV changes
sample CSV changes
new GUI widgets
GUI layout changes
scenario runner integration
run_wom_scenario integration
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
capacity applicability status enforcement
new optimization logic
```

This request is source wiring into Explicit KPI preflight only.

---

## 6. Source Hint Policy

The source helper should be called only when at least one source hint is available.

Possible source hints may be found on `env` or `self`:

```text
env.capacity_master_path
env.scenario_root
env.scenario_config
self.capacity_master_path
self.scenario_root
self.scenario_config
self.current_scenario_root
self.current_scenario_config
```

Inspect the current code and choose the least invasive existing source hints.

Do not invent new GUI controls.

Do not add new user-facing configuration.

Recommended minimal policy:

```python
capacity_master_path = getattr(self.env, "capacity_master_path", None)
scenario_root = getattr(self.env, "scenario_root", None)
scenario_config = getattr(self.env, "scenario_config", None)
```

If no hint exists:

```text
do not call load_capacity_weekly_rows_to_env(...)
allow the existing runtime attachment preflight to skip safely if env.capacity_weekly_rows is missing
```

This avoids adding noisy missing-source messages to existing demos that do not yet have source configuration.

---

## 7. Required vs Optional Loading

Use:

```python
required=False
```

for Explicit KPI preflight wiring.

Reason:

```text
Explicit KPI demo should not crash merely because a canonical capacity_master.csv source is not configured.
```

A missing configured source should be reported via summary if the helper is called.

A malformed configured source may raise `ValueError` from the canonical loader unless the existing GUI preflight style explicitly catches and reports such errors.

---

## 8. Recommended Call Order

In Explicit KPI preflight, the recommended order is:

```text
1. Existing Explicit KPI demo flag setup.
2. Capacity source load helper, if a source hint exists.
3. Existing backward / forward capacity context setup, if any.
4. Existing capacity runtime attachment preflight.
5. Existing capacity scenario alignment diagnostic.
6. Existing ctx guard check.
7. Existing Explicit KPI view-model / message construction.
```

The key requirement:

```text
load_capacity_weekly_rows_to_env(...) must run before apply_capacity_runtime_attachment_preflight(...).
```

This lets the runtime attachment preflight consume:

```text
env.capacity_weekly_rows
```

---

## 9. Env Attachment Expectations

When a source file is found and loaded, the source helper should attach:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
env.capacity_weekly_rows_load_summary
```

Then the existing runtime attachment preflight should attach:

```text
env.capacity_runtime_attachment_preflight_result
env.capacity_runtime_attachment_summary
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

The implementation should not replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

---

## 10. Message Policy

The source helper returns messages inside:

```text
summary["messages"]
```

The Explicit KPI wiring should append those messages to the same local preflight message list used by the runtime attachment preflight.

Example source messages:

```text
Capacity weekly rows source: loaded 1 rows from capacity_master.csv.
Capacity weekly rows source: loaded 0 rows from capacity_master.csv.
Capacity weekly rows source: no capacity master source found.
```

Runtime attachment messages should continue to be appended by:

```python
apply_capacity_runtime_attachment_preflight(...)
```

Do not change GUI layout.

Do not add new widgets.

Do not double-prefix messages.

---

## 11. Diagnostic Policy

This request should not add a new diagnostic section.

The source helper should attach:

```text
env.capacity_weekly_rows_load_summary
```

The existing runtime attachment and capacity scenario alignment diagnostics should continue to work.

Future work may add:

```text
diagnostic["capacity_weekly_rows_source"]
```

but that is out of scope for this request.

---

## 12. Error Handling Policy

### 12.1 No source hint

If no source hint exists:

```text
do not call source helper
do not attach env.capacity_weekly_rows_load_summary
runtime preflight safe skip behavior remains unchanged
```

### 12.2 Source hint exists but file missing

If source hint exists and `required=False`, the helper returns unavailable summary.

The wiring should attach / preserve that summary and its messages.

### 12.3 Source file exists but invalid

Allow canonical loader `ValueError` to surface unless the existing GUI preflight code has a clear safe-error style.

Do not silently ignore malformed configured capacity files.

### 12.4 Empty valid file

If source file exists but has no rows:

```text
env.capacity_weekly_rows = []
env.capacity_weekly_rows_load_summary["available"] = True
runtime preflight applied=True with empty rows
```

---

## 13. Idempotency Policy

Explicit KPI preflight may run repeatedly.

The source wiring should be deterministic.

Expected repeated-call behavior:

```text
env.capacity_weekly_rows is reloaded/replaced deterministically
env.capacity_weekly_rows_load_summary is replaced deterministically
runtime attachment preflight remains deterministic
source rows are not mutated
persistent env messages do not accumulate unless existing flow already does so
```

---

## 14. Suggested Tests

Add a focused test file:

```text
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Use the existing testing style from:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

### 14.1 Source path loads rows before runtime preflight

Given a test capacity master CSV and env/cockpit with:

```text
env.capacity_master_path = path
```

Run the Explicit KPI preflight method.

Assert:

```text
env.capacity_weekly_rows exists
env.capacity_weekly_rows_load_summary["available"] is True
env.capacity_runtime_attachment_preflight_result["applied"] is True
env.explicit_pipeline_forward_weekly_capacity exists
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows exists
```

### 14.2 No source hint preserves safe skip

Given no source hint and no `env.capacity_weekly_rows`, run Explicit KPI preflight.

Assert:

```text
env.capacity_runtime_attachment_preflight_result["applied"] is False
env.capacity_runtime_attachment_preflight_result["reason"] == "capacity_weekly_rows_missing"
```

Do not require `env.capacity_weekly_rows_load_summary` in this case if the implementation skips source helper when no hint exists.

### 14.3 Scenario root default masters path

Given:

```text
env.scenario_root = tmp_path / "scenario"
scenario_root / "masters" / "capacity_master.csv"
```

Run Explicit KPI preflight.

Assert rows load and runtime preflight applies.

### 14.4 Source messages are available

Assert one of the following:

```text
Capacity weekly rows source: loaded
```

appears in the preflight messages, diagnostic messages, or summary messages.

At minimum, assert:

```text
env.capacity_weekly_rows_load_summary["messages"]
```

contains the source load message.

### 14.5 Empty valid file

Given a valid capacity master header with no data rows, assert:

```text
env.capacity_weekly_rows == []
env.capacity_weekly_rows_load_summary["row_count"] == 0
env.capacity_runtime_attachment_preflight_result["applied"] is True
```

### 14.6 Repeated invocation

Run Explicit KPI preflight twice.

Assert:

```text
no exception
env.capacity_weekly_rows remains deterministic
env.capacity_runtime_attachment_preflight_result remains deterministic
```

### 14.7 No planner behavior change

Do not assert plan result changes.

Do not require planner execution.

### 14.8 No GUI layout change

Do not assert new widgets.

Do not modify GUI layout.

---

## 15. Test Commands

Run focused source wiring test:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Run related tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Run capacity regression tests:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 16. Safety Boundaries

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
data/*.csv
```

Avoid modifying unless strictly necessary:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Expected changed files:

```text
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Possibly changed only if needed:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

Do not change planner behavior.

Do not change capacity enforcement.

Do not change data CSV files.

---

## 17. Acceptance Criteria

This request is complete when:

```text
load_capacity_weekly_rows_to_env(...) is called before apply_capacity_runtime_attachment_preflight(...) when a source hint exists
env.capacity_weekly_rows is populated from capacity_master.csv
env.capacity_weekly_rows_load_summary is attached
runtime preflight consumes loaded env.capacity_weekly_rows
rows-present source case leads to runtime preflight applied=True
missing source hint preserves safe skip behavior
empty valid source file is handled deterministically
source messages are preserved
focused tests pass
related preflight/diagnostic tests pass
no planner behavior changes are made
no capacity enforcement changes are made
no GUI layout changes are made
no data CSV files are changed
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was load_capacity_weekly_rows_to_env wired?
At what point in Explicit KPI preflight is it called?
What source hints are used?
What happens when a capacity_master_path is present?
What happens when no source hint exists?
What happens when scenario_root/masters/capacity_master.csv exists?
Are source messages preserved?
Does runtime preflight consume loaded env.capacity_weekly_rows?
Did you change planner behavior?
Did you change capacity enforcement?
Did you change GUI layout?
Did you change data CSV files?
Which tests passed?
```

---

## 19. Development Meaning

This request connects the source loading dock to the Explicit KPI preflight route.

Already completed:

```text
capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
```

and:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
Explicit KPI diagnostic visibility
```

This request connects them:

```text
capacity_master.csv
    ↓
env.capacity_weekly_rows
    ↓
Explicit KPI runtime attachment preflight
```

Do not change the planner train schedule.

Just connect the cargo conveyor to the pre-departure inspection route.
