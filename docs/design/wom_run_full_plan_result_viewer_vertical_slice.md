# WOM Run Full Plan Result Viewer Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-03  
**Status:** Design memo  
**Target path:** `docs/design/wom_run_full_plan_result_viewer_vertical_slice.md`

**Preceding design docs / memos:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
docs/design/wom_master_data_loading_and_runtime_model_map.md
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice_completion.md
```

**Implemented bridge:**

```text
be4c4a9 Add WOM run full plan bridge
```

**Implemented adapter:**

```text
4570ade Add WOM run full plan graph panel adapter
```

**Strategic role:** Display standard Run Full Plan output through a small read-only viewer  
**Primary scope:** output directory reader, graph-panel adapter reuse, Tkinter read-only result viewer, capacity gate chart/table/totals/summary  
**Current north star:** Management-visible simulation before recommendation AI  
**Development principle:** GUI displays standard output data; GUI does not read planner internals

---

## 1. Purpose

This memo defines the next vertical slice after the successful Run Full Plan bridge and graph panel adapter.

The current implemented chain is:

```text
python -m pysi.runners.run_full_plan
  ↓
full_plan_result.json
visual_capacity_gate_weekly.csv
  ↓
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
  ↓
graph panel model
chart dataset
chart series
summary text
```

The next step is to place that graph-ready data on screen with a small read-only viewer.

Target flow:

```text
run_full_plan output dir
  ↓
wom_run_full_plan_graph_panel_adapter
  ↓
read-only viewer
  ↓
capacity gate chart
  ↓
weekly table
  ↓
totals
  ↓
summary text
```

This is not yet the main cockpit.

It is a small, safe, read-only viewer that proves the standard Run Full Plan output can be displayed on screen.

---

## 2. Strategic Meaning

The WOM pipeline now has:

```text
standard launch command
standard output files
standard graph-panel data adapter
```

The next missing piece is:

```text
standard result viewer
```

This viewer is important because it proves the following end-to-end chain:

```text
Run Full Plan
  ↓
standard output
  ↓
adapter
  ↓
screen display
```

This is the first visible expression of the new WOM execution architecture.

---

## 3. Why a Read-Only Viewer First

The main cockpit should not be modified too early.

A read-only viewer is safer because it:

```text
does not change planner behavior
does not change existing GUI behavior
does not add scenario editing
does not add interactive planning
does not require main cockpit refactoring
```

It simply reads an existing output directory and displays what is already there.

This makes it an ideal bridge between:

```text
headless Run Full Plan execution
```

and:

```text
future main cockpit integration
```

---

## 4. Current Proven Assets

### 4.1 Run Full Plan bridge

Implemented in:

```text
pysi/runners/run_full_plan.py
```

Produces:

```text
outputs/run_full_plan/<run_id>/full_plan_result.json
outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
```

Current bridge status:

```text
contract_version = wom_full_plan_result_v0r1
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

### 4.2 Graph panel adapter

Implemented in:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

Provides:

```text
load_full_plan_result_json(...)
load_visual_capacity_gate_weekly_csv(...)
extract_run_full_plan_capacity_gate_graph_model(...)
extract_run_full_plan_graph_panel_model_from_output_dir(...)
build_run_full_plan_capacity_gate_chart_dataset(...)
build_run_full_plan_capacity_gate_chart_series(...)
format_run_full_plan_graph_panel_summary_text(...)
```

### 4.3 Existing visual pattern

The Japanese Rice smoke GUI already proved that a Tkinter Canvas chart can display:

```text
requested
capacity
accepted
blocked
```

by week.

This viewer should reuse the same pattern conceptually, but consume the generic adapter output.

---

## 5. Scope

### 5.1 In scope

This vertical slice should define:

```text
new read-only viewer module
CLI command to open a run output directory
adapter-based model extraction
capacity gate chart display
weekly table display
totals display
summary text display
safe unavailable display
focused tests
manual Windows GUI smoke
```

### 5.2 Out of scope

Do not implement:

```text
main cockpit integration
Run Full Plan button inside main cockpit
scenario editor
interactive capacity override editor
new planner behavior
cost / money graph
tariff graph
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

## 6. Recommended New Module

Add a new module:

```text
pysi/gui/wom_run_full_plan_result_viewer.py
```

Reason:

```text
it is generic to Run Full Plan outputs
it is separate from the Japanese Rice smoke viewer
it is separate from the main cockpit
it can later be reused by the main cockpit
```

The module should not open a GUI window on import.

Only CLI execution or explicit function call should launch the viewer.

---

## 7. Recommended CLI Command

Add a module CLI:

```bat
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/<run_id>
```

Example:

```bat
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/cli_smoke_run_full_plan_v0r1
```

Optional future convenience:

```bat
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/latest
```

The first slice only needs `--run-dir`.

---

## 8. Viewer Input Contract

The viewer reads a Run Full Plan output directory.

Required files:

```text
full_plan_result.json
visual_capacity_gate_weekly.csv
```

The viewer should not run planning by default.

It should be read-only:

```text
read files
extract model
build chart dataset
build chart series
display result
```

---

## 9. Viewer High-Level Flow

Recommended flow:

```text
main(argv)
  ↓
parse --run-dir
  ↓
extract_run_full_plan_graph_panel_model_from_output_dir(run_dir)
  ↓
build_run_full_plan_capacity_gate_chart_dataset(model)
  ↓
build_run_full_plan_capacity_gate_chart_series(dataset)
  ↓
launch Tkinter viewer
```

If the model is unavailable:

```text
display a simple unavailable message window
do not crash
```

---

## 10. Viewer Window Layout

Recommended layout:

```text
Title:
  WOM Run Full Plan Result Viewer

Header:
  scenario_id
  run_id
  run_mode
  full_psi_plan
  status

Summary:
  text from adapter summary_text

Chart:
  requested / capacity / accepted / blocked by week

Weekly table:
  week
  requested
  capacity
  accepted
  blocked
  capacity_usage_pct
  blocked_pct

Totals:
  requested
  capacity
  accepted
  blocked

Messages / diagnostics:
  bridge message
  diagnostic_smoke_bridge truthfulness note
```

The layout should be scrollable if needed.

A practical initial size:

```text
1280x900
```

This matches the previous scrollable GUI direction.

---

## 11. Chart Panel

The chart should display the series returned by:

```text
build_run_full_plan_capacity_gate_chart_series(...)
```

Expected current values:

```text
weeks = ["2027-W40", "2027-W41", "2027-W42"]

requested = [80, 95, 110]
capacity = [90, 90, 90]
accepted = [80, 90, 90]
blocked = [0, 5, 20]
```

The chart implementation can reuse a Tkinter Canvas approach.

No matplotlib dependency should be introduced.

The chart does not need to be beautiful in v0r1.

It needs to be:

```text
visible
stable
readable
testable through non-GUI helpers
```

---

## 12. Weekly Table

The weekly table should show at least:

```text
Week
Requested
Capacity
Accepted
Blocked
Usage %
Blocked %
```

Expected rows:

```text
2027-W40  80   90  80   0   88.9%   0.0%
2027-W41  95   90  90   5  100.0%   5.3%
2027-W42 110   90  90  20  100.0%  18.2%
```

Formatting may vary, but values should be preserved.

---

## 13. Totals Section

Expected current totals:

```text
Requested: 285
Capacity: 270
Accepted: 260
Blocked: 25
```

This should be visible below or beside the table.

---

## 14. Truthfulness Note

The viewer must preserve the diagnostic bridge status.

It should clearly show:

```text
Run mode: diagnostic_smoke_bridge
Full PSI plan: False
```

It should also include the note:

```text
This result is generated through diagnostic_smoke_bridge; final full PSI planning is not yet executed.
```

This prevents misunderstanding that the final full WOM planner is already complete.

---

## 15. Safe Unavailable Display

If the run directory is missing or output files are incomplete, the viewer should show a safe message instead of crashing.

Example display:

```text
WOM Run Full Plan Result Viewer

Status: unavailable
Reason: missing full_plan_result.json

No graph data is available.
```

This should be implemented through the adapter's safe unavailable model.

---

## 16. Import Safety

The module must import without opening GUI.

Test should verify:

```python
import pysi.gui.wom_run_full_plan_result_viewer
```

does not create a Tkinter window.

Only explicit launcher functions or `python -m` should start GUI.

---

## 17. Proposed Public Functions

In:

```text
pysi/gui/wom_run_full_plan_result_viewer.py
```

Recommended functions:

```python
def build_viewer_title(model: dict) -> str:
    ...

def format_capacity_gate_weekly_table_rows(model: dict) -> list[dict]:
    ...

def launch_run_full_plan_result_viewer(run_dir: str | Path) -> int:
    ...

def main(argv: list[str] | None = None) -> int:
    ...
```

Optional lower-level helpers:

```python
def _create_scrollable_frame(root) -> tuple:
    ...

def _draw_capacity_gate_chart(canvas, chart_series: dict) -> None:
    ...

def _add_summary_section(parent, model: dict) -> None:
    ...

def _add_capacity_gate_table(parent, rows: list[dict]) -> None:
    ...

def _add_totals_section(parent, totals: dict) -> None:
    ...
```

Private helper names are flexible.

---

## 18. Testing Strategy

Automated tests should avoid opening actual GUI windows where possible.

Focused test file:

```text
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Tests should cover:

```text
module import safety
title builder
weekly table row formatting
unavailable model formatting
main argument parsing if implemented without launching GUI
source inspection for __main__ guard
```

Manual Windows smoke should be performed for actual GUI display.

Because Tkinter GUI testing is environment-sensitive, keep automated tests focused on non-window helpers.

---

## 19. Test Data Strategy

Tests can reuse the same temporary Run Full Plan output pattern:

```python
from pysi.runners.run_full_plan import (
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)

config = WomRunConfig(
    scenario_root="examples/scenarios/japanese_rice_vslice_001",
    scenario_id="japanese_rice_vslice_001",
    run_id="test_viewer_v0r1",
    output_dir=str(tmp_path),
)

result = run_full_plan(config)
write_full_plan_outputs(result, output_dir=str(tmp_path))
run_dir = tmp_path / "test_viewer_v0r1"
```

Then use adapter and viewer formatting helpers.

---

## 20. Manual GUI Smoke

After implementation, manually run on Windows:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

Confirm:

```text
window opens
summary text is visible
capacity gate chart is visible
weekly table is visible
totals are visible
diagnostic_smoke_bridge note is visible
no crash
```

If the environment is headless, document that manual GUI smoke could not be verified.

---

## 21. Required Test Commands

Focused viewer tests:

```bat
python -m pytest tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Adapter tests:

```bat
python -m pytest tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Run Full Plan bridge tests:

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Compile / format:

```bat
python -m compileall -q pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
python -m black --check pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Manual GUI smoke:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

---

## 22. Safety Boundaries

Do not modify:

```text
planner behavior
pysi/runners/run_full_plan.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/gui/japanese_rice_first_runner_view.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
scenario master CSV files
NetworkX usage
```

The viewer should be additive.

It should read the Run Full Plan output files and display them.

---

## 23. Acceptance Criteria for This Design

This design is useful if it defines:

```text
why a read-only viewer comes before main cockpit integration
what output files the viewer reads
which adapter functions it reuses
what viewer module should be added
what CLI command should launch it
what layout should be shown
how unavailable output is handled
which tests should be automated
which smoke test should be manual
what should remain out of scope
```

---

## 24. Recommended Next Codex Request

Create:

```text
docs/codex_requests/wom_run_full_plan_result_viewer_vertical_slice_request.md
```

Implementation target:

```text
pysi/gui/wom_run_full_plan_result_viewer.py
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Scope:

```text
read-only viewer
uses existing graph panel adapter
Tkinter Canvas chart
weekly table
totals
summary text
safe unavailable display
import-safe tests
manual Windows GUI smoke
no main cockpit integration
```

---

## 25. Future Main Cockpit Integration

After this viewer works, the next phase can be:

```text
docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md
```

Target:

```text
main cockpit button
  ↓
run_full_plan(config)
  ↓
write outputs
  ↓
adapter
  ↓
graph panel update
```

But this should happen only after the read-only viewer is stable.

---

## 26. Completion Summary

This design defines the first read-only viewer for standard WOM Run Full Plan output.

It connects:

```text
Run Full Plan output directory
  ↓
Graph Panel Adapter
  ↓
Tkinter read-only viewer
```

The viewer is intentionally separate from the main cockpit.

It proves that the standard output connector can be displayed on screen.

In simple terms:

```text
The launch command creates the result.
The adapter converts it to instrument-panel data.
The viewer places that instrument on screen.
```
