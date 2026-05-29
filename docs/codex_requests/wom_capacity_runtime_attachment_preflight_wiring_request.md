# Codex Request: WOM Capacity Runtime Attachment Preflight Wiring

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_runtime_attachment_preflight_wiring_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
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

Please implement the first safe preflight wiring helper for WOM capacity runtime attachment.

This request is intentionally narrow.

Implement a helper equivalent to:

```python
apply_capacity_runtime_attachment_preflight(
    env,
    *,
    messages: list[str] | None = None,
) -> dict
```

The helper should:

```text
look for env.capacity_weekly_rows
if rows exist, call attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
then call build_capacity_runtime_attachment_diagnostic(env)
return a structured preflight result
append diagnostic messages to an external messages list if provided
```

Do not wire this helper into GUI preflight yet.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change data CSV files.

Do not implement scenario package loading.

Do not normalize week keys.

---

## 2. Why This Request Exists

WOM now has the following implemented capacity path:

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
```

The next safe step is not planner integration.

The next safe step is a preflight helper that can be called when `env.capacity_weekly_rows` already exists.

This helper should prepare runtime capacity contexts and diagnostics before planning, without changing planner behavior.

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach.md
```

Also inspect these implementation and test files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Reuse existing helpers:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
build_capacity_runtime_attachment_diagnostic(...)
```

Do not duplicate their logic.

---

## 4. Implementation Scope

### Required

Add a preflight helper equivalent to:

```python
apply_capacity_runtime_attachment_preflight(
    env,
    *,
    messages: list[str] | None = None,
) -> dict
```

Preferred location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Reason:

```text
The helper is preflight/diagnostic oriented.
It should not change planning behavior.
It will call diagnostic helpers already located in reporting.
```

If Codex finds a clearly better location, use it and explain in the summary.

### Required behavior

The helper should:

```text
read env.capacity_weekly_rows if present
skip safely if env.capacity_weekly_rows is missing
if rows are present, call attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows)
call build_capacity_runtime_attachment_diagnostic(env)
return structured result
append diagnostic messages to messages list if provided
```

---

## 5. Explicit Non-Scope

Do not implement:

```text
GUI preflight wiring
Explicit KPI preflight wiring
scenario runner wiring
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
data CSV changes
sample CSV changes
scenario package loading
capacity master CSV loading
week-key normalization
calendar conversion
capacity applicability status
Management Cockpit layout changes
```

This request is helper + focused tests only.

---

## 6. Input Contract

Input:

```text
env: any Python object supporting attribute access
messages: optional list[str]
```

Tests may use:

```python
from types import SimpleNamespace

env = SimpleNamespace()
messages = []
```

The helper should look for:

```text
env.capacity_weekly_rows
```

If present, it should be treated as:

```python
list[WeeklyCapacityRow]
```

Do not load rows from CSV in this request.

Do not create rows from scenario yaml in this request.

---

## 7. Output Contract

The helper should return a dictionary.

Recommended structure when rows are present:

```python
{
    "applied": True,
    "reason": None,
    "row_source": "env.capacity_weekly_rows",
    "input_row_count": 2,
    "attachment_summary": {...},
    "runtime_attachment": {...},
    "messages": [...],
}
```

Recommended structure when rows are missing:

```python
{
    "applied": False,
    "reason": "capacity_weekly_rows_missing",
    "row_source": "missing",
    "input_row_count": 0,
    "attachment_summary": None,
    "runtime_attachment": {
        "available": False,
        "summary_available": False,
        "reason": "missing_capacity_runtime_attachment_summary",
        ...
    },
    "messages": [
        "Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.",
        ...
    ],
}
```

Recommended structure when rows exist but are empty:

```python
{
    "applied": True,
    "reason": None,
    "row_source": "env.capacity_weekly_rows",
    "input_row_count": 0,
    "attachment_summary": {
        "available": False,
        "input_row_count": 0,
        ...
    },
    "runtime_attachment": {...},
    "messages": [...],
}
```

---

## 8. Skip Policy

If `env.capacity_weekly_rows` is missing:

```text
do not call attach_capacity_runtime_contexts_to_env_from_weekly_rows
do call build_capacity_runtime_attachment_diagnostic(env)
return applied=False
reason="capacity_weekly_rows_missing"
append skip message
```

Recommended skip message:

```text
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

This is not an error.

It means no canonical capacity row source is available in env.

---

## 9. Empty Rows Policy

If `env.capacity_weekly_rows` exists but is an empty list:

```text
call attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, [])
return applied=True
attach empty runtime contexts
runtime attachment summary should report available=False and input_row_count=0
```

This is different from missing rows.

```text
missing rows:
    no capacity row source exists

empty rows:
    a capacity row source exists but contains no rows
```

The test suite should cover both cases.

---

## 10. Message Policy

The helper should build a result-level message list.

It should also append to an external `messages` list if provided.

Recommended behavior:

```python
local_messages = []
...
if messages is not None:
    messages.extend(local_messages)
return {"messages": local_messages, ...}
```

Messages should include runtime attachment diagnostic messages.

When skipped, include:

```text
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

When applied, runtime attachment diagnostic messages should appear, such as:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical side context attached.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment: week keys preserved.
```

Do not change GUI message formatting in this request.

---

## 11. Idempotency Policy

The helper may be called multiple times.

Recommended behavior:

```text
Repeated calls rebuild/replace derived env attributes deterministically.
Repeated calls should not raise exceptions.
```

The helper should not append messages to a persistent env-level message list unless explicitly passed by the caller.

The caller owns duplicate message handling.

---

## 12. Attachment Strategy

When rows are present, call:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows)
```

This should attach:

```text
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
env.capacity_weekly_rows
env.capacity_runtime_attachment_summary
```

The preflight helper should not directly construct contexts itself.

It should delegate to the existing attach helper.

---

## 13. Runtime Attachment Diagnostic Strategy

After attach or skip, call:

```python
build_capacity_runtime_attachment_diagnostic(env)
```

The result should be included in:

```text
result["runtime_attachment"]
```

If the diagnostic returns messages, include them in the result-level messages and external messages list.

---

## 14. Backward Attribute Safety

The helper must preserve the existing safe backward strategy:

```text
attach canonical product-first backward context to:
  env.explicit_pipeline_backward_weekly_capability_from_weekly_rows

do not replace:
  env.explicit_pipeline_backward_weekly_capability
```

Do not wire canonical backward context into planner-facing consumer behavior.

Do not change consumer-facing backward shape.

---

## 15. Week Key Policy

Do not normalize week keys.

Do not convert:

```text
business week label -> integer index
integer index -> business week label
```

The helper delegates to existing attach and diagnostic helpers, which preserve week keys and report:

```text
week_key_domain = "preserve"
```

No calendar conversion should be added.

---

## 16. Suggested Tests

Add focused tests:

```text
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

Use:

```python
types.SimpleNamespace
WeeklyCapacityRow
```

### 16.1 Skips when rows missing

Given env without `capacity_weekly_rows`, assert:

```text
result["applied"] is False
result["reason"] == "capacity_weekly_rows_missing"
result["row_source"] == "missing"
result["runtime_attachment"]["available"] is False
skip message is present
env.explicit_pipeline_forward_weekly_capacity does not exist
```

### 16.2 Applies when rows exist

Given env with non-empty `capacity_weekly_rows`, assert:

```text
result["applied"] is True
result["row_source"] == "env.capacity_weekly_rows"
env.explicit_pipeline_forward_weekly_capacity exists
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows exists
env.capacity_runtime_attachment_summary exists
result["runtime_attachment"]["summary_available"] is True
messages include summary available
```

### 16.3 Empty rows

Given:

```python
env.capacity_weekly_rows = []
```

Assert:

```text
result["applied"] is True
result["input_row_count"] == 0
env.explicit_pipeline_forward_weekly_capacity == {}
runtime attachment summary reports available=False
messages mention no WeeklyCapacityRow rows
```

### 16.4 External messages list

Pass:

```python
messages = []
```

Assert:

```text
messages are appended
messages == result["messages"] or contain result messages
```

### 16.5 Idempotency

Call helper twice with the same env.

Assert:

```text
both calls applied successfully
env contexts are deterministic
no exception occurs
```

### 16.6 No planner / GUI dependency

The test should not import:

```text
pysi.gui.*
weekly_forward_push_with_capacity
capacity_aware_inbound_backward
explicit_bridge_capacity_pipeline
```

---

## 17. Test Commands

Run focused test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

Run related diagnostic / attachment tests:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
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
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

Possibly changed only if necessary:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Do not wire into GUI or scenario runner in this request.

---

## 19. Acceptance Criteria

This request is complete when:

```text
apply_capacity_runtime_attachment_preflight or equivalent helper exists
the helper skips safely when env.capacity_weekly_rows is missing
the helper applies attach helper when env.capacity_weekly_rows exists
the helper handles empty row list deterministically
the helper builds runtime attachment diagnostic after attach or skip
the helper returns structured result
the helper appends messages to supplied external list
the helper is idempotent enough for repeated calls
focused tests pass
related diagnostic / attachment tests pass
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
no scenario package loading is added
no preflight GUI wiring is added
```

---

## 20. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is apply_capacity_runtime_attachment_preflight implemented?
What does it do when env.capacity_weekly_rows is missing?
What does it do when env.capacity_weekly_rows is present?
Does it call attach_capacity_runtime_contexts_to_env_from_weekly_rows?
Does it call build_capacity_runtime_attachment_diagnostic?
Does it append messages to an external list?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSVs?
Did you wire this into GUI or scenario runner preflight?
Which tests passed?
```

---

## 21. Development Meaning

This request adds a preflight-safe route inspection step.

Already completed:

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

This request adds:

```text
preflight helper
    ↓
safe env attachment
    ↓
diagnostic explanation
```

Do not run the planner train yet.

Do not wire the route inspection into GUI yet.

Just implement the route inspection helper.
