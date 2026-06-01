# Japanese Rice First Runner Chart Dataset Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice.md`

**Strategic role:** Convert the Japanese Rice GUI wrapper weekly table data into a stable chart-ready dataset  
**Primary case:** Japanese Rice Case  
**Current north star:** Management-visible simulation before recommendation AI  
**Immediate goal:** Prepare requested / capacity / accepted / blocked weekly data for a simple visual chart without changing planner behavior

---

## 1. Purpose

This memo defines the next vertical slice after the Japanese Rice first runner GUI wrapper.

The current GUI wrapper can display:

```text
weekly requested / capacity / accepted / blocked table
```

The next step is to define a chart-ready dataset so that the same weekly data can be shown visually.

The objective is not yet a full management cockpit.

The objective is:

```text
Convert the stable GUI model weekly_rows into a chart-ready dataset.
```

This prepares the next screen from:

```text
table-visible
```

to:

```text
chart-visible
```

---

## 2. Current Completed Foundation

The Japanese Rice Case has reached this point:

```text
master data
  ↓
ProductPlanNode
  ↓
DemandAnchoredLot
  ↓
DC_KANTO capacity gate
  ↓
runner output contract
  ↓
CLI summary / JSON
  ↓
independent Tkinter GUI wrapper
  ↓
visible weekly table
```

Latest key implementation:

```text
63d7e5b Add Japanese Rice first runner GUI wrapper
```

Latest completion memo:

```text
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice_completion.md
```

Current GUI wrapper file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Current focused test file:

```text
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

---

## 3. Why Chart Dataset Comes Next

The current GUI table is useful, but a chart is more intuitive for management-visible simulation.

A manager can understand a weekly pattern faster from a visual comparison:

```text
demand/requested
capacity
accepted
blocked
```

The first chart does not need to be beautiful.

The first chart needs to be:

```text
correct
stable
testable
based on the existing runner output contract
independent from full planner behavior
```

The purpose of this design is to define the dataset before chart rendering.

In other words:

```text
data contract first
chart drawing second
```

This keeps the GUI robust.

---

## 4. Scope of This Vertical Slice

### 4.1 In scope

Define and implement a chart-ready dataset helper.

The helper should consume the existing GUI model or runner result and return rows such as:

```python
[
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 10,
        "capacity_usage_ratio": 0.8888888889,
        "blocked_ratio": 0.0,
    },
    ...
]
```

It should be usable by:

```text
future Tkinter chart
future Matplotlib chart
future Plotly chart
future web dashboard
future note screenshot generation
```

### 4.2 Out of scope

Do not implement yet:

```text
full chart rendering
Matplotlib embedding
Plotly embedding
scenario comparison
cost / profit chart
full PSI graph
network graph
multi-gate capacity flow
leadtime-aware propagation
recommendation AI
note article
```

This slice is only:

```text
chart-ready dataset contract
```

---

## 5. Source Data

The source of truth should be:

```text
demo_summary.capacity_gate_summary.weekly
```

or the GUI model:

```text
model["weekly_rows"]
```

The design should prefer the stable path:

```text
runner result
  ↓
demo_summary
  ↓
GUI model
  ↓
weekly_rows
  ↓
chart_dataset
```

Do not parse deep internal diagnostics if the same values are already available in:

```text
demo_summary
```

---

## 6. Current Weekly Rows

Current GUI weekly rows:

```python
[
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
    },
    {
        "week": "2027-W41",
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
    },
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
    },
]
```

These rows should be the base of the chart dataset.

---

## 7. Required Chart Dataset Fields

The chart-ready dataset should include the original fields:

```text
week
requested
capacity
accepted
blocked
```

It should also add derived fields:

```text
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
```

Recommended definitions:

```text
shortage = blocked
unused_capacity = max(capacity - accepted, 0)
capacity_usage_ratio = accepted / capacity if capacity > 0 else 0
blocked_ratio = blocked / requested if requested > 0 else 0
```

Optional display-friendly fields:

```text
capacity_usage_pct = capacity_usage_ratio * 100
blocked_pct = blocked_ratio * 100
```

---

## 8. Expected Dataset

Expected chart rows:

```python
[
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
        "shortage": 0,
        "unused_capacity": 10,
        "capacity_usage_ratio": 80 / 90,
        "blocked_ratio": 0 / 80,
        "capacity_usage_pct": 88.8888888889,
        "blocked_pct": 0.0,
    },
    {
        "week": "2027-W41",
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
        "shortage": 5,
        "unused_capacity": 0,
        "capacity_usage_ratio": 90 / 90,
        "blocked_ratio": 5 / 95,
        "capacity_usage_pct": 100.0,
        "blocked_pct": 5.2631578947,
    },
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
        "shortage": 20,
        "unused_capacity": 0,
        "capacity_usage_ratio": 90 / 90,
        "blocked_ratio": 20 / 110,
        "capacity_usage_pct": 100.0,
        "blocked_pct": 18.1818181818,
    },
]
```

For tests, exact percentages can be checked using approximate comparison.

---

## 9. Totals Dataset

The chart helper should also support totals.

Current totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

Derived totals:

```text
shortage = 25
unused_capacity = 10
capacity_usage_ratio = 260 / 270
blocked_ratio = 25 / 285
capacity_usage_pct = 96.2962962963
blocked_pct = 8.7719298246
```

Recommended totals contract:

```python
{
    "requested": 285,
    "capacity": 270,
    "accepted": 260,
    "blocked": 25,
    "shortage": 25,
    "unused_capacity": 10,
    "capacity_usage_ratio": 260 / 270,
    "blocked_ratio": 25 / 285,
    "capacity_usage_pct": 96.2962962963,
    "blocked_pct": 8.7719298246,
}
```

---

## 10. Recommended Helper Functions

Add helpers to the existing GUI wrapper module:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Recommended functions:

```python
build_japanese_rice_capacity_gate_chart_dataset(model_or_result: dict) -> dict
```

Return:

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

Alternative smaller helper:

```python
build_japanese_rice_capacity_gate_chart_rows(model_or_result: dict) -> list[dict]
```

Recommended approach:

```text
return both rows and totals in one dataset object
```

This makes future GUI chart code easier.

---

## 11. Chart Type Direction

The preferred future chart should be:

```text
line chart
```

Reason:

```text
weeks are ordered time buckets
pattern over time matters
requested and capacity are easiest to compare as time series
```

A grouped bar chart is also acceptable for a small 3-week smoke horizon.

Recommended chart direction:

```text
v0r1:
  grouped bar or table-adjacent line dataset

v0r2:
  line chart with requested/capacity/accepted/blocked

v0r3:
  scenario comparison chart
```

This design defines the dataset only.

Rendering can be decided later.

---

## 12. Relationship to Current GUI Wrapper

The current GUI wrapper already has:

```text
extract_japanese_rice_first_runner_gui_model(...)
build_japanese_rice_weekly_capacity_gate_rows(...)
format_japanese_rice_gui_summary_text(...)
```

The new chart dataset helper should build on:

```text
weekly_rows
totals
```

It should not duplicate runner logic.

Recommended flow:

```text
result = run_japanese_rice_first_psi_vslice(...)
model = extract_japanese_rice_first_runner_gui_model(result)
chart_dataset = build_japanese_rice_capacity_gate_chart_dataset(model)
```

---

## 13. Relationship to Future GUI Chart

Future GUI chart can consume:

```text
chart_dataset["rows"]
```

Columns:

```text
week
requested
capacity
accepted
blocked
```

This can later drive:

```text
Tkinter Treeview plus Matplotlib
Matplotlib FigureCanvasTkAgg
Plotly HTML export
static PNG chart
note article screenshot
```

The chart dataset must therefore be simple and portable.

---

## 14. Relationship to Management Visibility

The chart should eventually answer:

```text
When does demand exceed capacity?
How much demand is blocked?
How fully is capacity used?
Does shortage grow week by week?
```

For current data:

```text
2027-W40:
  demand/requested is below capacity
  no blocked lots

2027-W41:
  demand exceeds capacity by 5
  capacity is fully used

2027-W42:
  demand exceeds capacity by 20
  capacity is fully used
  shortage grows
```

This is the first visual management message.

---

## 15. Relationship to Scenario Variation

The chart dataset should be designed so scenario comparison can be added later.

Future scenario comparison fields may include:

```text
scenario_name
scenario_label
base_or_changed
delta_accepted
delta_blocked
delta_shortage
```

Do not implement these now.

But keep the row structure simple so a future `scenario` field can be added.

---

## 16. Safety Boundaries

Do not change:

```text
run_japanese_rice_first_psi_vslice(...)
runner output contract
scenario master CSV files
existing GUI behavior
planner behavior
NetworkX dependency
```

This slice should only add helpers and tests.

Expected modified file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Expected new test file:

```text
tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 17. Test Requirements

Add:

```text
tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

### 17.1 Dataset exists

Call:

```python
result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
model = extract_japanese_rice_first_runner_gui_model(result)
dataset = build_japanese_rice_capacity_gate_chart_dataset(model)
```

Assert:

```text
dataset["title"] == "Japanese Rice DC_KANTO capacity gate"
dataset["unit"] == "lot"
dataset["x_key"] == "week"
```

### 17.2 Rows

Assert:

```text
len(dataset["rows"]) == 3
```

Expected rows:

```text
2027-W40 requested=80 capacity=90 accepted=80 blocked=0 shortage=0 unused_capacity=10
2027-W41 requested=95 capacity=90 accepted=90 blocked=5 shortage=5 unused_capacity=0
2027-W42 requested=110 capacity=90 accepted=90 blocked=20 shortage=20 unused_capacity=0
```

### 17.3 Derived ratios

Assert approximately:

```text
W40 capacity_usage_ratio = 80/90
W41 capacity_usage_ratio = 1.0
W42 capacity_usage_ratio = 1.0

W40 blocked_ratio = 0.0
W41 blocked_ratio = 5/95
W42 blocked_ratio = 20/110
```

### 17.4 Totals

Assert:

```text
totals.requested = 285
totals.capacity = 270
totals.accepted = 260
totals.blocked = 25
totals.shortage = 25
totals.unused_capacity = 10
```

Assert approximately:

```text
totals.capacity_usage_ratio = 260/270
totals.blocked_ratio = 25/285
```

### 17.5 Missing or zero capacity safety

Test helper with a small artificial model:

```python
model = {
    "weekly_rows": [
        {"week": "W0", "requested": 10, "capacity": 0, "accepted": 0, "blocked": 10}
    ],
    "totals": {"requested": 10, "capacity": 0, "accepted": 0, "blocked": 10},
}
```

Assert no division by zero.

Expected:

```text
capacity_usage_ratio = 0
blocked_ratio = 1.0
```

### 17.6 Empty model safety

Test:

```python
dataset = build_japanese_rice_capacity_gate_chart_dataset({"weekly_rows": [], "totals": {}})
```

Assert:

```text
rows = []
totals requested/capacity/accepted/blocked default to 0 or totals is safe
```

---

## 18. Test Commands

Focused chart dataset test:

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

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py
```

---

## 19. Acceptance Criteria

This slice is complete when:

```text
build_japanese_rice_capacity_gate_chart_dataset(...) exists
the helper consumes GUI model weekly_rows and totals
the helper returns rows with requested/capacity/accepted/blocked
the helper returns derived shortage and unused_capacity
the helper returns capacity_usage_ratio and blocked_ratio
the helper returns safe totals with derived ratios
division by zero is handled
empty input is safe
focused chart dataset tests pass
existing GUI wrapper tests pass
existing output contract tests pass
existing Japanese Rice tests pass
compileall passes
no planner behavior is changed
no existing cockpit file is changed
no scenario master CSV file is changed
NetworkX is untouched
```

---

## 20. Future Codex Request Name

Recommended next Codex request:

```text
docs/codex_requests/japanese_rice_first_runner_chart_dataset_vertical_slice_request.md
```

Scope:

```text
add chart dataset helper
add derived ratio logic
add focused tests
do not render chart yet
do not modify existing cockpit
do not change planner behavior
```

---

## 21. Development Meaning

Before this slice:

```text
The GUI can show a weekly table.
```

After this slice:

```text
The GUI has chart-ready data.
```

This is the bridge from:

```text
table
```

to:

```text
graph
```

It is a small step, but it matters.

Management-visible simulation depends on visual patterns.

In simple terms:

```text
The meter panel now shows numbers.
Next, the same numbers become a chart-ready signal.
