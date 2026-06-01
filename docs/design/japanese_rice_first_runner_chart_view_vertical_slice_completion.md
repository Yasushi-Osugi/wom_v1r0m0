# Japanese Rice First Runner Chart View Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_first_runner_chart_view_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_chart_view_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_first_runner_chart_view_vertical_slice_request.md
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

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice first runner chart view vertical slice.

This phase moved the Japanese Rice Case from:

```text
GUI table-visible
```

to:

```text
GUI chart-visible
```

The chart view displays the first visible capacity-gate balance pattern:

```text
requested
capacity
accepted
blocked
```

by week.

This is an important milestone because the Japanese Rice Case now shows the first visible form of the supply-demand balance pattern.

In WOM terms, this is the first visible form of the:

```text
supply-demand Balance Line
```

or, more precisely for this vertical slice:

```text
DC_KANTO capacity-gate weekly balance line
```

This is not full PSI planning yet.

This is not scenario comparison yet.

This is not cost / profit simulation yet.

This is the first chart view for the Japanese Rice first runner.

---

## 2. Key Commit

Implementation commit:

```text
b8bd68d Add Japanese Rice first runner chart view
```

Related preceding commits:

```text
b920066 Add Japanese Rice first runner chart view Codex request
24551ce Add Japanese Rice first runner chart dataset completion memo
5dce6d2 Add Japanese Rice capacity gate chart dataset
02b3362 Add Japanese Rice first runner chart dataset Codex request
acbea49 Add Japanese Rice first runner chart dataset vertical slice design
b3ae91d Add Japanese Rice first runner GUI wrapper completion memo
63d7e5b Add Japanese Rice first runner GUI wrapper
39943b8 Add Japanese Rice first runner GUI wrapper Codex request
8a56a5f Add Japanese Rice first runner GUI wrapper vertical slice design
```

---

## 3. Files Changed / Added

This implementation modified:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

This implementation added:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

The commit created:

```text
2 files changed
235 insertions
5 deletions
```

No existing cockpit file was modified.

Specifically, this phase did not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

No planner engine file was modified.

No scenario master CSV file was modified.

No NetworkX dependency was removed or modified.

---

## 4. Chart View Implemented

The chart view was implemented in:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

The implementation adds a chart panel to the independent Japanese Rice Tkinter GUI wrapper.

The GUI wrapper now shows:

```text
summary text
chart panel
weekly table
totals
management message
```

This preserves the prior GUI content and adds the chart panel between the summary text and the weekly table.

---

## 5. Chart Series Helper Implemented

The implementation added:

```python
build_japanese_rice_capacity_gate_chart_series(...)
```

This helper consumes the existing chart dataset rows and returns:

```text
weeks
requested array
capacity array
accepted array
blocked array
```

Expected current output:

```text
weeks      = ["2027-W40", "2027-W41", "2027-W42"]
requested  = [80, 95, 110]
capacity   = [90, 90, 90]
accepted   = [80, 90, 90]
blocked    = [0, 5, 20]
```

This helper does not re-parse the runner result.

The data flow remains:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
extract_japanese_rice_first_runner_gui_model(...)
    ↓
build_japanese_rice_capacity_gate_chart_dataset(...)
    ↓
build_japanese_rice_capacity_gate_chart_series(...)
    ↓
chart panel
```

---

## 6. Chart Panel Implemented with Tkinter Canvas

The chart view was implemented as a Tkinter Canvas chart panel.

Matplotlib was not used in this implementation.

The reason is practical:

```text
Matplotlib was not available in the Codex execution environment.
```

Therefore, the chart panel was implemented directly with Tkinter Canvas.

This is acceptable for this vertical slice because the goal was not sophisticated chart rendering.

The goal was:

```text
show the requested / capacity / accepted / blocked pattern in the GUI
```

The Canvas chart is lightweight and keeps the dependency footprint small.

---

## 7. Matplotlib Figure Helper

A Matplotlib figure helper was not implemented.

Not implemented:

```python
build_japanese_rice_capacity_gate_matplotlib_figure(...)
```

Reason:

```text
Matplotlib was not installed in the Codex environment.
```

This is acceptable because the Codex request allowed an optional Matplotlib figure helper.

The implemented Tkinter Canvas chart satisfies the chart-visible requirement.

---

## 8. Chart Series Displayed

The chart panel displays:

```text
requested
capacity
accepted
blocked
```

by week.

The displayed pattern is:

```text
requested: 80 → 95 → 110
capacity:  90 → 90 → 90
accepted:  80 → 90 → 90
blocked:    0 → 5 → 20
```

This is the first visible WOM chart showing how demand begins to exceed capacity and how blocked lots grow.

---

## 9. Management Pattern Made Visible

The chart makes the following pattern visible at a glance:

```text
2027-W40:
  requested demand is below capacity
  no blocked lots
  accepted equals requested

2027-W41:
  requested demand exceeds capacity
  5 lots are blocked
  accepted reaches capacity

2027-W42:
  requested demand exceeds capacity more strongly
  20 lots are blocked
  accepted remains capped by capacity
```

This is the first concrete visual form of the Rice Case capacity constraint.

The chart therefore supports the current WOM principle:

```text
Visualization before recommendation.
```

---

## 10. GUI Display Confirmed on Windows

Manual GUI smoke was run locally on Windows.

Command:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Observed result:

```text
Tkinter window opened.
Summary text displayed.
Chart panel displayed.
Weekly table displayed.
Totals displayed.
Management message displayed.
```

The chart showed the expected requested / capacity / accepted / blocked series.

This confirms that the Japanese Rice Case is now chart-visible in the independent GUI wrapper.

---

## 11. Tests Added

Focused test file:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

The tests verify:

```text
chart series helper exists
chart series helper returns expected weeks
chart series helper returns requested / capacity / accepted / blocked arrays
empty dataset safety
import safety
```

The tests intentionally avoid fragile pixel-level GUI rendering assertions.

---

## 12. Tests Executed

Focused chart view test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

Observed result:

```text
3 passed
```

Existing chart dataset test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

Observed result:

```text
6 passed
```

Existing GUI wrapper test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Observed result:

```text
7 passed
```

Existing output contract test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Observed result:

```text
9 passed
```

Existing Japanese Rice related tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
55 passed
```

Capacity integration / diagnostic tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
40 passed
```

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

Manual Windows GUI smoke:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Observed result:

```text
GUI chart window displayed successfully
```

---

## 13. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
existing cockpit layout
NetworkX dependency
scenario master CSV files
full PSI planner behavior
capacity enforcement engine behavior
inventory calculation
CO / backlog calculation
cost / price / profit behavior
```

This phase did not add:

```text
scenario comparison
cost / profit logic
multi-gate capacity flow
leadtime-aware propagation
recommendation AI
note article generation
```

This phase only added:

```text
chart series helper
Tkinter Canvas chart panel
focused tests
```

---

## 14. Current Japanese Rice Case State

The Japanese Rice Case now has:

```text
Capacity master
Demand master
Network master
Actual ProductPlanNode tree
DemandAnchoredLot attachment to MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted_lot_ids / blocked_lot_ids
first PSI smoke runner exposing diagnostics
stable output contract
CLI summary / JSON smoke output
independent GUI wrapper
weekly requested / capacity / accepted / blocked table
chart-ready capacity gate dataset
visible capacity gate chart
```

The current visibility chain is:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
contract_version
demo_summary
cli_summary_lines
    ↓
extract_japanese_rice_first_runner_gui_model(...)
    ↓
weekly_rows
    ↓
build_japanese_rice_capacity_gate_chart_dataset(...)
    ↓
build_japanese_rice_capacity_gate_chart_series(...)
    ↓
Tkinter Canvas chart panel
```

---

## 15. Development Meaning

This is a major visualization milestone.

Before this phase:

```text
The GUI could show the weekly capacity-gate table.
```

After this phase:

```text
The GUI can show the weekly capacity-gate pattern as a chart.
```

A table gives the numbers.

A chart gives the pattern.

This phase therefore moves the Japanese Rice Case closer to management-visible simulation.

---

## 16. Relationship to WOM North Star

The current WOM north star is:

```text
Management-visible simulation before recommendation AI.
```

This chart view supports that direction because it makes the weekly supply-demand imbalance visible without requiring a recommendation engine.

The chart does not tell the manager what to do yet.

It first shows:

```text
where demand exceeds capacity
how accepted lots are capped
how blocked lots grow
```

This is the right order.

First visibility.

Then comparison.

Then evaluation.

Then recommendation.

---

## 17. Relationship to Supply-Demand Balance Line

This slice shows the first simple form of the supply-demand balance line.

In this vertical slice, the line is still limited to:

```text
DC_KANTO S capacity gate
three weeks
one product
one market demand source
```

But the concept is already visible:

```text
requested demand line
capacity line
accepted flow line
blocked shortage line
```

The chart makes it possible to recognize the imbalance pattern visually.

This is a foundational step toward the future WOM balance-line visualization across:

```text
MOM nodes
DAD nodes
capacity gates
lanes
products
scenarios
```

---

## 18. Still Deferred

The following remain intentionally deferred.

### 18.1 Scenario comparison

Not yet implemented:

```text
base scenario
changed scenario
before / after chart
delta accepted
delta blocked
delta shortage
```

### 18.2 Cost / Profit Structure connection

Not yet implemented:

```text
accepted lots to revenue
blocked lots to lost sales
profit impact
cost structure ratio impact
```

### 18.3 Full cockpit integration

Not yet implemented:

```text
menu item or button in existing WOM cockpit
embedding chart into cockpit_tk.py
management cockpit tab
```

### 18.4 Multi-gate capacity visualization

Not yet implemented:

```text
RICE_MILL_A capacity chart
FARM_REGION_A capacity chart
multi-stage bottleneck visualization
```

### 18.5 Full PSI chart

Not yet implemented:

```text
S / CO / I / P time-series chart
leadtime-aware propagation
inventory carry-over
CO / backlog
```

---

## 19. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md
```

Purpose:

```text
Define a small scenario variation such as DC_KANTO capacity 90 -> 100 and compare the resulting accepted / blocked pattern.
```

Alternative next design:

```text
docs/design/japanese_rice_first_runner_chart_view_completion.md
```

Only needed if a shorter public-facing completion summary is desired.

Recommended order:

```text
1. Chart view completion memo
2. Scenario variation vertical slice
3. Before / after comparison chart
4. Cost / profit impact
5. Existing cockpit integration
```

The reason is simple:

```text
The chart now shows one scenario.
The next meaningful step is to change the scenario and compare the result.
```

---

## 20. Future Scenario Comparison Meaning

The first scenario variation could be:

```text
DC_KANTO capacity 90 -> 100
```

Expected management question:

```text
If DC_KANTO capacity increases from 90 to 100,
how much blocked demand is reduced?
```

This would be the first step from:

```text
visualization
```

to:

```text
management evaluation
```

It should still remain simple and deterministic.

---

## 21. Completion Summary

Completed:

```text
build_japanese_rice_capacity_gate_chart_series(...) implemented
chart series helper returns weeks and requested/capacity/accepted/blocked arrays
Tkinter Canvas chart panel implemented
independent GUI wrapper displays chart panel
summary text still displays
weekly table still displays
totals still display
management message still displays
manual Windows GUI smoke confirms chart appears
focused chart view tests passed
existing chart dataset tests passed
existing GUI wrapper tests passed
existing output contract tests passed
existing Japanese Rice tests passed
capacity integration tests passed
compileall passed
planner behavior unchanged
existing cockpit files unchanged
scenario master CSV files unchanged
NetworkX untouched
no scenario comparison added
no cost / profit logic added
```

Current milestone:

```text
Japanese Rice Case now has a visible capacity-gate chart.
```

In simple terms:

```text
The dashboard already had numbers.
Now the dashboard has its first graph.
The first visible supply-demand balance pattern has appeared.
