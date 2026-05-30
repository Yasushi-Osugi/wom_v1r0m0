# Codex Request: WOM Capacity Master to Env Capacity Weekly Rows Source

**Version:** v0r1  
**Date:** 2026-05-30  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_master_to_env_capacity_weekly_rows_source_request.md`

**Parent design docs:**

```text
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

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first source-side helper that loads canonical WOM capacity master rows into:

```text
env.capacity_weekly_rows
```

This request is intentionally narrow.

Implement a helper equivalent to:

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

The helper should:

```text
resolve a capacity_master.csv source
load it with the existing canonical load_capacity_master_csv(...)
attach the resulting list[WeeklyCapacityRow] to env.capacity_weekly_rows
attach source metadata / load summary to env
return a structured load summary
```

Do not wire this helper into GUI.

Do not wire this helper into scenario runner.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change data CSV files.

Do not normalize week keys.

Do not implement legacy PySI V0R8 adapter dispatch in this request.

---

## 2. Why This Request Exists

The current capacity runtime path is already implemented:

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

The remaining source-side gap is:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
```

This request implements only that source-side helper.

In short:

```text
Create the capacity row loading dock.
Do not connect it to GUI or planner yet.
```

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_runtime_attachment_preflight_wiring_completion.md
```

Also inspect these implementation and test files:

```text
pysi/capacity/capacity_master_loader.py
pysi/adapters/capacity_input_granularity.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_wom_capacity_master_canonical_loader_adapter.py
tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
tests/test_capacity_master_io.py
```

Reuse the existing canonical loader:

```python
load_capacity_master_csv(path)
```

Do not duplicate its CSV parsing / validation logic.

---

## 4. Implementation Scope

### Required

Implement:

```python
load_capacity_weekly_rows_to_env(...)
```

Recommended location:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

Reason:

```text
capacity_master_loader.py should remain the pure CSV loader.
source resolution and env attachment are a higher-level source concern.
```

Optional export convenience:

```text
pysi/capacity/__init__.py
```

Only modify `__init__.py` if the package already uses it for public exports and doing so is low-risk.

### Required behavior

The helper should:

```text
resolve the capacity master source path
call load_capacity_master_csv(path)
attach rows to env.capacity_weekly_rows when a source file is found
attach env.capacity_weekly_rows_source_kind
attach env.capacity_weekly_rows_source_path
attach env.capacity_weekly_rows_load_summary
return the same summary object/dict
```

---

## 5. Explicit Non-Scope

Do not implement:

```text
GUI wiring
Explicit KPI source wiring
scenario runner integration
run_wom_scenario integration
planner behavior changes
capacity enforcement changes
blocked lot behavior changes
data CSV changes
sample CSV changes
week-key normalization
calendar conversion
legacy PySI V0R8 adapter dispatch
capacity applicability status enforcement
new optimization logic
```

This request is source helper + focused tests only.

---

## 6. Source Resolution Order

Use this deterministic resolution order:

```text
1. Explicit capacity_master_path argument
2. scenario_config["masters"]["capacity_master"] relative to scenario_root
3. scenario_root / "masters" / "capacity_master.csv"
4. scenario_root / "capacity_master.csv"
5. No source found
```

### 6.1 Explicit capacity_master_path

If `capacity_master_path` is supplied:

```text
source_kind = "capacity_master_csv"
```

or:

```text
source_kind = "explicit_capacity_master_path"
```

Either is acceptable, but be deterministic and test it.

Recommended:

```text
source_kind = "capacity_master_csv"
```

### 6.2 scenario_config masters.capacity_master

If:

```python
scenario_config = {"masters": {"capacity_master": "masters/capacity_master.csv"}}
```

and `scenario_root` is provided, resolve relative to `scenario_root`.

Recommended source kind:

```text
scenario_package_capacity_master
```

### 6.3 default scenario_root masters path

If:

```text
scenario_root / "masters" / "capacity_master.csv"
```

exists, use it.

Recommended source kind:

```text
scenario_package_capacity_master
```

### 6.4 default scenario_root direct path

If:

```text
scenario_root / "capacity_master.csv"
```

exists, use it.

Recommended source kind:

```text
scenario_package_capacity_master
```

### 6.5 missing source

If no source is found:

```text
source_kind = "missing"
source_path = None
```

---

## 7. Input Contract

Function signature:

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

Input details:

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
  if True, missing source should raise FileNotFoundError
  if False, missing source should return unavailable summary
```

Tests may use:

```python
from types import SimpleNamespace

env = SimpleNamespace()
```

---

## 8. Output Summary Contract

The helper should return a dictionary.

### 8.1 Successful load summary

Example:

```python
{
    "available": True,
    "source_kind": "scenario_package_capacity_master",
    "source_path": ".../masters/capacity_master.csv",
    "row_count": 52,
    "attached_to_env": True,
    "messages": [
        "Capacity weekly rows source: loaded 52 rows from capacity_master.csv."
    ],
}
```

### 8.2 Missing source summary

If missing and `required=False`:

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

### 8.3 Empty valid file summary

If file exists but contains only valid header and no data rows:

```python
{
    "available": True,
    "source_kind": "...",
    "source_path": ".../capacity_master.csv",
    "row_count": 0,
    "attached_to_env": True,
    "messages": [
        "Capacity weekly rows source: loaded 0 rows from capacity_master.csv."
    ],
}
```

---

## 9. Env Attachment Contract

### 9.1 When source file is loaded

Attach:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
env.capacity_weekly_rows_load_summary
```

### 9.2 When source is missing and required=False

Attach:

```text
env.capacity_weekly_rows_load_summary
```

Do not attach:

```text
env.capacity_weekly_rows
```

Reason:

```text
Missing row source and empty row source must remain distinguishable.
```

### 9.3 When source is missing and required=True

Raise:

```text
FileNotFoundError
```

The function may still attach a summary before raising, but this is not required.

Keep behavior simple and tested.

---

## 10. Error Handling Policy

### 10.1 Missing source

If `required=False`:

```text
return unavailable summary
do not raise
```

If `required=True`:

```text
raise FileNotFoundError
```

### 10.2 Invalid CSV schema

If source file exists but required columns are missing:

```text
raise ValueError
```

This should come from or be consistent with:

```python
load_capacity_master_csv(...)
```

Do not silently skip invalid files.

### 10.3 Invalid capacity_qty

Allow the canonical loader to raise its existing error.

Do not duplicate validation.

### 10.4 Duplicate rows

Do not aggregate duplicate rows.

The canonical loader preserves rows.

Runtime context adapters aggregate duplicates later.

---

## 11. Week Key Policy

Do not normalize week keys.

Do not convert:

```text
2027-W40 -> integer index
0 -> 2027-W40
```

The source helper should simply call the canonical loader and attach rows.

Week-key handling remains downstream.

---

## 12. Suggested Test File

Add focused tests:

```text
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Use temporary files and `SimpleNamespace`.

Do not modify repository data CSV files.

---

## 13. Required Tests

### 13.1 Explicit path loads rows

Create a temporary valid `capacity_master.csv`.

Call:

```python
summary = load_capacity_weekly_rows_to_env(
    env,
    capacity_master_path=path,
)
```

Assert:

```text
summary["available"] is True
summary["row_count"] == expected
summary["attached_to_env"] is True
env.capacity_weekly_rows exists
env.capacity_weekly_rows_source_path == str(path)
env.capacity_weekly_rows_load_summary == summary
```

### 13.2 Scenario config path loads rows

Given:

```python
scenario_root = tmp_path / "scenario"
scenario_config = {"masters": {"capacity_master": "masters/capacity_master.csv"}}
```

Assert rows load from:

```text
scenario_root / "masters" / "capacity_master.csv"
```

### 13.3 Default masters path loads rows

Given:

```text
scenario_root / "masters" / "capacity_master.csv"
```

and no config, assert rows load.

### 13.4 Default direct scenario path loads rows

Given:

```text
scenario_root / "capacity_master.csv"
```

and no config / no masters file, assert rows load.

### 13.5 Missing source with required=False

Assert:

```text
summary["available"] is False
summary["source_kind"] == "missing"
summary["attached_to_env"] is False
not hasattr(env, "capacity_weekly_rows")
hasattr(env, "capacity_weekly_rows_load_summary")
```

### 13.6 Missing source with required=True

Assert:

```text
FileNotFoundError
```

### 13.7 Empty valid file

Create a valid CSV with header only.

Assert:

```text
summary["available"] is True
summary["row_count"] == 0
env.capacity_weekly_rows == []
```

### 13.8 Invalid schema

Create a malformed CSV missing required columns.

Assert:

```text
ValueError
```

---

## 14. Test Data Helper

Use a helper inside the test file to write a minimal valid capacity master CSV.

Required columns should match the current canonical loader.

Likely header:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

Example row:

```csv
RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,10,hard,lot,1,CAL_STD,test row
```

Adjust only if the current loader requires a different exact header.

---

## 15. Test Commands

Run focused source helper test:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Run related loader/preflight tests:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
python -m pytest tests/test_wom_capacity_runtime_attachment_preflight_wiring.py
python -m pytest tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Run capacity regression:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 16. Safety Boundaries

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
pysi/capacity/capacity_weekly_rows_source.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Possibly changed only if needed:

```text
pysi/capacity/__init__.py
```

Do not wire into GUI or scenario runner in this request.

---

## 17. Acceptance Criteria

This request is complete when:

```text
load_capacity_weekly_rows_to_env or equivalent helper exists
explicit capacity_master_path loads rows
scenario_config masters.capacity_master loads rows
scenario_root/masters/capacity_master.csv default path loads rows
scenario_root/capacity_master.csv default path loads rows
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
no scenario runner integration is added
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is load_capacity_weekly_rows_to_env implemented?
Does it reuse load_capacity_master_csv?
What source resolution order is implemented?
What env attributes are attached on success?
What happens when source is missing and required=False?
What happens when source is missing and required=True?
Does empty valid CSV attach env.capacity_weekly_rows = []?
Does invalid schema raise ValueError?
Did you change planner behavior?
Did you change GUI files?
Did you change data CSV files?
Did you wire this into GUI or scenario runner?
Which tests passed?
```

---

## 19. Development Meaning

This request adds the source-side loading dock for canonical capacity rows.

Already completed:

```text
env.capacity_weekly_rows
    ↓
runtime capacity attachment preflight
    ↓
Explicit KPI diagnostic visibility
```

This request adds:

```text
capacity_master.csv / scenario package path
    ↓
env.capacity_weekly_rows
```

Do not connect the loading dock to GUI yet.

Do not start planner operations.

Just load the capacity cargo into the canonical row container.
