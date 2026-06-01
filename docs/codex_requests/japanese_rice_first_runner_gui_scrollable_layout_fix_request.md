# Codex Request: Japanese Rice First Runner GUI Scrollable Layout Fix

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_runner_gui_scrollable_layout_fix_request.md`

**Related design docs:**

```text
docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md
docs/design/japanese_rice_first_runner_chart_view_vertical_slice_completion.md
docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice_completion.md
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice_completion.md
```

**Related Codex requests:**

```text
docs/codex_requests/japanese_rice_first_runner_scenario_variation_vertical_slice_request.md
docs/codex_requests/japanese_rice_first_runner_chart_view_vertical_slice_request.md
docs/codex_requests/japanese_rice_first_runner_chart_dataset_vertical_slice_request.md
docs/codex_requests/japanese_rice_first_runner_gui_wrapper_vertical_slice_request.md
```

**Related implementation file:**

```text
pysi/gui/japanese_rice_first_runner_view.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement a scrollable layout fix for the independent Japanese Rice first runner GUI wrapper.

After adding the scenario variation section, the GUI content became vertically larger than the initial window height.

On local Windows GUI smoke, the bottom scenario variation text is partially hidden near the bottom edge of the window.

The target section includes text such as:

```text
Scenario variation:
Base DC_KANTO capacity: 90
Capacity-up capacity: 100
Accepted lots: 260 -> 275
Blocked lots: 25 -> 10
Blocked reduction: 15 lots / 60.0%
```

The functional scenario variation implementation is correct.

The issue is layout only.

This request should fix the GUI so the full content can be viewed reliably.

---

## 2. Strategic Context

The current Japanese Rice Case has progressed through:

```text
runner
CLI summary
GUI table
chart-ready dataset
GUI chart
scenario variation comparison
```

The current issue is not data logic.

The current issue is:

```text
the GUI wrapper now has more content than the window can show vertically
```

This is expected as WOM moves from simple visibility to comparison evaluation.

Therefore, the independent GUI wrapper needs a more robust layout foundation.

The correct next step is a scrollable window layout.

---

## 3. Scope Control

### 3.1 In scope

Implement:

```text
scrollable vertical layout for the independent Japanese Rice GUI wrapper
safe containment of all existing sections
manual Windows GUI smoke path
focused tests for import safety and helper availability
```

The GUI should show all sections through scrolling:

```text
header
scenario info
summary text
capacity-gate chart panel
weekly table
totals
management message
scenario variation section
```

### 3.2 Out of scope

Do not implement:

```text
new scenario logic
new comparison logic
comparison chart rendering
full cockpit integration
cost / profit logic
full scenario editor
database persistence
CSV master mutation
recommendation AI
```

Do not modify planner behavior.

Do not modify scenario master CSV files.

Do not remove or modify NetworkX.

Do not modify existing cockpit files.

---

## 4. Expected Changed / Added Files

Expected modified file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Optional focused test file if useful:

```text
tests/test_japanese_rice_first_runner_gui_scrollable_layout_fix.py
```

However, if the fix is purely GUI layout and hard to test without opening a real window, it is acceptable to update existing focused tests only if needed.

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

No scenario master CSV changes.

No planner behavior changes.

---

## 5. Current GUI Sections

The independent GUI currently displays the following sections:

```text
1. Header
2. Scenario info
3. Summary text
4. Chart panel
5. Weekly table
6. Totals
7. Management message
8. Scenario variation section
```

The scenario variation section was added below the existing management message.

The content is now too tall for the initial window.

Therefore, the GUI must allow vertical scrolling.

---

## 6. Required Layout Direction

Use a scrollable Tkinter container.

Recommended pattern:

```text
root window
  ↓
outer frame
  ↓
canvas
  ↓
vertical scrollbar
  ↓
scrollable inner frame
```

Place all current content inside the scrollable inner frame.

Recommended helper:

```python
create_scrollable_container(root_or_parent) -> tuple[tk.Frame, tk.Canvas, tk.Scrollbar]
```

or a private helper equivalent:

```python
_create_scrollable_frame(parent)
```

Expected behavior:

```text
returns a frame into which all GUI sections can be packed
updates scrollregion when content size changes
supports mouse wheel scrolling if feasible
does not open GUI on import
```

---

## 7. Required Behavior

The GUI should continue to be launched with:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Expected behavior after fix:

```text
Tkinter window opens.
Header appears.
Summary appears.
Chart panel appears.
Weekly table appears.
Totals appear.
Management message appears.
Scenario variation section appears.
If the lower section does not fit in the initial window, the user can scroll down to it.
The scenario variation text is no longer permanently hidden.
```

---

## 8. Initial Window Size

Set a practical initial window size.

Recommended:

```text
width: 1200 to 1400
height: 850 to 950
```

Example:

```python
root.geometry("1280x900")
```

This alone is not enough.

The main fix should still be a scrollable layout.

Reason:

```text
future comparison sections and charts will continue to increase vertical content
```

---

## 9. Mouse Wheel Support

If feasible, add mouse wheel support.

Expected behavior on Windows:

```text
mouse wheel scrolls the scrollable canvas vertically
```

Implementation can bind:

```python
<MouseWheel>
```

Optional Linux support:

```python
<Button-4>
<Button-5>
```

Do not over-engineer this.

If mouse wheel support is too invasive, scrollbar support is enough for v0r1.

---

## 10. Existing Content Must Remain

Do not remove or regress any existing content.

The GUI must still show:

```text
summary text
chart panel
weekly table
totals
management message
scenario variation section
```

The chart panel should still show:

```text
requested
capacity
accepted
blocked
```

The weekly table should still show:

```text
2027-W40 requested=80 capacity=90 accepted=80 blocked=0
2027-W41 requested=95 capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

The scenario variation section should still show:

```text
Base capacity 90
Capacity-up capacity 100
Accepted lots 260 -> 275
Blocked lots 25 -> 10
Blocked reduction 15 lots / 60.0%
```

---

## 11. Safety Requirements

Do not change any calculation helpers:

```text
build_capacity_override_chart_dataset(...)
build_capacity_gate_scenario_comparison(...)
format_capacity_gate_scenario_comparison_text(...)
build_japanese_rice_capacity_gate_chart_dataset(...)
build_japanese_rice_capacity_gate_chart_series(...)
extract_japanese_rice_first_runner_gui_model(...)
```

Only change layout code unless a small refactor is needed for safe packing.

Do not change expected numeric outputs.

---

## 12. Test Strategy

GUI layout is difficult to test without opening a real window.

Therefore, tests should focus on:

```text
module import safety
helper functions still exist
scenario variation helper outputs unchanged
chart helper outputs unchanged
```

If adding a new test file, keep it lightweight:

```text
tests/test_japanese_rice_first_runner_gui_scrollable_layout_fix.py
```

Suggested tests:

```text
import does not open GUI
_launch_model_window or scroll helper exists if public/private access is practical
scenario variation text helper still includes 25 -> 10 and 60.0%
```

Do not create a real Tkinter root in CI unless already safe.

Manual Windows GUI smoke is required for layout confirmation.

---

## 13. Required Test Commands

Focused scenario variation test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
```

Existing chart view test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

Existing chart dataset test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

Existing GUI wrapper test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Existing output contract test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing related Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile and format check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py
python -m black --check pysi/gui/japanese_rice_first_runner_view.py
```

If a new test file is added:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_gui_scrollable_layout_fix.py
python -m black --check pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_gui_scrollable_layout_fix.py
```

---

## 14. Manual Windows GUI Smoke

Run:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Expected manual result:

```text
GUI opens.
Chart appears.
Weekly table appears.
Totals appear.
Management message appears.
Scenario variation section can be fully viewed.
If not visible at first, vertical scrolling reveals it.
No content is permanently hidden behind the window edge.
```

This manual smoke is the most important acceptance check for this layout fix.

---

## 15. Acceptance Criteria

This request is complete when:

```text
independent Japanese Rice GUI wrapper uses a scrollable vertical layout
all existing GUI sections are packed inside the scrollable content area
scenario variation text is not permanently hidden
vertical scrollbar works
mouse wheel works if feasible
summary text still displays
chart panel still displays
weekly table still displays
totals still display
management message still displays
scenario variation section still displays
focused scenario variation tests still pass
existing chart view tests still pass
existing chart dataset tests still pass
existing GUI wrapper tests still pass
existing output contract tests still pass
existing Japanese Rice tests still pass
capacity integration tests still pass
compileall passes
black check passes
manual Windows GUI smoke confirms the lower section can be viewed
planner behavior unchanged
existing cockpit files unchanged
scenario master CSV files unchanged
NetworkX untouched
```

---

## 16. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the scrollable layout implemented?
Was a scrollable container added?
Was a vertical scrollbar added?
Was mouse wheel support added?
Does the GUI still show summary text?
Does the GUI still show chart panel?
Does the GUI still show weekly table?
Does the GUI still show totals?
Does the GUI still show management message?
Does the GUI still show scenario variation section?
Can the scenario variation text be fully viewed by scrolling?
Was manual Windows GUI smoke run?
Did you modify existing cockpit_tk.py?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 17. Non-Goals

This request does not implement:

```text
new scenario calculations
comparison chart
cost / profit impact
full cockpit integration
scenario editor
database persistence
recommendation AI
```

This request is only a GUI layout fix.

---

## 18. Development Meaning

Before this request:

```text
The GUI can calculate and partially display scenario variation text,
but the bottom section may be hidden by the window edge.
```

After this request:

```text
The GUI can display the full scenario variation result reliably through scrolling.
```

This is a necessary usability fix.

In simple terms:

```text
The comparison result exists.
Now it must be visible.
```
