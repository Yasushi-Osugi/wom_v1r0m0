# Codex Request: WOM Run Full Plan Result Viewer Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-03  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_run_full_plan_result_viewer_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/wom_run_full_plan_result_viewer_vertical_slice.md
```

**Preceding design docs / completion memos:**

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice_completion.md
```

**Related implementation files:**

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/japanese_rice_first_runner_view.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first read-only WOM Run Full Plan Result Viewer vertical slice.

The current Run Full Plan bridge can generate:

```text
outputs/run_full_plan/<run_id>/full_plan_result.json
outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
```

The current graph panel adapter can transform those output files into:

```text
graph panel model
chart dataset
chart series
summary text
```

This request should implement a small read-only Tkinter viewer that reads a Run Full Plan output directory and displays:

```text
summary text
capacity gate chart
weekly table
totals
diagnostic bridge note
```

The target flow is:

```text
run_full_plan output dir
  ↓
wom_run_full_plan_graph_panel_adapter
  ↓
read-only viewer
  ↓
capacity gate chart + table + totals + summary
```

This request should not integrate into the main cockpit yet.

---

## 2. Strategic Context

The current WOM execution and visualization chain is:

```text
WOM Top Routine / Pipeline Core design
  ↓
Run Full Plan bridge
  ↓
FullPlanResult JSON + visual CSV
  ↓
Graph Panel Adapter
  ↓
Graph-ready data
  ↓
Read-only Result Viewer
```

The previous implementation added:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

This request should consume that adapter.

The goal is to prove that standard Run Full Plan output can be displayed on screen without reaching into planner internals.

---

## 3. Scope

### 3.1 In scope

Implement:

```text
new read-only viewer module
CLI command: python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir ...
adapter-based model extraction
Tkinter Canvas capacity gate chart
weekly table
totals section
summary text section
safe unavailable display
focused tests for import safety and non-window helpers
manual Windows GUI smoke
```

### 3.2 Out of scope

Do not implement:

```text
main cockpit integration
Run Full Plan button in main cockpit
scenario editor
interactive capacity override editor
new planner behavior
cost / money chart
tariff chart
Rule Base / AI diagnosis
BI connector
database persistence
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
pysi/gui/wom_run_full_plan_result_viewer.py
```

Expected new test file:

```text
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

No other production files should be changed unless absolutely necessary.

In particular, do not modify:

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/japanese_rice_first_runner_view.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
scenario master CSV files
```

---

## 5. Required Public API

Add the following functions in:

```text
pysi/gui/wom_run_full_plan_result_viewer.py
```

### 5.1 `build_viewer_title(...)`

```python
def build_viewer_title(model: dict) -> str:
    ...
```

Expected behavior:

```text
return a readable title
include scenario_id or run_id when available
handle unavailable model safely
```

Example:

```text
WOM Run Full Plan Result Viewer - japanese_rice_vslice_001
```

### 5.2 `format_capacity_gate_weekly_table_rows(...)`

```python
def format_capacity_gate_weekly_table_rows(model: dict) -> list[dict]:
    ...
```

Input:

```text
adapter graph-panel model
```

Output rows should include:

```text
week
requested
capacity
accepted
blocked
capacity_usage_pct
blocked_pct
```

Expected Japanese Rice rows:

```text
2027-W40  80   90  80   0   88.9   0.0
2027-W41  95   90  90   5  100.0   5.3
2027-W42 110   90  90  20  100.0  18.2
```

Formatting may vary, but values must be preserved.

### 5.3 `build_totals_display_rows(...)`

```python
def build_totals_display_rows(model: dict) -> list[dict]:
    ...
```

Expected output:

```text
Requested 285
Capacity 270
Accepted 260
Blocked 25
```

### 5.4 `launch_run_full_plan_result_viewer(...)`

```python
def launch_run_full_plan_result_viewer(run_dir: str | Path) -> int:
    ...
```

Behavior:

```text
load adapter model from run_dir
open Tkinter viewer window
return 0 on normal close
return nonzero only for unexpected fatal errors
display safe unavailable message if model is unavailable
```

### 5.5 `main(...)`

```python
def main(argv: list[str] | None = None) -> int:
    ...
```

CLI:

```bat
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/<run_id>
```

Required argument:

```text
--run-dir
```

Optional future arguments are not required in this slice.

---

## 6. Import Safety

The module must not open a GUI window on import.

This must be true:

```python
import pysi.gui.wom_run_full_plan_result_viewer
```

Only explicit calls to:

```text
launch_run_full_plan_result_viewer(...)
main(...)
```

or module execution should launch the viewer.

---

## 7. Viewer Layout

Use Tkinter.

Recommended initial geometry:

```text
1280x900
```

The viewer should include:

```text
header
summary text
capacity gate chart
weekly table
totals section
messages / diagnostics section
```

The content should be scrollable if practical.

If implementing a scrollable frame would make the slice too large, keep the layout simple but ensure all sections can be seen in a 1280x900 window for the current Japanese Rice case.

---

## 8. Header Section

Show:

```text
WOM Run Full Plan Result Viewer
Scenario
Run ID
Run mode
Full PSI plan
Status
```

Expected values for current bridge:

```text
scenario_id = japanese_rice_vslice_001
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

---

## 9. Summary Text Section

Use the adapter-provided summary text where possible:

```text
model["summary_text"]
```

It should include:

```text
WOM Run Full Plan
Run mode: diagnostic_smoke_bridge
Full PSI plan: False
Capacity gate: DC_KANTO S
Requested: 285
Accepted: 260
Blocked: 25
```

It must preserve the truthfulness note:

```text
final full PSI planning is not yet executed
```

---

## 10. Chart Section

Use adapter helpers:

```python
build_run_full_plan_capacity_gate_chart_dataset(model)
build_run_full_plan_capacity_gate_chart_series(dataset)
```

Draw the following series using Tkinter Canvas:

```text
requested
capacity
accepted
blocked
```

Expected values:

```text
weeks = ["2027-W40", "2027-W41", "2027-W42"]

requested = [80, 95, 110]
capacity = [90, 90, 90]
accepted = [80, 90, 90]
blocked = [0, 5, 20]
```

No matplotlib dependency should be introduced.

The chart does not need to be highly polished in v0r1, but it should be readable.

---

## 11. Weekly Table Section

Show columns:

```text
Week
Requested
Capacity
Accepted
Blocked
Usage %
Blocked %
```

For current Japanese Rice bridge output, display:

```text
2027-W40  80   90  80   0   88.9%   0.0%
2027-W41  95   90  90   5  100.0%   5.3%
2027-W42 110   90  90  20  100.0%  18.2%
```

Use Tkinter labels or a simple Treeview if convenient.

Avoid making this slice dependent on complex GUI widgets.

---

## 12. Totals Section

Show:

```text
Requested: 285
Capacity: 270
Accepted: 260
Blocked: 25
```

This should be visible without needing scenario editing.

---

## 13. Messages / Diagnostics Section

Show:

```text
messages
diagnostics
management_message if available
```

Keep it concise.

If no diagnostics, show nothing or a simple note.

---

## 14. Safe Unavailable Display

If the run directory is missing or incomplete, the viewer should still open and display:

```text
Status: unavailable
Reason: <reason>
No graph data is available.
```

This should use the adapter's safe unavailable model:

```python
extract_run_full_plan_graph_panel_model_from_output_dir(...)
```

Do not allow expected missing-file errors to crash the GUI.

---

## 15. Required Tests

Add focused test file:

```text
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Automated tests should avoid opening actual GUI windows.

### 15.1 Import safety

Assert:

```python
import pysi.gui.wom_run_full_plan_result_viewer
```

does not launch a GUI.

### 15.2 Title builder

Given an available model, assert title includes:

```text
WOM Run Full Plan Result Viewer
japanese_rice_vslice_001
```

Given an unavailable model, assert title is still safe.

### 15.3 Weekly table row formatting

Create temporary Run Full Plan output using:

```python
WomRunConfig
run_full_plan
write_full_plan_outputs
extract_run_full_plan_graph_panel_model_from_output_dir
```

Then call:

```python
format_capacity_gate_weekly_table_rows(model)
```

Assert:

```text
3 rows
W40 values 80/90/80/0
W41 values 95/90/90/5
W42 values 110/90/90/20
```

### 15.4 Totals display rows

Assert totals rows contain:

```text
Requested 285
Capacity 270
Accepted 260
Blocked 25
```

### 15.5 Summary text contains truthfulness note

Assert summary text or viewer helper output includes:

```text
diagnostic_smoke_bridge
Full PSI plan: False
final full PSI planning is not yet executed
```

### 15.6 Unavailable model formatting

Call helpers with:

```text
available = False
status = unavailable
reason = missing full_plan_result.json
```

Assert:

```text
no crash
safe title
empty table rows
empty or safe totals rows
```

### 15.7 Source inspection for module guard

Optionally assert source contains:

```python
if __name__ == "__main__":
```

to ensure CLI execution path is explicit.

---

## 16. Manual GUI Smoke

After implementation, run on Windows:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

Confirm manually:

```text
window opens
summary text is visible
capacity gate chart is visible
weekly table is visible
totals are visible
diagnostic_smoke_bridge note is visible
no crash
```

If the Codex environment is headless, document that manual GUI smoke could not be verified there.

Do not fail the implementation solely because headless environment cannot open Tkinter.

---

## 17. Required Test Commands

Focused viewer test:

```bat
python -m pytest tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Adapter test:

```bat
python -m pytest tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Run Full Plan bridge test:

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Compile / format:

```bat
python -m compileall -q pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
python -m black --check pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Manual smoke commands:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

---

## 18. Safety Boundaries

Do not modify:

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/gui/japanese_rice_first_runner_view.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
scenario master CSV files
planner behavior
NetworkX usage
```

Do not implement:

```text
main cockpit integration
Run Full Plan button
scenario editing
cost / money graph
tariff graph
Rule Base / AI diagnosis
```

This request is only the read-only viewer vertical slice.

---

## 19. Acceptance Criteria

This request is complete when:

```text
pysi/gui/wom_run_full_plan_result_viewer.py exists
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py exists
viewer module imports without opening GUI
build_viewer_title(...) exists
format_capacity_gate_weekly_table_rows(...) exists
build_totals_display_rows(...) exists
launch_run_full_plan_result_viewer(...) exists
main(...) exists
CLI command is defined
viewer uses wom_run_full_plan_graph_panel_adapter
viewer displays summary text
viewer can display capacity gate chart
viewer can display weekly table
viewer can display totals
viewer handles unavailable model safely
focused tests pass
adapter tests pass
Run Full Plan bridge tests pass
compileall passes
black check passes
planner behavior unchanged
GUI behavior of existing modules unchanged
scenario master CSV files unchanged
NetworkX untouched
manual Windows GUI smoke is attempted or explicitly documented as not possible in headless environment
```

---

## 20. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
What viewer module was added?
What test file was added?
Does the module import without opening GUI?
Does build_viewer_title(...) exist?
Does format_capacity_gate_weekly_table_rows(...) exist?
Does build_totals_display_rows(...) exist?
Does launch_run_full_plan_result_viewer(...) exist?
Does main(...) exist?
What CLI command launches the viewer?
Does the viewer use wom_run_full_plan_graph_panel_adapter?
Does the viewer display summary text?
Does the viewer display capacity gate chart?
Does the viewer display weekly table?
Does the viewer display totals?
Does unavailable output display safely?
Was manual Windows GUI smoke run?
If not, why not?
Did you modify pysi/runners/run_full_plan.py?
Did you modify wom_run_full_plan_graph_panel_adapter.py?
Did you modify existing Japanese Rice runner/viewer behavior?
Did you modify main cockpit?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 21. Development Meaning

Before this request:

```text
Run Full Plan outputs could be converted into graph-panel-ready data.
```

After this request:

```text
Run Full Plan outputs can be displayed on screen in a read-only viewer.
```

This is still not the main cockpit.

It is the first standard output viewer.

In simple terms:

```text
The launch command creates the result.
The adapter creates the instrument data.
The viewer places the instrument on screen.
```
