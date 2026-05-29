# Codex Request: WOM Capacity Weekly Rows to Explicit Backward Context

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_weekly_rows_to_explicit_backward_context_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the explicit backward capability runtime-context adapter for WOM canonical capacity rows.

This request is intentionally narrow.

Implement:

```text
WeeklyCapacityRow
    ↓
explicit backward capability context
```

Recommended function:

```python
weekly_capacity_rows_to_explicit_backward_capability(rows: list[WeeklyCapacityRow]) -> dict
```

Recommended target shape:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

Do not attach anything to `env` yet.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change sample CSV files.

Do not implement `env.weekly_capability`.

Do not implement scenario package loading.

---

## 2. Why This Request Exists

The forward runtime-context adapter has already been completed:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

Now we want to build the matching backward-side pure adapter:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

This completes the forward/backward pure conversion pair before either side is attached to `env`.

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
```

Also inspect these existing implementation and test files:

```text
pysi/adapters/capacity_input_granularity.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_forward_capacity_context.py
```

Reuse existing modules and patterns.

Do not create a second `WeeklyCapacityRow`.

---

## 4. Implementation Scope

### Required

Implement a function equivalent to:

```python
weekly_capacity_rows_to_explicit_backward_capability(
    rows: list[WeeklyCapacityRow],
) -> dict[str, dict[str, dict[str, dict[object, int | float]]]]
```

The function should convert canonical capacity rows into the explicit backward capability context shape:

```python
{
    product_id: {
        node_id: {
            capacity_type: {
                week: capacity_qty
            }
        }
    }
}
```

Example:

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

## 5. Explicit Non-Scope

Do not implement:

```text
env attachment
env.explicit_pipeline_backward_weekly_capability mutation
WeeklyCapacityRow -> explicit forward capacity context changes
WeeklyCapacityRow -> env.weekly_capability
scenario package loader integration
capacity applicability status
planner behavior changes
blocked lot behavior changes
week-key normalization
calendar conversion
GUI / KPI message changes
sample CSV changes
```

Those are later phases.

---

## 6. Preferred Implementation Location

Preferred location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
weekly_capacity_rows_to_explicit_forward_capacity already lives there.
The backward adapter should be its symmetrical pair.
```

If an existing module is clearly more appropriate, use it and explain why in the summary.

Avoid adding a new module for this small pure adapter.

---

## 7. Input Contract

Input:

```python
list[WeeklyCapacityRow]
```

Use the existing class:

```text
pysi.adapters.capacity_input_granularity.WeeklyCapacityRow
```

Do not create another row class.

Expected row fields include:

```text
scenario_id
product_id
capacity_owner_type
capacity_owner_id
tree_side
week
capacity_type
capacity_qty
cap_mode
unit
priority
calendar_id
source_granularity
source_id
source_file
comment
```

The adapter should primarily use:

```text
product_id
capacity_owner_id
capacity_type
week
capacity_qty
```

---

## 8. Output Contract

Output shape:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

Python type conceptually:

```python
dict[str, dict[str, dict[str, dict[object, int | float]]]]
```

The output should be deterministic.

Empty input should return:

```python
{}
```

---

## 9. Backward Shape Compatibility Check

Before implementation, inspect the current backward capability context consumer, if any, especially around:

```text
env.explicit_pipeline_backward_weekly_capability
backward capability shape detection
capacity scenario alignment diagnostic
capacity_aware_inbound_backward
explicit_bridge_capacity_pipeline
```

If the current consumer expects a different shape, do not wire this function to that consumer in this request.

This request may still implement a pure product-first adapter, as long as it is not attached to the consumer.

In the Codex summary, explicitly state whether the implemented adapter is:

```text
consumer-compatible now
```

or:

```text
pure product-first adapter only, not yet wired
```

---

## 10. Duplicate Row Policy

Duplicate key:

```text
product_id
capacity_owner_id
capacity_type
week
```

Recommended behavior:

```text
sum capacity_qty deterministically
```

Example:

```text
Row 1: RICE / MILL_EAST / P / 2027-W40 / 5
Row 2: RICE / MILL_EAST / P / 2027-W40 / 3
```

Expected output:

```python
{
    "RICE": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 8
            }
        }
    }
}
```

This should match the forward adapter behavior.

---

## 11. Filtering Policy

Do not filter rows by default.

Do not filter by:

```text
scenario_id
product_id
tree_side
cap_mode
capacity_type
```

The caller is responsible for passing appropriate rows.

Rationale:

```text
Filtering can hide mismatch.
Diagnostics should remain able to detect product/node/week-domain mismatches.
```

---

## 12. Tree Side Policy

Backward capability is usually associated with inbound / supply-side capability.

However, this adapter should not silently filter by `tree_side`.

For this request:

```text
convert all provided rows
```

Later requests may add explicit filtering with metadata.

---

## 13. Cap Mode Policy

The backward capability context is quantity-only in this first request.

Therefore:

```text
WeeklyCapacityRow.cap_mode is ignored by this conversion.
```

Do not change planner contracts to consume rich capacity objects.

A future metadata sidecar may preserve:

```text
cap_mode
unit
priority
calendar_id
source_id
source_file
```

---

## 14. Week Domain Policy

Do not normalize week keys.

Do not convert:

```text
business week label -> integer index
integer index -> business week label
monthly label -> weekly label
```

Preserve the row's `week` value exactly.

Tests should cover both:

```text
2027-W40
0
```

---

## 15. Numeric Policy

`capacity_qty` should already be numeric from the canonical loader.

Preserve numeric semantics:

```text
5 -> 5
5.5 -> 5.5
```

Do not round.

Do not cast all values to int.

---

## 16. Required Tests

Add focused tests.

Preferred test file:

```text
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

### 16.1 Empty input

Assert:

```python
weekly_capacity_rows_to_explicit_backward_capability([]) == {}
```

### 16.2 Happy path

Create two `WeeklyCapacityRow` objects:

```text
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W40 / 5
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W41 / 6
```

Expected output:

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

### 16.3 Product separation

Rows for two products should produce separate top-level keys.

### 16.4 Node separation

Rows for two nodes should produce separate node keys.

### 16.5 Capacity type separation

Rows for `P` and `S` should produce separate capacity type keys.

### 16.6 Duplicate aggregation

Duplicate product/node/type/week rows should sum capacity quantities.

### 16.7 Week preservation

Rows with weeks:

```text
2027-W40
0
```

should preserve those keys exactly.

### 16.8 Forward/backward symmetry

If the forward adapter is available, test or assert that for the same rows:

```text
weekly_capacity_rows_to_explicit_backward_capability(rows)
```

has the same nested quantity shape as:

```text
weekly_capacity_rows_to_explicit_forward_capacity(rows)
```

This confirms the pair is symmetrical at the pure adapter level.

---

## 17. Suggested Test Helper

Use a small helper in the test file:

```python
def row(
    product_id="PACKAGED_RICE_STANDARD",
    node_id="MILL_EAST",
    capacity_type="P",
    week="2027-W40",
    qty=5,
):
    return WeeklyCapacityRow(
        scenario_id="RICE_AS_IS",
        product_id=product_id,
        capacity_owner_type="node",
        capacity_owner_id=node_id,
        week=week,
        capacity_type=capacity_type,
        capacity_qty=qty,
        cap_mode="hard",
        unit="lot",
        source_granularity="weekly",
    )
```

Adjust if the current `WeeklyCapacityRow` constructor requires additional fields.

---

## 18. Test Commands

Run focused test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Run related tests:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Optionally run related capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

---

## 19. Safety Boundaries

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
data/*.csv
```

Expected changed/new files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Do not add sample CSVs.

Use in-test `WeeklyCapacityRow` objects.

---

## 20. Acceptance Criteria

This request is complete when:

```text
weekly_capacity_rows_to_explicit_backward_capability exists
the function reuses WeeklyCapacityRow
the function returns product -> node -> capacity_type -> week -> capacity_qty
empty input returns {}
products are separated
nodes are separated
capacity types are separated
duplicate keys are summed
week keys are preserved
forward/backward pure adapter symmetry is confirmed
focused tests pass
related tests pass
no planner behavior changes are made
no GUI changes are made
no data CSV files are changed
```

---

## 21. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is weekly_capacity_rows_to_explicit_backward_capability implemented?
Did you reuse WeeklyCapacityRow?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSVs?
Are week keys preserved?
How are duplicates handled?
Is the output shape symmetric with the forward adapter?
Is the adapter wired to env or planner?
Which tests passed?
```

---

## 22. Development Meaning

This request builds the backward runtime track from the canonical capacity station.

Already completed:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

This request adds:

```text
WeeklyCapacityRow
    ↓
explicit backward capability context
```

Do not attach it to env yet.

Do not run it through planner behavior yet.

Just lay the backward track correctly.
