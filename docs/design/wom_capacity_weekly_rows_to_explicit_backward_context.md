# WOM Capacity Weekly Rows to Explicit Backward Context

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_weekly_rows_to_explicit_backward_context.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

---

## 1. Purpose

This memo defines the design direction for converting canonical WOM capacity rows into the Explicit Pipeline backward capability context.

The completed forward path is:

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

This memo designs the backward-side pair:

```text
WeeklyCapacityRow
    ↓
explicit backward capability context
```

The goal is to complete the forward/backward conversion pair before attaching either context to `env`.

This memo is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Forward and backward runtime capacity contexts should be derived from the same canonical capacity rows.
```

This means:

```text
capacity_master.csv is not forward-only
WeeklyCapacityRow is not forward-only
explicit forward capacity and explicit backward capability are derived views
```

The adapter should be:

```text
pure
deterministic
side-effect free
planner-neutral
GUI-neutral
diagnostic-friendly
```

---

## 3. Current Completed State

The following path is already implemented:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

Implementation commit:

```text
31d6d8e Add canonical capacity master loader
```

The following forward runtime path is already implemented:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

Implementation commit:

```text
3a933fd Add weekly capacity row forward context adapter
```

Forward completion memo:

```text
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
```

---

## 4. Problem to Solve

The Explicit Pipeline currently has both forward capacity and backward capability concepts.

Forward capacity has now received a pure adapter from `WeeklyCapacityRow`.

Backward capability should receive a corresponding adapter so that the capacity runtime architecture does not become one-sided.

The problem to solve is:

```text
How should WeeklyCapacityRow be converted into the runtime shape expected by
env.explicit_pipeline_backward_weekly_capability or its pure context builder,
without attaching to env and without changing planner behavior?
```

---

## 5. Non-Goals

This memo does not propose:

```text
env attachment
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI changes
data CSV changes
scenario package loader integration
env.weekly_capability implementation
capacity applicability status implementation
week-domain normalization
calendar conversion
optimization logic
```

The design is limited to a pure adapter for backward capability context construction.

---

## 6. Terminology

### 6.1 Forward capacity

Forward capacity refers to a runtime capacity context used by forward / push / explicit pipeline logic.

Current forward adapter shape:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

### 6.2 Backward capability

Backward capability refers to a runtime capability context used by backward / pull / inbound / capability-aware planning logic.

It may use the same shape as forward capacity, or it may use an existing different shape in the repository.

The implementation request must inspect current consumer expectations before coding.

### 6.3 Capacity vs capability

In this memo:

```text
capacity:
    quantity limit in a specific runtime context

capability:
    available ability of a node/resource to fulfill backward planning requirements
```

They may share the same canonical row source.

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

The adapter should primarily use:

```text
product_id
capacity_owner_id
capacity_type
week
capacity_qty
```

Other fields may be preserved for future metadata, but should not be required for the first pure adapter.

---

## 8. Target Runtime Shape Policy

The near-term recommended shape is the same product-first nested structure used by the forward adapter:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
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

However, before implementation, Codex should inspect the current repository to confirm the expected backward capability consumer shape.

If the existing backward context consumer expects a different shape, the implementation should either:

```text
1. produce the existing consumer-compatible shape, or
2. add a clearly named pure adapter for the recommended product-first shape,
   while not wiring it into runtime consumers yet.
```

The first implementation must not silently break existing backward capability consumers.

---

## 9. Recommended Function

Recommended function name:

```python
weekly_capacity_rows_to_explicit_backward_capability(
    rows: list[WeeklyCapacityRow],
) -> dict
```

Preferred location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
The forward adapter already lives in the explicit capacity context module.
The backward adapter is its symmetrical pair.
```

If the repository already has a more appropriate backward capability module, Codex may use it and explain in the summary.

---

## 10. Output Contract

Recommended output for the pure adapter:

```text
product_id -> node_id -> capacity_type -> week -> capacity_qty
```

Python type conceptually:

```python
dict[str, dict[str, dict[str, dict[object, int | float]]]]
```

Week keys should be preserved exactly.

Examples:

```text
2027-W40
0
1
```

No calendar conversion should occur.

---

## 11. Duplicate Row Policy

Duplicate key candidate:

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

This matches the forward adapter behavior and keeps the forward/backward pair consistent.

---

## 12. Filtering Policy

The first backward adapter should not filter by default.

Do not filter by:

```text
scenario_id
product_id
tree_side
cap_mode
capacity_type
```

The caller is responsible for passing the desired rows.

Rationale:

```text
Filtering can hide mismatch.
Diagnostics need to see product/node/week mismatches explicitly.
```

Later versions may add optional filtering with metadata.

---

## 13. Tree Side Policy

Backward capability is usually related to inbound / supply-side capability.

However, this adapter should not silently filter rows by `tree_side`.

Recommended first implementation:

```text
convert all rows provided
```

Later implementation may add explicit optional filtering:

```python
tree_side_filter={"IN", "BOTH"}
```

but only with diagnostic metadata.

---

## 14. Cap Mode Policy

The backward context in this phase is quantity-only.

Therefore:

```text
cap_mode is ignored by the pure conversion
```

This is intentional.

Do not change existing planner contracts to consume rich capacity objects.

Future metadata may preserve:

```text
cap_mode
unit
priority
calendar_id
source_id
source_file
```

---

## 15. Week Domain Policy

Do not normalize week keys.

Do not convert:

```text
business week label -> integer index
integer index -> business week label
monthly label -> weekly label
```

Preserve the row's `week` value exactly.

Week-domain conversion remains a later adapter-boundary feature.

---

## 16. Relationship to Existing Diagnostics

The backward adapter should support future use by capacity scenario alignment diagnostics.

Current diagnostic concepts include:

```text
backward capability shape detection
product mismatch
node mismatch
week-domain mismatch
shape mismatch
```

The first pure adapter does not need to call diagnostics.

However, it should produce a deterministic context shape that future diagnostics can inspect.

---

## 17. Relationship to Env Attachment

This design does not attach to:

```text
env.explicit_pipeline_backward_weekly_capability
```

The first implementation should return only a context dictionary.

A later env attach phase may do:

```python
env.explicit_pipeline_backward_weekly_capability = (
    weekly_capacity_rows_to_explicit_backward_capability(rows)
)
```

That wiring should be a separate request.

---

## 18. Recommended Test Strategy

Create a focused test file:

```text
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Use in-test `WeeklyCapacityRow` objects.

Do not add data CSV files.

### 18.1 Empty input

```python
weekly_capacity_rows_to_explicit_backward_capability([]) == {}
```

### 18.2 Happy path

Rows:

```text
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W40 / 5
PACKAGED_RICE_STANDARD / MILL_EAST / P / 2027-W41 / 6
```

Expected:

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

### 18.3 Product separation

Rows for different products should produce different top-level keys.

### 18.4 Node separation

Rows for different capacity_owner_id values should produce different node keys.

### 18.5 Capacity type separation

Rows for `P` and `S` should produce separate capacity type keys.

### 18.6 Duplicate aggregation

Duplicate keys should be summed.

### 18.7 Week preservation

Weeks such as:

```text
2027-W40
0
```

should remain unchanged.

---

## 19. Suggested Test Helper

Use a helper similar to the forward context test:

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

## 20. Suggested Implementation Files

Likely files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Do not touch:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
data/*.csv
```

---

## 21. Test Commands for Future Codex Request

Focused test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Optional capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

---

## 22. Safety Boundaries for Future Implementation

The future implementation request should explicitly state:

```text
no env attach
no planner behavior change
no capacity enforcement change
no GUI change
no data CSV change
no week normalization
no calendar conversion
```

Only implement:

```text
WeeklyCapacityRow -> explicit backward capability context
focused tests
```

---

## 23. Acceptance Criteria for Future Implementation

The future implementation is complete when:

```text
weekly_capacity_rows_to_explicit_backward_capability exists
the function reuses WeeklyCapacityRow
empty input returns {}
output shape is deterministic
products are separated
nodes are separated
capacity types are separated
duplicate keys are summed
week keys are preserved
focused tests pass
related tests pass
planner behavior is unchanged
GUI is unchanged
data CSV files are unchanged
```

---

## 24. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_weekly_rows_to_explicit_backward_context_request.md
```

Scope:

```text
WeeklyCapacityRow -> explicit backward capability context
focused tests
no env attach
no planner changes
```

---

## 25. Summary

The forward runtime track is now complete:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
```

This memo designs the matching backward track:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
```

The backward adapter should remain pure and side-effect free.

It should preserve week keys, sum duplicates, and avoid env attachment.

In short:

```text
Build the backward rail next, but do not connect the trains yet.
```
