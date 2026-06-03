# Codex Request: WOM Run Full Plan Graph Panel Adapter Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-03  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_run_full_plan_graph_panel_adapter_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
```

**Preceding design docs / memos:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
docs/design/wom_master_data_loading_and_runtime_model_map.md
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
```

**Related implementation:**

```text
pysi/runners/run_full_plan.py
tests/test_wom_entrypoint_and_run_full_plan_contract.py
pysi/gui/japanese_rice_first_runner_view.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first WOM Run Full Plan Graph Panel Adapter vertical slice.

The current Run Full Plan bridge can generate:

```text
outputs/run_full_plan/<run_id>/full_plan_result.json
outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
```

This request should implement a safe, headless, testable adapter that reads those Run Full Plan outputs and builds:

```text
graph panel model
chart dataset
chart series
summary text
```

This request should not open a GUI window.

This request should not modify planner behavior.

This request should not modify the existing Japanese Rice runner contract.

The goal is to prove the next connection:

```text
python -m pysi.runners.run_full_plan
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
  ↓
Run Full Plan Graph Panel Adapter
  ↓
capacity gate chart dataset
  ↓
chart series
```

---

## 2. Strategic Context

The current implementation sequence is:

```text
WOM Top Routine / Pipeline Core design
  ↓
Master Data Loading / Runtime Model Map
  ↓
Source-code grounded Master Data Audit
  ↓
Entrypoint and Run Full Plan Contract
  ↓
Run Full Plan bridge implementation
  ↓
Run Full Plan Graph Panel Adapter design
  ↓
Run Full Plan Graph Panel Adapter implementation
```

The previous implementation added:

```text
pysi/runners/run_full_plan.py
```

with:

```text
WomRunConfig
FullPlanResult
run_full_plan(config)
full_plan_result.json export
visual_capacity_gate_weekly.csv export
```

This request should consume those outputs.

---

## 3. Scope

### 3.1 In scope

Implement:

```text
new adapter module
full_plan_result.json loader
visual_capacity_gate_weekly.csv loader
capacity gate graph panel model extractor
chart dataset builder
chart series builder
summary text formatter
safe unavailable model handling
focused tests
```

### 3.2 Out of scope

Do not implement:

```text
GUI window
main cockpit integration
new PSI planning logic
cost / money chart
tariff chart
Rule Base / AI diagnosis
scenario editor
database persistence
BI connector
```

Do not modify:

```text
planner behavior
existing Japanese Rice runner contract
scenario master CSV files
NetworkX usage
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

---

## 4. Expected Changed / Added Files

Expected new file:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

Expected new test file:

```text
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

No other production files should be changed unless absolutely necessary.

In particular, do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
scenario master CSV files
```

---

## 5. Required Public API

Add the following functions in:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

### 5.1 `load_full_plan_result_json(...)`

```python
def load_full_plan_result_json(path: str | Path) -> dict:
    ...
```

Requirements:

```text
read JSON
return dict
raise FileNotFoundError for missing file
raise ValueError or json.JSONDecodeError for malformed JSON
do not silently swallow low-level loader errors
```

### 5.2 `load_visual_capacity_gate_weekly_csv(...)`

```python
def load_visual_capacity_gate_weekly_csv(path: str | Path) -> list[dict]:
    ...
```

Requirements:

```text
read CSV
return list of dict rows
preserve CSV row order
convert numeric columns to int/float where appropriate
keep week as string
keep scenario_id, run_id, product_name, node_name, capacity_type as strings
```

Numeric fields include:

```text
requested
capacity
accepted
blocked
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
capacity_usage_pct
blocked_pct
```

### 5.3 `extract_run_full_plan_capacity_gate_graph_model(...)`

```python
def extract_run_full_plan_capacity_gate_graph_model(
    *,
    full_plan_result: dict,
    capacity_gate_rows: list[dict],
) -> dict:
    ...
```

Return a graph-panel model with at least:

```text
available
contract_version
run_id
scenario_id
scenario_root
run_mode
full_psi_plan
status
product_name
node_name
capacity_type
rows
totals
summary_text
messages
diagnostics
management_message
```

Expected for Japanese Rice bridge:

```text
available = True
contract_version = wom_full_plan_result_v0r1
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
scenario_id = japanese_rice_vslice_001
node_name = DC_KANTO
capacity_type = S
```

Expected totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 5.4 `extract_run_full_plan_graph_panel_model_from_output_dir(...)`

```python
def extract_run_full_plan_graph_panel_model_from_output_dir(output_dir: str | Path) -> dict:
    ...
```

Requirements:

```text
read output_dir/full_plan_result.json
read output_dir/visual_capacity_gate_weekly.csv
return available model if both are valid
return safe unavailable model if files are missing or malformed
do not raise to GUI layer for expected missing output files
```

Unavailable model shape:

```text
available = False
status = unavailable
reason = concise reason
rows = []
totals = {}
summary_text = concise explanation
messages = []
diagnostics = [...]
```

### 5.5 `build_run_full_plan_capacity_gate_chart_dataset(...)`

```python
def build_run_full_plan_capacity_gate_chart_dataset(model: dict) -> dict:
    ...
```

Return dataset contract:

```text
title
unit
x_key
series
rows
totals
chart_hint
```

Expected fields:

```text
title = WOM Run Full Plan Capacity Gate
unit = lot
x_key = week
chart_hint = line_or_grouped_bar
```

Series should include:

```text
requested
capacity
accepted
blocked
```

Rows should include:

```text
week
requested
capacity
accepted
blocked
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
capacity_usage_pct
blocked_pct
```

### 5.6 `build_run_full_plan_capacity_gate_chart_series(...)`

```python
def build_run_full_plan_capacity_gate_chart_series(dataset: dict) -> dict:
    ...
```

Return:

```text
weeks
series
```

Expected Japanese Rice bridge result:

```text
weeks = ["2027-W40", "2027-W41", "2027-W42"]

series.requested = [80, 95, 110]
series.capacity = [90, 90, 90]
series.accepted = [80, 90, 90]
series.blocked = [0, 5, 20]
```

### 5.7 `format_run_full_plan_graph_panel_summary_text(...)`

```python
def format_run_full_plan_graph_panel_summary_text(model: dict) -> str:
    ...
```

Include stable, concise lines:

```text
WOM Run Full Plan
Scenario: japanese_rice_vslice_001
Run mode: diagnostic_smoke_bridge
Full PSI plan: False
Status: success

Capacity gate: DC_KANTO S
Requested: 285
Capacity: 270
Accepted: 260
Blocked: 25
```

Also include a truthfulness note:

```text
This result is generated through diagnostic_smoke_bridge; final full PSI planning is not yet executed.
```

---

## 6. Optional `__all__`

If this module follows existing project style, export the public functions through `__all__`.

Suggested:

```python
__all__ = [
    "load_full_plan_result_json",
    "load_visual_capacity_gate_weekly_csv",
    "extract_run_full_plan_capacity_gate_graph_model",
    "extract_run_full_plan_graph_panel_model_from_output_dir",
    "build_run_full_plan_capacity_gate_chart_dataset",
    "build_run_full_plan_capacity_gate_chart_series",
    "format_run_full_plan_graph_panel_summary_text",
]
```

---

## 7. Input Data Source for Tests

The tests should use the existing Run Full Plan bridge to create temporary outputs.

Recommended pattern:

```python
from pysi.runners.run_full_plan import (
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)

config = WomRunConfig(
    scenario_root="examples/scenarios/japanese_rice_vslice_001",
    scenario_id="japanese_rice_vslice_001",
    run_id="test_graph_adapter_v0r1",
    output_dir=str(tmp_path),
)

result = run_full_plan(config)
write_full_plan_outputs(result, output_dir=str(tmp_path))
run_dir = tmp_path / "test_graph_adapter_v0r1"
```

Then load:

```text
run_dir/full_plan_result.json
run_dir/visual_capacity_gate_weekly.csv
```

This keeps the test grounded in the actual bridge output.

---

## 8. Required Tests

Add focused test file:

```text
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

### 8.1 Import safety

Assert the module imports without opening a GUI window.

```text
import pysi.gui.wom_run_full_plan_graph_panel_adapter
```

### 8.2 Load JSON and CSV

Use temporary Run Full Plan output.

Assert:

```text
full_plan_result["contract_version"] == "wom_full_plan_result_v0r1"
len(capacity_gate_rows) == 3
```

### 8.3 Extract available graph model

Assert:

```text
model["available"] is True
model["contract_version"] == "wom_full_plan_result_v0r1"
model["run_mode"] == "diagnostic_smoke_bridge"
model["full_psi_plan"] is False
model["status"] == "success"
model["scenario_id"] == "japanese_rice_vslice_001"
model["node_name"] == "DC_KANTO"
model["capacity_type"] == "S"
```

Assert totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 8.4 Preserve weekly rows

Assert rows contain:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

### 8.5 Build chart dataset

Assert:

```text
dataset["title"] == "WOM Run Full Plan Capacity Gate"
dataset["unit"] == "lot"
dataset["x_key"] == "week"
dataset["chart_hint"] == "line_or_grouped_bar"
```

Assert dataset rows and totals preserve expected values.

### 8.6 Build chart series

Assert:

```text
series["weeks"] == ["2027-W40", "2027-W41", "2027-W42"]
series["series"]["requested"] == [80, 95, 110]
series["series"]["capacity"] == [90, 90, 90]
series["series"]["accepted"] == [80, 90, 90]
series["series"]["blocked"] == [0, 5, 20]
```

### 8.7 Summary text

Assert summary text includes:

```text
WOM Run Full Plan
diagnostic_smoke_bridge
Full PSI plan: False
DC_KANTO S
Requested: 285
Accepted: 260
Blocked: 25
final full PSI planning is not yet executed
```

### 8.8 Missing output dir

Call:

```python
extract_run_full_plan_graph_panel_model_from_output_dir(tmp_path / "missing")
```

Assert:

```text
available is False
status == unavailable
rows == []
totals == {}
reason is present
```

### 8.9 Missing CSV

Create output dir with only `full_plan_result.json`.

Assert safe unavailable model.

### 8.10 Missing JSON

Create output dir with only `visual_capacity_gate_weekly.csv`.

Assert safe unavailable model.

### 8.11 Empty rows safety

Pass empty rows to the lower-level extractor.

Assert:

```text
available is False or available is True with empty totals
```

Use whichever design is implemented, but it must not crash.

---

## 9. Required Test Commands

Focused test:

```bat
python -m pytest tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Existing Run Full Plan bridge test:

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Existing Japanese Rice GUI/runner tests:

```bat
python -m pytest tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Compile and format:

```bat
python -m compileall -q pysi/gui/wom_run_full_plan_graph_panel_adapter.py tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
python -m black --check pysi/gui/wom_run_full_plan_graph_panel_adapter.py tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

---

## 10. Safety Boundaries

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/runners/run_full_plan.py
scenario master CSV files
NetworkX usage
planner behavior
```

Modification of `pysi/runners/run_full_plan.py` should not be necessary.

If a tiny change is required, explain why and keep it backward compatible.

Do not open GUI windows in tests.

Do not introduce matplotlib dependency in this request.

Do not implement a Tkinter viewer in this request.

This is a data adapter vertical slice.

---

## 11. Acceptance Criteria

This request is complete when:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py exists
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py exists
load_full_plan_result_json(...) exists
load_visual_capacity_gate_weekly_csv(...) exists
extract_run_full_plan_capacity_gate_graph_model(...) exists
extract_run_full_plan_graph_panel_model_from_output_dir(...) exists
build_run_full_plan_capacity_gate_chart_dataset(...) exists
build_run_full_plan_capacity_gate_chart_series(...) exists
format_run_full_plan_graph_panel_summary_text(...) exists
adapter imports without opening a GUI window
adapter reads full_plan_result.json
adapter reads visual_capacity_gate_weekly.csv
adapter returns available graph model for Japanese Rice bridge output
adapter preserves W40/W41/W42 values
adapter totals requested=285, capacity=270, accepted=260, blocked=25
chart dataset is generated
chart series is generated
summary text includes diagnostic_smoke_bridge truthfulness note
missing output files return safe unavailable model
focused tests pass
existing Run Full Plan bridge tests pass
existing Japanese Rice GUI/runner tests pass
compileall passes
black check passes
planner behavior unchanged
GUI behavior unchanged
scenario master CSV files unchanged
NetworkX untouched
```

---

## 12. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
What adapter module was added?
What test file was added?
Does the adapter import without opening GUI?
Does load_full_plan_result_json(...) exist?
Does load_visual_capacity_gate_weekly_csv(...) exist?
Does extract_run_full_plan_capacity_gate_graph_model(...) exist?
Does extract_run_full_plan_graph_panel_model_from_output_dir(...) exist?
Does build_run_full_plan_capacity_gate_chart_dataset(...) exist?
Does build_run_full_plan_capacity_gate_chart_series(...) exist?
Does format_run_full_plan_graph_panel_summary_text(...) exist?
Does the adapter read full_plan_result.json?
Does the adapter read visual_capacity_gate_weekly.csv?
Does the model show contract_version wom_full_plan_result_v0r1?
Does the model show run_mode diagnostic_smoke_bridge?
Does the model preserve full_psi_plan False?
Does the model show DC_KANTO S?
Does the model show totals requested=285 capacity=270 accepted=260 blocked=25?
Does the chart series contain W40/W41/W42 expected values?
Does missing output dir return unavailable model safely?
Did you modify pysi/runners/run_full_plan.py?
Did you modify existing Japanese Rice runner contract?
Did you modify GUI behavior?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 13. Development Meaning

Before this request:

```text
Run Full Plan can generate standard result files.
```

After this request:

```text
Run Full Plan result files can be transformed into graph-panel-ready data.
```

This is still not the final main cockpit.

It is the next necessary adapter layer.

In simple terms:

```text
The launch command now produces a result.
This adapter turns that result into instrument-panel data.
```
