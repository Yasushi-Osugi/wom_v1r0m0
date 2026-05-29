# WOM Capacity Weekly Rows Runtime Env Attach Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md`

**Related design docs:**

```text
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
docs/codex_requests/wom_capacity_weekly_rows_runtime_env_attach_request.md
```

---

## 1. Purpose

This completion memo records the completion of the first runtime env attachment helper for WOM canonical capacity rows.

The completed scope is intentionally narrow:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
env runtime attributes
```

This phase installs the first runtime switchyard for canonical capacity contexts.

It does not wire the helper into GUI preflight.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change GUI behavior.

It does not change data CSV files.

It does not implement scenario package loading.

---

## 2. Key Commit

Implementation commit:

```text
d8a8a36 Add weekly capacity runtime env attach helper
```

Related preceding commits:

```text
39a1d37 Add WOM capacity weekly rows runtime env attach design
07780b9 Add WOM capacity weekly rows runtime env attach Codex request
c798216 Add WOM capacity weekly rows to explicit backward context completion memo
1ee4008 Add weekly capacity backward context adapter
7161490 Add WOM capacity weekly rows to explicit backward context Codex request
31ed777 Add WOM capacity weekly rows to explicit backward context design
d48e51e Add WOM capacity weekly rows to explicit forward context completion memo
3a933fd Add weekly capacity row forward context adapter
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation added:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

in:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

The helper builds requested forward/backward runtime contexts locally, prepares a summary, and then attaches the requested attributes to `env`.

The implementation follows a transaction-like order:

```text
1. Build forward context locally.
2. Build backward context locally.
3. Build diagnostic/attachment summary locally.
4. Attach requested attributes to env.
5. Return summary.
```

This avoids partially attaching inconsistent runtime state.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

### 4.1 explicit_pipeline_capacity_context.py

Added env attachment helper:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

The helper uses the existing pure adapters:

```python
weekly_capacity_rows_to_explicit_forward_capacity(...)
weekly_capacity_rows_to_explicit_backward_capability(...)
```

### 4.2 test_wom_capacity_weekly_rows_runtime_env_attach.py

Added focused tests covering:

```text
forward context attachment
safe backward canonical side-attribute attachment
source row attachment
summary attachment
summary content
empty rows behavior
switch flags
```

---

## 5. Attached Env Attributes

Depending on flags, the helper attaches the following attributes.

### 5.1 Forward context

```text
env.explicit_pipeline_forward_weekly_capacity
```

This is attached when:

```text
attach_forward=True
```

The attached shape is:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

### 5.2 Backward canonical side context

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

This is attached when:

```text
attach_backward=True
```

The implementation intentionally does **not** replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

because the existing consumer-facing backward capability shape may still be:

```text
node_product_week_map_v1
```

The new product-first backward context is therefore attached to a safe canonical side attribute.

### 5.3 Source rows

```text
env.capacity_weekly_rows
```

This is attached when:

```text
attach_rows=True
```

### 5.4 Attachment summary

```text
env.capacity_runtime_attachment_summary
```

This is attached when:

```text
attach_summary=True
```

---

## 6. Backward Context Safety Strategy

The implementation used the safe canonical side-attribute strategy.

Completed behavior:

```text
Attach product-first backward context to:
  env.explicit_pipeline_backward_weekly_capability_from_weekly_rows

Do not replace:
  env.explicit_pipeline_backward_weekly_capability
```

The returned summary reports:

```text
backward_consumer_attribute_replaced = False
backward_canonical_attribute_attached = True
```

This is important because the current backward consumer-facing shape may not be the same as the product-first canonical context shape.

This phase therefore prepares the backward canonical context without risking planner compatibility.

---

## 7. Attachment Summary

The helper returns a summary dictionary and can attach the same summary to:

```text
env.capacity_runtime_attachment_summary
```

Summary fields include:

```text
available
input_row_count
attached_rows
attached_forward
attached_backward
forward_shape
backward_shape
forward_product_count
backward_product_count
node_count
capacity_type_count
week_key_count
week_key_domain
backward_consumer_attribute_replaced
backward_canonical_attribute_attached
messages
```

The shape name used for both pure forward and pure backward contexts is:

```text
product_node_type_week_qty_v1
```

Week key domain is reported as:

```text
preserve
```

---

## 8. Empty Rows Behavior

If the helper is called with an empty row list:

```text
rows = []
```

the helper does not crash.

It attaches requested empty contexts as empty dictionaries and returns a summary such as:

```text
available = False
input_row_count = 0
messages includes "No WeeklyCapacityRow rows provided."
```

This gives deterministic behavior for preflight or future scenario-loader paths where capacity input may be absent.

---

## 9. Switch Flags

The helper supports the following flags:

```python
attach_forward: bool = True
attach_backward: bool = True
attach_rows: bool = True
attach_summary: bool = True
```

Focused tests confirm:

```text
attach_forward=False
    does not attach env.explicit_pipeline_forward_weekly_capacity

attach_backward=False
    does not attach env.explicit_pipeline_backward_weekly_capability_from_weekly_rows

attach_rows=False
    does not attach env.capacity_weekly_rows

attach_summary=False
    does not attach env.capacity_runtime_attachment_summary
    but still returns summary
```

---

## 10. Week Key Policy

Week keys remain preserved.

This phase does not implement:

```text
business week label -> integer index
integer index -> business week label
calendar conversion
week-domain normalization
```

The helper delegates to the pure forward/backward adapters, both of which preserve week keys.

The summary reports:

```text
week_key_domain = "preserve"
```

---

## 11. Tests Executed

The focused env attach test passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

Observed result:

```text
6 passed
```

Related adapter tests passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Observed results:

```text
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py     7 passed
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py    8 passed
tests/test_wom_capacity_master_canonical_loader_adapter.py             6 passed
```

Related diagnostic / capacity tests passed:

```bat
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Observed results:

```text
tests/test_explicit_pipeline_forward_capacity_context.py          12 passed
tests/test_explicit_pipeline_capacity_scenario_alignment.py       11 passed
tests/test_capacity_input_granularity_adapter.py                  11 passed
```

The related capacity regression set also passed:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
34 passed
```

---

## 12. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
GUI behavior
data CSV files
sample CSV files
scenario selection
explicit KPI preflight wiring
Management Cockpit behavior
scenario package loading
week-key normalization
calendar conversion
capacity applicability status
```

This phase only added:

```text
runtime env attach helper
focused tests
```

---

## 13. Current Architecture After This Phase

The completed capacity canonical path is now:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

This is the first completed env switchyard for canonical capacity contexts.

---

## 14. Still Deferred

The following work remains intentionally deferred.

### 14.1 Preflight wiring

The helper is not yet wired into:

```text
Explicit KPI preflight
GUI preflight
scenario runner preflight
```

### 14.2 Planner consumption

No planner currently consumes the newly attached canonical backward side attribute.

Planner behavior remains unchanged.

### 14.3 Consumer-facing backward shape bridge

The canonical product-first backward context is not yet converted into the existing consumer-facing backward shape if that shape remains:

```text
node_product_week_map_v1
```

### 14.4 Diagnostic metadata integration

The existing capacity scenario alignment diagnostic does not yet fully consume:

```text
env.capacity_runtime_attachment_summary
```

### 14.5 Scenario package integration

Scenario yaml loading is not yet implemented.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

### 14.6 Capacity applicability status

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

## 15. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
```

Purpose:

```text
Define how env.capacity_runtime_attachment_summary should be used by capacity diagnostics
without changing planner behavior.
```

This design should address:

```text
capacity rows attached
forward context attached
backward canonical side context attached
backward consumer-facing context not replaced
shape metadata
week-domain metadata
diagnostic messages
Explicit KPI message surfacing later
```

Recommended Codex request after that:

```text
docs/codex_requests/wom_capacity_runtime_attachment_diagnostic_integration_request.md
```

The first implementation should remain narrow:

```text
diagnostic reads attachment summary
diagnostic reports attachment status
no planner behavior changes
no GUI changes
no preflight wiring changes
```

---

## 16. Development Meaning

Before this phase, WOM had:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
    ↓
explicit backward capability context
```

After this phase, WOM has:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
forward/backward runtime contexts
    ↓
env attach helper
```

This is a significant architectural step.

Capacity is now moving from:

```text
master file
```

to:

```text
canonical row
```

to:

```text
runtime context
```

to:

```text
env-attached diagnostic-ready state
```

without changing planner behavior.

In short:

```text
The switchyard is installed.
The next task is to connect the signal system: diagnostics.
```

---

## 17. Summary

Completed:

```text
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

Confirmed:

```text
forward context attached when requested
backward canonical side context attached when requested
source rows attached when requested
summary attached when requested
empty rows handled safely
switch flags work
week keys preserved
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
preflight wiring unchanged
```

Next:

```text
env.capacity_runtime_attachment_summary
    ↓
capacity diagnostic integration
```

Recommended next design:

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
```
