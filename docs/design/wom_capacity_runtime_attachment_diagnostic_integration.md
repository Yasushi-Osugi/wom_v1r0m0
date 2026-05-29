# WOM Capacity Runtime Attachment Diagnostic Integration

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_backward_context_completion.md
docs/design/wom_capacity_weekly_rows_to_explicit_forward_context_completion.md
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md
```

---

## 1. Purpose

This memo defines how WOM capacity diagnostics should integrate with the runtime capacity attachment summary.

The completed runtime env attach phase established:

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

This memo designs the next diagnostic step:

```text
env.capacity_runtime_attachment_summary
    ↓
capacity diagnostic integration
    ↓
diagnostic payload and messages
```

The goal is to make WOM able to explain not only whether capacity data exists, but also whether it has been converted, attached, and made diagnostic-visible.

---

## 2. Core Design Principle

The core principle is:

```text
Capacity should be explainable at every boundary.
```

The diagnostic layer should explain:

```text
1. Was capacity master data loaded?
2. Was it converted into WeeklyCapacityRow?
3. Were forward/backward runtime contexts built?
4. Were those contexts attached to env?
5. Was backward attached to the consumer-facing attribute or a safe canonical side attribute?
6. Are week keys preserved or converted?
7. Is the runtime shape compatible with current diagnostics and consumers?
8. Is the capacity context likely applicable to the selected product/node/week scenario?
```

The diagnostic should not hide mismatch.

It should not silently treat attached capacity as applied capacity.

---

## 3. Current Completed State

### 3.1 Canonical loader completed

```text
capacity_master.csv -> WeeklyCapacityRow
```

Implementation commit:

```text
31d6d8e Add canonical capacity master loader
```

### 3.2 Forward context adapter completed

```text
WeeklyCapacityRow -> explicit forward capacity context
```

Implementation commit:

```text
3a933fd Add weekly capacity row forward context adapter
```

### 3.3 Backward context adapter completed

```text
WeeklyCapacityRow -> explicit backward capability context
```

Implementation commit:

```text
1ee4008 Add weekly capacity backward context adapter
```

### 3.4 Runtime env attach helper completed

```text
WeeklyCapacityRow-derived forward/backward contexts -> env attach
```

Implementation commit:

```text
d8a8a36 Add weekly capacity runtime env attach helper
```

Completion memo:

```text
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
```

### 3.5 Diagnostic integration not yet completed

The runtime attachment summary exists, but the existing capacity scenario alignment diagnostic does not yet fully consume:

```text
env.capacity_runtime_attachment_summary
```

This memo defines how to add that bridge.

---

## 4. Existing Diagnostic Context

The existing diagnostic module is:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Existing diagnostic concepts include:

```text
selected product mismatch
capacity product set mismatch
node mismatch
week-domain mismatch
forward capacity shape mismatch
backward capability shape detection
runtime tree node extraction
diagnostic messages
Explicit KPI View message surfacing
```

Existing env attachment completion already surfaced capacity alignment diagnostic messages in Explicit KPI view messages with the prefix:

```text
Capacity scenario alignment:
```

This memo does not replace that diagnostic.

It extends it with runtime attachment information.

---

## 5. Problem to Solve

After the env attach helper, WOM can attach:

```text
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

But diagnostics may still only inspect:

```text
forward capacity context
backward capability context
runtime tree
consumer expectation
```

The problem is that the diagnostic may not yet know:

```text
capacity rows were canonical WeeklyCapacityRows
forward context was attached by the canonical env attach helper
backward product-first context was attached to a safe side attribute
consumer-facing backward capability was intentionally not replaced
empty rows were handled deterministically
week domain is preserved
shape name is product_node_type_week_qty_v1
```

Therefore, the next step is to make runtime attachment status part of the diagnostic payload.

---

## 6. Non-Goals

This memo does not propose:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI layout changes
data CSV changes
sample CSV changes
scenario package loading
week-key normalization
calendar conversion
optimization logic
replacing existing backward consumer-facing capability shape
preflight wiring changes
```

The diagnostic integration should remain read-only.

---

## 7. Target Integration

The existing diagnostic should read, if present:

```text
env.capacity_runtime_attachment_summary
```

and include it in the diagnostic result.

Recommended diagnostic payload addition:

```text
runtime_attachment
```

Example:

```python
{
    "runtime_attachment": {
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
        "backward_consumer_attribute_replaced": False,
        "backward_canonical_attribute_attached": True,
        "messages": [],
    }
}
```

If the summary is missing:

```python
{
    "runtime_attachment": {
        "available": False,
        "reason": "env.capacity_runtime_attachment_summary not found",
        "messages": [
            "Capacity runtime attachment summary is not available."
        ],
    }
}
```

---

## 8. Diagnostic Message Policy

The diagnostic should add messages that are clear but not noisy.

Recommended messages:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: WeeklyCapacityRow count = N.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical context attached.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment: week keys preserved.
Capacity runtime attachment: no WeeklyCapacityRow rows provided.
Capacity runtime attachment: summary missing.
```

These may later be surfaced to Explicit KPI View, but the first implementation may only add them to diagnostic payload messages.

---

## 9. Severity Policy

Runtime attachment diagnostic should distinguish information from warnings.

Recommended severity categories:

```text
info
warning
error
```

Suggested mapping:

### 9.1 Info

```text
summary available
rows attached
forward attached
backward canonical attached
week keys preserved
```

### 9.2 Warning

```text
input_row_count = 0
backward consumer-facing attribute not replaced
summary missing while capacity contexts exist
forward attached but no rows retained
backward canonical side attribute attached but consumer-facing backward context absent
```

### 9.3 Error

```text
summary indicates adapter failure
summary inconsistent with env attributes
forward shape unknown
backward shape unknown
```

Near-term implementation may only append message strings, but the design should leave room for structured severity.

---

## 10. Attachment Consistency Checks

The diagnostic should check consistency between summary and env state.

### 10.1 Forward summary vs env attribute

If summary says:

```text
attached_forward = True
```

then env should have:

```text
env.explicit_pipeline_forward_weekly_capacity
```

If missing, diagnostic should report warning or error.

### 10.2 Backward summary vs env attribute

If summary says:

```text
backward_canonical_attribute_attached = True
```

then env should have:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

If missing, diagnostic should report warning or error.

### 10.3 Source rows summary vs env attribute

If summary says:

```text
attached_rows = True
```

then env should have:

```text
env.capacity_weekly_rows
```

If missing, diagnostic should report warning.

### 10.4 Summary attached to env

If env has runtime contexts but no summary, diagnostic should report:

```text
runtime contexts exist but attachment summary missing
```

This is important because future debugging should not have to guess how the contexts were built.

---

## 11. Backward Context Safety Diagnostic

The backward canonical side attribute is intentionally:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

not:

```text
env.explicit_pipeline_backward_weekly_capability
```

The diagnostic should explicitly state:

```text
Backward canonical product-first context is attached to a side attribute.
Existing consumer-facing backward capability was not replaced.
```

This avoids misunderstanding.

The diagnostic should not imply that the backward canonical side context is already consumed by the planner.

---

## 12. Shape Diagnostics

The runtime attachment summary reports:

```text
forward_shape
backward_shape
```

Recommended shape names:

```text
product_node_type_week_qty_v1
node_product_week_map_v1
unknown
unavailable
```

The diagnostic should compare these with existing shape detection functions where available.

For example:

```text
forward_shape from summary = product_node_type_week_qty_v1
forward shape detected from env context = product_node_type_week_qty_v1
```

If they differ, report warning.

For backward:

```text
backward_shape from summary = product_node_type_week_qty_v1
consumer-facing backward shape = node_product_week_map_v1 or unavailable
```

This may be expected and should be reported as a controlled difference, not automatically an error.

---

## 13. Week-Domain Diagnostics

The runtime attachment summary reports:

```text
week_key_domain = preserve
```

The existing diagnostic may also classify week key domains from actual context keys.

The integrated diagnostic should report:

```text
summary week domain
detected forward context week domain
detected backward canonical context week domain
```

If mixed or mismatched, report warning.

Do not normalize week keys in this diagnostic phase.

---

## 14. Product and Node Diagnostics

The runtime attachment summary reports counts:

```text
forward_product_count
backward_product_count
node_count
capacity_type_count
week_key_count
```

The diagnostic should use these counts to improve messages.

Examples:

```text
Capacity runtime attachment: 1 product, 3 nodes, 52 weeks attached.
Capacity runtime attachment: no product found in attached forward context.
Capacity runtime attachment: selected product not found in attached capacity product set.
```

The selected product mismatch diagnostic should remain the primary authority for selected product alignment.

The runtime attachment diagnostic simply adds attachment provenance.

---

## 15. Data Flow After Integration

The intended flow after implementation:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
    ↓
diagnostic.runtime_attachment
    ↓
diagnostic.messages
```

No planner behavior changes are involved.

---

## 16. Recommended Function Changes

### 16.1 New helper function

Add a helper in:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Suggested function:

```python
build_capacity_runtime_attachment_diagnostic(env) -> dict
```

This function should:

```text
read env.capacity_runtime_attachment_summary if present
check consistency with attached env attributes
return a structured runtime_attachment diagnostic section
return messages
```

### 16.2 Integrate into existing diagnostic builder

Extend:

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

or related env-attached helper so that the final diagnostic payload includes:

```text
runtime_attachment
```

and appends runtime attachment messages to the existing diagnostic messages.

### 16.3 Do not change attach helper

The first diagnostic integration should not require changing:

```text
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
```

unless tests reveal a missing summary key.

---

## 17. Suggested Runtime Attachment Diagnostic Payload

Recommended structure:

```python
{
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
        "backward_consumer_shape_expected": "node_product_week_map_v1",
    },
    "messages": [
        "Capacity runtime attachment: summary available.",
        "Capacity runtime attachment: forward context attached.",
        "Capacity runtime attachment: backward canonical side context attached.",
    ],
}
```

If summary is absent:

```python
{
    "available": False,
    "summary_available": False,
    "reason": "missing_capacity_runtime_attachment_summary",
    "messages": [
        "Capacity runtime attachment: summary missing."
    ],
}
```

---

## 18. Suggested Tests

Create focused tests:

```text
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

### 18.1 Summary available

Given env with:

```text
capacity_runtime_attachment_summary
explicit_pipeline_forward_weekly_capacity
explicit_pipeline_backward_weekly_capability_from_weekly_rows
capacity_weekly_rows
```

Assert diagnostic includes:

```text
runtime_attachment.available == True
summary_available == True
messages include summary available
```

### 18.2 Summary missing

Given env with no summary, assert:

```text
runtime_attachment.available == False
reason == missing_capacity_runtime_attachment_summary
messages include summary missing
```

### 18.3 Forward consistency

If summary says forward attached but env forward attribute is missing, assert warning message.

### 18.4 Backward canonical consistency

If summary says backward canonical attached but side attribute is missing, assert warning message.

### 18.5 Backward consumer not replaced message

If summary includes:

```text
backward_consumer_attribute_replaced = False
backward_canonical_attribute_attached = True
```

assert message states that backward consumer-facing capability was not replaced.

### 18.6 Integration with existing diagnostic builder

If feasible, call existing diagnostic builder and assert:

```text
diagnostic["runtime_attachment"]
```

exists and messages include runtime attachment status.

Do not require GUI tests in the first implementation.

---

## 19. Test Commands for Future Codex Request

Focused test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
python -m pytest tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Optional capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

---

## 20. Safety Boundaries for Future Implementation

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

Do not wire into GUI or preflight in this first diagnostic integration request.

---

## 21. Acceptance Criteria for Future Implementation

The diagnostic integration is complete when:

```text
runtime_attachment section is added to capacity scenario alignment diagnostic
env.capacity_runtime_attachment_summary is read when available
missing summary is reported clearly
forward env attachment consistency is checked
backward canonical side attachment consistency is checked
backward consumer-facing not-replaced status is visible
week_key_domain from summary is visible
messages include runtime attachment status
focused tests pass
related diagnostic tests pass
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
no preflight wiring is added
```

---

## 22. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_runtime_attachment_diagnostic_integration_request.md
```

Scope:

```text
diagnostic reads env.capacity_runtime_attachment_summary
diagnostic adds runtime_attachment section
focused tests
no planner changes
no GUI changes
no preflight wiring
```

---

## 23. Development Meaning

Before this phase, WOM can attach runtime capacity contexts to env.

After the future diagnostic integration phase, WOM will be able to explain that attachment.

The progression is:

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

This is central to WOM becoming a context-engineered planning environment rather than a black-box planner.

In short:

```text
The switchyard exists.
Now the signal system must explain the switch positions.
```

---

## 24. Summary

This memo designs the diagnostic integration for:

```text
env.capacity_runtime_attachment_summary
```

The diagnostic should report:

```text
summary available / missing
forward context attached / missing
backward canonical side context attached / missing
backward consumer-facing context not replaced
week key domain
runtime shape names
row/product/node/week counts
consistency between summary and env attributes
```

The next implementation should remain read-only and diagnostic-only.

Recommended next request:

```text
docs/codex_requests/wom_capacity_runtime_attachment_diagnostic_integration_request.md
```
