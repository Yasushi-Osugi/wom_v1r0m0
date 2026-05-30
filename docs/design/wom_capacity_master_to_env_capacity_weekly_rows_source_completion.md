# WOM Capacity Master to Env Capacity Weekly Rows Source Completion Memo

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_diagnostic_integration_completion.md
docs/design/wom_capacity_weekly_rows_runtime_env_attach_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_master_to_env_capacity_weekly_rows_source_request.md
```

---

## 1. Purpose

This completion memo records the completion of the first source-side helper that loads canonical WOM capacity master rows into:

```text
env.capacity_weekly_rows
```

The completed scope is intentionally narrow:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

This phase creates the official source-side loading dock for canonical capacity rows.

It does not wire the source helper into GUI.

It does not wire the source helper into scenario runner.

It does not change planner behavior.

It does not change capacity enforcement behavior.

It does not change data CSV files.

It does not normalize week keys.

It does not implement legacy PySI V0R8 adapter dispatch.

---

## 2. Key Commit

Implementation commit:

```text
8886c03 Add capacity weekly rows env source helper
```

Related preceding commits:

```text
13ff010 Add WOM capacity master to env capacity weekly rows source Codex request
7ae35ed Add WOM capacity master to env capacity weekly rows source design
ad7435e Add WOM capacity runtime attachment Explicit KPI preflight wiring completion memo
f480156 Wire capacity runtime preflight into explicit KPI
03c3d82 Add WOM capacity runtime attachment Explicit KPI preflight wiring Codex request
804caef Add WOM capacity runtime attachment Explicit KPI preflight wiring design
c109378 Add WOM capacity runtime attachment preflight wiring completion memo
258eb31 Add capacity runtime attachment preflight helper
31d6d8e Add canonical capacity master loader
```

---

## 3. Implementation Summary

The implementation added:

```python
load_capacity_weekly_rows_to_env(...)
```

in:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

The helper reuses the canonical loader:

```python
load_capacity_master_csv(path)
```

from:

```text
pysi/capacity/capacity_master_loader.py
```

It does not duplicate CSV parsing or validation logic.

The helper resolves a capacity source path, loads canonical `WeeklyCapacityRow` rows, attaches them to `env.capacity_weekly_rows`, attaches source metadata, and returns a structured summary.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/capacity/capacity_weekly_rows_source.py
pysi/capacity/__init__.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

### 4.1 capacity_weekly_rows_source.py

Added:

```python
load_capacity_weekly_rows_to_env(...)
```

This module handles:

```text
source resolution
canonical loader invocation
env attachment
load summary creation
```

### 4.2 pysi/capacity/__init__.py

Exported:

```python
load_capacity_weekly_rows_to_env
```

for low-risk package-level convenience.

### 4.3 test_wom_capacity_master_to_env_capacity_weekly_rows_source.py

Added focused tests covering:

```text
explicit capacity_master_path
scenario_config masters.capacity_master
scenario_root / masters / capacity_master.csv
scenario_root / capacity_master.csv
missing source with required=False
missing source with required=True
empty valid CSV
invalid schema
```

---

## 5. Implemented Helper

Implemented signature:

```python
load_capacity_weekly_rows_to_env(
    env,
    *,
    capacity_master_path: str | Path | None = None,
    scenario_root: str | Path | None = None,
    scenario_config: dict | None = None,
    required: bool = False,
) -> dict
```

Input contract:

```text
env:
  any Python object supporting attribute assignment

capacity_master_path:
  explicit file path to capacity_master.csv

scenario_root:
  root path for scenario package lookup

scenario_config:
  optional dict, may include masters.capacity_master

required:
  if True, missing source raises FileNotFoundError
  if False, missing source returns unavailable summary
```

---

## 6. Source Resolution Order

The helper implements deterministic source resolution in this order:

```text
1. Explicit capacity_master_path argument
2. scenario_config["masters"]["capacity_master"] relative to scenario_root
3. scenario_root / "masters" / "capacity_master.csv"
4. scenario_root / "capacity_master.csv"
5. No source found
```

This is important because capacity row source loading must be explainable and stable.

The selected source path and source kind are recorded in the load summary and env metadata.

---

## 7. Env Attributes Attached

### 7.1 On successful source load

When a source file is found and loaded, the helper attaches:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
env.capacity_weekly_rows_load_summary
```

### 7.2 On missing source with required=False

When no source is found and `required=False`, the helper attaches only:

```text
env.capacity_weekly_rows_load_summary
```

It does **not** attach:

```text
env.capacity_weekly_rows
```

This preserves the important distinction between:

```text
missing capacity row source
empty capacity source file
loaded non-empty capacity source file
```

### 7.3 On missing source with required=True

When no source is found and `required=True`, the helper raises:

```text
FileNotFoundError
```

---

## 8. Load Summary

The helper returns a structured summary.

### 8.1 Successful load

Conceptual summary:

```python
{
    "available": True,
    "source_kind": "...",
    "source_path": ".../capacity_master.csv",
    "row_count": N,
    "attached_to_env": True,
    "messages": [
        "Capacity weekly rows source: loaded N rows from capacity_master.csv."
    ],
}
```

### 8.2 Missing source

Conceptual summary:

```python
{
    "available": False,
    "source_kind": "missing",
    "source_path": None,
    "row_count": 0,
    "attached_to_env": False,
    "messages": [
        "Capacity weekly rows source: no capacity master source found."
    ],
}
```

### 8.3 Empty valid CSV

If the file exists and has a valid header but no data rows:

```python
{
    "available": True,
    "row_count": 0,
    "attached_to_env": True,
    ...
}
```

and:

```text
env.capacity_weekly_rows == []
```

This is intentionally different from a missing source.

---

## 9. Error Handling

### 9.1 Missing source

Behavior:

```text
required=False:
  return unavailable summary
  attach env.capacity_weekly_rows_load_summary
  do not attach env.capacity_weekly_rows

required=True:
  raise FileNotFoundError
```

### 9.2 Invalid CSV schema

Invalid schema propagates:

```text
ValueError
```

from the canonical loader path.

The source helper does not silently skip invalid files.

### 9.3 Invalid capacity_qty

Invalid quantity parsing remains the responsibility of:

```text
load_capacity_master_csv(...)
```

### 9.4 Duplicate rows

Duplicate rows are not aggregated by this source helper.

They remain in the loaded row list.

Aggregation occurs later in runtime context adapters.

---

## 10. Week Key Policy

The helper does not normalize week keys.

It does not convert:

```text
2027-W40 -> integer index
0 -> business week label
```

The helper only loads canonical rows and attaches them to env.

Week-domain handling remains downstream.

---

## 11. Tests Executed

Focused source helper tests passed:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Observed result:

```text
8 passed
```

Related loader / preflight / capacity tests passed:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_wom_capacity_runtime_attachment_preflight_wiring.py tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py tests/test_explicit_pipeline_capacity_scenario_alignment.py tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
55 passed
```

---

## 12. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
blocked lot behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
GUI behavior
GUI preflight wiring
scenario runner wiring
data CSV files
sample CSV files
scenario package runner
legacy PySI V0R8 adapter dispatch
week-key normalization
calendar conversion
capacity applicability status enforcement
```

This phase only added:

```text
source helper
package-level export
focused tests
```

---

## 13. Current Architecture After This Phase

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

This means WOM now has:

```text
source-side loading dock
runtime attachment preflight
diagnostic visibility
Explicit KPI preflight wiring
```

The source helper is not yet connected to GUI or scenario runner.

---

## 14. Still Deferred

The following work remains intentionally deferred.

### 14.1 Explicit KPI source wiring

The source helper is not yet called by:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags
```

or any GUI flow.

The next design may define:

```text
when and how load_capacity_weekly_rows_to_env(...) should be called before apply_capacity_runtime_attachment_preflight(...)
```

### 14.2 Scenario package runner integration

No scenario runner integration was added.

Future direction:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

### 14.3 Legacy PySI V0R8 adapter dispatch

Legacy capacity inputs are not yet routed through:

```text
legacy capacity input
    ↓
legacy adapter
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
```

### 14.4 GUI message surfacing

The source helper returns a load summary, but no GUI display behavior was added.

### 14.5 Capacity applicability status

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

---

## 15. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
```

Purpose:

```text
Define how load_capacity_weekly_rows_to_env(...) should be called before
apply_capacity_runtime_attachment_preflight(...) in the Explicit KPI preflight flow.
```

This design should address:

```text
where capacity_master_path or scenario_root comes from in the current GUI/env
whether source loading is optional or required
how missing source is reported
how env.capacity_weekly_rows_load_summary is surfaced
call order relative to existing capacity runtime attachment preflight
no planner behavior change
no GUI layout change
```

Possible later Codex request:

```text
docs/codex_requests/wom_capacity_source_explicit_kpi_preflight_wiring_request.md
```

The first implementation should remain narrow:

```text
call source helper only when a known capacity source path or scenario root is present
attach load summary to env
then existing runtime attachment preflight consumes env.capacity_weekly_rows
do not change planner behavior
do not change data CSV files
```

---

## 16. Development Meaning

Before this phase, WOM had:

```text
env.capacity_weekly_rows
    ↓
runtime capacity attachment preflight
```

but the source of `env.capacity_weekly_rows` was manual or test-provided.

After this phase, WOM has:

```text
capacity_master.csv / scenario package source
    ↓
env.capacity_weekly_rows
```

This is a major source-side step.

The canonical capacity row container now has an official loading dock.

In short:

```text
The train has a capacity inspection route.
Now the capacity cargo has a formal loading platform.
```

---

## 17. Summary

Completed:

```text
load_capacity_weekly_rows_to_env(...)
```

Confirmed:

```text
explicit capacity_master_path loads rows
scenario_config masters.capacity_master loads rows
scenario_root/masters/capacity_master.csv loads rows
scenario_root/capacity_master.csv loads rows
missing source with required=False skips safely
missing source with required=True raises FileNotFoundError
empty valid CSV attaches env.capacity_weekly_rows = []
invalid schema raises ValueError
env.capacity_weekly_rows_load_summary is attached
focused tests passed
related tests passed
planner behavior unchanged
GUI unchanged
data CSV unchanged
scenario runner unchanged
legacy adapter dispatch unchanged
```

Next:

```text
load_capacity_weekly_rows_to_env(...)
    ↓
Explicit KPI source-side preflight wiring
```

Recommended next design:

```text
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
```
