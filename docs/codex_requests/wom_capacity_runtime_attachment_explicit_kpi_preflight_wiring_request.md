# Codex Request: WOM Capacity Runtime Attachment Explicit KPI Preflight Wiring

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please wire the existing capacity runtime attachment preflight helper into the existing Explicit KPI preflight flow.

This request is intentionally narrow.

Use the existing helper:

```python
apply_capacity_runtime_attachment_preflight(...)
```

and call it from the Explicit KPI preflight path.

The wiring should:

```text
call apply_capacity_runtime_attachment_preflight(env, messages=...)
attach the returned result to env.capacity_runtime_attachment_preflight_result
allow safe skip when env.capacity_weekly_rows is missing
preserve existing capacity scenario alignment diagnostic flow
preserve existing Explicit KPI view-model behavior
```

Do not change planner behavior.

Do not change capacity enforcement.

Do not change blocked lot behavior.

Do not change data CSV files.

Do not load capacity_master.csv here.

Do not implement scenario package loading.

Do not normalize week keys.

Do not change GUI layout.

---

## 2. Why This Request Exists

WOM now has the following completed capacity runtime path:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
apply_capacity_runtime_attachment_preflight(...)
```

The preflight helper exists, but it is not yet called by the Explicit KPI preflight path.

This request connects the helper into the Explicit KPI preflight flow so that capacity runtime attachment status becomes visible during the existing Explicit KPI diagnostic path.

This is a wiring step, not a planner behavior step.

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
```

Also inspect these implementation and test files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Reuse the existing helper:

```python
apply_capacity_runtime_attachment_preflight(...)
```

Do not duplicate its logic.

---

## 4. Implementation Scope

### Required

Wire this helper into the existing Explicit KPI preflight path:

```python
apply_capacity_runtime_attachment_preflight(env, messages=...)
```

The expected preflight result should be attached to:

```text
env.capacity_runtime_attachment_preflight_result
```

The helper should be called in a safe location before the existing capacity scenario alignment diagnostic is built, so that the diagnostic can include:

```text
runtime_attachment
```

### Expected behavior

If `env.capacity_weekly_rows` exists:

```text
apply_capacity_runtime_attachment_preflight(...) applies runtime attachment
env.explicit_pipeline_forward_weekly_capacity may be attached
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows may be attached
env.capacity_runtime_attachment_summary may be attached
env.capacity_runtime_attachment_preflight_result is attached
```

If `env.capacity_weekly_rows` is missing:

```text
apply_capacity_runtime_attachment_preflight(...) skips safely
env.capacity_runtime_attachment_preflight_result is still attached
result["applied"] == False
result["reason"] == "capacity_weekly_rows_missing"
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
scenario package loading
capacity_master.csv loading
week-key normalization
calendar conversion
capacity applicability status enforcement
new optimization logic
new planner calls
GUI layout changes
new GUI widgets
```

This request only wires an existing preflight helper into the Explicit KPI preflight path.

---

## 6. Preferred Implementation Location

Likely location:

```text
pysi/gui/cockpit_tk.py
```

Likely existing method / area:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

or the existing Explicit KPI preflight helper code that currently attaches capacity scenario alignment diagnostics.

The exact method name should be confirmed by inspecting the current code.

The wiring should be minimal:

```text
import apply_capacity_runtime_attachment_preflight
call it during Explicit KPI preflight
store the result on env
pass or collect messages without changing GUI layout
```

---

## 7. Recommended Call Order

Recommended order inside Explicit KPI preflight:

```text
1. Existing Explicit KPI demo flag setup.
2. Existing backward / forward capacity context setup, if any.
3. Call apply_capacity_runtime_attachment_preflight(env, messages=preflight_messages).
4. Attach returned result to env.capacity_runtime_attachment_preflight_result.
5. Existing capacity scenario alignment diagnostic.
6. Existing ctx guard check.
7. Existing Explicit KPI view-model / message construction.
```

The key requirement:

```text
apply_capacity_runtime_attachment_preflight(...) should run before the capacity scenario alignment diagnostic is built.
```

Reason:

```text
The diagnostic can then read env.capacity_runtime_attachment_summary and include diagnostic["runtime_attachment"].
```

---

## 8. Message Policy

The helper accepts:

```python
messages: list[str] | None
```

Use the existing preflight / diagnostic message list if one exists.

If there is no suitable existing list, use a local list and attach messages through the existing diagnostic path only if safe.

Do not change GUI layout.

Do not add new view components.

Do not double-prefix messages.

Current helper messages may include:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical side context attached.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

If existing Explicit KPI view-model already surfaces diagnostic messages, let the existing mechanism handle them.

---

## 9. Safe Skip Policy

Call the helper even if `env.capacity_weekly_rows` may be missing.

The helper already handles this safely.

When missing:

```text
env.capacity_runtime_attachment_preflight_result should exist
result["applied"] == False
result["reason"] == "capacity_weekly_rows_missing"
```

This is preferred over silently doing nothing.

Reason:

```text
The diagnostic path can explain that no canonical capacity rows were available.
```

---

## 10. Rows-Present Policy

If `env.capacity_weekly_rows` exists, the helper should attach contexts via the existing env attach helper.

Expected attributes after wiring, when rows are present:

```text
env.capacity_runtime_attachment_preflight_result
env.capacity_runtime_attachment_summary
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

The wiring must not replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

The safe canonical side-attribute strategy must remain intact.

---

## 11. Runtime Attachment Diagnostic Policy

After the helper is called, the existing capacity scenario alignment diagnostic should continue to be built.

The final diagnostic should include:

```text
diagnostic["runtime_attachment"]
```

If rows are missing, the diagnostic should still report:

```text
summary missing
or preflight skipped because capacity_weekly_rows is missing
```

Do not create a separate GUI diagnostic panel in this request.

---

## 12. Idempotency Policy

Explicit KPI preflight may run repeatedly.

Wiring should be safe under repeated calls.

Expected behavior:

```text
derived env capacity runtime attributes may be rebuilt deterministically
messages should not accumulate on persistent env state unless existing flow already does so
no source rows should be mutated
no planner state should be altered
```

Tests should cover repeated preflight invocation if feasible.

---

## 13. Error Handling Policy

If the existing preflight code has a safe wrapper pattern, follow it.

Otherwise, keep the wiring simple and rely on the helper's tested normal behavior.

Do not add broad exception handling that hides errors unless existing style requires it.

If a broad catch is added, it must:

```text
attach a safe unavailable preflight result
append a clear warning message
avoid planner behavior changes
```

Near-term preference:

```text
simple direct call with focused tests
```

---

## 14. Suggested Tests

Add focused tests in a new file or extend existing GUI wiring tests.

Preferred new file:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

Alternative:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Use the existing test style in the repository.

### 14.1 Rows-present case

Given an env / cockpit preflight setup with:

```text
env.capacity_weekly_rows
```

assert after Explicit KPI preflight:

```text
env.capacity_runtime_attachment_preflight_result exists
env.capacity_runtime_attachment_preflight_result["applied"] is True
env.capacity_runtime_attachment_summary exists
env.explicit_pipeline_forward_weekly_capacity exists
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows exists
```

### 14.2 Rows-missing safe skip

Given an env / cockpit preflight setup without:

```text
env.capacity_weekly_rows
```

assert:

```text
env.capacity_runtime_attachment_preflight_result exists
result["applied"] is False
result["reason"] == "capacity_weekly_rows_missing"
```

### 14.3 Diagnostic contains runtime_attachment

Assert the existing capacity scenario alignment diagnostic includes:

```text
runtime_attachment
```

### 14.4 Message propagation

Assert messages include one of:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

depending on test setup.

### 14.5 Repeated preflight

If feasible, call the preflight twice.

Assert:

```text
no exception
result remains deterministic
no duplicate persistent env message accumulation if applicable
```

### 14.6 No planner behavior change

Do not assert changes in plan results.

Do not require planner execution.

### 14.7 No GUI layout change

Do not assert new widgets.

Do not modify view layout.

---

## 15. Test Commands

Run focused test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

If modifying existing GUI wiring test:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Run related tests:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Run capacity regression if reasonable:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
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

Avoid modifying unless absolutely necessary:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Expected changed files:

```text
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

or, if extending existing tests:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Possibly changed only for imports or helper access:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Do not change planner behavior.

Do not change data CSV files.

Do not load capacity_master.csv here.

---

## 17. Acceptance Criteria

This request is complete when:

```text
apply_capacity_runtime_attachment_preflight(...) is called during Explicit KPI preflight
env.capacity_runtime_attachment_preflight_result is attached
rows-present case attaches runtime capacity contexts
rows-missing case skips safely
runtime_attachment diagnostic remains visible
messages propagate through existing message path or are available on preflight result
no planner behavior changes are made
no capacity enforcement changes are made
no GUI layout changes are made
no data CSV files are changed
no capacity master loading is added
focused tests pass
related GUI/preflight/diagnostic tests pass
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was apply_capacity_runtime_attachment_preflight wired?
At what point in the Explicit KPI preflight order is it called?
Is env.capacity_runtime_attachment_preflight_result attached?
What happens when env.capacity_weekly_rows is present?
What happens when env.capacity_weekly_rows is missing?
Does runtime_attachment remain visible in the diagnostic?
How are messages propagated?
Did you change planner behavior?
Did you change capacity enforcement?
Did you change GUI layout?
Did you change data CSV files?
Did you load capacity_master.csv?
Which tests passed?
```

---

## 19. Development Meaning

This request connects the preflight helper into the actual Explicit KPI operation route.

Already completed:

```text
capacity runtime preflight helper
```

This request adds:

```text
Explicit KPI preflight
    ↓
capacity runtime preflight helper
```

Still not included:

```text
planner behavior change
capacity enforcement change
scenario package loading
data loading
GUI layout change
```

The purpose is to make capacity runtime attachment visible in the Explicit KPI preflight route without changing the train schedule.

In short:

```text
The route inspection helper exists.
This request inserts it into the Explicit KPI route inspection path.
```
