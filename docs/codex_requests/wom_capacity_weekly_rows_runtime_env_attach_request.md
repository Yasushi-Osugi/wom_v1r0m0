# Codex Request: WOM Capacity Weekly Rows Runtime Env Attach

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_weekly_rows_runtime_env_attach_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first runtime env attachment helper for WOM canonical capacity rows.

This request is intentionally narrow.

Implement a helper that attaches `WeeklyCapacityRow`-derived capacity contexts to an `env` object.

Recommended function:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

The helper should build and attach:

```text
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability or a safe canonical backward attribute
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

Do not wire this helper into GUI preflight yet.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change data CSV files.

Do not implement scenario package loading.

---

## 2. Why This Request Exists

The following canonical capacity path is now implemented:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

The following pure runtime context adapters are also implemented:

```text
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_forward_capacity(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty

WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_explicit_backward_capability(...)
    ↓
product -> node -> capacity_type -> week -> capacity_qty
```

The next safe step is not planner integration.

The next safe step is a small env attachment helper that is easy to test.

---

## 3. Source Documents to Read First

Please read these documents first:

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
```

Also inspect existing implementation and tests:

```text
pysi/adapters/capacity_input_granularity.py
pysi/capacity/capacity_master_loader.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Reuse existing modules and patterns.

---

## 4. Implementation Scope

### Required

Implement a helper equivalent to:

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

The helper should:

```text
build explicit forward capacity context from WeeklyCapacityRow
build explicit backward capability context from WeeklyCapacityRow
attach requested context attributes to env
optionally attach source rows to env.capacity_weekly_rows
build and return an attachment summary
optionally attach summary to env.capacity_runtime_attachment_summary
```

### Expected attachment attributes

Forward:

```text
env.explicit_pipeline_forward_weekly_capacity
```

Backward:

Prefer safe behavior.

If product-first backward context is confirmed safe for the current env attribute, attach to:

```text
env.explicit_pipeline_backward_weekly_capability
```

If not confirmed safe, attach to a canonical side attribute:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

and report in summary that consumer-facing backward context was not replaced.

---

## 5. Explicit Non-Scope

Do not implement:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI changes
data CSV changes
sample CSV changes
scenario package loading
week-key normalization
calendar conversion
capacity applicability status
explicit KPI preflight wiring
management cockpit message changes
```

This request should only implement a helper and focused tests.

---

## 6. Preferred Implementation Location

Preferred location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
weekly_capacity_rows_to_explicit_forward_capacity
weekly_capacity_rows_to_explicit_backward_capability
```

already live there.

If Codex finds a clearly better existing module, use it and explain in the summary.

Avoid creating a new module unless needed.

---

## 7. Input Contract

Input rows:

```python
list[WeeklyCapacityRow]
```

Use the existing class:

```text
pysi.adapters.capacity_input_granularity.WeeklyCapacityRow
```

Do not create another row class.

Input env:

```text
any Python object that supports attribute assignment
```

Tests may use:

```python
from types import SimpleNamespace

env = SimpleNamespace()
```

---

## 8. Output Summary Contract

The helper should return a dictionary.

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
backward_consumer_attribute_replaced
backward_canonical_attribute_attached
messages
```

Example:

```python
{
    "available": True,
    "input_row_count": 2,
    "attached_rows": True,
    "attached_forward": True,
    "attached_backward": True,
    "forward_shape": "product_node_type_week_qty_v1",
    "backward_shape": "product_node_type_week_qty_v1",
    "forward_product_count": 1,
    "backward_product_count": 1,
    "node_count": 1,
    "capacity_type_count": 1,
    "week_key_count": 2,
    "week_key_domain": "preserve",
    "backward_consumer_attribute_replaced": False,
    "backward_canonical_attribute_attached": True,
    "messages": [],
}
```

Do not over-engineer the summary, but it should be useful for diagnostics.

---

## 9. Shape Names

Use explicit shape names.

Recommended shape name for both pure forward and pure backward contexts:

```text
product_node_type_week_qty_v1
```

If the helper attaches to a separate canonical backward attribute because the existing consumer-facing shape is different, the summary should state:

```text
backward_shape = product_node_type_week_qty_v1
backward_consumer_attribute_replaced = False
backward_canonical_attribute_attached = True
```

---

## 10. Backward Attachment Safety

The design memo notes that existing backward capability shape detection may identify:

```text
node_product_week_map_v1
```

while the pure backward adapter produces:

```text
product_node_type_week_qty_v1
```

Therefore, the first implementation must avoid accidentally breaking existing consumer-facing backward context.

Recommended implementation:

```text
Attach forward context to:
  env.explicit_pipeline_forward_weekly_capacity

Attach backward product-first context to:
  env.explicit_pipeline_backward_weekly_capability_from_weekly_rows

Do not replace:
  env.explicit_pipeline_backward_weekly_capability

unless existing tests or code inspection confirm it is safe.
```

In the final summary, explicitly state which strategy was used.

---

## 11. Row Attachment Policy

If `attach_rows=True`, attach:

```python
env.capacity_weekly_rows = list(rows)
```

This supports diagnostics and traceability.

If `attach_rows=False`, do not attach source rows.

The returned summary should still report `input_row_count`.

---

## 12. Summary Attachment Policy

If `attach_summary=True`, attach:

```python
env.capacity_runtime_attachment_summary = summary
```

If `attach_summary=False`, only return the summary.

---

## 13. Empty Rows Behavior

If `rows` is empty:

Recommended behavior:

```text
do not crash
attach empty contexts if requested, or attach no contexts with clear summary
return available=False
input_row_count=0
messages includes "No WeeklyCapacityRow rows provided."
```

Preferred implementation:

```text
attach empty {} contexts when attach_forward / attach_backward are True
```

This keeps env attributes deterministic.

Summary example:

```python
{
    "available": False,
    "input_row_count": 0,
    "attached_forward": True,
    "attached_backward": True,
    "messages": ["No WeeklyCapacityRow rows provided."],
}
```

---

## 14. Transaction-Like Attachment Policy

Avoid half-attached env state.

Recommended sequence:

```text
1. Build forward context into local variable.
2. Build backward context into local variable.
3. Build summary into local variable.
4. Attach attributes to env.
5. Return summary.
```

Do not attach forward first and then fail while building backward.

---

## 15. Week Key Policy

Do not normalize week keys.

Do not convert:

```text
business week label -> integer index
integer index -> business week label
```

The helper should preserve whatever the pure adapters produce.

Summary should report:

```text
week_key_domain = preserve
```

or, if a safe classifier already exists, one of:

```text
business_week_label
integer_index
mixed
unknown
```

Do not add calendar conversion in this request.

---

## 16. Required Tests

Add focused tests.

Preferred test file:

```text
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

Use in-test `WeeklyCapacityRow` objects and `types.SimpleNamespace`.

### 16.1 Attaches forward context

Assert:

```text
env.explicit_pipeline_forward_weekly_capacity
```

exists and has:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

### 16.2 Attaches backward canonical context safely

Assert the chosen backward attribute exists.

Preferred safe attribute:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

If implementation replaces the consumer-facing attribute, tests must clearly assert that shape and summary.

### 16.3 Attaches source rows

With `attach_rows=True`, assert:

```text
env.capacity_weekly_rows
```

contains the same row objects or equivalent list.

### 16.4 Attaches summary

With `attach_summary=True`, assert:

```text
env.capacity_runtime_attachment_summary
```

exists and matches the returned summary.

### 16.5 Summary contents

Assert summary contains:

```text
available
input_row_count
attached_forward
attached_backward
forward_shape
backward_shape
week_key_domain
messages
```

### 16.6 Empty rows

Assert empty rows do not crash.

Assert summary reports no rows.

### 16.7 Switch flags

Test:

```python
attach_forward=False
```

does not attach forward context.

Test:

```python
attach_backward=False
```

does not attach backward context.

Test:

```python
attach_rows=False
```

does not attach `capacity_weekly_rows`.

Test:

```python
attach_summary=False
```

does not attach `capacity_runtime_attachment_summary`, but still returns summary.

### 16.8 No planner / GUI imports

Tests should not import planner execution modules or GUI modules.

---

## 17. Suggested Test Helper

Use helper:

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

Adjust if the existing constructor requires additional fields.

---

## 18. Test Commands

Run focused test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

Run related adapter tests:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Run related diagnostics/capacity tests:

```bat
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Optional capacity regression:

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
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
```

Do not add sample CSV files.

Do not wire into preflight.

---

## 20. Acceptance Criteria

This request is complete when:

```text
attach_capacity_runtime_contexts_to_env_from_weekly_rows exists
it reuses WeeklyCapacityRow-derived pure adapters
it attaches forward context when requested
it attaches backward canonical context safely
it attaches source rows when requested
it attaches summary when requested
empty rows do not crash
switch flags work
week keys remain preserved
focused tests pass
related adapter tests pass
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
no preflight wiring is added
```

---

## 21. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is attach_capacity_runtime_contexts_to_env_from_weekly_rows implemented?
Which env attributes are attached?
Was the backward product-first context attached to the consumer-facing attribute or a safe canonical side attribute?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSVs?
Did you wire this into preflight?
Are week keys preserved?
Which tests passed?
```

---

## 22. Development Meaning

This request installs the first switchyard for canonical WOM capacity runtime contexts.

Already completed:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward capacity context
    ↓
explicit backward capability context
```

This request adds:

```text
WeeklyCapacityRow-derived contexts
    ↓
env attachment helper
```

Do not run trains through the planner yet.

Do not connect the switchyard to GUI preflight yet.

Just install the switchyard safely.
