# WOM Capacity Master to Env Capacity Weekly Rows Source

**Version:** v0r1 draft  
**Date:** 2026-05-30  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md`

**Parent / related design docs:**

```text
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring.md
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
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
```

---

## 1. Purpose

This memo defines how WOM should populate:

```text
env.capacity_weekly_rows
```

from capacity master inputs before the Explicit KPI capacity runtime attachment preflight runs.

The completed runtime path is now:

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

The missing source-side link is:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

This memo designs that source-side link.

This is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Capacity source loading should create canonical WeeklyCapacityRow rows,
then attach those rows to env.capacity_weekly_rows.
```

The source loader should not directly build planner-specific runtime shapes.

It should not bypass canonical rows.

It should not modify planner behavior.

The canonical path should remain:

```text
capacity source
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
    ↓
runtime attachment preflight
    ↓
runtime contexts
    ↓
diagnostic visibility
```

This keeps WOM’s capacity data path explainable.

---

## 3. Current Completed State

### 3.1 Canonical capacity loader completed

Implemented:

```text
capacity_master.csv -> list[WeeklyCapacityRow]
```

Function:

```python
load_capacity_master_csv(path)
```

Location:

```text
pysi/capacity/capacity_master_loader.py
```

Key commit:

```text
31d6d8e Add canonical capacity master loader
```

### 3.2 Runtime context adapters completed

Implemented:

```text
WeeklyCapacityRow -> explicit forward capacity context
WeeklyCapacityRow -> explicit backward capability context
```

Key commits:

```text
3a933fd Add weekly capacity row forward context adapter
1ee4008 Add weekly capacity backward context adapter
```

### 3.3 Runtime env attach helper completed

Implemented:

```text
WeeklyCapacityRow-derived contexts -> env runtime attributes
```

Key commit:

```text
d8a8a36 Add weekly capacity runtime env attach helper
```

### 3.4 Runtime attachment diagnostic completed

Implemented:

```text
env.capacity_runtime_attachment_summary -> diagnostic["runtime_attachment"]
```

Key commit:

```text
45477fc Add capacity runtime attachment diagnostic
```

### 3.5 Generic preflight helper completed

Implemented:

```text
env.capacity_weekly_rows -> apply_capacity_runtime_attachment_preflight(...)
```

Key commit:

```text
258eb31 Add capacity runtime attachment preflight helper
```

### 3.6 Explicit KPI preflight wiring completed

Implemented:

```text
Explicit KPI preflight -> apply_capacity_runtime_attachment_preflight(...)
```

Key commit:

```text
f480156 Wire capacity runtime preflight into explicit KPI
```

### 3.7 Remaining gap

The current remaining source-side gap is:

```text
Who populates env.capacity_weekly_rows?
```

This memo addresses that gap.

---

## 4. Problem to Solve

The Explicit KPI preflight now calls:

```python
apply_capacity_runtime_attachment_preflight(env, messages=...)
```

That helper checks:

```text
env.capacity_weekly_rows
```

If the attribute exists, capacity runtime contexts are attached and diagnosed.

If the attribute is missing, the helper safely skips.

Therefore, the next missing work is:

```text
Load canonical capacity rows from a scenario-level capacity master source
and attach them to env.capacity_weekly_rows before Explicit KPI preflight runs.
```

This must be done without:

```text
changing planner behavior
changing capacity enforcement behavior
loading data from an ambiguous location
hiding missing capacity inputs
duplicating capacity adapters
bypassing WeeklyCapacityRow
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
capacity applicability enforcement
full scenario package runner implementation
```

The design is limited to defining how canonical capacity rows should be sourced and attached to env.

---

## 6. Source Types

WOM has at least three relevant source patterns.

### 6.1 Canonical capacity_master.csv

Preferred WOM V1 source:

```text
capacity_master.csv
```

Representative columns:

```text
scenario_id
tree_side
node_name
product_name
week
capacity_type
capacity_qty
cap_mode
unit
priority
calendar_id
comment
```

The loader should return:

```text
list[WeeklyCapacityRow]
```

### 6.2 Scenario package master path

Preferred scenario package direction:

```text
scenarios/<case>/<scenario>/masters/capacity_master.csv
```

or, if scenario yaml is present:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

This path should resolve relative to the scenario package directory.

### 6.3 Legacy PySI V0R8 capacity inputs

Legacy inputs include patterns such as:

```text
sku_P_month_data.csv
monthly capacity files
weekly capacity files
existing capacity provider plugin inputs
```

These should not be directly consumed by the new Explicit KPI source wiring unless routed through an adapter.

The design direction should be:

```text
legacy capacity input
    ↓
legacy adapter
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
```

Not:

```text
legacy capacity input
    ↓
planner-specific runtime shape directly
```

---

## 7. Canonical Source Contract

The canonical source contract is:

```text
capacity source
    ↓
list[WeeklyCapacityRow]
    ↓
env.capacity_weekly_rows
```

Recommended env attribute:

```text
env.capacity_weekly_rows
```

Optional metadata attributes:

```text
env.capacity_weekly_rows_source
env.capacity_weekly_rows_source_path
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_load_summary
```

Recommended source kinds:

```text
capacity_master_csv
scenario_package_capacity_master
legacy_monthly_capacity_adapter
legacy_weekly_capacity_adapter
manual_test_rows
missing
```

---

## 8. Recommended Loader Helper

Recommended helper:

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

Purpose:

```text
resolve capacity source
load WeeklyCapacityRow rows
attach rows to env.capacity_weekly_rows
attach source metadata
return load summary
```

Possible location:

```text
pysi/capacity/capacity_master_loader.py
```

or:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

Near-term recommendation:

```text
create a small new module pysi/capacity/capacity_weekly_rows_source.py
```

Reason:

```text
capacity_master_loader.py should remain a pure CSV loader.
source resolution and env attachment are a higher-level concern.
```

---

## 9. Source Resolution Order

Recommended source resolution order:

```text
1. Explicit capacity_master_path argument
2. scenario_config["masters"]["capacity_master"] relative to scenario_root
3. scenario_root / "masters" / "capacity_master.csv"
4. scenario_root / "capacity_master.csv"
5. No source found
```

This keeps behavior deterministic.

The function should report which source was selected.

Example summary:

```python
{
    "available": True,
    "source_kind": "scenario_package_capacity_master",
    "source_path": "scenarios/japanese_rice/as_is/masters/capacity_master.csv",
    "row_count": 52,
    "attached_to_env": True,
    "messages": [
        "Capacity weekly rows source: loaded 52 rows from scenario package capacity_master.csv."
    ],
}
```

If no source is found and `required=False`:

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

If no source is found and `required=True`, raise:

```text
FileNotFoundError
```

Near-term recommendation:

```text
required=False for GUI / Explicit KPI demo preflight
required=True only for strict scenario runner validation
```

---

## 10. Env Attributes to Attach

When rows are loaded successfully:

```text
env.capacity_weekly_rows = rows
env.capacity_weekly_rows_source_kind = source_kind
env.capacity_weekly_rows_source_path = str(path)
env.capacity_weekly_rows_load_summary = summary
```

When source is missing and `required=False`:

```text
do not attach env.capacity_weekly_rows
always attach env.capacity_weekly_rows_load_summary
```

Recommended rule:

```text
always attach env.capacity_weekly_rows_load_summary
only attach env.capacity_weekly_rows when a source file is loaded
```

This preserves the distinction between:

```text
missing capacity row source
empty capacity file
loaded non-empty capacity rows
```

---

## 11. Empty File / Empty Row Policy

If a source file exists but yields zero rows:

```text
env.capacity_weekly_rows = []
env.capacity_weekly_rows_load_summary.available = True
env.capacity_weekly_rows_load_summary.row_count = 0
```

This is different from a missing file.

The later preflight helper should then apply with empty rows and produce:

```text
applied = True
input_row_count = 0
runtime attachment summary available=False
```

This gives deterministic diagnostics.

---

## 12. Error Handling Policy

### 12.1 Missing file

If `required=False`:

```text
return unavailable summary
do not raise
```

If `required=True`:

```text
raise FileNotFoundError
```

### 12.2 Invalid CSV schema

If a file exists but is invalid:

```text
raise ValueError
```

Reason:

```text
A malformed capacity source should not be silently ignored.
```

### 12.3 Invalid capacity_qty

Handled by:

```text
load_capacity_master_csv(...)
```

The source helper should not duplicate validation.

### 12.4 Duplicate rows

The loader preserves row order and duplicate rows.

Duplicate aggregation is handled later by runtime context adapters.

---

## 13. Relationship to Explicit KPI Preflight

The current Explicit KPI preflight now handles:

```text
env.capacity_weekly_rows if already present
```

This design adds an earlier optional source step:

```text
capacity_master source
    ↓
env.capacity_weekly_rows
    ↓
Explicit KPI preflight capacity runtime attachment
```

Potential future call order:

```text
1. Scenario / demo setup
2. Load capacity rows to env, if a capacity source is configured
3. Existing backward / forward capacity context setup
4. apply_capacity_runtime_attachment_preflight(...)
5. Existing capacity scenario alignment diagnostic
6. ctx guard
7. view-model / messages
```

Near-term implementation should be separate from GUI wiring.

Recommended first implementation:

```text
helper + focused tests only
no GUI wiring
```

Then later:

```text
Explicit KPI source wiring
```

---

## 14. Relationship to Scenario Package Control Model

The scenario package model should ultimately provide:

```yaml
scenario_id: japanese_rice_as_is

masters:
  network_nodes: masters/nodes.csv
  network_flows: masters/flows.csv
  demand: masters/demand_weekly.csv
  capacity_master: masters/capacity_master.csv
  cost_master: masters/cost_master.csv
  price_master: masters/price_master.csv
```

This design focuses only on:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

The helper should not require the full scenario package runner to exist.

It should accept:

```text
scenario_root
scenario_config
```

as optional inputs.

---

## 15. Relationship to PySI V0R8 Legacy Master Data

PySI V0R8 has existing master data and loaders.

The design direction is:

```text
PySI V0R8 legacy master
    ↓
legacy adapter
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
```

This keeps the canonical model stable while preserving backward compatibility.

Legacy monthly capacity adapter should remain separate from the canonical CSV loader.

The new source helper may later dispatch to legacy adapters, but the first implementation should focus on canonical capacity_master.csv.

---

## 16. Diagnostic Visibility

The load helper should return a load summary and optionally attach it to env:

```text
env.capacity_weekly_rows_load_summary
```

This can later be included in diagnostics.

Example messages:

```text
Capacity weekly rows source: loaded 52 rows from capacity_master.csv.
Capacity weekly rows source: no capacity master source found.
Capacity weekly rows source: capacity master file exists but contains no rows.
Capacity weekly rows source: using explicit capacity_master_path.
Capacity weekly rows source: using scenario package masters.capacity_master.
```

Future diagnostic may include:

```text
capacity_weekly_rows_source
```

as a diagnostic section.

This memo does not require that diagnostic integration yet.

---

## 17. Recommended Implementation Phases

### Phase S1: Source helper only

Implement:

```python
load_capacity_weekly_rows_to_env(...)
```

with focused tests.

No GUI wiring.

No scenario runner wiring.

No planner behavior change.

### Phase S2: Explicit KPI source wiring

Wire source helper before:

```python
apply_capacity_runtime_attachment_preflight(...)
```

only when a scenario root or capacity path is available.

### Phase S3: Scenario package integration

Connect scenario yaml:

```yaml
masters:
  capacity_master: ...
```

to source helper.

### Phase S4: Legacy adapter integration

Allow legacy capacity inputs to produce WeeklyCapacityRow rows.

---

## 18. Suggested Tests for Future Phase S1

Create focused test file:

```text
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

### 18.1 Explicit path loads rows

Create temporary capacity_master.csv.

Call:

```python
load_capacity_weekly_rows_to_env(env, capacity_master_path=path)
```

Assert:

```text
env.capacity_weekly_rows exists
row_count matches
env.capacity_weekly_rows_source_path == path
summary.available == True
summary.row_count == expected
```

### 18.2 Scenario config path loads rows

Given:

```python
scenario_root = tmp_path / "scenario"
scenario_config = {"masters": {"capacity_master": "masters/capacity_master.csv"}}
```

Assert rows load from scenario-relative path.

### 18.3 Default masters path loads rows

Given:

```text
scenario_root/masters/capacity_master.csv
```

with no config, assert rows load.

### 18.4 Missing source with required=False

Assert:

```text
summary.available == False
summary.source_kind == "missing"
env.capacity_weekly_rows is not attached
```

### 18.5 Missing source with required=True

Assert:

```text
FileNotFoundError
```

### 18.6 Empty file

Given a valid header but no rows, assert:

```text
env.capacity_weekly_rows == []
summary.available == True
summary.row_count == 0
```

### 18.7 Invalid schema

Assert loader raises ValueError from canonical loader.

---

## 19. Test Commands for Future Codex Request

Focused source helper tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Related tests:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 20. Safety Boundaries for Future Implementation

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
data/*.csv
```

Expected changed/new files for Phase S1:

```text
pysi/capacity/capacity_weekly_rows_source.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Possibly changed only for export convenience:

```text
pysi/capacity/__init__.py
```

Do not wire into GUI or scenario runner in Phase S1.

---

## 21. Acceptance Criteria for Future Phase S1

The source helper phase is complete when:

```text
load_capacity_weekly_rows_to_env or equivalent helper exists
explicit capacity_master_path loads rows
scenario_config masters.capacity_master loads rows
scenario_root/masters/capacity_master.csv default path loads rows
missing source with required=False skips safely
missing source with required=True raises FileNotFoundError
empty valid CSV attaches empty list
invalid schema raises ValueError
env.capacity_weekly_rows is attached only when a source file is loaded
env.capacity_weekly_rows_load_summary is attached
focused tests pass
related loader/preflight tests pass
no planner behavior changes are made
no GUI files are changed
no data CSV files are changed
```

---

## 22. Recommended Next Codex Request

Recommended request file:

```text
docs/codex_requests/wom_capacity_master_to_env_capacity_weekly_rows_source_request.md
```

Scope:

```text
implement load_capacity_weekly_rows_to_env(...)
focused tests
no GUI wiring
no planner changes
no data CSV changes
no scenario runner integration
```

---

## 23. Development Meaning

Before this phase, WOM has:

```text
env.capacity_weekly_rows
    ↓
runtime capacity attachment preflight
```

but the source of `env.capacity_weekly_rows` remains manual or test-provided.

This design prepares the missing source-side link:

```text
capacity_master.csv / scenario package
    ↓
env.capacity_weekly_rows
```

This matters because the Explicit KPI preflight now has a formal place to consume canonical capacity rows.

The next step is to define where those rows are loaded.

In short:

```text
The train has a pre-departure capacity inspection route.
Now we define where the capacity cargo is loaded onto the train.
```

---

## 24. Summary

This memo designs the source-side path:

```text
capacity_master.csv / scenario package capacity master
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

The first implementation should remain narrow:

```text
source helper only
focused tests
no GUI changes
no planner changes
no scenario runner changes
no data CSV changes
```

Recommended next request:

```text
docs/codex_requests/wom_capacity_master_to_env_capacity_weekly_rows_source_request.md
```
