# WOM Capacity Source Explicit KPI Preflight Wiring Completion Memo

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md`

**Related design docs:**

```text
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
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_source_explicit_kpi_preflight_wiring_request.md
```

---

## 1. Purpose

This completion memo records the completion of wiring the canonical capacity source helper into the existing Explicit KPI preflight route.

The completed source-side path is:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
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
capacity runtime attachment diagnostic
```

This implementation connects those paths inside Explicit KPI preflight:

```text
Explicit KPI preflight
    ↓
load_capacity_weekly_rows_to_env(...), when a source hint exists
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_preflight_result
    ↓
capacity scenario alignment diagnostic
```

This phase connects the capacity cargo loading dock to the Explicit KPI pre-departure inspection route.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change blocked lot behavior.

It does not change data CSV files.

It does not normalize week keys.

It does not change GUI layout.

It does not implement scenario runner integration.

It does not implement legacy PySI V0R8 adapter dispatch.

---

## 2. Key Commit

Implementation commit:

```text
34080fc Wire capacity source into explicit KPI preflight
```

Related preceding commits:

```text
589efc7 Add WOM capacity source Explicit KPI preflight wiring Codex request
3540ab1 Add WOM capacity source Explicit KPI preflight wiring design
cb45f61 Add WOM capacity master to env capacity weekly rows source completion memo
8886c03 Add capacity weekly rows env source helper
13ff010 Add WOM capacity master to env capacity weekly rows source Codex request
7ae35ed Add WOM capacity master to env capacity weekly rows source design
ad7435e Add WOM capacity runtime attachment Explicit KPI preflight wiring completion memo
f480156 Wire capacity runtime preflight into explicit KPI
```

---

## 3. Implementation Summary

The implementation wired:

```python
load_capacity_weekly_rows_to_env(...)
```

into the existing Explicit KPI preflight flow.

The wiring was added in:

```text
pysi/gui/cockpit_tk.py
```

through a helper method:

```text
_maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight
```

This helper is called from:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

and runs before:

```text
_maybe_apply_capacity_runtime_attachment_preflight
```

The source helper is called only when a capacity source hint exists.

If no source hint exists, the source helper is not called, and the existing runtime attachment preflight safe-skip behavior remains unchanged.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

### 4.1 cockpit_tk.py

Added source-side wiring to the Explicit KPI preflight flow.

The new helper:

```text
inspects existing env/self source hints
calls load_capacity_weekly_rows_to_env(..., required=False) only when a source hint exists
appends source load messages to the local preflight message stream
lets the existing runtime preflight consume env.capacity_weekly_rows
```

### 4.2 test_wom_capacity_source_explicit_kpi_preflight_wiring.py

Added focused tests covering:

```text
explicit capacity_master_path loading
no source hint safe skip
scenario_root / masters / capacity_master.csv loading
source message preservation
empty valid capacity master file handling
repeated invocation determinism
```

---

## 5. Completed Call Order

The completed Explicit KPI preflight order is:

```text
1. Existing Explicit KPI demo flag setup.
2. Capacity source loading, if a source hint exists.
3. Existing backward / forward capacity context setup, if any.
4. Existing capacity runtime attachment preflight.
5. Existing capacity scenario alignment diagnostic.
6. Existing ctx guard check.
7. Existing Explicit KPI view-model / message construction.
```

The newly completed connection is:

```text
Capacity source loading
    ↓
Capacity runtime attachment preflight
```

This means that when a valid capacity source is configured, Explicit KPI preflight can now load capacity rows before runtime capacity attachment.

---

## 6. Source Hint Policy Implemented

The wiring uses existing env / self attributes only.

Source hints include:

```text
capacity_master_path
scenario_root
current_scenario_root
scenario_config
current_scenario_config
```

If at least one source hint exists, the source helper can be called.

If no source hint exists:

```text
load_capacity_weekly_rows_to_env(...) is not called
env.capacity_weekly_rows_load_summary is not attached
runtime attachment preflight still safely reports capacity_weekly_rows_missing
```

This avoids noisy missing-source messages in flows where no capacity source path is configured.

---

## 7. Behavior When capacity_master_path Is Present

When:

```text
env.capacity_master_path
```

or an equivalent source hint points to a valid canonical `capacity_master.csv`, the source helper:

```text
loads WeeklyCapacityRow rows
attaches env.capacity_weekly_rows
attaches env.capacity_weekly_rows_load_summary
attaches env.capacity_weekly_rows_source_kind
attaches env.capacity_weekly_rows_source_path
```

Then the existing runtime attachment preflight consumes:

```text
env.capacity_weekly_rows
```

and attaches:

```text
env.capacity_runtime_attachment_preflight_result
env.capacity_runtime_attachment_summary
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows
```

The canonical backward side attribute remains safe.

The consumer-facing backward capability attribute is not replaced.

---

## 8. Behavior When No Source Hint Exists

When no source hint exists and no `env.capacity_weekly_rows` exists:

```text
source helper is not called
runtime attachment preflight runs as before
runtime attachment preflight result is attached
result["applied"] == False
result["reason"] == "capacity_weekly_rows_missing"
```

This preserves prior safe-skip behavior.

The implementation does not force source loading or introduce new required capacity files for existing demos.

---

## 9. Behavior With scenario_root / masters / capacity_master.csv

When:

```text
env.scenario_root
```

or equivalent scenario root is provided and the following file exists:

```text
scenario_root / "masters" / "capacity_master.csv"
```

the source helper uses the existing source resolution behavior and loads rows from that default scenario package path.

Then runtime attachment preflight applies as expected.

This is the first bridge from scenario-style capacity source layout into Explicit KPI preflight.

---

## 10. Behavior With Empty Valid Capacity Master File

If the configured capacity master file exists and has a valid header but no data rows:

```text
env.capacity_weekly_rows == []
env.capacity_weekly_rows_load_summary["available"] == True
env.capacity_weekly_rows_load_summary["row_count"] == 0
```

Runtime attachment preflight still applies in the sense that it sees a provided row source:

```text
env.capacity_runtime_attachment_preflight_result["applied"] == True
```

The runtime attachment summary and diagnostic then explain that there are no WeeklyCapacityRow rows.

This preserves the distinction between:

```text
missing source
empty valid source
loaded non-empty source
```

---

## 11. Message Propagation

Source messages are preserved in:

```text
env.capacity_weekly_rows_load_summary["messages"]
```

and are appended into the local preflight message stream.

Examples include:

```text
Capacity weekly rows source: loaded N rows from capacity_master.csv.
Capacity weekly rows source: loaded 0 rows from capacity_master.csv.
```

Runtime attachment messages remain available through the existing runtime preflight result and diagnostic path.

No new GUI widgets or layout changes were introduced.

---

## 12. Diagnostic Visibility

This phase does not add a new diagnostic section.

It relies on:

```text
env.capacity_weekly_rows_load_summary
```

for source load information and the existing runtime attachment diagnostic for runtime context visibility.

Existing diagnostic flow remains:

```text
capacity source load
    ↓
env.capacity_weekly_rows
    ↓
runtime attachment preflight
    ↓
capacity scenario alignment diagnostic
```

Future work may add:

```text
diagnostic["capacity_weekly_rows_source"]
```

but that is intentionally deferred.

---

## 13. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
blocked lot behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
data CSV files
sample CSV files
GUI layout
Management Cockpit layout
scenario runner behavior
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
capacity applicability status enforcement
```

This phase only added:

```text
Explicit KPI preflight source wiring
focused tests
```

---

## 14. Tests Executed

Focused source wiring test passed:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Observed result:

```text
6 passed
```

Related source / runtime attachment / Explicit KPI diagnostic tests passed:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_runtime_attachment_preflight_wiring.py tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
38 passed
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

## 15. Current Architecture After This Phase

The capacity canonical path is now:

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
build_capacity_runtime_attachment_diagnostic(env)
    ↓
Explicit KPI preflight diagnostic visibility
```

Operationally:

```text
Explicit KPI preflight
    ↓
capacity source loading, if source hint exists
    ↓
runtime capacity attachment preflight
    ↓
capacity scenario alignment diagnostic
```

This is the first completed source-to-runtime capacity preflight path inside Explicit KPI.

---

## 16. Still Deferred

The following work remains intentionally deferred.

### 16.1 Dedicated source diagnostic section

No new diagnostic section was added.

Future direction:

```text
diagnostic["capacity_weekly_rows_source"]
```

could expose:

```text
source_kind
source_path
row_count
available
messages
```

### 16.2 Scenario package runner integration

No scenario runner integration was added.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

could be loaded by scenario package runner and passed into the same source helper.

### 16.3 Legacy PySI V0R8 adapter dispatch

Legacy capacity inputs are not yet routed through:

```text
legacy input
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
```

### 16.4 Planner consumption

No planner behavior has changed.

### 16.5 GUI message layout

No GUI layout or widget changes were introduced.

---

## 17. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic.md
```

Purpose:

```text
Define how env.capacity_weekly_rows_load_summary should be exposed in diagnostics.
```

This design should address:

```text
diagnostic key name
available / missing source status
source_kind
source_path
row_count
messages
relationship to runtime_attachment diagnostic
message ordering
safe behavior when no source hint exists
no planner behavior change
no GUI layout change
```

Possible Codex request:

```text
docs/codex_requests/wom_capacity_weekly_rows_source_diagnostic_request.md
```

This would make the source side just as explainable as the runtime attachment side.

---

## 18. Development Meaning

Before this phase, WOM had:

```text
capacity source helper
```

and:

```text
Explicit KPI runtime attachment preflight
```

but they were separate.

After this phase, WOM has:

```text
capacity source helper
    ↓
Explicit KPI runtime attachment preflight
```

This means capacity master rows can now be loaded into the canonical row container and then consumed by Explicit KPI preflight without changing planner behavior.

In short:

```text
The capacity cargo loading dock exists.
The Explicit KPI inspection route exists.
The conveyor belt between them is now connected.
```

---

## 19. Summary

Completed:

```text
load_capacity_weekly_rows_to_env(...)
    ↓
Explicit KPI preflight source wiring
```

Confirmed:

```text
source helper called before runtime attachment preflight when source hint exists
env.capacity_weekly_rows populated from capacity_master.csv
env.capacity_weekly_rows_load_summary attached
runtime preflight consumes loaded env.capacity_weekly_rows
rows-present source case leads to runtime preflight applied=True
no source hint preserves safe skip behavior
empty valid source file handled deterministically
source messages preserved
focused tests passed
related tests passed
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
data CSV unchanged
scenario runner unchanged
legacy adapter dispatch unchanged
```

Next:

```text
env.capacity_weekly_rows_load_summary
    ↓
diagnostic visibility
```

Recommended next design:

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic.md
```
