# WOM Capacity Weekly Rows to Explicit Forward Context Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_weekly_rows_to_explicit_forward_context_request.md
```

---

## 1. Purpose

This completion memo records the completion of the first runtime-context adapter phase for WOM canonical capacity rows.

The completed scope is intentionally narrow:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

This phase does not attach anything to `env`.

It does not change planner behavior.

It does not change GUI behavior.

It does not change data CSV files.

It does not implement backward capability context.

It does not implement `env.weekly_capability`.

---

## 2. Key Commit

Implementation commit:

```text
3a933fd Add weekly capacity row forward context adapter
```

Related preceding commits:

```text
4bec580 Add WOM capacity weekly rows runtime context adapter design
f89a5b6 Add WOM capacity weekly rows to explicit forward context Codex request
dd51f72 Add WOM capacity master canonical loader adapter completion memo
31d6d8e Add canonical capacity master loader
0b2799a Add WOM capacity master canonical loader adapter Codex request
4b7ffc8 Add WOM capacity master canonical loader adapter design
69f6717 Add WOM capacity schema inventory
```

---

## 3. Implementation Summary

The implementation added:

```python
weekly_capacity_rows_to_explicit_forward_capacity(...)
```

in:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

The function converts canonical capacity rows into the explicit forward capacity context shape:

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
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

### 4.1 explicit_pipeline_capacity_context.py

Added the forward runtime context adapter:

```python
weekly_capacity_rows_to_explicit_forward_capacity(...)
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
does not use cap_mode in this phase
sums duplicate product/node/capacity_type/week rows deterministically
returns {} for empty input
```

### 4.2 test_wom_capacity_weekly_rows_to_explicit_forward_context.py

Added focused tests covering:

```text
happy path
product separation
node separation
capacity type separation
duplicate aggregation
week key preservation
empty input
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

The explicit forward context built in this phase is quantity-only.

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

## 8. Tests Executed

The focused test passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

Observed result:

```text
7 passed
```

Related capacity and explicit pipeline tests passed:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Observed results:

```text
tests/test_wom_capacity_master_canonical_loader_adapter.py        6 passed
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

## 9. Safety Boundaries Honored

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
backward capability context
env.weekly_capability
week-key normalization
calendar conversion
capacity applicability status
```

This phase only added:

```text
WeeklyCapacityRow -> explicit forward capacity context adapter
focused tests
```

---

## 10. Current Architecture After This Phase

The completed capacity path is now:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

This is the first runtime track from the canonical capacity row station.

---

## 11. Still Deferred

The following work remains deferred.

### 11.1 Env attachment

```text
env.explicit_pipeline_forward_weekly_capacity = ...
```

is not performed in this phase.

### 11.2 Backward capability context

```text
WeeklyCapacityRow -> env.explicit_pipeline_backward_weekly_capability
```

is not implemented.

### 11.3 Generic weekly capability

```text
WeeklyCapacityRow -> env.weekly_capability
```

is not implemented.

### 11.4 Capacity applicability status

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

### 11.5 Scenario package integration

Scenario yaml loading is not implemented in this phase.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

---

## 12. Recommended Next Step

There are two reasonable next paths.

### Option A: Complete the forward/backward pair

Create the next design/request for:

```text
WeeklyCapacityRow -> explicit backward capability context
```

This keeps the forward/backward pair symmetrical.

Possible files:

```text
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context.md
docs/codex_requests/wom_capacity_weekly_rows_to_explicit_backward_context_request.md
```

### Option B: Begin env attach

Create the next design/request for:

```text
WeeklyCapacityRow-derived explicit forward context
    ↓
env.explicit_pipeline_forward_weekly_capacity
```

Possible files:

```text
docs/design/wom_capacity_explicit_forward_context_env_attach.md
docs/codex_requests/wom_capacity_explicit_forward_context_env_attach_request.md
```

### Recommendation

Recommended next step:

```text
Option A: WeeklyCapacityRow -> explicit backward capability context
```

Reason:

```text
Complete the forward/backward conversion pair before attaching either to env.
```

This keeps runtime integration safer and avoids half-wired capacity contexts.

---

## 13. Development Meaning

Before this phase, WOM had:

```text
capacity_master.csv -> WeeklyCapacityRow
```

After this phase, WOM has:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

This is a small but important step.

It connects the canonical capacity row to one concrete runtime context shape without changing planner behavior.

In short:

```text
The first runtime track from the canonical capacity station is now laid.
The trains are not running yet.
```

---

## 14. Summary

Completed:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

Confirmed:

```text
existing WeeklyCapacityRow reused
week keys preserved
duplicates summed
empty input returns {}
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
```

Next:

```text
WeeklyCapacityRow -> explicit backward capability context
```

or:

```text
explicit forward context -> env attach
```

Recommended order:

```text
1. build explicit backward capability adapter
2. then design env attachment
```
