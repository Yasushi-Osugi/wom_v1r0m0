# Explicit Pipeline Backward Weekly Capability GUI Preflight Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines Phase 2B for:

```text
explicit_pipeline_backward_weekly_capability
```

Phase 1 implemented the pure context adapter.

Phase 2A implemented the optional CSV attach helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

Phase 2B defines how to call that helper from the Explicit KPI GUI preflight path.

The goal is:

```text
Explicit KPI ON checked
    ↓
Run Full Plan
    ↓
preflight applies demo flags
    ↓
preflight optionally loads default capability CSV
    ↓
env.explicit_pipeline_backward_weekly_capability may be attached
    ↓
ctx guard checks required context
```

This phase is the first point where the existing GUI path can use the capability CSV automatically.

---

## 2. Current State

Current completed components:

```text
Explicit KPI ON checkbox
demo flag helper
required ctx guard
ctx guard diagnostics view
capability context builder
capability CSV loader
env attach helper
optional CSV attach helper
```

The current remaining gap is:

```text
Explicit KPI ON preflight does not yet call the optional CSV attach helper.
```

Therefore, even though the helper exists, the GUI still cannot automatically load the capability context.

---

## 3. Scope

This phase should add a small, safe call from the Explicit KPI preflight path to:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

The intended integration point is:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

in:

```text
pysi/gui/cockpit_tk.py
```

This phase should not create sample CSV data.

This phase should not modify the planning engine.

This phase should not run exports or replanning.

---

## 4. Non-Goals

This phase must not implement:

```text
sample capability CSV commit
scenario selector
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
process-level capacity
resource-level capacity
planning algorithm changes
export execution
ReplanCommand execution
automatic replanning
OR optimization
database persistence
large GUI redesign
```

This phase only wires the already implemented optional attach helper into the Explicit KPI ON preflight path.

---

## 5. Existing Preflight Flow

The existing method:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

currently does roughly this:

```text
if checkbox variable is missing:
    return None

if Explicit KPI ON is unchecked:
    return None

apply_explicit_pipeline_kpi_demo_flags(env, include_exports=False)

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(env)

if missing_ctx_keys:
    record ctx guard diagnostics
    force explicit flags off
    return applied

record ctx guard not skipped
return applied
```

This flow is correct and should be preserved.

---

## 6. New Preflight Flow

Recommended new flow:

```text
if checkbox variable is missing:
    return None

if Explicit KPI ON is unchecked:
    return None

apply_explicit_pipeline_kpi_demo_flags(env, include_exports=False)

maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env,
    path="data/explicit_pipeline_backward_weekly_capability.csv",
    scenario="base",
    strict=False,
)

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(env)

if missing_ctx_keys:
    record ctx guard diagnostics
    force explicit flags off
    return applied

record ctx guard not skipped
return applied
```

This preserves current safety behavior.

---

## 7. Default CSV Path

The default path remains:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

This file is not created in this phase.

If it does not exist, the helper returns:

```text
reason = file_missing
attached = False
```

Then the current ctx guard diagnostic remains visible.

---

## 8. Safe Behavior Matrix

### 8.1 Explicit KPI OFF

```text
checkbox OFF
    ↓
no demo flags
    ↓
no attach attempt
    ↓
existing behavior preserved
```

### 8.2 Explicit KPI ON + no CSV

```text
checkbox ON
    ↓
demo flags applied
    ↓
attach helper called
    ↓
file_missing
    ↓
ctx guard sees missing capability
    ↓
explicit pipeline skipped
    ↓
diagnostic shown
```

This is the same user-visible behavior as today, with additional attach diagnostics on env.

### 8.3 Explicit KPI ON + invalid / empty CSV

```text
checkbox ON
    ↓
demo flags applied
    ↓
attach helper called
    ↓
empty_context
    ↓
ctx guard sees missing capability
    ↓
explicit pipeline skipped
    ↓
diagnostic shown
```

This also preserves safety.

### 8.4 Explicit KPI ON + valid CSV

```text
checkbox ON
    ↓
demo flags applied
    ↓
attach helper called
    ↓
valid context attached
    ↓
ctx guard no longer reports explicit_pipeline_backward_weekly_capability
    ↓
explicit flags remain enabled
    ↓
explicit bridge capacity pipeline may run
```

If the explicit pipeline still fails or produces no data, the next diagnostic should inspect:

```text
context shape
node names
product names
week keys
other required context keys
pipeline expectations
```

---

## 9. Import Strategy

Inside:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

the helper can be imported together with existing preflight imports.

Current import pattern likely includes:

```python
from pysi.reporting import (
    apply_explicit_pipeline_kpi_demo_flags,
    get_missing_explicit_pipeline_demo_ctx_keys,
)
```

Add a local import:

```python
from pysi.plan.explicit_pipeline_capacity_context import (
    maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
)
```

Local import is acceptable here because the method is a preflight hook and this keeps module import side effects minimal.

---

## 10. Diagnostics

The optional attach helper already records:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_source_path
explicit_pipeline_backward_weekly_capability_source_scenario
explicit_pipeline_backward_weekly_capability_attached
```

The GUI preflight does not need to add new diagnostics in this phase.

However, it may keep the result in a local variable for easier future debugging:

```python
attach_result = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

No UI display is required in this phase.

---

## 11. Error Handling

Recommended MVP:

```text
Use strict=False.
Do not catch unexpected exceptions unless the helper already handles them.
```

Reason:

```text
invalid rows should be skipped by the loader/builder
missing files should be handled by the helper
unexpected programming errors should remain visible during development
```

If later GUI hardening is needed, a defensive try/except can be added, but not in this phase unless tests show a need.

---

## 12. Tests to Add / Update

Recommended test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Add tests for the new preflight behavior.

### 12.1 Explicit KPI OFF does not attempt attach

Given:

```text
Explicit KPI OFF
```

Expected:

```text
_maybe_apply_explicit_kpi_demo_flags() returns None
no attach diagnostics are required
no flags are changed
```

If monkeypatching the helper is easy, assert helper was not called.

### 12.2 Explicit KPI ON + helper missing file keeps guard skip

Monkeypatch helper to return:

```python
{
    "attached": False,
    "reason": "file_missing",
    ...
}
```

or use a missing temp path if path injection is added.

Expected:

```text
ctx guard skipped remains True
explicit flags forced off
missing ctx keys includes explicit_pipeline_backward_weekly_capability
```

### 12.3 Explicit KPI ON + helper attaches context allows guard pass

Monkeypatch helper so it sets:

```python
env.explicit_pipeline_backward_weekly_capability = {"MOM_A": {"P1": {"202601": 100}}}
```

Expected:

```text
ctx guard skipped is False
missing ctx keys == []
enable_explicit_bridge_capacity_pipeline remains True
```

### 12.4 Preflight ordering

Ensure order remains:

```text
apply demo flags
then attach capability context
then ctx guard check
then Run Full Plan continues
```

If existing test already checks run_full_plan preflight ordering, extend it carefully without brittle GUI assumptions.

---

## 13. Test Design Note

The helper has a default hardcoded path:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Unit tests should avoid depending on a real file in `data/`.

Recommended approach:

```text
monkeypatch the imported helper function used by cockpit_tk.py
```

or factor the preflight call into a tiny private method:

```python
WOMCockpit._maybe_attach_explicit_pipeline_backward_weekly_capability()
```

Recommended MVP:

```text
Add a small private method to WOMCockpit
```

Example:

```python
def _maybe_attach_explicit_pipeline_backward_weekly_capability(self) -> dict[str, Any] | None:
    from pysi.plan.explicit_pipeline_capacity_context import (
        maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
    )
    return maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(self.env)
```

Then `_maybe_apply_explicit_kpi_demo_flags()` calls:

```python
self._maybe_attach_explicit_pipeline_backward_weekly_capability()
```

This makes monkeypatching or subclass testing easier.

---

## 14. Recommended Implementation Pattern

Add private method:

```python
def _maybe_attach_explicit_pipeline_backward_weekly_capability(self) -> dict[str, Any] | None:
    from pysi.plan.explicit_pipeline_capacity_context import (
        maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
    )

    return maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(self.env)
```

Then in `_maybe_apply_explicit_kpi_demo_flags()`:

```python
applied = apply_explicit_pipeline_kpi_demo_flags(
    self.env,
    include_exports=False,
)

self._maybe_attach_explicit_pipeline_backward_weekly_capability()

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(self.env)
```

This keeps the new behavior small and testable.

---

## 15. Completion Criteria

This phase is complete when:

```text
[OK] Explicit KPI ON preflight calls optional capability attach helper
[OK] Explicit KPI OFF does not call attach helper
[OK] missing CSV behavior remains safe
[OK] invalid/empty context behavior remains safe
[OK] valid context can allow ctx guard pass
[OK] current ctx guard diagnostic behavior is preserved when no valid context exists
[OK] no planning/export/replan execution is added
[OK] no sample CSV is added
[OK] focused tests pass
```

---

## 16. Manual GUI Validation Target

Manual GUI validation is optional in this phase if no sample CSV exists.

Without CSV:

```text
1. python -m main
2. Explicit KPI ON
3. Run Full Plan
4. Explicit KPI View still shows missing context diagnostic
```

This confirms no regression.

With a manually created matching CSV:

```text
1. create data/explicit_pipeline_backward_weekly_capability.csv
2. python -m main
3. Explicit KPI ON
4. Run Full Plan
5. Explicit KPI View no longer shows missing context diagnostic for explicit_pipeline_backward_weekly_capability
```

However, matching node/product/week values are required for the pipeline to produce meaningful data.

A later sample CSV phase should define these values deliberately.

---

## 17. Risks and Mitigations

### 17.1 Risk: CSV exists but does not match scenario

Mitigation:

```text
helper attaches context if non-empty,
but later pipeline may produce no meaningful result.
Use diagnostics and tests to inspect node/product/week shape.
```

### 17.2 Risk: invalid CSV silently yields empty context

Mitigation:

```text
empty_context result is recorded on env.
ctx guard still explains missing context.
```

### 17.3 Risk: helper call changes behavior when no file exists

Mitigation:

```text
missing file returns file_missing and does not attach.
ctx guard behavior remains unchanged.
```

### 17.4 Risk: existing manually attached context is overwritten

Mitigation:

```text
Phase 2A helper already preserves existing context on failed attach.
```

---

## 18. Later Phase: Sample CSV

A later Phase 2C should define and commit a scenario-specific sample CSV.

Candidate file:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

or:

```text
pysi/master_data/explicit_pipeline_backward_weekly_capability_sample.csv
```

Before committing a sample file, confirm:

```text
actual MOM node id
actual product id/name
actual week bucket format
expected capability lot counts
```

---

## 19. Later Phase: Capability Diagnostics in View

The attach diagnostics could later be surfaced in the Explicit KPI View.

Potential rows:

```text
Capability CSV Attach: attached / file_missing / empty_context
Capability CSV Path: data/explicit_pipeline_backward_weekly_capability.csv
Capability Scenario: base
Capability Records: N
```

This is not required in Phase 2B.

---

## 20. Summary

Phase 2B connects the optional CSV attach helper to the Explicit KPI ON preflight.

Safe rule:

```text
Explicit KPI OFF:
    do nothing

Explicit KPI ON:
    apply demo flags
    try optional capability CSV attach
    then run ctx guard
```

This preserves current safety while allowing a valid capability CSV to supply:

```text
env.explicit_pipeline_backward_weekly_capability
```

before the explicit bridge capacity pipeline is enabled.

This is the first runtime bridge from the capability CSV master to the Explicit KPI cockpit path.
