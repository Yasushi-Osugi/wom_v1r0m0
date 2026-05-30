# WOM Capacity Weekly Rows Source Diagnostic

**Version:** v0r1 draft  
**Date:** 2026-05-30  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_weekly_rows_source_diagnostic.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_scenario_package_control_model.md
```

---

## 1. Purpose

This memo defines how WOM should expose the capacity weekly rows source load summary as a diagnostic payload.

The completed source-to-runtime path is now:

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

The missing diagnostic link is:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]
```

This memo designs that diagnostic link.

This is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
The capacity source side should be as explainable as the runtime attachment side.
```

The runtime side already has:

```text
env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

The source side should similarly have:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]
```

This diagnostic should explain:

```text
Was a capacity source loaded?
Where did it come from?
How many WeeklyCapacityRow rows were loaded?
Was the source missing, empty, or populated?
Were source load messages recorded?
```

It must not change planner behavior.

It must not change capacity enforcement.

It must not change GUI layout.

---

## 3. Current Completed State

### 3.1 Canonical capacity loader

Implemented:

```text
capacity_master.csv -> list[WeeklyCapacityRow]
```

Function:

```python
load_capacity_master_csv(path)
```

Key commit:

```text
31d6d8e Add canonical capacity master loader
```

### 3.2 Capacity source helper

Implemented:

```text
capacity source -> env.capacity_weekly_rows
```

Function:

```python
load_capacity_weekly_rows_to_env(...)
```

Key commit:

```text
8886c03 Add capacity weekly rows env source helper
```

### 3.3 Explicit KPI source preflight wiring

Implemented:

```text
Explicit KPI preflight -> load_capacity_weekly_rows_to_env(...)
```

Key commit:

```text
34080fc Wire capacity source into explicit KPI preflight
```

### 3.4 Runtime attachment diagnostic

Implemented:

```text
env.capacity_runtime_attachment_summary -> diagnostic["runtime_attachment"]
```

Key commit:

```text
45477fc Add capacity runtime attachment diagnostic
```

### 3.5 Remaining diagnostic gap

The source load summary is attached to env:

```text
env.capacity_weekly_rows_load_summary
```

but it is not yet represented as a first-class diagnostic section.

This memo addresses that gap.

---

## 4. Problem to Solve

The Explicit KPI preflight can now load capacity rows from source.

However, diagnostic visibility currently focuses on runtime attachment status.

The source-side state remains less visible.

The problem is:

```text
When capacity source loading happens,
or when it is skipped,
how should the user / developer see that in the capacity diagnostic payload?
```

The diagnostic should answer:

```text
Was the source helper called?
Was a source available?
Which source kind was used?
Which path was used?
How many rows were loaded?
Was env.capacity_weekly_rows attached?
Were there source messages?
How does the source status relate to runtime_attachment status?
```

---

## 5. Non-Goals

This memo does not propose:

```text
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
GUI layout changes
new GUI widgets
data CSV changes
sample CSV changes
scenario runner integration
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
new optimization logic
replacement of existing backward consumer-facing capability shape
capacity applicability enforcement
```

The design is limited to read-only diagnostic exposure.

---

## 6. Proposed Diagnostic Key

Recommended diagnostic payload key:

```text
capacity_weekly_rows_source
```

It should be included in the existing capacity scenario alignment diagnostic payload.

Conceptual shape:

```python
diagnostic = {
    ...,
    "capacity_weekly_rows_source": {...},
    "runtime_attachment": {...},
    "messages": [...],
}
```

This keeps source-side and runtime-side diagnostics adjacent.

---

## 7. Proposed Helper

Recommended helper:

```python
build_capacity_weekly_rows_source_diagnostic(env) -> dict
```

Preferred location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Reason:

```text
The existing capacity scenario alignment diagnostic and runtime attachment diagnostic live there.
The new diagnostic is read-only and belongs to the same diagnostic surface.
```

The helper should read:

```text
env.capacity_weekly_rows_load_summary
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
```

and return a deterministic diagnostic dictionary.

---

## 8. Diagnostic Payload Shape

Recommended payload when summary is available:

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
    "messages": [
        "Capacity weekly rows source: loaded 52 rows from capacity_master.csv."
    ],
}
```

Recommended payload when source is missing but summary exists:

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
        "Capacity weekly rows source: no capacity master source found."
    ],
}
```

Recommended payload when no summary exists:

```python
{
    "available": False,
    "summary_available": False,
    "reason": "missing_capacity_weekly_rows_load_summary",
    "env_rows_present": hasattr(env, "capacity_weekly_rows"),
    "env_row_count": ...,
    "messages": [
        "Capacity weekly rows source: load summary missing."
    ],
}
```

---

## 9. Field Definitions

### 9.1 available

Meaning:

```text
A source was available and loaded successfully.
```

This should usually mirror:

```text
summary["available"]
```

### 9.2 summary_available

Meaning:

```text
env.capacity_weekly_rows_load_summary exists.
```

### 9.3 source_kind

Possible values:

```text
capacity_master_csv
scenario_package_capacity_master
legacy_monthly_capacity_adapter
legacy_weekly_capacity_adapter
manual_test_rows
missing
unknown
```

Actual implementation should reflect current source helper values.

### 9.4 source_path

String path from summary or env metadata.

If no source exists:

```text
None
```

### 9.5 row_count

Row count reported by source load summary.

### 9.6 attached_to_env

Whether the source helper reported that rows were attached to env.

### 9.7 env_rows_present

Whether:

```text
hasattr(env, "capacity_weekly_rows")
```

### 9.8 env_row_count

If `env.capacity_weekly_rows` exists:

```text
len(env.capacity_weekly_rows)
```

otherwise:

```text
0
```

### 9.9 source_path_matches_env

When both summary and env path exist, whether they match.

This is a consistency check, not a behavior change.

### 9.10 messages

A deterministic list of source diagnostic messages.

---

## 10. Consistency Checks

The diagnostic should check consistency between summary and env attributes.

Recommended checks:

```text
summary says attached_to_env=True but env.capacity_weekly_rows missing
summary row_count differs from len(env.capacity_weekly_rows)
summary source_path differs from env.capacity_weekly_rows_source_path
summary source_kind differs from env.capacity_weekly_rows_source_kind
```

If inconsistencies exist, include warning messages.

Example:

```text
Capacity weekly rows source: summary says rows attached, but env.capacity_weekly_rows is missing.
Capacity weekly rows source: summary row_count differs from env row count.
Capacity weekly rows source: summary source path differs from env source path.
```

Do not fail or raise.

This is diagnostic-only.

---

## 11. Message Policy

The diagnostic should include source messages from:

```text
summary["messages"]
```

and add deterministic diagnostic messages.

Recommended message examples:

```text
Capacity weekly rows source: load summary available.
Capacity weekly rows source: loaded 52 rows.
Capacity weekly rows source: no capacity master source found.
Capacity weekly rows source: load summary missing.
Capacity weekly rows source: env.capacity_weekly_rows present.
Capacity weekly rows source: env.capacity_weekly_rows missing.
```

Avoid duplicate messages where possible.

If the existing summary messages are already clear, preserve them and add only minimal diagnostic messages.

---

## 12. Relationship to Runtime Attachment Diagnostic

The source diagnostic should appear before runtime attachment messages in the top-level diagnostic message stream.

Recommended ordering:

```text
capacity_weekly_rows_source messages
runtime_attachment messages
existing scenario alignment messages
```

Reason:

```text
source loading happens before runtime attachment.
```

This ordering tells the story correctly:

```text
Where did capacity rows come from?
Were they attached as runtime contexts?
Are runtime shapes aligned?
```

---

## 13. Relationship to Existing Capacity Scenario Alignment Diagnostic

The existing diagnostic builder should include:

```text
diagnostic["capacity_weekly_rows_source"] = build_capacity_weekly_rows_source_diagnostic(env)
```

The diagnostic builder should append source diagnostic messages into:

```text
diagnostic["messages"]
```

No new GUI layout should be required.

The existing Explicit KPI diagnostic message path can surface these messages if it already surfaces diagnostic messages.

---

## 14. Cases to Support

### 14.1 Source loaded with non-empty rows

Expected:

```text
available=True
summary_available=True
env_rows_present=True
row_count > 0
env_row_count == row_count
messages include loaded N rows
```

### 14.2 Source loaded with empty valid file

Expected:

```text
available=True
summary_available=True
env_rows_present=True
row_count == 0
env_row_count == 0
messages explain loaded 0 rows
```

This should not be treated as missing.

### 14.3 Source missing and summary attached

Expected:

```text
available=False
summary_available=True
source_kind="missing"
env_rows_present=False
reason="capacity_weekly_rows_source_missing"
```

### 14.4 No source hint and no source helper call

Expected:

```text
available=False
summary_available=False
reason="missing_capacity_weekly_rows_load_summary"
```

This is safe and expected in demos without source hints.

### 14.5 Manually attached rows without summary

Expected:

```text
available=False or unknown
summary_available=False
env_rows_present=True
env_row_count > 0
message explains rows exist but load summary is missing
```

This is useful for tests or manual setup.

---

## 15. Error Handling Policy

The diagnostic helper is read-only.

It should not raise for missing attributes.

It should safely handle:

```text
no env.capacity_weekly_rows_load_summary
summary as dict
summary as object with attributes
missing keys
env.capacity_weekly_rows not list but sized iterable
env.capacity_weekly_rows not sized
```

Recommended helper utility:

```python
_summary_value(summary, key, default=None)
```

similar to the existing runtime attachment diagnostic helper.

---

## 16. Test Plan

Add focused tests:

```text
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

### 16.1 Missing summary

Given env with no source summary:

```text
diagnostic["summary_available"] is False
diagnostic["reason"] == "missing_capacity_weekly_rows_load_summary"
messages include load summary missing
```

### 16.2 Loaded non-empty source

Given env with source summary and rows:

```text
available is True
row_count matches env row count
env_rows_present is True
messages include load summary available / loaded rows
```

### 16.3 Missing source summary from helper

Given env with:

```text
env.capacity_weekly_rows_load_summary = {"available": False, "source_kind": "missing", ...}
```

assert:

```text
available is False
reason == "capacity_weekly_rows_source_missing"
```

### 16.4 Empty valid source

Given summary with row_count 0 and env.capacity_weekly_rows = []:

```text
available is True
env_rows_present is True
env_row_count == 0
```

### 16.5 Consistency warning

Given summary row_count 3 but env rows length 2:

```text
messages include row_count differs
```

### 16.6 Integration into scenario alignment diagnostic

Assert:

```text
diagnostic["capacity_weekly_rows_source"]
```

exists in the existing capacity scenario alignment diagnostic.

### 16.7 Message ordering

Assert source messages appear before runtime attachment messages if both exist.

---

## 17. Test Commands for Future Codex Request

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

## 18. Safety Boundaries for Future Implementation

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

## 19. Acceptance Criteria for Future Implementation

The source diagnostic implementation is complete when:

```text
build_capacity_weekly_rows_source_diagnostic(env) exists
diagnostic["capacity_weekly_rows_source"] is included in scenario alignment diagnostic
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
GUI layout unchanged
data CSV unchanged
```

---

## 20. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_weekly_rows_source_diagnostic_request.md
```

Scope:

```text
implement build_capacity_weekly_rows_source_diagnostic(env)
integrate into capacity scenario alignment diagnostic
focused tests
no planner changes
no GUI changes
no data CSV changes
```

---

## 21. Development Meaning

Before this phase, WOM can load capacity rows and attach runtime contexts.

However, the diagnostic story is still incomplete:

```text
runtime attachment is visible
source loading is only indirectly visible
```

This design completes the explanatory path:

```text
capacity source
    ↓
capacity rows
    ↓
runtime contexts
    ↓
diagnostics
```

In short:

```text
The cargo can now be loaded.
The next step is to show the driver where the cargo came from.
```

---

## 22. Summary

This memo designs:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]
```

The first implementation should remain narrow:

```text
read-only diagnostic helper
integration into existing capacity scenario alignment diagnostic
focused tests
no planner changes
no GUI changes
no data changes
```

Recommended next request:

```text
docs/codex_requests/wom_capacity_weekly_rows_source_diagnostic_request.md
```
