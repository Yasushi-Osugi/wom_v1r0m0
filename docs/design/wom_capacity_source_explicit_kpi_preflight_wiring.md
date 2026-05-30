# WOM Capacity Source Explicit KPI Preflight Wiring

**Version:** v0r1 draft  
**Date:** 2026-05-30  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md`

**Parent / related design docs:**

```text
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
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
```

---

## 1. Purpose

This memo defines how the completed capacity source helper should be connected to the existing Explicit KPI preflight flow.

The completed source helper is:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

The completed Explicit KPI runtime path is:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)
    ↓
build_capacity_runtime_attachment_diagnostic(env)
    ↓
Explicit KPI preflight diagnostic visibility
```

This memo designs the next source-side wiring step:

```text
Explicit KPI preflight
    ↓
load capacity source into env.capacity_weekly_rows, if source is available
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
capacity scenario alignment diagnostic
```

This is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Explicit KPI preflight may load canonical capacity rows when a known capacity source exists,
but must not change planner behavior or capacity enforcement.
```

This means:

```text
OK:
  call load_capacity_weekly_rows_to_env(...)
  attach env.capacity_weekly_rows
  attach env.capacity_weekly_rows_load_summary
  then let existing runtime attachment preflight consume env.capacity_weekly_rows
  report source loading messages / diagnostics

Not OK:
  run planner
  change capacity enforcement
  change blocked lot behavior
  alter runtime planner context manually
  bypass WeeklyCapacityRow
  silently normalize week keys
  change GUI layout
  alter data CSV files
```

The source helper should only load canonical rows.

The runtime attachment helper should remain responsible for runtime context attachment.

The diagnostic layer should remain responsible for explanation.

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

### 3.2 Source helper

Implemented:

```text
capacity source -> env.capacity_weekly_rows
```

Function:

```python
load_capacity_weekly_rows_to_env(...)
```

Location:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

Key commit:

```text
8886c03 Add capacity weekly rows env source helper
```

### 3.3 Runtime attachment preflight

Implemented:

```text
env.capacity_weekly_rows -> apply_capacity_runtime_attachment_preflight(...)
```

Key commit:

```text
258eb31 Add capacity runtime attachment preflight helper
```

### 3.4 Explicit KPI runtime preflight wiring

Implemented:

```text
Explicit KPI preflight -> apply_capacity_runtime_attachment_preflight(...)
```

Key commit:

```text
f480156 Wire capacity runtime preflight into explicit KPI
```

### 3.5 Remaining gap

The current gap is:

```text
Explicit KPI preflight does not yet call load_capacity_weekly_rows_to_env(...)
```

Therefore, the runtime attachment preflight can consume capacity rows only when they were already attached to env by tests or external setup.

This memo defines how to wire the source helper into the Explicit KPI preflight path.

---

## 4. Problem to Solve

The Explicit KPI preflight currently handles:

```text
env.capacity_weekly_rows
```

but does not yet populate it from a source.

The problem to solve is:

```text
Where should load_capacity_weekly_rows_to_env(...) be called,
what source path should it use,
and how should missing source be handled,
without changing planner behavior?
```

The wiring should answer:

```text
1. What is the capacity source path?
2. Is loading optional or required?
3. Where is the load summary attached?
4. Does the runtime attachment preflight run after source loading?
5. How are source loading messages made visible?
6. How do missing capacity sources behave?
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
week-key normalization
calendar conversion
new optimization logic
replacement of existing backward consumer-facing capability shape
legacy PySI V0R8 adapter dispatch
full scenario package runner implementation
```

The design is limited to optional capacity source loading in the Explicit KPI preflight route.

---

## 6. Desired High-Level Flow

Recommended high-level flow:

```text
1. Existing Explicit KPI demo flag setup
2. Optional capacity source loading
3. Existing backward / forward capacity context setup, if any
4. Existing capacity runtime attachment preflight
5. Existing capacity scenario alignment diagnostic
6. Existing ctx guard check
7. Existing view-model / message construction
```

Expanded:

```text
Explicit KPI preflight
    ↓
load_capacity_weekly_rows_to_env(..., required=False)
    ↓
env.capacity_weekly_rows, if source exists
env.capacity_weekly_rows_load_summary, always
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_preflight_result
    ↓
capacity scenario alignment diagnostic
```

The key rule:

```text
load_capacity_weekly_rows_to_env(...) should run before apply_capacity_runtime_attachment_preflight(...).
```

---

## 7. Source Path Policy

The source helper supports:

```python
load_capacity_weekly_rows_to_env(
    env,
    *,
    capacity_master_path=None,
    scenario_root=None,
    scenario_config=None,
    required=False,
)
```

Explicit KPI wiring should use available env / GUI context to pass one or more of:

```text
capacity_master_path
scenario_root
scenario_config
```

### 7.1 Preferred source order

The source helper already implements deterministic resolution order:

```text
1. Explicit capacity_master_path argument
2. scenario_config["masters"]["capacity_master"] relative to scenario_root
3. scenario_root / "masters" / "capacity_master.csv"
4. scenario_root / "capacity_master.csv"
5. No source found
```

Explicit KPI wiring should not duplicate this logic.

It should only provide available arguments.

### 7.2 Where arguments may come from

Possible env / cockpit attributes may include:

```text
env.capacity_master_path
env.scenario_root
env.scenario_config
self.capacity_master_path
self.scenario_root
self.scenario_config
self.current_scenario_root
self.current_scenario_config
```

The implementation should inspect current code and use the least invasive existing source of path/config data.

Do not invent new GUI settings in this phase.

### 7.3 If no source context exists

If no source path or scenario root exists, still call the source helper only if doing so is useful and safe.

Recommended approach:

```text
call source helper with required=False if a scenario root or explicit capacity path is available
otherwise skip source loading and let runtime attachment preflight report env.capacity_weekly_rows missing
```

Alternative acceptable approach:

```text
call source helper with no source args and required=False
attach an unavailable load summary
then continue
```

The safer first implementation may be:

```text
call source helper only when at least one capacity source hint exists
```

This avoids creating new noise in existing demos that do not yet have a capacity source location.

---

## 8. Required vs Optional Loading

For Explicit KPI preflight, source loading should be optional:

```python
required=False
```

Reason:

```text
Explicit KPI demo should not fail just because a canonical capacity_master.csv is absent.
```

If the source is missing:

```text
source helper returns unavailable summary
or source loading is skipped
runtime attachment preflight can still safely skip
diagnostic explains missing rows
```

Strict required loading should be reserved for future scenario runner validation.

---

## 9. Env Attributes After Source Loading

When source file is loaded:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
env.capacity_weekly_rows_load_summary
```

When source is missing and helper is called with `required=False`:

```text
env.capacity_weekly_rows_load_summary
```

should be attached.

The Explicit KPI preflight may also attach:

```text
env.capacity_weekly_rows_source_preflight_result
```

or reuse:

```text
env.capacity_weekly_rows_load_summary
```

Recommendation:

```text
Do not introduce a second result attribute unless needed.
Use env.capacity_weekly_rows_load_summary as the source load result.
```

---

## 10. Interaction with Runtime Attachment Preflight

The existing runtime attachment preflight expects:

```text
env.capacity_weekly_rows
```

Therefore, the intended order is:

```text
load_capacity_weekly_rows_to_env(...)
    ↓
apply_capacity_runtime_attachment_preflight(...)
```

Behavior:

### 10.1 Source loaded with rows

```text
env.capacity_weekly_rows exists
runtime attachment preflight applied=True
runtime contexts attached
runtime_attachment diagnostic available
```

### 10.2 Source loaded but empty

```text
env.capacity_weekly_rows == []
runtime attachment preflight applied=True
runtime attachment summary available=False
diagnostic explains no WeeklyCapacityRow rows
```

### 10.3 Source missing

```text
env.capacity_weekly_rows absent
runtime attachment preflight applied=False
reason = capacity_weekly_rows_missing
diagnostic explains missing runtime attachment summary / skipped rows
```

---

## 11. Message Policy

Source loading messages should be preserved.

Examples:

```text
Capacity weekly rows source: loaded 52 rows from capacity_master.csv.
Capacity weekly rows source: no capacity master source found.
Capacity weekly rows source: loaded 0 rows from capacity_master.csv.
```

Runtime attachment messages should continue to be preserved.

Examples:

```text
Capacity runtime attachment: summary available.
Capacity runtime attachment preflight: skipped because env.capacity_weekly_rows is missing.
```

Recommended first implementation:

```text
append source load summary messages into the same local preflight_messages list
then pass that list to apply_capacity_runtime_attachment_preflight(...)
```

This provides a single preflight message chain.

Do not change GUI layout.

Do not add new widgets.

---

## 12. Diagnostic Visibility

The source load summary is not yet part of the scenario alignment diagnostic payload.

Near-term options:

### Option A: messages only

Append source messages to the preflight message list.

This is simplest.

### Option B: env summary only

Attach:

```text
env.capacity_weekly_rows_load_summary
```

and rely on future diagnostic integration.

### Recommendation

For first implementation:

```text
Use both message propagation and env.capacity_weekly_rows_load_summary.
Do not add a new diagnostic section yet.
```

Future work may add:

```text
diagnostic["capacity_weekly_rows_source"]
```

as a separate diagnostic section.

---

## 13. Idempotency Policy

Explicit KPI preflight may run repeatedly.

Source wiring should be safe under repeated calls.

Recommended behavior:

```text
Repeated source loading replaces env.capacity_weekly_rows deterministically.
Repeated source loading replaces env.capacity_weekly_rows_load_summary deterministically.
No source rows are mutated.
No persistent env messages are appended repeatedly unless existing flow does so.
```

If the same preflight call creates a local message list, duplicate accumulation is avoided.

---

## 14. Error Handling Policy

### 14.1 Missing source

Use:

```python
required=False
```

for Explicit KPI preflight.

Missing source should not crash.

### 14.2 Invalid source file

If a configured capacity master file exists but is invalid, allow `ValueError` to surface unless existing preflight style requires safe degradation.

Rationale:

```text
missing optional source is acceptable
malformed configured source is a real data error
```

If existing GUI preflight has safe warning wrappers, follow the existing style.

### 14.3 Broad exception handling

Do not hide errors unnecessarily.

If a broad catch is added, it should:

```text
attach an unavailable load summary
append a clear warning message
continue only if safe
```

Near-term recommendation:

```text
simple direct call with focused tests
```

---

## 15. Suggested Implementation Location

Likely file:

```text
pysi/gui/cockpit_tk.py
```

Likely method:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

or a new small helper:

```text
_maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight
```

Recommended helper:

```python
def _maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight(
    self,
    *,
    messages: list[str],
) -> dict | None:
    ...
```

This helper should:

```text
determine available source hints from self/env
call load_capacity_weekly_rows_to_env(..., required=False)
append summary messages
return summary
```

Then `_maybe_apply_explicit_kpi_demo_flags` calls it before:

```text
_maybe_apply_capacity_runtime_attachment_preflight
```

---

## 16. Suggested Pseudocode

Conceptual pseudocode:

```python
from pysi.capacity import load_capacity_weekly_rows_to_env

def _maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight(self, *, messages):
    capacity_master_path = getattr(self.env, "capacity_master_path", None)
    scenario_root = getattr(self.env, "scenario_root", None)
    scenario_config = getattr(self.env, "scenario_config", None)

    if not any([capacity_master_path, scenario_root, scenario_config]):
        return None

    summary = load_capacity_weekly_rows_to_env(
        self.env,
        capacity_master_path=capacity_master_path,
        scenario_root=scenario_root,
        scenario_config=scenario_config,
        required=False,
    )

    messages.extend(summary.get("messages", []))
    return summary
```

Call order:

```python
preflight_messages = []

self._maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight(
    messages=preflight_messages,
)

self._maybe_apply_capacity_runtime_attachment_preflight(
    messages=preflight_messages,
)
```

If there is already a preflight message list, use it.

Do not create persistent duplicate message accumulation.

---

## 17. Suggested Tests

Add a focused test file:

```text
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

or extend:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

### 17.1 Source path loads rows before runtime preflight

Given a test capacity_master.csv and env/cockpit with:

```text
env.capacity_master_path = path
```

Run Explicit KPI preflight.

Assert:

```text
env.capacity_weekly_rows exists
env.capacity_weekly_rows_load_summary["available"] is True
env.capacity_runtime_attachment_preflight_result["applied"] is True
env.explicit_pipeline_forward_weekly_capacity exists
```

### 17.2 Missing source hint preserves current safe skip

Given no source hint and no env.capacity_weekly_rows:

```text
runtime preflight still skips safely
source helper may not be called
env.capacity_runtime_attachment_preflight_result["applied"] is False
```

### 17.3 Scenario root default masters path

Given:

```text
env.scenario_root = tmp_path / "scenario"
scenario_root / "masters" / "capacity_master.csv"
```

Run Explicit KPI preflight.

Assert rows load and runtime preflight applies.

### 17.4 Source messages propagate

Assert messages include:

```text
Capacity weekly rows source: loaded
```

or that summary messages are available via:

```text
env.capacity_weekly_rows_load_summary["messages"]
```

### 17.5 Invalid configured source raises or is reported

If a configured source exists but is invalid, assert behavior matches chosen error policy.

### 17.6 No GUI layout change

Do not assert layout changes.

### 17.7 No planner behavior change

Do not assert plan result changes.

---

## 18. Test Commands for Future Codex Request

Focused source wiring test:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 19. Safety Boundaries for Future Implementation

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
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Possibly changed only if needed:

```text
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
```

Do not change planner behavior.

Do not change capacity enforcement.

Do not change data CSV files.

---

## 20. Acceptance Criteria for Future Implementation

The Explicit KPI source wiring is complete when:

```text
load_capacity_weekly_rows_to_env(...) is called before apply_capacity_runtime_attachment_preflight(...) when a source hint exists
env.capacity_weekly_rows is populated from capacity_master.csv
env.capacity_weekly_rows_load_summary is attached
runtime preflight consumes loaded env.capacity_weekly_rows
rows-present source case leads to runtime preflight applied=True
missing source hint still preserves safe skip behavior
source messages are preserved
focused tests pass
related preflight/diagnostic tests pass
no planner behavior changes are made
no capacity enforcement changes are made
no GUI layout changes are made
no data CSV files are changed
```

---

## 21. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_source_explicit_kpi_preflight_wiring_request.md
```

Scope:

```text
wire load_capacity_weekly_rows_to_env into Explicit KPI preflight
only when source hint exists
call before apply_capacity_runtime_attachment_preflight
focused tests
no planner changes
no data changes
no GUI layout changes
```

---

## 22. Development Meaning

Before this phase, WOM has:

```text
capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
```

and:

```text
env.capacity_weekly_rows
    ↓
Explicit KPI runtime attachment preflight
```

but these two routes are not yet connected inside Explicit KPI preflight.

This design connects the loading dock to the pre-departure inspection route.

In short:

```text
The capacity cargo loading dock exists.
The Explicit KPI inspection route exists.
This memo designs the conveyor belt between them.
```

---

## 23. Summary

This memo designs:

```text
Explicit KPI preflight
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
```

The first implementation should remain narrow:

```text
source wiring only
focused tests
no planner changes
no capacity enforcement changes
no GUI layout changes
no data CSV changes
```

Recommended next request:

```text
docs/codex_requests/wom_capacity_source_explicit_kpi_preflight_wiring_request.md
```
