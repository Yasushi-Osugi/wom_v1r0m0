# WOM Main Cockpit Run Full Plan Button Vertical Slice Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-06-03  
**Status:** Completed implementation memo  
**Target path:** `docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md
```

**Codex request:**

```text
docs/codex_requests/wom_main_cockpit_run_full_plan_button_vertical_slice_request.md
```

**Implemented commit:**

```text
cfaad1e Add cockpit Run Full Plan viewer action
```

**Branch:**

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 1. Completion Summary

The first safe main cockpit entry point to the new Run Full Plan standard-output path has been implemented, tested, manually smoke-verified on Windows, committed, and pushed.

This implementation adds a new button to the existing WOM main cockpit:

```text
Run Full Plan → Viewer
```

The existing legacy/internal button remains in place:

```text
Run Full Plan
```

The new button opens the already proven standard-output execution and viewer path:

```text
main cockpit
  ↓
Run Full Plan → Viewer
  ↓
WomRunConfig
  ↓
run_full_plan(config)
  ↓
outputs/run_full_plan/<run_id>/
  ├─ full_plan_result.json
  └─ visual_capacity_gate_weekly.csv
  ↓
Graph Panel Adapter
  ↓
Read-only Result Viewer
```

This is a major milestone because the new standard-output path is now callable from the main cockpit without replacing the existing internal WOM GUI execution flow.

---

## 2. What Was Added

### 2.1 New main cockpit button

A new button was added to the main cockpit:

```text
Run Full Plan → Viewer
```

It appears near the existing upper-right cockpit control area.

The existing button remains:

```text
Run Full Plan
```

The two paths are now visibly parallel.

### 2.2 Modified cockpit file

The file modified to add the new button was:

```text
pysi/gui/cockpit_tk.py
```

The source audit found:

```text
Existing Run Full Plan button:
  pysi/gui/cockpit_tk.py
  WOMCockpit._build_header

Existing Run Full Plan handler:
  pysi/gui/cockpit_tk.py
  WOMCockpit.run_full_plan
```

The existing handler was not replaced.

### 2.3 New helper module

A helper module was added:

```text
pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py
```

Purpose:

```text
keep the new Run Full Plan standard-output orchestration out of the large cockpit file
keep the cockpit button handler thin
make helper behavior testable without opening a GUI
```

### 2.4 New focused test file

A focused test file was added:

```text
tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

This test verifies helper import safety, run-id generation, config defaults, cockpit source wiring, public symbols, and the standard-output orchestration path.

---

## 3. Source Audit Result

The source audit confirmed the current cockpit structure.

```text
Existing Run Full Plan button:
  pysi/gui/cockpit_tk.py
  WOMCockpit._build_header

Existing Run Full Plan handler:
  pysi/gui/cockpit_tk.py
  WOMCockpit.run_full_plan

Current main cockpit launch path:
  main.py
    ↓
  launch_cockpit
    ↓
  WOMCockpit
```

This was important because the implementation needed to add a new path without disturbing the old one.

---

## 4. New Button Behavior

The new button follows this execution path:

```text
Run Full Plan → Viewer
  ↓
wom_main_cockpit_run_full_plan_viewer_action.py
  ↓
build WomRunConfig
  ↓
run_full_plan(config)
  ↓
write_full_plan_outputs(...)
  ↓
outputs/run_full_plan/<run_id>/
  ↓
launch_run_full_plan_result_viewer(run_dir)
```

This reuses the already implemented modules:

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/wom_run_full_plan_result_viewer.py
```

No viewer logic was embedded directly into the cockpit.

---

## 5. Run ID Format

The helper generates cockpit viewer run IDs in the following format:

```text
cockpit_viewer_YYYYMMDD_HHMMSS
```

Example from manual smoke:

```text
cockpit_viewer_20260603_195803
```

Output directory pattern:

```text
outputs/run_full_plan/<run_id>/
```

---

## 6. Default Scenario Root

The new helper uses a conservative default scenario root when the cockpit does not provide a selected scenario root:

```text
examples/scenarios/japanese_rice_vslice_001
```

Default scenario id:

```text
japanese_rice_vslice_001
```

This is consistent with the current diagnostic bridge path and keeps v0r1 scope small.

---

## 7. Diagnostic Bridge Status Preserved

The new path preserves the current truthfulness status.

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
```

The viewer displays this status.

This is important because the current path is not yet the final production full PSI planning engine.

The button is deliberately named:

```text
Run Full Plan → Viewer
```

not:

```text
Run Final Full Plan
```

or:

```text
Run Production Full Plan
```

---

## 8. Manual Windows GUI Smoke Confirmed

Manual Windows smoke confirmed that the main cockpit opens and the new button is visible.

Observed cockpit state:

```text
existing Run Full Plan button remains visible
new Run Full Plan → Viewer button is visible on the right side
```

The new button was clicked and the result viewer opened successfully.

Observed result viewer:

```text
WOM Run Full Plan Result Viewer - japanese_rice_vslice_001
```

Observed viewer sections:

```text
Header
Summary
Capacity Gate Chart
Weekly Table
Totals
Messages / Diagnostics
```

The viewer displayed:

```text
scenario_id = japanese_rice_vslice_001
run_id = cockpit_viewer_YYYYMMDD_HHMMSS
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

This confirms that the main cockpit can now launch the new standard-output result viewer path.

---

## 9. Capacity Gate Viewer Output Confirmed

The result viewer launched from the main cockpit displayed the same proven Japanese Rice capacity gate result.

Capacity gate:

```text
DC_KANTO S
```

Expected totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

Expected weekly rows:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

This confirms that the cockpit button did not bypass the standard-output path.

It used the same output and viewer chain as the CLI smoke path.

---

## 10. Test Results Confirmed

The following tests and checks passed.

### 10.1 Cockpit button focused test

```bat
python -m pytest tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

Result:

```text
6 passed
```

### 10.2 Viewer / adapter / bridge tests

```bat
python -m pytest tests/test_wom_run_full_plan_result_viewer_vertical_slice.py tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Result:

```text
24 passed
```

### 10.3 Compile check

```bat
python -m compileall -q pysi/gui/cockpit_tk.py pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

Result:

```text
OK
```

### 10.4 Black check

```bat
python -m black --check pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

Result:

```text
All done.
2 files would be left unchanged.
```

A full black check including `pysi/gui/cockpit_tk.py` was intentionally not used as the acceptance condition because the existing large cockpit file is not globally Black-formatted. Formatting the whole file would create broad unrelated churn.

---

## 11. Safety Confirmation

The implementation preserved the requested safety boundaries.

No changes were made to:

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/wom_run_full_plan_result_viewer.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/gui/japanese_rice_first_runner_view.py
scenario master CSV files
planner behavior
NetworkX usage
```

The existing cockpit `Run Full Plan` button and its handler were preserved.

The change is additive.

---

## 12. What Was Not Changed

This implementation does not mean:

```text
the legacy Run Full Plan button was replaced
the main cockpit now embeds the full viewer panel
the final full PSI planning engine is complete
visual_psi_weekly.csv is available
cost / money view is connected to the new viewer
tariff simulation is implemented
Rule Base / AI diagnosis is implemented
```

The new path still uses:

```text
diagnostic_smoke_bridge
```

and:

```text
full_psi_plan = False
```

This truthfulness is preserved.

---

## 13. Development Meaning

Before this implementation:

```text
Run Full Plan standard-output path could be launched from CLI and shown in a read-only viewer.
```

After this implementation:

```text
The existing main cockpit can launch the new standard-output path through a clearly separate button.
```

The new architecture now has the first working path from the production-facing cockpit to the new output-contract execution line.

Current spine:

```text
main cockpit
  ↓
Run Full Plan → Viewer
  ↓
run_full_plan
  ↓
FullPlanResult JSON / visual CSV
  ↓
Graph Panel Adapter
  ↓
Read-only Result Viewer
```

This is a major structural milestone.

---

## 14. Relationship to Existing Run Full Plan

The existing button remains:

```text
Run Full Plan
```

The new button is:

```text
Run Full Plan → Viewer
```

These two buttons represent two runways:

```text
old runway:
  legacy/internal cockpit execution path

new runway:
  standard-output contract path
```

The correct v0r1 strategy was not to close the old runway.

The correct v0r1 strategy was to open the new runway beside it.

This was achieved.

---

## 15. Relationship to North Star

The north star is:

```text
Global Weekly Economic & Management Simulation Tool
```

This milestone is important because the main cockpit now has a safe entry point into the contract-first architecture.

The architecture can now grow by adding standard outputs and adapters, such as:

```text
visual_psi_weekly.csv
visual_money_weekly.csv
kpi_summary.csv
scenario comparison datasets
tariff cost datasets
Rule Base action candidates
AI-assisted Meta Plan Action TODO
```

But the important rule remains:

```text
contract-first expansion
```

The GUI should not directly reach into planner internals.

The cockpit should orchestrate standard execution, outputs, adapters, and panels.

---

## 16. Recommended Next Step

There are two plausible next routes.

### Route A: Add PSI weekly visual output

Recommended next design:

```text
docs/design/wom_run_full_plan_visual_psi_weekly_dataset_vertical_slice.md
```

Purpose:

```text
expand Run Full Plan output beyond capacity gate
export node/product/week PSI series
prepare PSI chart adapter
```

This would make the new viewer much more meaningful.

### Route B: Embed viewer panel in cockpit

Possible later design:

```text
docs/design/wom_main_cockpit_embedded_result_panel_vertical_slice.md
```

However, this should probably wait until `visual_psi_weekly.csv` is available.

### Recommended near-term direction

The safest next technical step is likely:

```text
visual_psi_weekly.csv design
```

Reason:

```text
the cockpit button already works
the viewer already opens
the current viewer only shows capacity gate
the next value comes from richer standard output datasets
```

In other words:

```text
The cockpit entry point exists.
Now make the standard output richer.
```

---

## 17. Future Roadmap From This Point

A practical roadmap:

```text
1. Main cockpit Run Full Plan viewer button completion memo
2. visual_psi_weekly.csv design
3. visual_psi_weekly.csv Codex request
4. visual_psi_weekly.csv implementation
5. PSI graph panel adapter
6. Result viewer PSI panel
7. Scenario comparison using two FullPlanResult directories
8. visual_money_weekly.csv / kpi_summary expansion
9. tariff cost simulation dataset
10. Rule Base / AI Meta Plan Action TODO
11. main cockpit embedded result panel
12. eventual unification of legacy Run Full Plan and standard-output Run Full Plan
```

This thickens the proven line instead of replacing it.

---

## 18. Completion Statement

The WOM Main Cockpit Run Full Plan Button vertical slice is complete for v0r1.

The main cockpit now has a safe and clearly labeled entry point to the new standard-output Run Full Plan path.

The old Run Full Plan remains.

The new Run Full Plan → Viewer path works.

In simple terms:

```text
The old runway remains open.
A new runway has been built beside it.
The new runway has working lights.
A plane has actually taken off.
```
