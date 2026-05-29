# WOM Capacity Runtime Attachment Explicit KPI Preflight Wiring Completion Memo

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md`

**Related design docs:**

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
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_request.md
```

---

## 1. Purpose

This completion memo records the completion of wiring the capacity runtime attachment preflight helper into the existing Explicit KPI preflight flow.

The completed scope is intentionally narrow:

```text
Explicit KPI preflight
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_preflight_result
    ↓
existing capacity scenario alignment diagnostic
```

This phase connects the already implemented preflight helper into the actual Explicit KPI preflight route.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change blocked lot behavior.

It does not change data CSV files.

It does not load `capacity_master.csv`.

It does not implement scenario package loading.

It does not normalize week keys.

It does not change GUI layout.

---

## 2. Key Commit

Implementation commit:

```text
f480156 Wire capacity runtime preflight into explicit KPI
```

Related preceding commits:

```text
804caef Add WOM capacity runtime attachment Explicit KPI preflight wiring design
03c3d82 Add WOM capacity runtime attachment Explicit KPI preflight wiring Codex request
c109378 Add WOM capacity runtime attachment preflight wiring completion memo
258eb31 Add capacity runtime attachment preflight helper
2c4aa30 Add WOM capacity runtime attachment preflight wiring Codex request
2cd048c Add WOM capacity runtime attachment preflight wiring design
b065c77 Add WOM capacity runtime attachment diagnostic integration completion memo
45477fc Add capacity runtime attachment diagnostic
d8a8a36 Add weekly capacity runtime env attach helper
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation wired:

```python
apply_capacity_runtime_attachment_preflight(...)
```

into the existing Explicit KPI preflight path.

The wiring was added in:

```text
pysi/gui/cockpit_tk.py
```

through a helper method:

```text
_maybe_apply_capacity_runtime_attachment_preflight
```

which is called from:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

The helper return value is attached to:

```text
env.capacity_runtime_attachment_preflight_result
```

The call is positioned:

```text
after existing backward / forward Explicit KPI capacity context attachment
before the existing capacity scenario alignment diagnostic is built
```

This ordering is important because the capacity scenario alignment diagnostic can now see the runtime attachment state.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

### 4.1 cockpit_tk.py

Added Explicit KPI preflight wiring for:

```python
apply_capacity_runtime_attachment_preflight(...)
```

The new wiring:

```text
creates / passes a local preflight message list
calls the preflight helper
attaches the returned result to env.capacity_runtime_attachment_preflight_result
preserves existing capacity scenario alignment diagnostic flow
```

### 4.2 test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py

Added focused tests covering:

```text
rows-present attachment
rows-missing safe skip
runtime_attachment diagnostic visibility
message availability
preflight call ordering
repeated invocation determinism
```

---

## 5. Completed Call Order

The completed call order in the Explicit KPI preflight flow is:

```text
1. Existing Explicit KPI demo flag setup.
2. Existing backward capacity context attachment.
3. Existing forward capacity context attachment.
4. New capacity runtime attachment preflight.
5. Existing capacity scenario alignment diagnostic.
6. Existing ctx guard check.
7. Existing Explicit KPI view-model / message construction.
```

The key newly completed step is:

```text
New capacity runtime attachment preflight
```

which calls:

```python
apply_capacity_runtime_attachment_preflight(...)
```

before the existing diagnostic hook.

---

## 6. Behavior When env.capacity_weekly_rows Is Present

When:

```text
env.capacity_weekly_rows
```

exists, the preflight helper applies runtime capacity attachment.

Expected env attributes after the preflight include:

```text
env.capacity_runtime_attachment_preflight_result
env.capacity_runtime_attachment_summary
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

The returned result has:

```text
applied = True
row_source = "env.capacity_weekly_rows"
```

The canonical backward context is still attached only to the safe side attribute:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

The implementation does not replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

This preserves the safe backward consumer-facing boundary.

---

## 7. Behavior When env.capacity_weekly_rows Is Missing

When:

```text
env.capacity_weekly_rows
```

is missing, the helper skips safely.

The preflight result is still attached:

```text
env.capacity_runtime_attachment_preflight_result
```

Expected result fields:

```text
applied = False
reason = "capacity_weekly_rows_missing"
row_source = "missing"
```

This means the Explicit KPI preflight can now explain that no canonical capacity rows were available.

It no longer silently lacks runtime capacity attachment state.

---

## 8. Diagnostic Visibility

The capacity scenario alignment diagnostic remains the main diagnostic object.

Because the runtime attachment preflight now runs before that diagnostic, the final diagnostic can include:

```text
runtime_attachment
```

The focused test verifies that:

```text
diagnostic["runtime_attachment"]
```

remains visible and is marked available when rows are present.

This confirms the intended flow:

```text
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
capacity scenario alignment diagnostic
    ↓
diagnostic["runtime_attachment"]
```

---

## 9. Message Propagation

The implementation uses a local preflight message list and passes it into:

```python
apply_capacity_runtime_attachment_preflight(...)
```

The returned preflight result retains helper messages.

The diagnostic path also continues to expose runtime attachment messages.

Examples of expected messages include:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical side context attached.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

This phase does not change GUI layout or add new view widgets.

Messages remain available through existing diagnostic / message paths.

---

## 10. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
blocked lot behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
data CSV files
sample CSV files
capacity_master.csv loading
scenario package loading
week-key normalization
calendar conversion
GUI layout
Management Cockpit layout
capacity applicability status enforcement
```

This phase only added:

```text
Explicit KPI preflight wiring
focused tests
```

---

## 11. Tests Executed

Focused Explicit KPI preflight wiring test passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py -q
```

Observed result:

```text
5 passed
```

Existing GUI wiring test passed:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py -q
```

Observed result:

```text
9 passed
```

Related runtime attachment / diagnostic / KPI view tests passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_wom_capacity_weekly_rows_runtime_env_attach.py tests/test_explicit_pipeline_capacity_scenario_alignment.py tests/test_explicit_pipeline_management_cockpit_kpi_view.py -q
```

Observed result:

```text
39 passed
```

Capacity regression tests passed:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py -q
```

Observed result:

```text
34 passed
```

---

## 12. Current Architecture After This Phase

The capacity canonical path is now:

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
    ↓
Explicit KPI preflight wiring
```

Operationally:

```text
Explicit KPI preflight
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_preflight_result
    ↓
capacity scenario alignment diagnostic
    ↓
runtime_attachment diagnostic visibility
```

This is the first completed wiring of canonical capacity runtime attachment into the actual Explicit KPI preflight route.

---

## 13. Still Deferred

The following work remains intentionally deferred.

### 13.1 Capacity row source loading

The Explicit KPI preflight now calls the helper, but the helper still depends on:

```text
env.capacity_weekly_rows
```

being already present.

This phase does not load:

```text
capacity_master.csv
scenario yaml
scenario package master files
```

### 13.2 Scenario package integration

Scenario package integration remains future work.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

### 13.3 Planner consumption

No planner behavior has changed.

The canonical backward side attribute is still not consumed by a planner-facing backward capability consumer.

### 13.4 GUI layout / message layout

No GUI layout changes were introduced.

Future work may decide how much of the runtime attachment diagnostic should be shown in the Explicit KPI View messages.

### 13.5 Capacity applicability status

No first-class status taxonomy is implemented yet.

Future candidates include:

```text
absent_unlimited_fallback
present_aligned_applied
present_misaligned_product
present_misaligned_node
present_misaligned_week_domain
present_misaligned_shape
applied_and_blocking
```

---

## 14. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
```

Purpose:

```text
Define how capacity_master.csv or scenario package capacity master inputs should populate env.capacity_weekly_rows
before Explicit KPI preflight runs.
```

This is the next missing source-side link.

Current status:

```text
apply_capacity_runtime_attachment_preflight(...) is wired into Explicit KPI preflight.
```

Remaining source-side question:

```text
Where does env.capacity_weekly_rows come from in actual scenario execution?
```

This next design should address:

```text
capacity_master.csv source location
scenario package master path
legacy PySI V0R8 adapter boundary
when load_capacity_master_csv(...) is called
where env.capacity_weekly_rows is attached
how missing file is handled
how explicit demo / scenario package behavior differs
no planner behavior change
```

Possible Codex request after that:

```text
docs/codex_requests/wom_capacity_master_to_env_capacity_weekly_rows_source_request.md
```

---

## 15. Development Meaning

Before this phase, WOM had a capacity runtime preflight helper, but it was not part of the Explicit KPI operation route.

After this phase, WOM has:

```text
Explicit KPI preflight
    ↓
capacity runtime preflight helper
    ↓
runtime attachment diagnostic
```

This is important because capacity runtime attachment is now visible during the actual Explicit KPI preflight route.

The train schedule is still unchanged.

But the route inspection is now part of the official pre-departure checklist.

In short:

```text
The route inspection helper has boarded the Explicit KPI train.
The next question is where the official capacity row cargo is loaded.
```

---

## 16. Summary

Completed:

```text
apply_capacity_runtime_attachment_preflight(...)
    ↓
Explicit KPI preflight wiring
```

Confirmed:

```text
helper is called during Explicit KPI preflight
result is attached to env.capacity_runtime_attachment_preflight_result
rows-present case attaches runtime contexts
rows-missing case skips safely
runtime_attachment remains visible in diagnostic
messages remain available
focused tests passed
related tests passed
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
data CSV unchanged
capacity_master.csv not loaded
scenario package loading unchanged
```

Next:

```text
capacity_master.csv / scenario package capacity input
    ↓
env.capacity_weekly_rows
```

Recommended next design:

```text
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
```
