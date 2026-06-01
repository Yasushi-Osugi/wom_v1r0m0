# Japanese Rice First Runner Chart Dataset Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_first_runner_chart_dataset_vertical_slice_request.md
```

**Related north-star doc:**

```text
docs/design/wom_tobe_management_simulator_image.md
```

**Related completion docs:**

```text
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

This completion memo records the successful completion of the Japanese Rice first runner chart dataset vertical slice.

This phase moved the Japanese Rice GUI data from:

```text
weekly table data
```

to:

```text
chart-ready dataset
```

The current GUI wrapper already displays requested / capacity / accepted / blocked by week.

This slice added a stable helper that converts those weekly rows into a chart-ready data contract with derived indicators.

This is not chart rendering yet.

This is the data bridge toward chart rendering.

---

## 2. Key Commit

Implementation commit:

```text
5dce6d2 Add Japanese Rice capacity gate chart dataset
```

Related preceding commits:

```text
02b3362 Add Japanese Rice first runner chart dataset Codex request
acbea49 Add Japanese Rice first runner chart dataset vertical slice design
b3ae91d Add Japanese Rice first runner GUI wrapper completion memo
63d7e5b Add Japanese Rice first runner GUI wrapper
39943b8 Add Japanese Rice first runner GUI wrapper Codex request
8a56a5f Add Japanese Rice first runner GUI wrapper vertical slice design
ebca2a3 Add Japanese Rice first runner output contract completion memo
6fba57d Add Japanese Rice runner output contract
faa64d1 Add Japanese Rice first runner output contract CLI smoke Codex request
```

---

## 3. Files Changed / Added

This implementation modified:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

This implementation added:

```text
tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

The commit created:

```text
2 files changed
269 insertions
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

No chart rendering was added.

---

## 4. Chart Dataset Helper Implemented

The new helper was implemented in:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Helper:

```python
build_japanese_rice_capacity_gate_chart_dataset(...)
```

The helper consumes:

```text
GUI model weekly_rows and totals
```

It can also convert a runner result through the existing GUI model extractor rather than duplicating runner logic.

Recommended flow:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
extract_japanese_rice_first_runner_gui_model(...)
    ↓
build_japanese_rice_capacity_gate_chart_dataset(...)
```

This keeps the chart dataset aligned with the stable GUI wrapper contract.

---

## 5. Dataset Contract

The helper returns a stable dataset object containing:

```text
title
unit
x_key
series
rows
totals
chart_hint
```

Expected metadata:

```text
title = Japanese Rice DC_KANTO capacity gate
unit = lot
x_key = week
series = requested, capacity, accepted, blocked
chart_hint = line_or_grouped_bar
```

This dataset is designed to support future chart rendering without forcing chart rendering in this slice.

---

## 6. Original Row Fields

Each chart row preserves the original weekly table fields:

```text
week
requested
capacity
accepted
blocked
```

These fields come from the existing GUI model weekly rows.

---

## 7. Derived Row Fields

Each chart row adds:

```text
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
capacity_usage_pct
blocked_pct
```

Definitions:

```text
shortage = blocked
unused_capacity = max(capacity - accepted, 0)
capacity_usage_ratio = accepted / capacity if capacity > 0 else 0
blocked_ratio = blocked / requested if requested > 0 else 0
capacity_usage_pct = capacity_usage_ratio * 100
blocked_pct = blocked_ratio * 100
```

All values remain numeric.

They are not formatted strings.

This is important for future chart rendering.

---

## 8. Expected Chart Rows

The current Japanese Rice chart dataset rows are:

```text
2027-W40:
  requested = 80
  capacity = 90
  accepted = 80
  blocked = 0
  shortage = 0
  unused_capacity = 10
  capacity_usage_ratio = 80 / 90
  blocked_ratio = 0
  capacity_usage_pct = 88.888...
  blocked_pct = 0

2027-W41:
  requested = 95
  capacity = 90
  accepted = 90
  blocked = 5
  shortage = 5
  unused_capacity = 0
  capacity_usage_ratio = 1.0
  blocked_ratio = 5 / 95
  capacity_usage_pct = 100.0
  blocked_pct = 5.263...

2027-W42:
  requested = 110
  capacity = 90
  accepted = 90
  blocked = 20
  shortage = 20
  unused_capacity = 0
  capacity_usage_ratio = 1.0
  blocked_ratio = 20 / 110
  capacity_usage_pct = 100.0
  blocked_pct = 18.181...
```

---

## 9. Expected Totals

The current totals are:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

The derived totals are:

```text
shortage = 25
unused_capacity = 10
capacity_usage_ratio = 260 / 270
blocked_ratio = 25 / 285
capacity_usage_pct = 96.296...
blocked_pct = 8.771...
```

These totals are now available for future summary cards and chart annotations.

---

## 10. Zero Division Safety

The helper handles zero capacity and zero requested values safely.

Example behavior for capacity = 0:

```text
capacity_usage_ratio = 0
capacity_usage_pct = 0
```

Example behavior for requested = 0:

```text
blocked_ratio = 0
blocked_pct = 0
```

This prevents chart dataset generation from failing on edge cases.

---

## 11. Empty Input Safety

The helper handles empty input safely.

For empty weekly rows and missing totals, it returns:

```text
rows = []
totals requested/capacity/accepted/blocked default to 0
derived ratios default to 0
```

This behavior is important for GUI robustness.

A chart view should be able to show an empty state rather than crashing.

---

## 12. Tests Added

Focused test file:

```text
tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

The tests verify:

```text
dataset metadata
dataset title/unit/x_key/series/chart_hint
W40/W41/W42 row values
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
capacity_usage_pct
blocked_pct
totals requested/capacity/accepted/blocked
totals shortage/unused_capacity
totals derived ratios and percentages
zero-capacity safety
empty-input safety
```

---

## 13. Tests Executed

Focused chart dataset test:

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
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

---

## 14. Safety Boundaries Honored

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
actual chart rendering
Matplotlib embedding
Plotly embedding
Tkinter chart panel
scenario comparison
cost / profit logic
multi-gate flow
leadtime-aware propagation
recommendation AI
```

This phase only added:

```text
chart-ready dataset helper
derived metric logic
focused tests
```

---

## 15. Current Japanese Rice Case State

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
chart-ready rows and totals
```

---

## 16. Development Meaning

This is a small but important visualization milestone.

Before this phase:

```text
The GUI could show a table.
```

After this phase:

```text
The GUI has chart-ready data.
```

The next chart view can now consume a stable dataset rather than re-parsing the runner output.

This keeps the future chart implementation clean.

---

## 17. Relationship to Management Visibility

The chart-ready dataset makes it easier to show the management pattern:

```text
2027-W40:
  demand/requested is below capacity
  no blocked lots
  unused capacity remains

2027-W41:
  demand exceeds capacity
  5 lots are blocked
  capacity is fully used

2027-W42:
  demand exceeds capacity more strongly
  20 lots are blocked
  capacity is fully used
  shortage grows
```

This is exactly the type of pattern that can be recognized quickly through visual display.

The dataset is now ready for such a display.

---

## 18. Still Deferred

The following remain intentionally deferred.

### 18.1 Chart rendering

Not yet implemented:

```text
line chart
grouped bar chart
Matplotlib FigureCanvasTkAgg
Plotly chart
static PNG export
```

### 18.2 Scenario comparison

Not yet implemented:

```text
base scenario
changed scenario
before / after accepted and blocked
delta chart
```

### 18.3 Cost / Profit Structure connection

Not yet implemented:

```text
accepted lots to revenue
blocked lots to lost sales
profit impact
cost structure ratio impact
```

### 18.4 Full cockpit integration

Not yet implemented:

```text
menu item or button in existing WOM cockpit
embedding chart into cockpit_tk.py
management cockpit tab
```

---

## 19. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_first_runner_chart_view_vertical_slice.md
```

Purpose:

```text
Use the chart-ready dataset to render a simple requested / capacity / accepted / blocked chart.
```

Recommended scope:

```text
add chart rendering helper
possibly use Matplotlib in the independent GUI wrapper
do not modify existing cockpit yet
do not add scenario comparison yet
```

Alternative next design:

```text
docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md
```

Purpose:

```text
Define a simple parameter change such as DC_KANTO capacity 90 -> 100 and compare accepted / blocked.
```

Recommended order:

```text
1. Chart dataset completion memo
2. Chart view vertical slice
3. Scenario variation vertical slice
4. Before / after comparison
5. Cost / profit impact
6. Existing cockpit integration
```

---

## 20. Future Chart Meaning

The first chart should answer:

```text
When does requested demand exceed capacity?
How much is accepted?
How much is blocked?
Is the shortage growing?
```

The chart-ready dataset now supports those questions.

Future chart series:

```text
requested
capacity
accepted
blocked
```

Future secondary display:

```text
capacity_usage_pct
blocked_pct
```

But v0r1 chart should remain simple.

---

## 21. Completion Summary

Completed:

```text
build_japanese_rice_capacity_gate_chart_dataset(...) implemented
helper consumes GUI model weekly_rows and totals
helper can convert runner result through GUI model extractor
helper returns requested/capacity/accepted/blocked rows
helper returns shortage and unused_capacity
helper returns capacity_usage_ratio and blocked_ratio
helper returns capacity_usage_pct and blocked_pct
helper returns safe totals with derived ratios
division by zero is handled
empty input is safe
focused chart dataset tests passed
existing GUI wrapper tests passed
existing output contract tests passed
existing Japanese Rice tests passed
capacity integration tests passed
compileall passed
planner behavior unchanged
existing cockpit files unchanged
scenario master CSV files unchanged
NetworkX untouched
no actual chart rendering added
```

Current milestone:

```text
Japanese Rice Case now has chart-ready capacity gate data.
```

In simple terms:

```text
The dashboard shows the numbers.
Now those numbers have become a graph-ready signal.
