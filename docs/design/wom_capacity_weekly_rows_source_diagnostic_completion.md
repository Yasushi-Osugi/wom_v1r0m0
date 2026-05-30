# WOM Capacity Weekly Rows Source Diagnostic Completion Memo

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_consolidation.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_weekly_rows_source_diagnostic_request.md
```

---

## 1. Purpose

This completion memo records the completion of the read-only diagnostic for WOM capacity weekly rows source loading.

The completed diagnostic path is:

```text
env.capacity_weekly_rows_load_summary
    ↓
build_capacity_weekly_rows_source_diagnostic(env)
    ↓
diagnostic["capacity_weekly_rows_source"]
```

This is now paired with the existing runtime attachment diagnostic path:

```text
env.capacity_runtime_attachment_summary
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
diagnostic["runtime_attachment"]
```

Together, these two diagnostic sections explain both:

```text
where the capacity rows came from
whether they were attached as runtime capacity contexts
```

This phase is diagnostic-only.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change blocked lot behavior.

It does not change GUI layout.

It does not change data CSV files.

It does not change source loading behavior.

It does not normalize week keys.

It does not implement scenario runner integration.

---

## 2. Key Commit

Implementation commit:

```text
f9856e4 Add capacity weekly rows source diagnostic
```

Related preceding commits:

```text
856491a Add WOM capacity weekly rows source diagnostic Codex request
f5b839a Add WOM capacity weekly rows source diagnostic design
abb8db5 Add WOM capacity source Explicit KPI preflight wiring completion memo
34080fc Wire capacity source into explicit KPI preflight
589efc7 Add WOM capacity source Explicit KPI preflight wiring Codex request
3540ab1 Add WOM capacity source Explicit KPI preflight wiring design
cb45f61 Add WOM capacity master to env capacity weekly rows source completion memo
8886c03 Add capacity weekly rows env source helper
```

---

## 3. Implementation Summary

The implementation added:

```python
build_capacity_weekly_rows_source_diagnostic(env)
```

in:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

The helper safely reads:

```text
env.capacity_weekly_rows_load_summary
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
```

It supports both:

```text
dict-style summaries
object-style summaries
```

It returns a deterministic diagnostic dictionary.

The existing capacity scenario alignment diagnostic now includes:

```text
diagnostic["capacity_weekly_rows_source"]
```

beside the existing:

```text
diagnostic["runtime_attachment"]
```

Source diagnostic messages are appended to the top-level diagnostic message stream before runtime attachment messages.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

### 4.1 explicit_pipeline_capacity_scenario_alignment.py

Added source diagnostic helper:

```python
build_capacity_weekly_rows_source_diagnostic(env)
```

Added supporting utility logic for:

```text
safe env row counting
unique message appending
summary message extraction
summary/env consistency checks
```

Integrated the new source diagnostic into the existing scenario alignment diagnostic payload.

### 4.2 test_wom_capacity_weekly_rows_source_diagnostic.py

Added focused tests covering:

```text
missing load summary
loaded non-empty source
object-style summary
missing source summary
empty valid source
manual rows without summary
summary/env mismatch warnings
integration into scenario alignment diagnostic
source-before-runtime message ordering
```

---

## 5. New Diagnostic Key

The new diagnostic key is:

```text
capacity_weekly_rows_source
```

It is included in the existing capacity scenario alignment diagnostic:

```python
diagnostic = {
    ...,
    "capacity_weekly_rows_source": {...},
    "runtime_attachment": {...},
    "messages": [...],
}
```

This gives the diagnostic payload a source-side section and a runtime-side section.

---

## 6. Diagnostic Payload Behavior

### 6.1 Missing load summary

When:

```text
env.capacity_weekly_rows_load_summary
```

is missing, the diagnostic reports:

```text
available = False
summary_available = False
reason = "missing_capacity_weekly_rows_load_summary"
```

It also reports whether:

```text
env.capacity_weekly_rows
```

is present.

This supports manual/test setup cases.

### 6.2 Source loaded with rows

When the source summary reports loaded rows and env rows are present, the diagnostic reports:

```text
available = True
summary_available = True
env_rows_present = True
row_count_matches_env = True
source_kind/path consistency checks
```

It preserves source summary messages and adds deterministic diagnostic messages.

### 6.3 Source loaded with an empty valid file

When the source file exists and is valid but has no data rows, the diagnostic reports:

```text
available = True
env_rows_present = True
env_row_count = 0
row_count_matches_env = True
```

This is intentionally different from a missing source.

### 6.4 Source summary says missing

When the source summary reports:

```text
source_kind = "missing"
available = False
attached_to_env = False
```

the diagnostic reports:

```text
reason = "capacity_weekly_rows_source_missing"
```

### 6.5 Manual rows without load summary

When:

```text
env.capacity_weekly_rows
```

exists but:

```text
env.capacity_weekly_rows_load_summary
```

is missing, the diagnostic reports:

```text
summary_available = False
env_rows_present = True
```

and includes a message explaining that rows are present without a load summary.

### 6.6 Summary/env inconsistencies

The diagnostic produces warnings without raising when summary and env disagree.

Examples:

```text
summary says rows attached, but env.capacity_weekly_rows is missing
summary row_count differs from env row count
summary source path differs from env source path
summary source kind differs from env source kind
```

These are diagnostic warnings only.

---

## 7. Message Ordering

The implementation appends source diagnostic messages before runtime attachment messages in the top-level diagnostic message list.

The intended story is:

```text
1. capacity source status
2. runtime attachment status
3. existing scenario alignment status
```

This ordering matches the actual preflight flow:

```text
source loading
    ↓
runtime attachment
    ↓
alignment diagnostic
```

---

## 8. Current Diagnostic Architecture

After this phase, the diagnostic architecture is:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]

env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

This means the capacity scenario alignment diagnostic can now explain:

```text
source availability
source path
source kind
source row count
source/env consistency
runtime context attachment
runtime context shape
runtime/env consistency
```

---

## 9. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
blocked lot behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
GUI behavior
GUI layout
Management Cockpit layout
data CSV files
sample CSV files
source loading behavior
scenario runner behavior
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
capacity applicability status enforcement
```

This phase only added:

```text
read-only source diagnostic helper
scenario alignment diagnostic integration
focused tests
```

---

## 10. Tests Executed

Focused source diagnostic test passed:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

Observed result:

```text
9 passed
```

Capacity weekly rows source helper tests passed:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Observed result:

```text
8 passed
```

Capacity source Explicit KPI preflight wiring tests passed:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Observed result:

```text
6 passed
```

Runtime attachment diagnostic integration tests passed:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Observed result:

```text
6 passed
```

Explicit pipeline capacity scenario alignment tests passed:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
11 passed
```

Capacity regression tests passed:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
28 passed
```

---

## 11. Current Architecture After This Phase

The full source-to-diagnostic path is now:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
capacity scenario alignment diagnostic
```

With diagnostic branches:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]

env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

This completes the first explainable capacity source-to-runtime diagnostic chain.

---

## 12. Still Deferred

The following work remains intentionally deferred.

### 12.1 GUI display refinement

No GUI layout was changed.

Future work may decide how much of:

```text
diagnostic["capacity_weekly_rows_source"]
```

should be surfaced in the Management Cockpit or Explicit KPI message panel.

### 12.2 Scenario package runner integration

No scenario runner integration was added.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

could be loaded by a scenario runner and passed through the same helper.

### 12.3 Legacy PySI V0R8 adapter dispatch

Legacy capacity inputs are not yet routed through:

```text
legacy input
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
```

### 12.4 Capacity applicability status

No first-class capacity applicability status taxonomy is implemented yet.

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

### 12.5 Planner consumption changes

No planner behavior has changed.

---

## 13. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_diagnostic_message_cockpit_visibility.md
```

Purpose:

```text
Define how capacity_weekly_rows_source and runtime_attachment diagnostic messages
should be surfaced in the Explicit KPI / Management Cockpit message area without
changing GUI layout or planner behavior.
```

This design should address:

```text
message selection
message ordering
source vs runtime message grouping
whether to expose source_kind/source_path/row_count
safe behavior for missing source
safe behavior for empty source
no planner behavior change
no data CSV change
```

Possible Codex request:

```text
docs/codex_requests/wom_capacity_diagnostic_message_cockpit_visibility_request.md
```

Alternative next direction:

```text
docs/design/wom_capacity_scenario_package_integration.md
```

if the priority is scenario package loading rather than GUI visibility.

---

## 14. Development Meaning

Before this phase, WOM could load capacity rows and attach runtime contexts, but the source side was only indirectly visible.

After this phase, WOM can explain:

```text
where capacity rows came from
whether they were loaded
whether they were empty or missing
whether env metadata matches source summary
whether runtime contexts were attached
```

In short:

```text
The cargo source is now visible on the diagnostic console.
```

The train still has the same schedule.

The cargo has the same content.

But the driver can now see where the cargo came from.

---

## 15. Summary

Completed:

```text
build_capacity_weekly_rows_source_diagnostic(env)
```

Confirmed:

```text
diagnostic["capacity_weekly_rows_source"] added
missing load summary handled safely
loaded non-empty source reported
loaded empty source reported distinctly from missing source
missing source summary reported
manual rows without summary reported
consistency warnings produced when summary and env disagree
source messages appended before runtime attachment messages
focused tests passed
related tests passed
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
data CSV unchanged
source loading behavior unchanged
scenario runner unchanged
legacy adapter dispatch unchanged
```

Next:

```text
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
    ↓
Cockpit / Explicit KPI message visibility
```

Recommended next design:

```text
docs/design/wom_capacity_diagnostic_message_cockpit_visibility.md
```
