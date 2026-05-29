# WOM Capacity Runtime Attachment Preflight Wiring

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_runtime_attachment_preflight_wiring.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_runtime_attachment_diagnostic_integration.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
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

This memo defines how WOM should safely wire capacity runtime attachment and runtime attachment diagnostics into a preflight flow.

The completed capacity path is now:

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

This memo designs the next controlled step:

```text
preflight
    ↓
if WeeklyCapacityRow rows are already available
    ↓
attach capacity runtime contexts to env
    ↓
build runtime attachment diagnostic
    ↓
make diagnostic messages visible to existing diagnostic flow
```

This memo is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Preflight may prepare and diagnose capacity context,
but must not change planner behavior.
```

Preflight wiring should be:

```text
safe
diagnostic-visible
side-effect limited to env attributes
idempotent enough for repeated preflight
planner-neutral
GUI-layout-neutral
data-file-neutral
```

This means:

```text
OK:
  attach runtime capacity contexts to env
  attach runtime attachment summary
  build diagnostics
  append diagnostic messages

Not OK:
  run planner
  change capacity enforcement
  alter blocked lot behavior
  normalize week keys silently
  modify data CSV files
  change GUI layout
```

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
WeeklyCapacityRow-derived contexts -> env attach helper
```

Implementation commit:

```text
d8a8a36 Add weekly capacity runtime env attach helper
```

### 3.5 Runtime attachment diagnostic completed

```text
env.capacity_runtime_attachment_summary -> diagnostic["runtime_attachment"]
```

Implementation commit:

```text
45477fc Add capacity runtime attachment diagnostic
```

### 3.6 What remains

Not yet implemented:

```text
preflight wiring
scenario package loading
capacity rows source discovery
GUI message surfacing changes
planner consumption of canonical backward context
```

This memo focuses only on preflight wiring.

---

## 4. Problem to Solve

WOM can now:

```text
load capacity rows
convert rows to runtime contexts
attach contexts to env
diagnose attachment state
```

But these pieces are not yet connected to any preflight flow.

The problem to solve is:

```text
When an env already has canonical WeeklyCapacityRow rows,
how should preflight call the env attach helper and diagnostic helper
without changing planning behavior?
```

The preflight wiring should answer:

```text
Are capacity rows present?
Were runtime contexts attached?
Was runtime attachment summary created?
Was runtime attachment diagnostic created?
Were messages appended to existing diagnostic messages?
Was anything skipped safely?
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
week-key normalization
calendar conversion
optimization logic
replacement of existing backward consumer-facing capability shape
new capacity applicability status enforcement
```

The design is limited to safe preflight invocation.

---

## 6. Preflight Entry Points

Potential preflight entry points include:

```text
Explicit KPI demo preflight
scenario runner preflight
future run_wom_scenario preflight
test-only preflight helper
```

Near-term recommendation:

```text
Start with a helper-level preflight function.
Do not immediately wire into GUI or scenario runner.
```

Recommended helper name:

```python
apply_capacity_runtime_attachment_preflight(env, *, messages: list[str] | None = None) -> dict
```

or:

```python
maybe_attach_capacity_runtime_contexts_during_preflight(env) -> dict
```

The helper should be pure-ish:

```text
read env.capacity_weekly_rows if present
call attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
call build_capacity_runtime_attachment_diagnostic(env)
attach / return summary
append messages to supplied list if provided
```

The first implementation should avoid direct GUI dependency.

---

## 7. Capacity Row Source Policy

The first preflight wiring should only use already-available rows.

Primary source:

```text
env.capacity_weekly_rows
```

Do not load CSV files in this first preflight wiring.

Do not read scenario yaml in this first preflight wiring.

If `env.capacity_weekly_rows` is missing:

```text
skip runtime attach
build diagnostic that summary is missing or attach a skip summary
return skipped status
```

Recommended first implementation:

```text
If env.capacity_weekly_rows exists:
    attach runtime contexts and build diagnostic.
Else:
    do not attach runtime contexts.
    return skipped summary.
```

This keeps scenario loading separate.

---

## 8. Proposed Preflight Flow

Recommended flow:

```text
1. Preflight begins.
2. Check whether env.capacity_weekly_rows exists.
3. If rows exist:
      call attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows)
4. Call build_capacity_runtime_attachment_diagnostic(env)
5. Attach or return diagnostic payload.
6. Append runtime attachment messages to existing diagnostic/preflight message list.
7. Continue existing preflight flow.
```

In pseudocode:

```python
def apply_capacity_runtime_attachment_preflight(env, messages=None):
    rows = getattr(env, "capacity_weekly_rows", None)

    if rows is None:
        diagnostic = build_capacity_runtime_attachment_diagnostic(env)
        if messages is not None:
            messages.extend(diagnostic.get("messages", []))
        return {
            "applied": False,
            "reason": "capacity_weekly_rows_missing",
            "runtime_attachment": diagnostic,
        }

    attach_summary = attach_capacity_runtime_contexts_to_env_from_weekly_rows(env, rows)
    diagnostic = build_capacity_runtime_attachment_diagnostic(env)

    if messages is not None:
        messages.extend(diagnostic.get("messages", []))

    return {
        "applied": True,
        "attachment_summary": attach_summary,
        "runtime_attachment": diagnostic,
    }
```

---

## 9. Ordering in Existing Explicit KPI Preflight

If this is later wired into the existing Explicit KPI flow, the recommended order is:

```text
1. Existing scenario / demo flag setup
2. Existing backward / forward capacity context attachment, if any
3. Canonical capacity runtime attachment preflight, if capacity_weekly_rows exists
4. Capacity scenario alignment diagnostic
5. Existing ctx guard check
6. Existing view-model / message construction
```

However, the first implementation request should avoid changing GUI preflight.

Near-term implementation should only create the preflight helper and focused tests.

---

## 10. Message Policy

The preflight helper should not invent a new GUI message format.

It should collect diagnostic messages.

Example messages:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment: WeeklyCapacityRow count = N.
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical side context attached.
Capacity runtime attachment: backward consumer-facing capability was not replaced.
Capacity runtime attachment: week keys preserved.
Capacity runtime attachment: summary missing.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

If these messages are later surfaced in Explicit KPI View, they may use an existing prefix such as:

```text
Capacity scenario alignment:
```

or a new prefix such as:

```text
Capacity runtime attachment:
```

The first implementation should not change GUI rendering.

---

## 11. Skip Policy

If no capacity rows are present:

```text
env.capacity_weekly_rows missing
```

the helper should not fail.

Recommended return:

```python
{
    "applied": False,
    "reason": "capacity_weekly_rows_missing",
    "messages": [
        "Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing."
    ],
    "runtime_attachment": {
        "available": False,
        "summary_available": False,
        "reason": "missing_capacity_runtime_attachment_summary",
        ...
    },
}
```

If rows are present but empty:

```text
env.capacity_weekly_rows = []
```

then the helper may call the attach helper and return `applied=True` with `available=False` in the attachment summary.

This distinction matters:

```text
missing rows attribute:
    no source was provided

empty rows list:
    source was provided but contained no rows
```

---

## 12. Idempotency Policy

The preflight helper may be called multiple times.

Recommended behavior:

```text
Repeated calls rebuild and replace derived env attributes deterministically.
```

It should not append duplicate messages to persistent env state unless explicitly controlled.

If `messages` list is passed in, the caller owns duplicate handling.

The helper itself should return messages in its result.

---

## 13. Backward Attribute Safety

The env attach helper currently uses safe canonical side attribute:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

and does not replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

Preflight wiring must preserve this safety rule.

It must not connect the canonical product-first backward context to a planner-facing consumer attribute unless a separate compatibility design and test exists.

---

## 14. Relationship to Existing Scenario Alignment Diagnostic

The scenario alignment diagnostic should remain the main diagnostic payload.

Preflight wiring should either:

```text
1. add runtime_attachment into the existing diagnostic builder, or
2. call build_capacity_runtime_attachment_diagnostic separately and pass messages along.
```

Since runtime attachment diagnostic integration is already completed, the recommended path is:

```text
call existing scenario alignment diagnostic after env attachment
```

so that:

```text
diagnostic["runtime_attachment"]
```

is included in the final diagnostic.

---

## 15. Relationship to GUI Message Surfacing

This design does not change GUI layout.

It only prepares messages that can later be surfaced.

Future GUI surfacing may show:

```text
Capacity runtime attachment: forward context attached.
Capacity runtime attachment: backward canonical side context attached.
```

But the first preflight wiring implementation should avoid changing:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

unless explicitly requested later.

---

## 16. Suggested Implementation Function

Preferred location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

or:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommendation:

```text
Place preflight helper in pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
if it is primarily diagnostic/preflight oriented.

Place it in pysi/plan/explicit_pipeline_capacity_context.py
if it is primarily context-attachment oriented.
```

Near-term recommendation:

```text
Use pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

because this helper will coordinate diagnostic messages and not change planning behavior.

Possible function:

```python
apply_capacity_runtime_attachment_preflight(env, *, messages: list[str] | None = None) -> dict
```

---

## 17. Suggested Tests

Create focused tests:

```text
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

### 17.1 Skips when rows missing

Given env without:

```text
capacity_weekly_rows
```

assert:

```text
result["applied"] == False
result["reason"] == "capacity_weekly_rows_missing"
messages include skipped
no forward context attached
```

### 17.2 Applies when rows exist

Given env with `capacity_weekly_rows`, assert:

```text
result["applied"] == True
env.explicit_pipeline_forward_weekly_capacity exists
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows exists
env.capacity_runtime_attachment_summary exists
result["runtime_attachment"]["summary_available"] == True
```

### 17.3 Empty rows

Given:

```text
env.capacity_weekly_rows = []
```

assert:

```text
result["applied"] == True
env.explicit_pipeline_forward_weekly_capacity == {}
runtime_attachment reports no rows / available False
```

### 17.4 Messages list

Pass an external messages list.

Assert runtime attachment diagnostic messages are appended.

### 17.5 Idempotency

Call helper twice.

Assert contexts remain deterministic and no exception occurs.

### 17.6 No GUI / planner imports

Test should not import GUI modules or planner execution modules.

---

## 18. Test Commands for Future Codex Request

Focused test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
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

## 19. Safety Boundaries for Future Implementation

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

Possibly changed only if placement is chosen there:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Do not wire into GUI or scenario runner in the first implementation request.

---

## 20. Acceptance Criteria for Future Implementation

The preflight wiring helper is complete when:

```text
apply_capacity_runtime_attachment_preflight or equivalent helper exists
it skips safely when env.capacity_weekly_rows is missing
it attaches runtime capacity contexts when env.capacity_weekly_rows exists
it builds runtime attachment diagnostic after attachment
it returns structured result
it appends messages to supplied list when provided
empty rows are handled deterministically
repeated calls are safe
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
no scenario package loading is added
```

---

## 21. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_runtime_attachment_preflight_wiring_request.md
```

Scope:

```text
apply_capacity_runtime_attachment_preflight helper
focused tests
no GUI changes
no planner changes
no data CSV changes
no scenario package loading
```

---

## 22. Development Meaning

Before this phase, WOM has:

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

The preflight wiring phase will add:

```text
preflight
    ↓
safe runtime capacity attachment
    ↓
diagnostic explanation
```

This means WOM will begin to behave like a self-checking planning environment.

The capacity path will no longer be only code that can be called.

It will become a preflight-visible context route.

In short:

```text
The signal system exists.
This memo designs the route inspection before the train departs.
```

---

## 23. Summary

This memo designs preflight wiring for:

```text
env.capacity_weekly_rows
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
preflight result and messages
```

The first implementation should remain safe and narrow:

```text
helper only
focused tests
no planner changes
no GUI changes
no data changes
no scenario loading
```

Recommended next request:

```text
docs/codex_requests/wom_capacity_runtime_attachment_preflight_wiring_request.md
```
