# Codex Request: WOM Capacity Weekly Rows to Explicit Forward Context

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_weekly_rows_to_explicit_forward_context_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first runtime-context adapter phase for WOM canonical capacity rows.

This request is intentionally narrow.

Implement:

```text
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

Target runtime shape:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

Do not attach anything to `env` yet.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change sample CSV files.

Do not implement backward capability context yet.

Do not implement `env.weekly_capability` yet.

---

## 2. Why This Request Exists

The previous implementation completed:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

The next safe step is to derive one runtime context from `WeeklyCapacityRow`:

```text
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

This provides a stable bridge toward:

```text
env.explicit_pipeline_forward_weekly_capacity
```

without yet attaching to `env` or changing any planner behavior.

---

## 3. Source Documents to Read First

Please read these documents first:

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
```

Also inspect existing implementation files:

```text
pysi/adapters/capacity_input_granularity.py
pysi/capacity/capacity_master_loader.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_forward_capacity_context.py
tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Reuse existing modules where appropriate.

Avoid creating duplicate capacity context builders if an existing suitable module already exists.

---

## 4. Implementation Scope

### Required

Implement a function equivalent to:

```python
weekly_capacity_rows_to_explicit_forward_capacity(rows: list[WeeklyCapacityRow]) -> dict
```

The function should convert canonical capacity rows into the explicit forward capacity context shape:

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
env.explicit_pipeline_forward_weekly_capacity mutation
WeeklyCapacityRow -> explicit backward capability context
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
This module already relates to Explicit Pipeline capacity context construction.
```

If the inventory or existing implementation indicates a better location, use it and explain in the summary.

Avoid adding a new module if an existing module can safely host the function.

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

Do not create a second row class.

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

Output:

```python
dict[str, dict[str, dict[str, dict[object, int | float]]]]
```

Conceptually:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

The week key should be preserved exactly as carried by `WeeklyCapacityRow`.

Examples:

```text
2027-W40
0
1
```

Do not normalize or reinterpret week keys in this request.

---

## 9. Duplicate Row Policy

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

Reason:

```text
runtime dict shape cannot represent duplicate scalar values cleanly
```

---

## 10. Filtering Policy

Do not filter by scenario, product, tree_side, or cap_mode in this first request.

The adapter should convert all rows provided.

If later filtering is needed, it should be added explicitly in a later request.

---

## 11. Tree Side Policy

Do not filter by `tree_side`.

This request creates an explicit forward context from the provided rows.

The caller is responsible for passing appropriate rows.

A later request may add filtering or metadata.

---

## 12. Cap Mode Policy

The output context is quantity-only in this first request.

It does not carry `cap_mode`.

Do not change planner contracts to support rich capacity objects.

Future metadata sidecar may preserve cap_mode.

For now:

```text
WeeklyCapacityRow.cap_mode is ignored by this conversion.
```

This should be documented in the function docstring or tests.

---

## 13. Week Domain Policy

Do not normalize week keys.

Do not convert business week labels to integer indexes.

Do not convert integer indexes to business week labels.

Preserve the row's `week` value.

Tests should cover both:

```text
2027-W40
0
```

---

## 14. Numeric Policy

`capacity_qty` should already be numeric from the canonical loader.

If a row carries `capacity_qty` as an integer-like float, preserve Python numeric semantics.

Recommended behavior:

```text
5 -> 5
5.5 -> 5.5
```

Do not round.

Do not cast all values to int.

---

## 15. Required Tests

Add focused tests.

Preferred test file:

```text
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

### 15.1 Happy path

Create two `WeeklyCapacityRow` objects:

```text
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W40 / 5
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W41 / 6
```

Assert output:

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

### 15.2 Product separation

Rows for two products should produce separate top-level keys.

### 15.3 Node separation

Rows for two nodes should produce separate node keys.

### 15.4 Capacity type separation

Rows for `P` and `S` should produce separate capacity type keys.

### 15.5 Duplicate aggregation

Duplicate product/node/type/week rows should sum capacity quantities.

### 15.6 Week preservation

Rows with weeks:

```text
2027-W40
0
```

should preserve those keys exactly.

### 15.7 Empty input

Empty list should return:

```python
{}
```

---

## 16. Suggested Test Helper

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

Adjust fields if the existing `WeeklyCapacityRow` constructor requires additional or different parameters.

---

## 17. Test Commands

Run the focused test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

Run related tests:

```bat
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

## 18. Safety Boundaries

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
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

If another existing module is a better fit, explain in summary.

Do not add sample CSVs.

Use in-test `WeeklyCapacityRow` objects.

---

## 19. Acceptance Criteria

This request is complete when:

```text
weekly_capacity_rows_to_explicit_forward_capacity exists
the function returns product -> node -> capacity_type -> week -> capacity_qty
empty input returns {}
products are separated
nodes are separated
capacity types are separated
duplicate keys are summed
week keys are preserved
focused tests pass
related capacity tests pass
no planner behavior changes are made
no GUI changes are made
no data CSV files are changed
```

---

## 20. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is weekly_capacity_rows_to_explicit_forward_capacity implemented?
Did you reuse WeeklyCapacityRow?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSVs?
Are week keys preserved?
How are duplicates handled?
Which tests passed?
```

---

## 21. Development Meaning

This request builds the first runtime track from the canonical capacity station.

Previous completed station:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
```

This request adds:

```text
WeeklyCapacityRow
    ↓
explicit forward capacity context
```

Do not attach it to env yet.

Do not run trains through the planner yet.

Just lay the first track correctly.
