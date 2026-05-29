# WOM Capacity Runtime Attachment Diagnostic Integration Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
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
docs/codex_requests/wom_capacity_runtime_attachment_diagnostic_integration_request.md
```

---

## 1. Purpose

This completion memo records the completion of diagnostic integration for WOM capacity runtime attachment.

The completed scope is intentionally narrow:

```text
env.capacity_runtime_attachment_summary
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
diagnostic["runtime_attachment"]
    ↓
diagnostic["messages"]
```

This phase adds diagnostic visibility for capacity runtime attachment.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change GUI behavior.

It does not change data CSV files.

It does not add preflight wiring.

It does not normalize week keys.

---

## 2. Key Commit

Implementation commit:

```text
45477fc Add capacity runtime attachment diagnostic
```

Related preceding commits:

```text
13f08e6 Add WOM capacity runtime attachment diagnostic integration design
2a59235 Add WOM capacity runtime attachment diagnostic integration Codex request
0b226d1 Add WOM capacity weekly rows runtime env attach completion memo
d8a8a36 Add weekly capacity runtime env attach helper
07780b9 Add WOM capacity weekly rows runtime env attach Codex request
39a1d37 Add WOM capacity weekly rows runtime env attach design
c798216 Add WOM capacity weekly rows to explicit backward context completion memo
1ee4008 Add weekly capacity backward context adapter
3a933fd Add weekly capacity row forward context adapter
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation added:

```python
build_capacity_runtime_attachment_diagnostic(env)
```

in:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

The helper reads:

```text
env.capacity_runtime_attachment_summary
```

and produces a diagnostic section that explains:

```text
whether runtime attachment summary exists
whether forward runtime context is attached
whether backward canonical side context is attached
whether backward consumer-facing capability was not replaced
whether capacity_weekly_rows exists
whether summary and env attributes are consistent
what week_key_domain is reported
what runtime shape names are reported
```

The existing capacity scenario alignment diagnostic now includes:

```text
runtime_attachment
```

and appends runtime attachment messages to the top-level diagnostic messages list.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

### 4.1 explicit_pipeline_capacity_scenario_alignment.py

Added:

```python
build_capacity_runtime_attachment_diagnostic(env)
```

and integrated the resulting section into the existing capacity scenario alignment diagnostic payload.

The diagnostic now includes:

```text
diagnostic["runtime_attachment"]
```

and appends runtime attachment messages to:

```text
diagnostic["messages"]
```

### 4.2 test_wom_capacity_runtime_attachment_diagnostic_integration.py

Added focused tests covering:

```text
summary available
summary missing
forward attachment mismatch
backward canonical side attachment mismatch
backward consumer-facing not-replaced reporting
integration into existing scenario alignment diagnostic
```

---

## 5. Diagnostic Payload Added

The diagnostic payload now includes:

```text
runtime_attachment
```

Conceptual structure:

```python
{
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
        "messages": [...],
    }
}
```

If summary is missing:

```python
{
    "runtime_attachment": {
        "available": False,
        "summary_available": False,
        "reason": "missing_capacity_runtime_attachment_summary",
        "messages": [
            "Capacity runtime attachment: summary missing."
        ],
    }
}
```

---

## 6. Diagnostic Meanings

### 6.1 Runtime attachment summary available / missing

The diagnostic checks whether this attribute exists:

```text
env.capacity_runtime_attachment_summary
```

If present, WOM has a receipt explaining how capacity runtime contexts were attached.

If missing, WOM reports:

```text
reason = "missing_capacity_runtime_attachment_summary"
```

and message:

```text
Capacity runtime attachment: summary missing.
```

### 6.2 Forward context attached / missing

The diagnostic checks whether this attribute exists:

```text
env.explicit_pipeline_forward_weekly_capacity
```

If the summary says:

```text
attached_forward = True
```

but the env attribute is missing, the diagnostic emits:

```text
Capacity runtime attachment: forward context missing despite summary.
```

### 6.3 Backward canonical side context attached / missing

The diagnostic checks whether this attribute exists:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

If the summary says:

```text
backward_canonical_attribute_attached = True
```

but the env attribute is missing, the diagnostic emits:

```text
Capacity runtime attachment: backward canonical side context missing despite summary.
```

### 6.4 Backward consumer-facing context not replaced

The diagnostic explicitly reports when:

```text
backward_consumer_attribute_replaced = False
```

This message is expected in the current design:

```text
Capacity runtime attachment: backward consumer-facing capability was not replaced.
```

This is not treated as a planner error.

It means the product-first backward canonical context is safely attached to the side attribute, while the existing consumer-facing backward capability remains untouched.

### 6.5 Week key domain

The diagnostic reports:

```text
week_key_domain = "preserve"
```

This confirms that week keys are not normalized or converted in this phase.

Examples:

```text
2027-W40
0
1
```

remain as-is.

### 6.6 Runtime shape

The diagnostic reports runtime shape names from summary.

Current shape:

```text
product_node_type_week_qty_v1
```

Meaning:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

### 6.7 Summary / env attribute consistency

The diagnostic compares what the summary claims with what is actually present on `env`.

Examples:

```text
summary says forward attached, but env forward attribute missing
summary says backward canonical side context attached, but side attribute missing
summary says rows attached, but env.capacity_weekly_rows missing
```

These are diagnostic warnings.

They help WOM detect inconsistencies between the runtime attachment receipt and actual runtime state.

---

## 7. Messages Added

The runtime attachment diagnostic can add deterministic messages such as:

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

These messages are also appended to the existing top-level scenario alignment diagnostic messages.

---

## 8. Tests Executed

The focused runtime attachment diagnostic test passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Observed result:

```text
6 passed
```

Diagnostic integration tests passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
17 passed
```

Adapter / diagnostic / capacity related tests passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py tests/test_explicit_pipeline_capacity_scenario_alignment.py tests/test_capacity_input_granularity_adapter.py tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Observed result:

```text
49 passed
```

Capacity regression set passed:

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
explicit KPI preflight wiring
Management Cockpit behavior
scenario package loading
week-key normalization
calendar conversion
capacity applicability status
```

This phase only added:

```text
runtime attachment diagnostic helper
runtime_attachment diagnostic payload section
runtime attachment diagnostic messages
focused tests
```

---

## 10. Current Architecture After This Phase

The completed capacity canonical path is now:

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
env.capacity_runtime_attachment_summary
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
diagnostic["runtime_attachment"]
    ↓
diagnostic["messages"]
```

This is the first diagnostic-visible capacity runtime attachment path.

---

## 11. Still Deferred

The following work remains intentionally deferred.

### 11.1 Preflight wiring

The diagnostic integration is not yet wired into:

```text
Explicit KPI preflight
GUI preflight
scenario runner preflight
```

### 11.2 GUI message surfacing

Runtime attachment diagnostic messages are part of diagnostic messages, but no new GUI layout or message surfacing change was introduced in this phase.

### 11.3 Planner consumption

No planner currently consumes the newly attached canonical backward side attribute.

Planner behavior remains unchanged.

### 11.4 Consumer-facing backward shape bridge

The canonical product-first backward context is not yet converted into the existing consumer-facing backward shape if that shape remains:

```text
node_product_week_map_v1
```

### 11.5 Scenario package integration

Scenario yaml loading is not yet implemented.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

### 11.6 Capacity applicability status

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

## 12. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
```

Purpose:

```text
Define how canonical capacity rows, runtime env attachment, and runtime attachment diagnostics
should be safely invoked during Explicit KPI preflight or scenario preflight.
```

The design should address:

```text
where capacity rows come from
when attach_capacity_runtime_contexts_to_env_from_weekly_rows is called
when build_capacity_runtime_attachment_diagnostic is called
how messages are surfaced
how missing capacity rows are handled
how existing explicit KPI diagnostic flow remains stable
no planner behavior change
```

Possible later Codex request:

```text
docs/codex_requests/wom_capacity_runtime_attachment_preflight_wiring_request.md
```

The first preflight wiring implementation should remain narrow:

```text
call env attach helper only when capacity_weekly_rows are already available
append diagnostic messages
no planner behavior changes
no GUI layout changes
```

---

## 13. Development Meaning

Before this phase, WOM could attach capacity runtime contexts to env.

After this phase, WOM can explain that attachment.

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

This is a significant step toward WOM as a context-engineered planning environment.

The capacity path is no longer only a data path.

It is becoming a self-explaining runtime context path.

In short:

```text
The switchyard exists.
The signal system now reports the switch positions.
```

---

## 14. Summary

Completed:

```text
build_capacity_runtime_attachment_diagnostic(env)
diagnostic["runtime_attachment"]
runtime attachment diagnostic messages
```

Confirmed:

```text
summary available / missing reported
forward attachment mismatch reported
backward canonical side attachment mismatch reported
backward consumer-facing not-replaced status reported
week_key_domain reported
shape name reported
summary/env consistency checked
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
preflight wiring unchanged
```

Next:

```text
runtime attachment diagnostic
    ↓
preflight wiring / message surfacing
```

Recommended next design:

```text
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
```
