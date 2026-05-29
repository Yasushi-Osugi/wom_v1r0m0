# WOM Capacity Weekly Rows Runtime Env Attach

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_weekly_rows_runtime_env_attach.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

---

## 1. Purpose

This memo defines how canonical WOM capacity rows should be attached to runtime `env` capacity contexts.

The completed pure conversion path is now:

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

This memo designs the next controlled step:

```text
WeeklyCapacityRow-derived forward/backward contexts
    ↓
env attachment helper
    ↓
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
    ↓
diagnostic metadata
```

This memo is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Attach runtime capacity contexts explicitly and diagnostically.
```

The env attachment layer should not be hidden inside the planner.

It should be:

```text
pure enough to test
side-effect limited
diagnostic-visible
planner-neutral
GUI-neutral
safe to call during preflight
```

The helper may mutate `env` by attaching attributes, but it must not run or alter planning logic.

---

## 3. Current Completed State

### 3.1 Canonical loader completed

Implemented:

```text
capacity_master.csv -> WeeklyCapacityRow
```

Commit:

```text
31d6d8e Add canonical capacity master loader
```

### 3.2 Forward pure adapter completed

Implemented:

```text
WeeklyCapacityRow -> explicit forward capacity context
```

Commit:

```text
3a933fd Add weekly capacity row forward context adapter
```

### 3.3 Backward pure adapter completed

Implemented:

```text
WeeklyCapacityRow -> explicit backward capability context
```

Commit:

```text
1ee4008 Add weekly capacity backward context adapter
```

### 3.4 What remains

Not yet implemented:

```text
WeeklyCapacityRow-derived contexts -> env attach
diagnostic metadata integration
runtime attachment summary
planner preflight integration
scenario package integration
```

---

## 4. Problem to Solve

WOM now has the ability to build forward and backward capacity/capability contexts from canonical `WeeklyCapacityRow`.

However, these contexts are not yet attached to the runtime environment.

The problem to solve is:

```text
How should WOM safely attach WeeklyCapacityRow-derived capacity contexts to env
without changing planner behavior or hiding mismatch?
```

The attachment layer must answer:

```text
Which rows were attached?
Which runtime attributes were populated?
What shape was attached?
Was the backward shape consumer-compatible?
Were products/nodes/weeks visible for diagnostics?
Did the operation fail safely?
```

---

## 5. Non-Goals

This memo does not propose:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI layout changes
data CSV changes
sample CSV changes
scenario package loading
week-domain normalization
calendar conversion
optimization logic
new allocation logic
replacement of existing backward planner consumer shape
```

The design is limited to `env` attachment and metadata.

---

## 6. Env Attributes to Attach

Recommended near-term env attributes:

```text
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

Optional future env attributes:

```text
env.capacity_runtime_context_metadata
env.capacity_applicability_status
env.capacity_week_domain_metadata
env.capacity_shape_metadata
```

Near-term implementation should avoid over-adding attributes.

The first implementation should attach only what is needed and return a summary.

---

## 7. Recommended Helper Function

Recommended function:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(
    env,
    rows: list[WeeklyCapacityRow],
    *,
    attach_forward: bool = True,
    attach_backward: bool = True,
    attach_rows: bool = True,
    attach_summary: bool = True,
) -> dict
```

Possible location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

or a new small module if necessary:

```text
pysi/plan/explicit_pipeline_capacity_env_attach.py
```

Preferred near-term location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
forward/backward pure adapters already live there.
A small env attachment helper can remain close to the context builders.
```

---

## 8. Helper Responsibilities

The helper should:

```text
accept env and list[WeeklyCapacityRow]
build explicit forward capacity context if requested
build explicit backward capability context if requested
attach requested contexts to env
optionally attach source rows to env.capacity_weekly_rows
build attachment summary
optionally attach summary to env.capacity_runtime_attachment_summary
return attachment summary
```

The helper should not:

```text
call planner
change planning result
run capacity enforcement
mutate existing PSI lists
modify GUI state
read or write CSV files
normalize week keys
perform scenario package loading
```

---

## 9. Forward Context Attachment

If `attach_forward=True`, the helper should do:

```python
env.explicit_pipeline_forward_weekly_capacity = (
    weekly_capacity_rows_to_explicit_forward_capacity(rows)
)
```

The attached shape is:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

This is the shape currently produced by the pure forward adapter.

---

## 10. Backward Context Attachment

If `attach_backward=True`, the helper should be careful.

The pure backward adapter produces:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

However, existing backward consumer-facing shape detection may currently identify:

```text
node_product_week_map_v1
```

Therefore, near-term env attachment has two possible strategies.

### Strategy A: Attach product-first pure backward context directly

```python
env.explicit_pipeline_backward_weekly_capability = (
    weekly_capacity_rows_to_explicit_backward_capability(rows)
)
```

Pros:

```text
symmetrical with forward adapter
simple
testable
canonical-row-derived
```

Cons:

```text
may not match existing backward consumer-facing shape
must not be wired into planner consumption without separate compatibility check
```

### Strategy B: Attach under a separate canonical attribute

```python
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows = (
    weekly_capacity_rows_to_explicit_backward_capability(rows)
)
```

Pros:

```text
avoids replacing existing consumer-facing env attribute
safer if current planner expects a different shape
```

Cons:

```text
adds another env attribute
requires later bridge to consumer-facing shape
```

### Recommendation

Recommended first implementation:

```text
Use Strategy B unless tests confirm the product-first shape is consumer-compatible.
```

If the implementation can prove the current consumer-facing attribute is safe to replace, Strategy A may be used.

Otherwise, attach to a separate canonical attribute and report that the consumer-facing backward context is not yet replaced.

---

## 11. Attachment Summary

The helper should return a summary dictionary.

Recommended keys:

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
messages
```

Example:

```python
{
    "available": True,
    "input_row_count": 52,
    "attached_rows": True,
    "attached_forward": True,
    "attached_backward": True,
    "forward_shape": "product_node_type_week_qty_v1",
    "backward_shape": "product_node_type_week_qty_v1",
    "forward_product_count": 1,
    "backward_product_count": 1,
    "node_count": 3,
    "capacity_type_count": 1,
    "week_key_count": 52,
    "week_key_domain": "preserve",
    "messages": [],
}
```

If backward context is attached only to a canonical side attribute, summary should say so:

```text
backward_consumer_attribute_replaced = False
backward_canonical_attribute_attached = True
```

---

## 12. Shape Names

Use explicit shape names.

Recommended shape names:

```text
product_node_type_week_qty_v1
node_product_week_map_v1
unknown
unavailable
```

Forward pure adapter shape:

```text
product_node_type_week_qty_v1
```

Backward pure adapter shape:

```text
product_node_type_week_qty_v1
```

Existing backward consumer-facing shape may be:

```text
node_product_week_map_v1
```

Do not blur these names.

---

## 13. Week Domain Policy

The attachment helper should not normalize week keys.

It should preserve the rows' week keys as carried by the pure adapters.

Recommended summary:

```text
week_key_domain = preserve
```

or, if a classifier is available:

```text
week_key_domain = business_week_label / integer_index / mixed / unknown
```

No calendar conversion should occur in the first implementation.

---

## 14. Row Retention Policy

The helper may attach source rows:

```python
env.capacity_weekly_rows = list(rows)
```

This is useful for diagnostics and future traceability.

However, if attaching full row objects to env is considered too heavy, the helper may skip it and only attach summary.

Recommended first implementation:

```text
attach_rows=True by default
```

Reason:

```text
WeeklyCapacityRow is the canonical source of truth.
Keeping it on env helps diagnostics.
```

---

## 15. Diagnostic Integration

The helper should not necessarily run full diagnostics in the first implementation.

But it should prepare metadata that diagnostics can use.

Potential future diagnostic call:

```python
attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(...)
```

The attachment summary should support future diagnostic messages such as:

```text
capacity rows attached
forward context attached
backward canonical context attached
backward consumer context not replaced
week keys preserved
no planner behavior changed
```

---

## 16. Error Handling

The helper should fail safely.

### 16.1 Empty rows

If rows is empty:

```text
attach empty contexts
return available=False or available=True with input_row_count=0
```

Recommended:

```text
available = False
messages = ["No WeeklyCapacityRow rows provided."]
```

Do not raise for empty rows.

### 16.2 Invalid row objects

If row objects are missing required attributes, raise `TypeError` or return unavailable summary.

Recommended for pure helper:

```text
raise TypeError
```

Recommended for GUI/preflight wrapper:

```text
catch error and attach unavailable diagnostic
```

### 16.3 Attachment failure

If context construction fails:

```text
do not partially attach inconsistent contexts
return available=False
messages include error
```

Implementation may choose to build contexts first, then attach only after both succeed.

---

## 17. Transaction-Like Attachment Policy

To avoid half-attached env state, use this flow:

```text
1. Build forward context into local variable.
2. Build backward context into local variable.
3. Build summary into local variable.
4. Attach all requested attributes to env.
5. Return summary.
```

Avoid:

```text
attach forward first
then fail while building backward
```

unless failure behavior is explicitly documented.

---

## 18. Suggested Tests

Create focused tests:

```text
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

### 18.1 Attaches forward context

Given rows, helper attaches:

```text
env.explicit_pipeline_forward_weekly_capacity
```

with expected product/node/type/week/qty shape.

### 18.2 Attaches backward context safely

Depending on chosen strategy, assert one of:

```text
env.explicit_pipeline_backward_weekly_capability
```

or:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

is attached.

### 18.3 Attaches source rows

If `attach_rows=True`, assert:

```text
env.capacity_weekly_rows == rows
```

or same list content.

### 18.4 Attaches summary

Assert:

```text
env.capacity_runtime_attachment_summary
```

exists and contains:

```text
input_row_count
attached_forward
attached_backward
forward_shape
backward_shape
```

### 18.5 Empty rows

Empty list should not crash.

Summary should report no rows.

### 18.6 No planner behavior

Test should avoid importing or calling planner execution functions.

### 18.7 No GUI behavior

Test should avoid GUI modules.

---

## 19. Suggested Implementation Files

Likely changed/new files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

Optional if separated:

```text
pysi/plan/explicit_pipeline_capacity_env_attach.py
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

## 20. Recommended Implementation Phase

### Phase E1: Pure env attachment helper

Implement:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

with focused tests.

No preflight wiring.

No GUI changes.

No planner changes.

### Phase E2: Diagnostic metadata integration

Extend existing diagnostic helper to read attachment summary.

No planner changes.

### Phase E3: Preflight wiring

Attach capacity runtime contexts during explicit KPI preflight, after loader/adapters are available and only if source rows are present.

### Phase E4: Scenario package integration

Load capacity rows from scenario package and call the attachment helper.

---

## 21. Acceptance Criteria for Future Implementation

The first env attachment implementation is complete when:

```text
attach_capacity_runtime_contexts_to_env_from_weekly_rows exists
it builds forward context from WeeklyCapacityRow
it builds backward context from WeeklyCapacityRow
it attaches contexts to env or safe canonical env attributes
it attaches or returns summary
it preserves week keys
it does not call planner
it does not change GUI
it does not change data CSV files
focused tests pass
related adapter tests pass
```

---

## 22. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_weekly_rows_runtime_env_attach_request.md
```

Scope:

```text
attach_capacity_runtime_contexts_to_env_from_weekly_rows
focused tests
no planner changes
no GUI changes
no data CSV changes
no preflight wiring yet
```

The first implementation should not wire into the GUI or explicit KPI preflight.

It should only provide a pure-ish env attachment helper.

---

## 23. Summary

The current completed architecture is:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
    ↓
explicit backward capability context
```

This memo designs the next step:

```text
WeeklyCapacityRow-derived contexts
    ↓
runtime env attachment helper
```

The helper should attach contexts safely, return a summary, preserve diagnostics, and avoid planner behavior changes.

In short:

```text
The rails are laid.
This memo designs the switchyard.
```
