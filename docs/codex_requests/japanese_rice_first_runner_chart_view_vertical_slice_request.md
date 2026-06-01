# Codex Request: Japanese Rice First Runner Chart View Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_runner_chart_view_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_chart_view_vertical_slice.md
```

**Related north-star doc:**

```text
docs/design/wom_tobe_management_simulator_image.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice_completion.md
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice_completion.md
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke_completion.md
docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_completion.md
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice_completion.md
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

**Related implementation files already present:**

```text
pysi/gui/japanese_rice_first_runner_view.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/plan/capacity_constrained_first_flow.py
pysi/plan/plan_node_tree_instantiation.py
pysi/network/network_master_loader.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/capacity/capacity_weekly_rows_source.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice first runner chart view vertical slice.

The current Japanese Rice GUI wrapper already displays:

```text
summary text
weekly table
totals
management message
```

The current chart dataset helper already returns chart-ready rows and totals:

```python
build_japanese_rice_capacity_gate_chart_dataset(...)
```

This request should use that dataset to display the first simple chart in the independent Japanese Rice GUI wrapper.

The chart should show:

```text
requested
capacity
accepted
blocked
```

by week.

This request should not integrate with the existing full cockpit yet.

This request should not implement scenario comparison.

This request should not implement cost / profit logic.

This request should only move the independent GUI wrapper from:

```text
table-visible
```

to:

```text
chart-visible
```

---

## 2. Strategic Context

The current WOM near-term strategy is:

```text
Visualization before recommendation.
Stable output before GUI wiring.
Chart-ready data before chart rendering.
Small independent GUI wrapper before full cockpit integration.
```

The Japanese Rice Case now has:

```text
master data
ProductPlanNode tree
DemandAnchoredLots
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted / blocked lots
runner output contract
CLI summary/json output
independent Tkinter GUI wrapper
weekly requested / capacity / accepted / blocked table
chart-ready capacity-gate dataset
```

The next step is:

```text
display the chart-ready data as a chart.
```

---

## 3. Scope Control

### 3.1 In scope

Implement:

```text
chart series helper
optional Matplotlib figure helper
simple chart panel in independent Tkinter GUI wrapper
focused tests for chart series and figure helper
manual Windows GUI smoke path
```

The chart should consume:

```text
build_japanese_rice_capacity_gate_chart_dataset(...)
```

### 3.2 Out of scope

Do not implement:

```text
scenario comparison
before / after chart
cost / profit chart
full PSI graph
network graph
multi-gate capacity chart
leadtime-aware propagation chart
existing cockpit integration
recommendation AI
note article generation
```

Do not change planner behavior.

Do not change existing scenario master CSV files.

Do not remove or modify NetworkX.

---

## 4. Expected Changed / Added Files

Expected modified file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Expected new focused test file:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

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

## 5. Existing Data Source

Use existing helper:

```python
build_japanese_rice_capacity_gate_chart_dataset(...)
```

Current dataset contract:

```python
{
    "title": "Japanese Rice DC_KANTO capacity gate",
    "x_key": "week",
    "series": ["requested", "capacity", "accepted", "blocked"],
    "rows": [...],
    "totals": {...},
    "unit": "lot",
    "chart_hint": "line_or_grouped_bar",
}
```

Expected current rows:

```text
2027-W40:
  requested = 80
  capacity = 90
  accepted = 80
  blocked = 0

2027-W41:
  requested = 95
  capacity = 90
  accepted = 90
  blocked = 5

2027-W42:
  requested = 110
  capacity = 90
  accepted = 90
  blocked = 20
```

The chart view must not re-parse the runner result directly.

The flow should remain:

```text
runner result
  ↓
GUI model
  ↓
chart dataset
  ↓
chart series
  ↓
chart view
```

---

## 6. Required Helper: Chart Series

Add a pure helper to:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Recommended name:

```python
build_japanese_rice_capacity_gate_chart_series(dataset: dict) -> dict
```

Expected return:

```python
{
    "title": "Japanese Rice DC_KANTO capacity gate",
    "x_key": "week",
    "unit": "lot",
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],
    "series": {
        "requested": [80, 95, 110],
        "capacity": [90, 90, 90],
        "accepted": [80, 90, 90],
        "blocked": [0, 5, 20],
    },
}
```

The helper should support empty rows safely:

```python
{
    "weeks": [],
    "series": {
        "requested": [],
        "capacity": [],
        "accepted": [],
        "blocked": [],
    },
}
```

---

## 7. Recommended Helper: Matplotlib Figure

If Matplotlib is available and already used in the project environment, add:

```python
build_japanese_rice_capacity_gate_matplotlib_figure(dataset: dict)
```

Expected behavior:

```text
create a Matplotlib Figure
plot requested / capacity / accepted / blocked by week
set title
set x-axis label
set y-axis label
add legend
add light grid
return Figure
```

Recommended chart semantics:

```text
title = Japanese Rice DC_KANTO capacity gate
x-axis label = Week
y-axis label = Lots
series = requested, capacity, accepted, blocked
```

Do not call `plt.show()`.

Do not open a GUI window inside this helper.

Return a Figure object so it can be embedded later.

---

## 8. GUI Chart Embedding

Extend the independent Tkinter GUI wrapper:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

The window currently displays:

```text
summary text
weekly table
totals
management message
```

After this slice, it should display:

```text
summary text
chart panel
weekly table
totals
management message
```

If using Matplotlib, embed the chart using:

```python
FigureCanvasTkAgg
```

Recommended helper:

```python
add_capacity_gate_chart_to_window(parent, dataset: dict)
```

or a private equivalent.

This helper can return:

```text
canvas
frame
None
```

Tests do not need to verify real Tkinter rendering.

Manual smoke should verify that the chart appears.

---

## 9. Chart Type

Recommended chart type:

```text
line chart
```

Reason:

```text
weeks are ordered time buckets
trend and crossing patterns matter
requested / capacity / accepted / blocked are comparable series
```

A grouped bar chart is also acceptable if simpler.

Prefer line chart if feasible.

---

## 10. Display Requirements

The chart panel should show:

```text
requested
capacity
accepted
blocked
```

by week.

Expected visual meaning:

```text
requested rises from 80 to 95 to 110
capacity remains flat at 90
accepted rises to 90 and then stays flat
blocked rises from 0 to 5 to 20
```

The chart should make the following pattern obvious:

```text
2027-W40:
  capacity is enough

2027-W41:
  demand exceeds capacity

2027-W42:
  demand exceeds capacity more strongly
```

---

## 11. Matplotlib Safety

If Matplotlib is used:

```text
do not require a display for figure construction
do not call plt.show()
do not assert colors in tests
do not assert exact pixel output in tests
```

Tests should focus on:

```text
chart series data
figure object exists
axis title / labels
number of plotted lines if stable
```

If backend configuration is needed, tests may set a non-interactive backend before importing pyplot.

Do not make production code globally force backend unless needed.

---

## 12. Test File

Add focused test:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

---

## 13. Required Tests

### 13.1 Chart series helper

Call:

```python
result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
model = extract_japanese_rice_first_runner_gui_model(result)
dataset = build_japanese_rice_capacity_gate_chart_dataset(model)
series = build_japanese_rice_capacity_gate_chart_series(dataset)
```

Assert:

```text
series["title"] == "Japanese Rice DC_KANTO capacity gate"
series["unit"] == "lot"
series["x_key"] == "week"
series["weeks"] == ["2027-W40", "2027-W41", "2027-W42"]
```

Assert:

```text
series["series"]["requested"] == [80, 95, 110]
series["series"]["capacity"] == [90, 90, 90]
series["series"]["accepted"] == [80, 90, 90]
series["series"]["blocked"] == [0, 5, 20]
```

### 13.2 Empty dataset safety

Use:

```python
dataset = {
    "title": "Japanese Rice DC_KANTO capacity gate",
    "unit": "lot",
    "x_key": "week",
    "series": ["requested", "capacity", "accepted", "blocked"],
    "rows": [],
    "totals": {},
    "chart_hint": "line_or_grouped_bar",
}
```

Assert:

```text
weeks = []
requested = []
capacity = []
accepted = []
blocked = []
```

### 13.3 Matplotlib figure helper

If implemented, call:

```python
fig = build_japanese_rice_capacity_gate_matplotlib_figure(dataset)
```

Assert:

```text
fig is not None
axis title includes Japanese Rice DC_KANTO capacity gate
x-axis label is Week
y-axis label is Lots
```

If stable, assert:

```text
four plotted lines exist
```

Do not assert colors.

Do not assert pixel output.

### 13.4 Import safety

Import:

```python
pysi.gui.japanese_rice_first_runner_view
```

Assert import does not open a GUI window.

This behavior must remain intact.

---

## 14. Test Commands

Focused chart view test:

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

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

---

## 15. Manual GUI Smoke

After implementation, run:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Expected:

```text
Tkinter window opens.
Summary text appears.
A chart panel appears.
The chart shows requested / capacity / accepted / blocked by week.
The weekly table still appears.
Totals still appear.
Management message still appears.
```

If manual GUI smoke cannot be run in a headless environment, report that honestly.

On local Windows, manual GUI smoke should be possible.

---

## 16. Safety Boundaries

Expected modified file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Expected new test file:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Do not remove NetworkX.

Do not modify scenario master CSV files.

Do not rename or remove:

```python
run_japanese_rice_first_psi_vslice(...)
```

Do not claim full PSI planning.

Do not add cost / profit logic in this slice.

Do not add scenario comparison in this slice.

---

## 17. Acceptance Criteria

This request is complete when:

```text
build_japanese_rice_capacity_gate_chart_series(...) exists
chart series helper consumes chart dataset rows
chart series helper returns weeks and requested/capacity/accepted/blocked arrays
Matplotlib figure helper exists if feasible
if figure helper exists, it returns a Figure without opening GUI
independent GUI wrapper displays a chart panel
summary text still displays
weekly table still displays
totals still display
management message still displays
focused chart view tests pass
existing chart dataset tests pass
existing GUI wrapper tests pass
existing output contract tests pass
existing Japanese Rice tests pass
capacity integration tests pass
compileall passes
manual Windows GUI smoke confirms chart appears
no planner behavior is changed
no existing cockpit file is changed
no scenario master CSV file is changed
NetworkX is untouched
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the chart view implemented?
What test file was added?
Does build_japanese_rice_capacity_gate_chart_series(...) exist?
Does the chart series helper return weeks and requested/capacity/accepted/blocked arrays?
Was a Matplotlib figure helper implemented?
If yes, what is its name?
Does the figure helper return a Figure without opening GUI?
Was the independent Tkinter GUI wrapper updated to display a chart panel?
Does the GUI still show summary text?
Does the GUI still show weekly table?
Does the GUI still show totals?
Does the GUI still show management message?
Was manual GUI smoke run?
Did the chart appear?
Did you modify existing cockpit_tk.py?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 19. Non-Goals

This request does not implement:

```text
scenario comparison
before / after chart
cost / profit impact
multi-gate capacity flow
leadtime-aware PSI
full cockpit integration
note article generation
```

This request only adds the first chart view to the independent Japanese Rice GUI wrapper.

---

## 20. Development Meaning

Before this request:

```text
The GUI has chart-ready weekly capacity-gate data.
```

After this request:

```text
The GUI shows the capacity-gate data as a chart.
```

This is a major step in management-visible simulation.

A table gives the numbers.

A chart gives the pattern.

The pattern is what a human recognizes quickly.

In simple terms:

```text
The dashboard already has numbers.
This request gives the dashboard its first graph.
```
