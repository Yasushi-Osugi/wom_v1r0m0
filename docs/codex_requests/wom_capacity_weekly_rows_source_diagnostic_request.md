# Codex Request: WOM Capacity Weekly Rows Source Diagnostic

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_weekly_rows_source_diagnostic_request.md`

**Parent design docs:**

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
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement a read-only diagnostic for the WOM capacity weekly rows source.

The target is to expose:

```text
env.capacity_weekly_rows_load_summary
```

as:

```text
diagnostic["capacity_weekly_rows_source"]
```

inside the existing capacity scenario alignment diagnostic.

The intended diagnostic path is:

```text
env.capacity_weekly_rows_load_summary
    ↓
build_capacity_weekly_rows_source_diagnostic(env)
    ↓
diagnostic["capacity_weekly_rows_source"]
```

This request is intentionally narrow.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI layout.

Do not change data CSV files.

Do not change source loading behavior.

Do not normalize week keys.

Do not implement scenario runner integration.

---

## 2. Why This Request Exists

WOM now has a working source-to-runtime path:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
Explicit KPI preflight
    ↓
capacity scenario alignment diagnostic
```

The runtime attachment side is already diagnostic-visible:

```text
env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

The source side is not yet first-class diagnostic-visible.

This request makes the source side explainable:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]
```

In short:

```text
Show where the capacity cargo came from.
```

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
```

Also inspect these implementation and test files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
pysi/capacity/capacity_weekly_rows_source.py
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Reuse existing diagnostic style.

Do not duplicate source loader logic.

---

## 4. Implementation Scope

### Required

Implement:

```python
build_capacity_weekly_rows_source_diagnostic(env) -> dict
```

Preferred location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Reason:

```text
The existing capacity scenario alignment diagnostic and runtime attachment diagnostic are already there.
This new helper is read-only and belongs to the same diagnostic surface.
```

Then integrate it into the existing capacity scenario alignment diagnostic payload:

```python
diagnostic["capacity_weekly_rows_source"] = build_capacity_weekly_rows_source_diagnostic(env)
```

Also append source diagnostic messages to:

```python
diagnostic["messages"]
```

### Expected changed files

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

---

## 5. Explicit Non-Scope

Do not implement:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI layout changes
new GUI widgets
data CSV changes
sample CSV changes
source loading behavior changes
scenario runner integration
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
capacity applicability enforcement
new optimization logic
```

This request is read-only diagnostic integration only.

---

## 6. Diagnostic Helper Contract

Implement:

```python
build_capacity_weekly_rows_source_diagnostic(env) -> dict
```

The helper should safely read:

```text
env.capacity_weekly_rows_load_summary
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
```

It should not raise if any of these are missing.

It should support summary as either:

```text
dict
object with attributes
```

Use or reuse a helper pattern similar to the existing runtime attachment diagnostic helper:

```python
_summary_value(summary, key, default=None)
```

If such a helper already exists, reuse it rather than duplicating unnecessarily.

---

## 7. Diagnostic Payload Contract

### 7.1 When load summary exists and source loaded

Return a dict similar to:

```python
{
    "available": True,
    "summary_available": True,
    "source_kind": "scenario_package_capacity_master",
    "source_path": ".../masters/capacity_master.csv",
    "row_count": 52,
    "attached_to_env": True,
    "env_rows_present": True,
    "env_row_count": 52,
    "source_path_matches_env": True,
    "source_kind_matches_env": True,
    "row_count_matches_env": True,
    "messages": [
        "Capacity weekly rows source: load summary available.",
        "Capacity weekly rows source: loaded 52 rows."
    ],
}
```

### 7.2 When source missing summary exists

If `env.capacity_weekly_rows_load_summary` exists and reports missing source:

```python
{
    "available": False,
    "summary_available": True,
    "source_kind": "missing",
    "source_path": None,
    "row_count": 0,
    "attached_to_env": False,
    "env_rows_present": False,
    "env_row_count": 0,
    "reason": "capacity_weekly_rows_source_missing",
    "messages": [
        "Capacity weekly rows source: load summary available.",
        "Capacity weekly rows source: no capacity master source found."
    ],
}
```

### 7.3 When load summary is missing

If no source load summary exists:

```python
{
    "available": False,
    "summary_available": False,
    "reason": "missing_capacity_weekly_rows_load_summary",
    "env_rows_present": False,
    "env_row_count": 0,
    "messages": [
        "Capacity weekly rows source: load summary missing."
    ],
}
```

If rows exist but summary is missing:

```python
{
    "available": False,
    "summary_available": False,
    "reason": "missing_capacity_weekly_rows_load_summary",
    "env_rows_present": True,
    "env_row_count": N,
    "messages": [
        "Capacity weekly rows source: load summary missing.",
        "Capacity weekly rows source: env.capacity_weekly_rows present without load summary."
    ],
}
```

---

## 8. Field Definitions

The helper should include these fields when possible:

```text
available
summary_available
source_kind
source_path
row_count
attached_to_env
env_rows_present
env_row_count
source_path_matches_env
source_kind_matches_env
row_count_matches_env
reason
messages
```

### 8.1 available

Mirror the source load summary’s `available` value when summary exists.

If summary is missing:

```text
False
```

### 8.2 summary_available

Whether:

```text
hasattr(env, "capacity_weekly_rows_load_summary")
```

### 8.3 source_kind

From summary or env metadata.

Fallback:

```text
"unknown"
```

### 8.4 source_path

From summary or env metadata.

If absent:

```text
None
```

### 8.5 row_count

From summary.

If missing:

```text
0
```

### 8.6 attached_to_env

From summary.

If missing:

```text
False
```

### 8.7 env_rows_present

Whether:

```text
hasattr(env, "capacity_weekly_rows")
```

### 8.8 env_row_count

Length of `env.capacity_weekly_rows` if present and sized.

If missing:

```text
0
```

If present but not sized, use:

```text
None
```

or a safe value, but do not raise.

### 8.9 consistency fields

Include consistency booleans when applicable:

```text
source_path_matches_env
source_kind_matches_env
row_count_matches_env
```

If comparison is not possible, use:

```text
None
```

or omit, but tests should cover the expected implemented behavior.

---

## 9. Consistency Warning Policy

The helper should produce warning messages, but must not raise, when summary and env disagree.

Recommended warnings:

```text
Capacity weekly rows source: summary says rows attached, but env.capacity_weekly_rows is missing.
Capacity weekly rows source: summary row_count differs from env row count.
Capacity weekly rows source: summary source path differs from env source path.
Capacity weekly rows source: summary source kind differs from env source kind.
```

These are diagnostic warnings only.

They should not change behavior.

---

## 10. Message Policy

The diagnostic should preserve messages from:

```text
summary["messages"]
```

and add deterministic diagnostic messages.

Recommended message examples:

```text
Capacity weekly rows source: load summary available.
Capacity weekly rows source: load summary missing.
Capacity weekly rows source: env.capacity_weekly_rows present.
Capacity weekly rows source: env.capacity_weekly_rows missing.
Capacity weekly rows source: loaded N rows.
Capacity weekly rows source: no capacity master source found.
```

Avoid excessive duplication where possible.

The top-level capacity scenario alignment diagnostic should include source messages before runtime attachment messages.

Recommended ordering:

```text
capacity_weekly_rows_source messages
runtime_attachment messages
existing scenario alignment messages
```

---

## 11. Integration Contract

In the existing capacity scenario alignment diagnostic builder, add:

```python
source_diagnostic = build_capacity_weekly_rows_source_diagnostic(env)
diagnostic["capacity_weekly_rows_source"] = source_diagnostic
diagnostic["messages"].extend(source_diagnostic.get("messages", []))
```

This should happen before runtime attachment messages are appended.

Reason:

```text
source loading happens before runtime attachment.
```

The final diagnostic should include both:

```text
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
```

No GUI layout changes are needed.

---

## 12. Cases to Support

### 12.1 Loaded non-empty source

Given:

```text
env.capacity_weekly_rows_load_summary reports available=True, row_count=N
env.capacity_weekly_rows has N rows
```

Expected:

```text
available=True
summary_available=True
env_rows_present=True
env_row_count=N
row_count_matches_env=True
```

### 12.2 Loaded empty source

Given:

```text
env.capacity_weekly_rows_load_summary reports available=True, row_count=0
env.capacity_weekly_rows == []
```

Expected:

```text
available=True
summary_available=True
env_rows_present=True
env_row_count=0
row_count_matches_env=True
```

Do not treat this as missing.

### 12.3 Source missing summary exists

Given summary:

```text
available=False
source_kind="missing"
attached_to_env=False
```

Expected:

```text
available=False
summary_available=True
reason="capacity_weekly_rows_source_missing"
```

### 12.4 Summary missing

Given no summary:

```text
summary_available=False
reason="missing_capacity_weekly_rows_load_summary"
```

### 12.5 Manual rows without summary

Given:

```text
env.capacity_weekly_rows exists
env.capacity_weekly_rows_load_summary missing
```

Expected:

```text
summary_available=False
env_rows_present=True
message says rows present without load summary
```

### 12.6 Inconsistent summary

Given:

```text
summary row_count=3
env.capacity_weekly_rows has 2 rows
```

Expected:

```text
row_count_matches_env=False
warning message included
```

---

## 13. Test Plan

Add focused tests:

```text
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

### 13.1 Missing summary

Assert:

```text
summary_available is False
reason == "missing_capacity_weekly_rows_load_summary"
messages include load summary missing
```

### 13.2 Loaded non-empty source

Assert:

```text
available is True
summary_available is True
env_rows_present is True
row_count_matches_env is True
messages include load summary available
```

### 13.3 Missing source summary

Assert:

```text
available is False
summary_available is True
reason == "capacity_weekly_rows_source_missing"
```

### 13.4 Empty valid source

Assert:

```text
available is True
env_rows_present is True
env_row_count == 0
row_count_matches_env is True
```

### 13.5 Manual rows without summary

Assert:

```text
summary_available is False
env_rows_present is True
message mentions rows present without load summary
```

### 13.6 Row count mismatch warning

Assert:

```text
row_count_matches_env is False
messages include row_count differs
```

### 13.7 Integration into scenario alignment diagnostic

Assert:

```text
diagnostic["capacity_weekly_rows_source"] exists
```

### 13.8 Message ordering

If both source and runtime attachment diagnostics exist, assert source messages appear before runtime attachment messages in the top-level messages list.

---

## 14. Test Commands

Focused diagnostic test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 15. Safety Boundaries

Expected changed files:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
data/*.csv
```

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI layout.

Do not change data CSV files.

---

## 16. Acceptance Criteria

This request is complete when:

```text
build_capacity_weekly_rows_source_diagnostic(env) exists
diagnostic["capacity_weekly_rows_source"] is included in capacity scenario alignment diagnostic
missing summary is handled safely
loaded non-empty source is reported
loaded empty source is reported distinctly from missing source
missing source summary is reported
manual rows without summary are reported
consistency warnings are produced when summary and env disagree
source messages are appended to top-level diagnostic messages
source messages appear before runtime attachment messages
focused tests pass
related diagnostic tests pass
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
data CSV unchanged
```

---

## 17. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is build_capacity_weekly_rows_source_diagnostic implemented?
What diagnostic key was added?
What does it report when load summary is missing?
What does it report when source is loaded with rows?
What does it report when source is loaded with an empty valid file?
What does it report when source summary says missing?
Does it report manual rows without summary?
Does it produce consistency warnings?
Are source messages appended before runtime attachment messages?
Did you change planner behavior?
Did you change capacity enforcement?
Did you change GUI layout?
Did you change data CSV files?
Which tests passed?
```

---

## 18. Development Meaning

This request completes the diagnostic visibility of the capacity source side.

Already completed:

```text
capacity_master.csv
    ↓
env.capacity_weekly_rows
    ↓
runtime attachment preflight
    ↓
runtime_attachment diagnostic
```

This request adds:

```text
env.capacity_weekly_rows_load_summary
    ↓
capacity_weekly_rows_source diagnostic
```

Do not move the train.

Do not change the cargo.

Just show the driver where the cargo came from.
