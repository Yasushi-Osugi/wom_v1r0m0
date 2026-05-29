# Codex Request: WOM Capacity Runtime Attachment Diagnostic Integration

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_runtime_attachment_diagnostic_integration_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement diagnostic integration for WOM capacity runtime attachment.

This request is intentionally narrow.

Implement diagnostic logic that reads:

```text
env.capacity_runtime_attachment_summary
```

and exposes its status in the existing capacity scenario alignment diagnostic payload.

The diagnostic should report:

```text
runtime attachment summary available / missing
forward context attached / missing
backward canonical side context attached / missing
backward consumer-facing context not replaced
week_key_domain = preserve
shape = product_node_type_week_qty_v1
summary/env attribute consistency
```

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change data CSV files.

Do not wire anything into preflight.

Do not normalize week keys.

---

## 2. Why This Request Exists

The following capacity path is now implemented:

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
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

The next step is not planner integration.

The next step is diagnostic visibility.

WOM should be able to explain whether capacity rows were attached to runtime env attributes, which shapes were used, and whether the summary is consistent with the actual env attributes.

---

## 3. Source Documents to Read First

Please read these documents first:

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
```

Also inspect these implementation and test files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Reuse existing diagnostic patterns.

Do not create a parallel diagnostic module unless clearly necessary.

---

## 4. Implementation Scope

### Required

Add diagnostic support for runtime attachment summary.

Recommended helper:

```python
build_capacity_runtime_attachment_diagnostic(env) -> dict
```

Preferred location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

The helper should read:

```text
env.capacity_runtime_attachment_summary
```

and return a structured diagnostic section.

### Required integration

Extend the existing capacity scenario alignment diagnostic so that its output includes:

```text
runtime_attachment
```

and appends runtime attachment messages to the diagnostic message list.

The integration should be read-only.

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
management cockpit layout changes
```

This request is diagnostic-only.

---

## 6. Diagnostic Meaning in Japanese / Conceptual Contract

The diagnostic should make the following concepts visible.

### 6.1 runtime attachment summary available / missing

Meaning:

```text
env.capacity_runtime_attachment_summary が存在するかどうか。
```

This tells whether WOM has a runtime attachment receipt.

If available, WOM can explain how capacity contexts were attached.

If missing, capacity contexts may still exist, but WOM cannot explain how they were attached.

### 6.2 forward context attached / missing

Meaning:

```text
env.explicit_pipeline_forward_weekly_capacity が存在するかどうか。
```

This indicates whether canonical WeeklyCapacityRow-derived forward capacity context has been attached to env.

### 6.3 backward canonical side context attached / missing

Meaning:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows が存在するかどうか。
```

This is the safe product-first backward context generated from WeeklyCapacityRow.

It is intentionally a side attribute.

### 6.4 backward consumer-facing context not replaced

Meaning:

```text
env.explicit_pipeline_backward_weekly_capability は置き換えていない。
```

This is important because the existing backward consumer-facing context may have a different shape, such as:

```text
node_product_week_map_v1
```

The diagnostic should clearly say that the canonical product-first backward context is attached safely, but it is not yet consumed as the planner-facing backward capability.

### 6.5 week_key_domain = preserve

Meaning:

```text
week key は変換されず、そのまま保持されている。
```

Examples:

```text
2027-W40
0
1
```

No calendar conversion should be implied.

### 6.6 shape = product_node_type_week_qty_v1

Meaning:

```text
runtime capacity context の形は、
product -> node -> capacity_type -> week -> capacity_qty
である。
```

This shape should be reported explicitly.

### 6.7 summary/env attribute consistency

Meaning:

```text
summary に書かれている attachment 状態と、実際の env 属性が一致しているか。
```

Example:

```text
summary says attached_forward=True
but env.explicit_pipeline_forward_weekly_capacity is missing
```

This should be reported as a warning or inconsistency.

---

## 7. Proposed Runtime Attachment Diagnostic Payload

Add a section like:

```python
"runtime_attachment": {
    "available": True,
    "summary_available": True,
    "summary": {...},
    "consistency": {
        "forward_env_attribute_present": True,
        "backward_canonical_env_attribute_present": True,
        "backward_consumer_env_attribute_present": False,
        "capacity_weekly_rows_present": True,
        "summary_matches_env": True,
    },
    "shape": {
        "forward_shape_from_summary": "product_node_type_week_qty_v1",
        "backward_shape_from_summary": "product_node_type_week_qty_v1",
        "backward_consumer_attribute_replaced": False,
    },
    "messages": [
        "Capacity runtime attachment: summary available.",
        "Capacity runtime attachment: forward context attached.",
        "Capacity runtime attachment: backward canonical side context attached.",
        "Capacity runtime attachment: backward consumer-facing capability was not replaced.",
        "Capacity runtime attachment: week keys preserved.",
    ],
}
```

If summary is missing:

```python
"runtime_attachment": {
    "available": False,
    "summary_available": False,
    "reason": "missing_capacity_runtime_attachment_summary",
    "messages": [
        "Capacity runtime attachment: summary missing."
    ],
}
```

---

## 8. Required Checks

### 8.1 Summary availability

Check:

```python
hasattr(env, "capacity_runtime_attachment_summary")
```

### 8.2 Forward env attribute

Check:

```python
hasattr(env, "explicit_pipeline_forward_weekly_capacity")
```

If summary says `attached_forward=True` but attribute is missing, add a warning message.

### 8.3 Backward canonical side attribute

Check:

```python
hasattr(env, "explicit_pipeline_backward_weekly_capability_from_weekly_rows")
```

If summary says `backward_canonical_attribute_attached=True` but attribute is missing, add a warning message.

### 8.4 Backward consumer-facing attribute

Check:

```python
hasattr(env, "explicit_pipeline_backward_weekly_capability")
```

If summary says:

```text
backward_consumer_attribute_replaced=False
```

then the diagnostic should explicitly report that consumer-facing backward capability was not replaced.

This is an informational or warning-level message, not an error.

### 8.5 Source row attribute

Check:

```python
hasattr(env, "capacity_weekly_rows")
```

If summary says `attached_rows=True` but env has no capacity_weekly_rows, add a warning message.

---

## 9. Message Policy

Append clear messages to the diagnostic.

Recommended messages:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: summary missing.
Capacity runtime attachment: WeeklyCapacityRow count = N.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: forward context missing despite summary.
Capacity runtime attachment: backward canonical side context attached.
Capacity runtime attachment: backward canonical side context missing despite summary.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment: week keys preserved.
Capacity runtime attachment: shape = product_node_type_week_qty_v1.
```

Messages should be deterministic.

Do not add noisy messages if no runtime attachment summary exists unless needed.

---

## 10. Severity Policy

Near-term implementation may use message strings only.

If easy, include a lightweight severity field:

```text
info
warning
error
```

But do not over-engineer.

Recommended near-term:

```text
messages: list[str]
warnings: list[str]
```

or simply:

```text
messages: list[str]
```

if that matches existing diagnostic style.

---

## 11. Integration With Existing Diagnostic Builder

The existing diagnostic builder likely returns a payload with top-level keys such as:

```text
forward_capacity
backward_capability
runtime_tree
consumer_expectation
alignment
messages
```

Add:

```text
runtime_attachment
```

to this payload.

Append runtime attachment messages to the top-level `messages` list.

Do not remove existing diagnostic keys.

Do not change existing message semantics.

---

## 12. Suggested Tests

Add focused tests:

```text
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

### 12.1 Summary available

Create a simple env object with:

```text
capacity_runtime_attachment_summary
explicit_pipeline_forward_weekly_capacity
explicit_pipeline_backward_weekly_capability_from_weekly_rows
capacity_weekly_rows
```

Assert:

```text
runtime_attachment.available == True
runtime_attachment.summary_available == True
messages include "summary available"
```

### 12.2 Summary missing

Create env without summary.

Assert:

```text
runtime_attachment.available == False
runtime_attachment.summary_available == False
reason == "missing_capacity_runtime_attachment_summary"
messages include "summary missing"
```

### 12.3 Forward inconsistency

Create summary:

```text
attached_forward=True
```

but omit:

```text
env.explicit_pipeline_forward_weekly_capacity
```

Assert a message reports forward context missing despite summary.

### 12.4 Backward canonical inconsistency

Create summary:

```text
backward_canonical_attribute_attached=True
```

but omit:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

Assert a message reports backward canonical side context missing despite summary.

### 12.5 Backward consumer-facing not replaced

Create summary:

```text
backward_consumer_attribute_replaced=False
backward_canonical_attribute_attached=True
```

Assert message reports that backward consumer-facing capability was not replaced.

### 12.6 Integration with existing diagnostic builder

If feasible, call the existing capacity scenario alignment diagnostic builder and assert:

```text
diagnostic["runtime_attachment"]
```

exists.

Assert top-level messages include runtime attachment messages.

Do not require GUI tests.

---

## 13. Test Commands

Run focused test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Run related tests:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Run related capacity tests:

```bat
python -m pytest tests/test_capacity_input_granularity_adapter.py
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Optional capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

---

## 14. Safety Boundaries

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
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Possibly changed only if necessary:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Do not wire into GUI or preflight in this request.

---

## 15. Acceptance Criteria

This request is complete when:

```text
build_capacity_runtime_attachment_diagnostic or equivalent helper exists
runtime_attachment section is added to capacity scenario alignment diagnostic
env.capacity_runtime_attachment_summary is read when available
missing summary is reported clearly
forward env attachment consistency is checked
backward canonical side attachment consistency is checked
backward consumer-facing not-replaced status is visible
week_key_domain from summary is visible
shape name from summary is visible
messages include runtime attachment status
focused tests pass
related diagnostic tests pass
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
no preflight wiring is added
```

---

## 16. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is the runtime attachment diagnostic helper implemented?
What key was added to the diagnostic payload?
Does the diagnostic read env.capacity_runtime_attachment_summary?
How does it report missing summary?
How does it report forward attachment mismatch?
How does it report backward canonical side attachment mismatch?
Does it state that backward consumer-facing capability was not replaced?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSVs?
Did you wire this into preflight?
Which tests passed?
```

---

## 17. Development Meaning

This request adds the signal system for the capacity runtime switchyard.

Already completed:

```text
master file
    ↓
canonical row
    ↓
runtime context
    ↓
env attachment
```

This request adds:

```text
env attachment
    ↓
diagnostic explanation
```

Do not run planner trains yet.

Do not wire into GUI preflight yet.

Just make the switch positions visible.
