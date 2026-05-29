# WOM Capacity Weekly Rows to Explicit Backward Context Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_weekly_rows_to_explicit_backward_context_request.md
```

---

## 1. Purpose

This completion memo records the completion of the explicit backward capability runtime-context adapter for WOM canonical capacity rows.

The completed scope is intentionally narrow:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

This phase completes the pure forward/backward runtime-context conversion pair.

It does not attach anything to `env`.

It does not change planner behavior.

It does not change GUI behavior.

It does not change data CSV files.

It does not implement `env.weekly_capability`.

It does not implement scenario package loading.

---

## 2. Key Commit

Implementation commit:

```text
1ee4008 Add weekly capacity backward context adapter
```

Related preceding commits:

```text
31ed777 Add WOM capacity weekly rows to explicit backward context design
7161490 Add WOM capacity weekly rows to explicit backward context Codex request
d48e51e Add WOM capacity weekly rows to explicit forward context completion memo
3a933fd Add weekly capacity row forward context adapter
f89a5b6 Add WOM capacity weekly rows to explicit forward context Codex request
4bec580 Add WOM capacity weekly rows runtime context adapter design
dd51f72 Add WOM capacity master canonical loader adapter completion memo
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation added:

```python
weekly_capacity_rows_to_explicit_backward_capability(...)
```

in:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

The function converts canonical capacity rows into the explicit backward capability context shape:

```text
product_id
  -> capacity_owner_id
    -> capacity_type
      -> week
        -> capacity_qty
```

Conceptual example:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

### 4.1 explicit_pipeline_capacity_context.py

Added the backward capability runtime context adapter:

```python
weekly_capacity_rows_to_explicit_backward_capability(...)
```

The adapter:

```text
uses existing WeeklyCapacityRow
produces product -> node -> capacity_type -> week -> capacity_qty
preserves week keys as provided
does not normalize or convert week keys
does not filter by scenario
does not filter by product
does not filter by tree_side
does not filter by capacity_type
does not use cap_mode in this phase
sums duplicate product/node/capacity_type/week rows deterministically
returns {} for empty input
is not wired to env or planner behavior
```

### 4.2 test_wom_capacity_weekly_rows_to_explicit_backward_context.py

Added focused tests covering:

```text
empty input
happy path
product separation
node separation
capacity type separation
duplicate aggregation
week key preservation
forward/backward pure adapter symmetry
```

---

## 5. Input and Output Contract

### 5.1 Input

The adapter consumes:

```python
list[WeeklyCapacityRow]
```

using the existing canonical row class:

```text
pysi.adapters.capacity_input_granularity.WeeklyCapacityRow
```

No new row class was introduced.

### 5.2 Output

The adapter returns:

```text
dict[str, dict[str, dict[str, dict[object, int | float]]]]
```

Conceptually:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

### 5.3 Duplicate policy

Duplicate key:

```text
product_id
capacity_owner_id
capacity_type
week
```

is handled by:

```text
sum capacity_qty deterministically
```

### 5.4 Forward/backward symmetry

At the pure adapter level, the backward output shape is symmetric with the forward adapter output shape.

For the same `WeeklyCapacityRow` input set:

```text
weekly_capacity_rows_to_explicit_forward_capacity(rows)
weekly_capacity_rows_to_explicit_backward_capability(rows)
```

produce the same nested quantity structure.

This symmetry is confirmed by the focused test.

---

## 6. Week Key Policy

Week keys are preserved exactly as carried by each `WeeklyCapacityRow`.

Examples covered by tests:

```text
2027-W40
0
```

This phase does not implement:

```text
business week label -> integer index
integer index -> business week label
calendar conversion
week-domain normalization
```

Week-domain conversion remains a later adapter-boundary responsibility.

---

## 7. Cap Mode Policy

The explicit backward capability context built in this phase is quantity-only.

Therefore:

```text
WeeklyCapacityRow.cap_mode is not carried into the runtime context
```

This is intentional.

The current phase does not change planner contracts to consume richer capacity objects.

Future work may add a metadata sidecar that preserves:

```text
cap_mode
unit
priority
calendar_id
source_file
source_id
```

---

## 8. Consumer Compatibility Note

This implementation is a pure product-first adapter only.

It is not yet wired to:

```text
env.explicit_pipeline_backward_weekly_capability
```

The current existing consumer-facing backward capability shape detection still identifies the existing shape as:

```text
node_product_week_map_v1
```

Therefore, this phase should be understood as:

```text
canonical WeeklyCapacityRow -> pure product-first backward capability context
```

not as:

```text
replacement of existing backward runtime consumer shape
```

A later env-attachment or consumer-adapter phase must explicitly decide whether to:

```text
1. attach this product-first shape directly, or
2. convert this product-first shape into the existing consumer-facing backward shape.
```

---

## 9. Tests Executed

The focused backward test passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Observed result:

```text
8 passed
```

Related forward/canonical/diagnostic tests passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Observed results:

```text
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py     7 passed
tests/test_wom_capacity_master_canonical_loader_adapter.py             6 passed
tests/test_explicit_pipeline_forward_capacity_context.py               12 passed
tests/test_explicit_pipeline_capacity_scenario_alignment.py            11 passed
tests/test_capacity_input_granularity_adapter.py                       11 passed
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

## 10. Safety Boundaries Honored

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
env attachment
env.weekly_capability
week-key normalization
calendar conversion
capacity applicability status
scenario package loader
```

This phase only added:

```text
WeeklyCapacityRow -> explicit backward capability context adapter
focused tests
```

---

## 11. Current Architecture After This Phase

The completed canonical capacity path is now:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
explicit forward capacity context
```

and:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
explicit backward capability context
```

Together:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
forward context
    ↓
backward context
```

The forward/backward pure conversion pair is now complete.

---

## 12. Still Deferred

The following work remains intentionally deferred.

### 12.1 Env attachment

No attachment has been implemented yet:

```text
env.explicit_pipeline_forward_weekly_capacity = ...
env.explicit_pipeline_backward_weekly_capability = ...
```

### 12.2 Consumer-facing backward shape conversion

The product-first backward adapter is not yet wired into the existing consumer-facing backward shape.

A future adapter may be needed if the consumer expects:

```text
node_product_week_map_v1
```

or another shape.

### 12.3 Generic weekly capability

```text
WeeklyCapacityRow -> env.weekly_capability
```

is not implemented.

### 12.4 Capacity applicability status

No new status taxonomy is implemented yet.

Future status candidates include:

```text
absent_unlimited_fallback
present_aligned_applied
present_misaligned_product
present_misaligned_node
present_misaligned_week_domain
present_misaligned_shape
applied_and_blocking
```

### 12.5 Scenario package integration

Scenario yaml loading is not implemented in this phase.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

---

## 13. Recommended Next Step

The recommended next step is to design env attachment explicitly.

Suggested design document:

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
```

Purpose:

```text
Define how canonical WeeklyCapacityRow-derived forward/backward contexts should be attached to env
without changing planner behavior.
```

The design should address:

```text
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
existing backward consumer shape
diagnostic metadata
capacity scenario alignment diagnostic
no planner behavior change
```

Possible later Codex request:

```text
docs/codex_requests/wom_capacity_weekly_rows_runtime_env_attach_request.md
```

The first env-attach implementation should be narrow:

```text
build forward/backward contexts from WeeklyCapacityRow
attach to env in a helper
return attachment summary
do not alter planner semantics
```

---

## 14. Development Meaning

Before this phase, WOM had:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

After this phase, WOM has:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
    ↓
explicit backward capability context
```

This completes the pure conversion pair.

The next architectural work is not another pure converter.

The next architectural work is controlled runtime attachment.

In short:

```text
The forward and backward rails are now laid.
The next task is the switchyard: env attachment and diagnostics.
```

---

## 15. Summary

Completed:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

Confirmed:

```text
existing WeeklyCapacityRow reused
week keys preserved
duplicates summed
empty input returns {}
forward/backward pure adapter symmetry confirmed
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
env unchanged
```

Next:

```text
WeeklyCapacityRow-derived forward/backward contexts -> env attach
```

Recommended next design:

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
```
