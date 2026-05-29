# WOM Capacity Runtime Attachment Preflight Wiring Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md`

**Related design docs:**

```text
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
docs/codex_requests/wom_capacity_runtime_attachment_preflight_wiring_request.md
```

---

## 1. Purpose

This completion memo records the completion of the first safe preflight wiring helper for WOM capacity runtime attachment.

The completed scope is intentionally narrow:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
preflight result / messages
```

This phase adds a preflight-level route inspection helper.

It does not wire the helper into GUI preflight.

It does not wire the helper into scenario runner preflight.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change GUI behavior.

It does not change data CSV files.

It does not implement scenario package loading.

It does not normalize week keys.

---

## 2. Key Commit

Implementation commit:

```text
258eb31 Add capacity runtime attachment preflight helper
```

Related preceding commits:

```text
2cd048c Add WOM capacity runtime attachment preflight wiring design
2c4aa30 Add WOM capacity runtime attachment preflight wiring Codex request
b065c77 Add WOM capacity runtime attachment diagnostic integration completion memo
45477fc Add capacity runtime attachment diagnostic
2a59235 Add WOM capacity runtime attachment diagnostic integration Codex request
13f08e6 Add WOM capacity runtime attachment diagnostic integration design
0b226d1 Add WOM capacity weekly rows runtime env attach completion memo
d8a8a36 Add weekly capacity runtime env attach helper
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation added:

```python
apply_capacity_runtime_attachment_preflight(...)
```

in:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

The helper:

```text
looks for env.capacity_weekly_rows
skips safely when env.capacity_weekly_rows is missing
calls attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows) when rows exist
calls build_capacity_runtime_attachment_diagnostic(env)
returns a structured preflight result
appends result-level messages to an external messages list when supplied
```

The helper delegates to existing functions.

It does not duplicate runtime attachment logic.

It does not duplicate diagnostic logic.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

### 4.1 explicit_pipeline_capacity_scenario_alignment.py

Added:

```python
apply_capacity_runtime_attachment_preflight(...)
```

The helper imports and delegates to:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
build_capacity_runtime_attachment_diagnostic(...)
```

### 4.2 test_wom_capacity_runtime_attachment_preflight_wiring.py

Added focused tests covering:

```text
missing env.capacity_weekly_rows
present env.capacity_weekly_rows
empty env.capacity_weekly_rows
external message propagation
idempotency / repeated calls
```

---

## 5. Helper Behavior

### 5.1 When env.capacity_weekly_rows is missing

If `env.capacity_weekly_rows` is missing, the helper:

```text
does not call runtime env attachment
returns applied=False
returns reason="capacity_weekly_rows_missing"
reports row_source="missing"
calls build_capacity_runtime_attachment_diagnostic(env)
returns runtime attachment diagnostic
emits skip message
```

Skip message:

```text
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

This is a safe skip, not an error.

It means that the preflight route did not receive a canonical capacity row source.

### 5.2 When env.capacity_weekly_rows is present

If `env.capacity_weekly_rows` exists, the helper:

```text
materializes rows as a list
calls attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, row_list)
calls build_capacity_runtime_attachment_diagnostic(env)
returns applied=True
returns row_source="env.capacity_weekly_rows"
returns input_row_count
returns attachment_summary
returns runtime_attachment diagnostic
returns messages
```

The helper attaches derived runtime attributes through the existing env attach helper.

### 5.3 When env.capacity_weekly_rows is an empty list

If `env.capacity_weekly_rows = []`, the helper treats this differently from a missing attribute.

It:

```text
returns applied=True
input_row_count=0
calls the attach helper with an empty list
attaches deterministic empty runtime contexts
returns runtime attachment summary with available=False
reports no WeeklyCapacityRow rows
```

This distinction is important.

```text
missing rows:
    no row source was provided

empty rows:
    row source exists, but it contains no rows
```

### 5.4 External messages list

If an external list is supplied:

```python
messages = []
apply_capacity_runtime_attachment_preflight(env, messages=messages)
```

the helper appends result-level messages into that list.

This supports later preflight / GUI message orchestration without requiring GUI changes in this phase.

### 5.5 Idempotency

Focused tests confirm that repeated calls are safe.

Repeated calls rebuild/replace derived env attributes deterministically and do not raise exceptions.

---

## 6. Returned Result Structure

The helper returns a structured dictionary.

Conceptual successful result:

```python
{
    "applied": True,
    "reason": None,
    "row_source": "env.capacity_weekly_rows",
    "input_row_count": 2,
    "attachment_summary": {...},
    "runtime_attachment": {...},
    "messages": [...],
}
```

Conceptual skipped result:

```python
{
    "applied": False,
    "reason": "capacity_weekly_rows_missing",
    "row_source": "missing",
    "input_row_count": 0,
    "attachment_summary": None,
    "runtime_attachment": {...},
    "messages": [
        "Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.",
        ...
    ],
}
```

---

## 7. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
GUI behavior
GUI preflight wiring
scenario runner wiring
data CSV files
sample CSV files
scenario package loading
capacity master CSV loading
week-key normalization
calendar conversion
capacity applicability status
```

This phase only added:

```text
preflight helper
focused tests
```

---

## 8. Tests Executed

Focused preflight wiring test passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

Observed result:

```text
5 passed
```

Related diagnostic / attachment / capacity tests passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_wom_capacity_weekly_rows_runtime_env_attach.py tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py tests/test_explicit_pipeline_capacity_scenario_alignment.py tests/test_capacity_input_granularity_adapter.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py
```

Observed result:

```text
72 passed
```

---

## 9. Current Architecture After This Phase

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
preflight result / messages
```

More practically:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
runtime capacity contexts attached
    ↓
runtime attachment diagnostic built
    ↓
preflight result returned
```

This is the first completed preflight helper for canonical capacity runtime attachment.

---

## 10. Still Deferred

The following work remains intentionally deferred.

### 10.1 GUI / Explicit KPI preflight wiring

The helper is not yet called from:

```text
cockpit_tk.py
Explicit KPI demo preflight
Management Cockpit view flow
```

### 10.2 Scenario runner wiring

The helper is not yet called from:

```text
run_wom_scenario
scenario package runner
Japanese Rice Case runner
```

### 10.3 Capacity row source loading

The helper assumes rows already exist at:

```text
env.capacity_weekly_rows
```

It does not load:

```text
capacity_master.csv
scenario yaml
scenario package master files
```

### 10.4 Planner consumption

No planner consumes the canonical backward side attribute yet:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

### 10.5 GUI message surfacing

The helper returns and appends messages, but no new GUI rendering behavior was introduced.

### 10.6 Capacity applicability status

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

## 11. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
```

Purpose:

```text
Define whether and how apply_capacity_runtime_attachment_preflight(...)
should be called from the existing Explicit KPI preflight flow.
```

This design should address:

```text
where env.capacity_weekly_rows comes from
whether existing Explicit KPI demo flow already has capacity rows
exact call order relative to current capacity context attach
exact call order relative to capacity scenario alignment diagnostic
message prefixing
safe skip behavior
no planner behavior change
no GUI layout change
```

Possible later Codex request:

```text
docs/codex_requests/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_request.md
```

The first implementation should remain narrow:

```text
call preflight helper only when env.capacity_weekly_rows already exists
append messages to existing diagnostic/message flow
do not load CSV
do not change planner behavior
do not change GUI layout
```

---

## 12. Development Meaning

Before this phase, WOM had:

```text
master file
    ↓
canonical row
    ↓
runtime context
    ↓
env attachment
    ↓
diagnostic explanation
```

After this phase, WOM has:

```text
preflight helper
    ↓
safe runtime capacity attachment
    ↓
diagnostic explanation
```

This is an important step toward WOM as a self-checking planning environment.

Capacity runtime context is no longer just manually callable code.

It now has a preflight-level route inspection helper.

In short:

```text
The signal system exists.
The route inspection helper is now implemented.
The train still has not departed.
```

---

## 13. Summary

Completed:

```text
apply_capacity_runtime_attachment_preflight(...)
```

Confirmed:

```text
missing env.capacity_weekly_rows skips safely
present env.capacity_weekly_rows applies env attach helper
empty env.capacity_weekly_rows handled deterministically
runtime attachment diagnostic built after skip or attach
structured result returned
external messages list supported
idempotency confirmed
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
scenario loading unchanged
GUI/scenario runner wiring unchanged
```

Next:

```text
apply_capacity_runtime_attachment_preflight(...)
    ↓
Explicit KPI / scenario preflight integration
```

Recommended next design:

```text
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
```
