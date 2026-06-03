# WOM Run Full Plan Result Viewer Vertical Slice Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-06-03  
**Status:** Completed implementation memo  
**Target path:** `docs/design/wom_run_full_plan_result_viewer_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/wom_run_full_plan_result_viewer_vertical_slice.md
```

**Codex request:**

```text
docs/codex_requests/wom_run_full_plan_result_viewer_vertical_slice_request.md
```

**Implemented commit:**

```text
4a0c2c9 Add WOM run full plan result viewer
```

**Branch:**

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 1. Completion Summary

The first read-only WOM Run Full Plan Result Viewer vertical slice has been implemented, tested, manually smoke-verified on Windows, committed, and pushed.

This implementation completes the first end-to-end display chain from standard WOM execution to screen display.

Completed chain:

```text
python -m pysi.runners.run_full_plan
  ↓
outputs/run_full_plan/<run_id>/
  ├─ full_plan_result.json
  └─ visual_capacity_gate_weekly.csv
  ↓
pysi.gui.wom_run_full_plan_graph_panel_adapter
  ↓
pysi.gui.wom_run_full_plan_result_viewer
  ↓
screen display
```

This is a major milestone.

It is not yet the production main cockpit.

It is the first working vertical line of:

```text
standard launch
  ↓
standard output
  ↓
standard adapter
  ↓
standard viewer
```

---

## 2. What Was Added

### 2.1 New read-only viewer module

```text
pysi/gui/wom_run_full_plan_result_viewer.py
```

This module provides a small Tkinter-based read-only viewer for a Run Full Plan output directory.

It reads:

```text
full_plan_result.json
visual_capacity_gate_weekly.csv
```

through the existing graph panel adapter:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

The viewer does not call planner internals directly.

### 2.2 New focused test file

```text
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

The test file verifies:

```text
module import safety
public helper APIs
temporary Run Full Plan output extraction
weekly table formatting
totals formatting
summary truthfulness note
unavailable model formatting
module guard
```

---

## 3. Public API Implemented

The viewer module implements the requested public helpers.

```text
build_viewer_title(...)
format_capacity_gate_weekly_table_rows(...)
build_totals_display_rows(...)
launch_run_full_plan_result_viewer(...)
main(...)
```

The CLI/module execution path is also available.

---

## 4. CLI Command

The viewer is launched with:

```bat
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/<run_id>
```

Manual smoke command used:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

---

## 5. Viewer Display Confirmed

The Windows GUI smoke confirmed that the viewer window opens and displays the Run Full Plan result.

Observed viewer title:

```text
WOM Run Full Plan Result Viewer - japanese_rice_vslice_001
```

Observed sections:

```text
Header
Summary
Capacity Gate Chart
Weekly Table
Totals
Messages / Diagnostics
```

The viewer showed the current bridge identity:

```text
scenario_id = japanese_rice_vslice_001
run_id = viewer_smoke_v0r1
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

The viewer also preserved the truthfulness note:

```text
This result is generated through diagnostic_smoke_bridge; final full PSI planning is not yet executed.
```

This is important because the current implementation is a bridge, not the final full PSI planning engine.

---

## 6. Capacity Gate Values Confirmed

The viewer displayed the Japanese Rice DC_KANTO capacity gate.

Capacity gate identity:

```text
DC_KANTO S
```

Expected weekly rows:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

Expected totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

The weekly table displayed:

```text
Week       Requested  Capacity  Accepted  Blocked  Usage %  Blocked %
2027-W40   80          90        80         0       88.9%    0.0%
2027-W41   95          90        90         5      100.0%    5.3%
2027-W42  110          90        90        20      100.0%   18.2%
```

---

## 7. Test Results Confirmed

The following tests and checks passed.

### 7.1 Viewer focused test

```bat
python -m pytest tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Result:

```text
7 passed
```

### 7.2 Graph panel adapter test

```bat
python -m pytest tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Result:

```text
11 passed
```

### 7.3 Run Full Plan bridge test

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Result:

```text
6 passed
```

### 7.4 Compile check

```bat
python -m compileall -q pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Result:

```text
OK
```

### 7.5 Black check

```bat
python -m black --check pysi/gui/wom_run_full_plan_result_viewer.py tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

Result:

```text
All done.
2 files would be left unchanged.
```

### 7.6 Manual Windows GUI smoke

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id viewer_smoke_v0r1 --format summary
python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/viewer_smoke_v0r1
```

Result:

```text
viewer window opened successfully on Windows
summary visible
capacity gate chart visible
weekly table visible
totals visible
messages / diagnostics visible
no crash observed
```

---

## 8. Safety Confirmation

The implementation preserved the requested safety boundaries.

No changes were made to:

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

The implementation is additive.

It introduces a new read-only viewer module and focused tests.

---

## 9. Development Meaning

Before this implementation:

```text
Run Full Plan outputs could be converted into graph-panel-ready data.
```

After this implementation:

```text
Run Full Plan outputs can be displayed on screen in a read-only viewer.
```

This means WOM now has the first working end-to-end vertical line:

```text
standard launch command
  ↓
standard result files
  ↓
standard adapter
  ↓
standard viewer
  ↓
visible management-facing output
```

This is a major architectural milestone.

---

## 10. Relationship to the North Star

The north star is:

```text
Global Weekly Economic & Management Simulation Tool
```

The viewer vertical slice is small, but it proves the most important direction:

```text
WOM execution should produce standard outputs.
Visualization should consume those outputs.
Main cockpit should eventually become an orchestrated viewer and controller, not a tightly coupled planner internals display.
```

The current achievement is not just a chart.

It is the first standard evidence chain:

```text
scenario execution
  ↓
documented result contract
  ↓
flat visualization dataset
  ↓
adapter
  ↓
screen
```

This is the practical foundation for management-visible simulation.

---

## 11. About the "Decorator-Like" Expansion Feeling

It is natural to feel that the current line can be expanded decorator-style toward the north star.

That feeling is partly correct.

The current architecture makes it possible to add successive layers such as:

```text
visual_psi_weekly.csv
visual_money_weekly.csv
kpi_summary.csv
scenario comparison
tariff cost simulation
rule-based diagnosis
AI-assisted Meta Plan Action TODO
```

Each can be added as a new output dataset, adapter, viewer panel, or cockpit section.

However, it is not as simple as only decorating the existing view.

The key risk is losing the clean contract boundaries.

The safe rule is:

```text
Extend by adding standard outputs and adapters.
Do not let GUI panels reach directly into planner internals.
Do not let AI or Rule Base mutate master data without validated Action TODOs.
Do not blur diagnostic_smoke_bridge with final full_psi_plan.
```

If these boundaries are preserved, the system can grow naturally.

If they are not preserved, the architecture can quickly become tangled.

Therefore, the correct mindset is:

```text
decorator-like expansion,
but contract-first expansion.
```

---

## 12. Current Architecture After This Milestone

The current architecture can be summarized as:

```text
Run Full Plan bridge
  ↓
FullPlanResult
  ↓
visual_capacity_gate_weekly.csv
  ↓
Graph Panel Adapter
  ↓
Read-only Result Viewer
```

Current implementation files:

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/wom_run_full_plan_result_viewer.py
```

Current test files:

```text
tests/test_wom_entrypoint_and_run_full_plan_contract.py
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
```

This set forms the first standard WOM execution-to-display spine.

---

## 13. What This Is Not Yet

This milestone does not yet mean:

```text
final full PSI planning is complete
main cockpit integration is complete
cost / money view is complete
tariff simulation is complete
scenario comparison is generalized
Rule Base / AI diagnosis is implemented
```

The current run mode remains:

```text
diagnostic_smoke_bridge
```

and:

```text
full_psi_plan = False
```

This truthfulness is preserved in the viewer.

---

## 14. Recommended Next Step

The next natural design step is:

```text
docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md
```

However, there are two possible routes.

### Route A: Connect to main cockpit next

```text
main cockpit button
  ↓
run_full_plan(config)
  ↓
write outputs
  ↓
adapter
  ↓
viewer-like graph panel in cockpit
```

This is attractive because it moves directly toward the production cockpit.

### Route B: Add visual_psi_weekly.csv next

```text
Run Full Plan
  ↓
visual_psi_weekly.csv
  ↓
PSI graph adapter
  ↓
PSI viewer panel
```

This strengthens the result content before cockpit integration.

### Recommended near-term choice

The safest next step is probably:

```text
docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md
```

with a very limited scope:

```text
add a button or menu path that launches / reuses the read-only viewer
do not refactor cockpit internals heavily
do not embed all logic directly
do not change planner behavior
```

This would connect the proven viewer path to the main user-facing environment.

---

## 15. Future Roadmap From This Point

A practical roadmap from here:

```text
1. Result viewer completion memo
2. Main cockpit Run Full Plan button design
3. Main cockpit Run Full Plan button Codex request
4. Minimal button implementation
5. Completion memo
6. visual_psi_weekly.csv design
7. PSI graph adapter
8. PSI viewer panel
9. Scenario comparison using two FullPlanResult directories
10. Cost / money visualization dataset
11. Tariff cost simulation dataset
12. Rule Base / AI Meta Plan Action TODO
```

This roadmap thickens the existing line rather than abandoning it.

---

## 16. Completion Statement

The WOM Run Full Plan Result Viewer vertical slice is complete for v0r1.

The first end-to-end standard execution-to-display path is now working:

```text
standard launch
  ↓
standard output
  ↓
standard adapter
  ↓
standard viewer
```

This is a foundational step toward the future main cockpit and toward the broader north star:

```text
Global Weekly Economic & Management Simulation Tool
```

In simple terms:

```text
The control tower can now launch.
The result is written in a standard form.
The adapter converts it to instrument data.
The first instrument is now visible on screen.
```
