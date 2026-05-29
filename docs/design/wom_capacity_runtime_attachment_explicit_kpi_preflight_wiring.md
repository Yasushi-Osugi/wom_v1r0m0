# WOM Capacity Runtime Attachment Explicit KPI Preflight Wiring

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
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
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md
```

---

## 1. Purpose

This memo defines how the capacity runtime attachment preflight helper should be wired into the existing Explicit KPI preflight flow.

The completed helper path is:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
preflight result / messages
```

This memo designs the next controlled step:

```text
Explicit KPI preflight
    ↓
capacity runtime attachment preflight helper
    ↓
existing capacity scenario alignment diagnostic
    ↓
Explicit KPI messages / diagnostics
```

This memo is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Wire capacity runtime attachment into Explicit KPI preflight only as a diagnostic-safe preparation step.
```

This means:

```text
OK:
  call apply_capacity_runtime_attachment_preflight(...)
  attach capacity runtime contexts to env when capacity_weekly_rows already exists
  build runtime attachment diagnostic
  append diagnostic messages to existing preflight/message flow
  keep safe skip behavior when rows are missing

Not OK:
  load capacity_master.csv here
  alter planner execution
  alter capacity enforcement
  alter blocked lot behavior
  convert week keys silently
  change GUI layout
  replace consumer-facing backward capability context
```

The goal is to make capacity runtime attachment visible in the Explicit KPI flow without making the planner behave differently.

---

## 3. Current Completed State

### 3.1 Canonical capacity loader

Implemented:

```text
capacity_master.csv -> WeeklyCapacityRow
```

Key commit:

```text
31d6d8e Add canonical capacity master loader
```

### 3.2 Forward runtime context adapter

Implemented:

```text
WeeklyCapacityRow -> explicit forward capacity context
```

Key commit:

```text
3a933fd Add weekly capacity row forward context adapter
```

### 3.3 Backward runtime context adapter

Implemented:

```text
WeeklyCapacityRow -> explicit backward capability context
```

Key commit:

```text
1ee4008 Add weekly capacity backward context adapter
```

### 3.4 Runtime env attach helper

Implemented:

```text
WeeklyCapacityRow-derived contexts -> env attach helper
```

Key commit:

```text
d8a8a36 Add weekly capacity runtime env attach helper
```

### 3.5 Runtime attachment diagnostic

Implemented:

```text
env.capacity_runtime_attachment_summary -> diagnostic["runtime_attachment"]
```

Key commit:

```text
45477fc Add capacity runtime attachment diagnostic
```

### 3.6 Generic preflight helper

Implemented:

```text
env.capacity_weekly_rows -> apply_capacity_runtime_attachment_preflight(...)
```

Key commit:

```text
258eb31 Add capacity runtime attachment preflight helper
```

### 3.7 Still not wired

Not yet implemented:

```text
Explicit KPI preflight wiring
GUI message surfacing change
scenario package loading
run_wom_scenario integration
planner consumption of canonical backward side context
```

This memo focuses only on how to wire the helper into Explicit KPI preflight safely.

---

## 4. Problem to Solve

The generic helper exists:

```python
apply_capacity_runtime_attachment_preflight(env, messages=...)
```

But the existing Explicit KPI preflight flow does not yet call it.

The problem to solve is:

```text
Where should apply_capacity_runtime_attachment_preflight(...) be called in the current Explicit KPI preflight flow,
and how should its messages and diagnostic result be handled,
without changing planner behavior or GUI layout?
```

The design must decide:

```text
1. call order
2. row-source assumptions
3. skip behavior
4. interaction with existing capacity context attach
5. interaction with existing capacity scenario alignment diagnostic
6. message propagation
7. safety boundaries
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
capacity_master.csv loading from GUI
week-key normalization
calendar conversion
optimization logic
replacement of existing backward consumer-facing capability shape
new capacity applicability enforcement
```

The design is limited to Explicit KPI preflight wiring.

---

## 6. Existing Explicit KPI Preflight Context

Earlier work already attached capacity scenario alignment diagnostics into the Explicit KPI flow.

Known existing flow conceptually includes:

```text
Explicit KPI demo flags / setup
backward / forward capacity context attachment
capacity scenario alignment diagnostic
ctx guard check
Explicit KPI view-model messages
```

The earlier completion note stated that the capacity scenario alignment diagnostic was attached:

```text
after backward / forward capacity context attachment
before ctx guard evaluation
```

This ordering should be preserved unless there is a strong reason to change it.

The new capacity runtime attachment preflight should fit into this area.

---

## 7. Recommended Call Order

Recommended order for Explicit KPI preflight:

```text
1. Existing Explicit KPI demo flag setup
2. Existing backward / forward capacity context setup, if any
3. New capacity runtime attachment preflight
4. Existing capacity scenario alignment diagnostic
5. Existing ctx guard check
6. Existing Explicit KPI view-model / message construction
```

In more concrete terms:

```text
Existing preflight prepares env
    ↓
apply_capacity_runtime_attachment_preflight(env, messages=preflight_messages)
    ↓
capacity scenario alignment diagnostic sees runtime_attachment
    ↓
diagnostic messages are available to Explicit KPI view-model
```

The key point:

```text
Run capacity runtime attachment preflight before capacity scenario alignment diagnostic.
```

Reason:

```text
The scenario alignment diagnostic now knows how to read runtime_attachment information.
It needs env.capacity_runtime_attachment_summary to be available before diagnostic construction.
```

---

## 8. Row Source Policy

The first Explicit KPI preflight wiring must not load files.

It should only use:

```text
env.capacity_weekly_rows
```

If `env.capacity_weekly_rows` exists:

```text
call apply_capacity_runtime_attachment_preflight(...)
```

If it does not exist:

```text
call apply_capacity_runtime_attachment_preflight(...)
and allow it to skip safely
```

This means the explicit KPI preflight wiring can be simple:

```python
capacity_preflight_result = apply_capacity_runtime_attachment_preflight(
    env,
    messages=preflight_messages,
)
env.capacity_runtime_attachment_preflight_result = capacity_preflight_result
```

The helper itself already handles missing rows safely.

---

## 9. Should the Helper Be Called Even When Rows Are Missing?

Recommendation:

```text
Yes.
```

Reason:

```text
Calling the helper even when rows are missing gives a deterministic diagnostic result.
It records that capacity runtime attachment preflight was skipped because env.capacity_weekly_rows was missing.
```

This is better than silently doing nothing.

The result can explain:

```text
capacity_weekly_rows missing
runtime attachment summary missing
capacity runtime attachment preflight skipped
```

This is useful for demos and debugging.

---

## 10. Env Attribute for Preflight Result

Recommended env attribute:

```text
env.capacity_runtime_attachment_preflight_result
```

This should store the result returned by:

```python
apply_capacity_runtime_attachment_preflight(...)
```

Example:

```python
{
    "applied": True,
    "reason": None,
    "row_source": "env.capacity_weekly_rows",
    "input_row_count": 52,
    "attachment_summary": {...},
    "runtime_attachment": {...},
    "messages": [...],
}
```

If skipped:

```python
{
    "applied": False,
    "reason": "capacity_weekly_rows_missing",
    "row_source": "missing",
    "input_row_count": 0,
    "attachment_summary": None,
    "runtime_attachment": {...},
    "messages": [...],
}
```

This attribute is diagnostic-only.

It must not be consumed by planner behavior in this phase.

---

## 11. Message Propagation Policy

The helper accepts:

```python
messages: list[str] | None
```

Recommended Explicit KPI wiring:

```text
pass the existing preflight / diagnostic message list if one exists
otherwise create a local list and attach it to env or diagnostic payload if appropriate
```

The messages should remain plain strings.

Do not change GUI layout.

Do not invent rich UI rendering.

The messages may later appear in Explicit KPI View via the existing diagnostic message path.

Recommended prefix behavior:

```text
Do not add another prefix inside the wiring function.
Let existing message strings remain:
  Capacity runtime attachment: ...
  Capacity runtime attachment preflight: ...
```

If the existing Explicit KPI view already prefixes diagnostic messages with:

```text
Capacity scenario alignment:
```

do not double-prefix.

---

## 12. Interaction with Existing Scenario Alignment Diagnostic

The existing scenario alignment diagnostic now includes:

```text
runtime_attachment
```

Therefore, recommended flow is:

```text
1. apply_capacity_runtime_attachment_preflight(...)
2. build / attach existing capacity scenario alignment diagnostic
```

The scenario alignment diagnostic should then include:

```text
diagnostic["runtime_attachment"]
```

and runtime attachment messages.

Avoid separately building another runtime attachment diagnostic and displaying it independently unless necessary.

The explicit KPI preflight should aim for one coherent diagnostic object.

---

## 13. Backward Context Safety

The env attach helper uses the safe canonical side attribute:

```text
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

It does not replace:

```text
env.explicit_pipeline_backward_weekly_capability
```

Explicit KPI preflight wiring must preserve this safety rule.

It must not connect the canonical product-first backward context to planner-facing consumer behavior.

The diagnostic should continue to report:

```text
Capacity runtime attachment: backward consumer-facing capability was not replaced.
```

This is expected and safe.

---

## 14. Week Key Policy

Explicit KPI preflight wiring must not normalize week keys.

It should not convert:

```text
2027-W40 -> integer index
integer index -> business week label
```

It should rely on existing helpers, which preserve week keys and report:

```text
week_key_domain = preserve
```

Any future week-domain conversion should be designed as a separate adapter-boundary phase.

---

## 15. Idempotency and Repeated GUI Actions

Explicit KPI preflight may be triggered repeatedly by GUI actions.

Therefore, wiring should be idempotent enough:

```text
Repeated calls should rebuild/replace derived capacity runtime attributes deterministically.
Repeated calls should not accumulate duplicated persistent env messages.
Repeated calls should not mutate source rows.
```

If a message list is constructed per preflight call, duplicate accumulation is not a problem.

If messages are stored on env, caller must clear or rebuild them per preflight.

Recommendation:

```text
Do not append directly to persistent env message list in the first implementation.
Pass a local messages list used by current preflight only.
```

---

## 16. Error Handling Policy

If `apply_capacity_runtime_attachment_preflight(...)` raises unexpectedly:

Recommended wrapper behavior in Explicit KPI preflight:

```text
catch exception
attach safe unavailable result to env.capacity_runtime_attachment_preflight_result
append warning message
continue existing preflight if safe
```

However, the first implementation may not need a broad catch if tests cover normal paths.

Future robust version may include safe wrapper.

Near-term recommendation:

```text
Use direct helper call and focused tests.
Avoid broad try/except unless existing preflight style uses it.
```

---

## 17. Proposed Implementation Location

Likely existing GUI/preflight file:

```text
pysi/gui/cockpit_tk.py
```

Possible function or method:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

or the current explicit KPI preflight helper area.

However, to avoid GUI layout changes, implementation should be minimal:

```text
import apply_capacity_runtime_attachment_preflight
call it in the existing preflight method
store result on env
pass/append messages through existing message list
```

Potential changed files for future implementation:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Possibly:

```text
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Do not change view layout files unless needed.

---

## 18. Suggested Pseudocode

Conceptual pseudocode:

```python
from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    apply_capacity_runtime_attachment_preflight,
)

def _maybe_apply_explicit_kpi_demo_flags(...):
    ...
    preflight_messages = []

    # existing capacity context attachment, if any
    ...

    capacity_runtime_result = apply_capacity_runtime_attachment_preflight(
        env,
        messages=preflight_messages,
    )
    env.capacity_runtime_attachment_preflight_result = capacity_runtime_result

    # existing capacity scenario alignment diagnostic
    ...

    # existing ctx guard check
    ...
```

If there is already an existing messages list, use that instead of creating a new one.

If messages are later merged into view-model messages through the diagnostic builder, avoid appending duplicates.

---

## 19. Suggested Tests

Add or extend focused tests.

Likely file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

or new test file:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

### 19.1 Preflight calls helper when rows exist

Given a minimal cockpit/env setup with:

```text
env.capacity_weekly_rows
```

assert after Explicit KPI preflight:

```text
env.capacity_runtime_attachment_preflight_result exists
env.explicit_pipeline_forward_weekly_capacity exists
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows exists
env.capacity_runtime_attachment_summary exists
```

### 19.2 Preflight skips safely when rows missing

Given env without `capacity_weekly_rows`, assert:

```text
env.capacity_runtime_attachment_preflight_result exists
result["applied"] == False
result["reason"] == "capacity_weekly_rows_missing"
```

### 19.3 Runtime attachment diagnostic appears in scenario alignment diagnostic

Assert the final capacity scenario alignment diagnostic includes:

```text
runtime_attachment
```

### 19.4 Message propagation

Assert messages include one of:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

Depending on whether rows are present.

### 19.5 No planner behavior change

Test should not require plan result changes.

### 19.6 No GUI layout change

Test should not assert layout changes.

---

## 20. Test Commands for Future Codex Request

Focused GUI/preflight wiring test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

or if modifying existing file:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
python -m pytest tests/test_wom_capacity_weekly_rows_runtime_env_attach.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Optional capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

---

## 21. Safety Boundaries for Future Implementation

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
data/*.csv
```

Avoid modifying unless required:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Expected changed files:

```text
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

or:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Do not change planner behavior.

Do not change data CSV files.

Do not load capacity_master.csv here.

---

## 22. Acceptance Criteria for Future Implementation

The Explicit KPI preflight wiring is complete when:

```text
apply_capacity_runtime_attachment_preflight(...) is called during Explicit KPI preflight
env.capacity_runtime_attachment_preflight_result is attached
rows-present case attaches forward context
rows-present case attaches backward canonical side context
rows-missing case skips safely
runtime_attachment diagnostic remains available
messages propagate without GUI layout changes
no planner behavior changes are made
no data CSV files are changed
no scenario package loading is added
focused tests pass
related GUI/preflight/diagnostic tests pass
```

---

## 23. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_request.md
```

Scope:

```text
wire apply_capacity_runtime_attachment_preflight into Explicit KPI preflight
attach result to env.capacity_runtime_attachment_preflight_result
focused tests
no planner changes
no GUI layout changes
no data CSV changes
no capacity master loading
```

---

## 24. Development Meaning

Before this phase, WOM has:

```text
capacity runtime preflight helper
```

but it is not yet part of the Explicit KPI preflight route.

This design prepares the next step:

```text
Explicit KPI preflight
    ↓
capacity runtime attachment preflight
    ↓
runtime attachment diagnostic
```

This is where capacity context begins to become visible in the actual Explicit KPI operation path.

In short:

```text
The route inspection helper exists.
This memo designs where it is inserted into the actual preflight route.
```

---

## 25. Summary

This memo designs the Explicit KPI preflight wiring for:

```text
apply_capacity_runtime_attachment_preflight(...)
```

The first implementation should:

```text
call helper during Explicit KPI preflight
store result on env
allow safe skip when rows are missing
attach contexts when rows are present
preserve existing diagnostic flow
avoid GUI layout changes
avoid planner changes
avoid data changes
avoid capacity master loading
```

Recommended next request:

```text
docs/codex_requests/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_request.md
```
