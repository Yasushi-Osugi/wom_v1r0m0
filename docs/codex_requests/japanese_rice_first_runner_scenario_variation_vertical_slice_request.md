# Codex Request: Japanese Rice First Runner Scenario Variation Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_runner_scenario_variation_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md
```

**Related north-star doc:**

```text
docs/design/wom_tobe_management_simulator_image.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_first_runner_chart_view_vertical_slice_completion.md
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

Please implement the Japanese Rice first runner scenario variation vertical slice.

The current Japanese Rice GUI wrapper can show one scenario as:

```text
requested
capacity
accepted
blocked
```

by week, both as a table and as a chart.

This request should add the first deterministic scenario variation:

```text
Base:
  DC_KANTO S capacity = 90 lots / week

Capacity-up:
  DC_KANTO S capacity = 100 lots / week
```

The implementation should compare Base vs Capacity-up and show how accepted / blocked lots change.

This request should not mutate scenario master CSV files.

This request should not implement a full scenario editor.

This request should not implement full PSI planning.

This request should only implement a small deterministic variation helper and tests.

---

## 2. Strategic Context

The current WOM near-term strategy is:

```text
Visualization before recommendation.
Stable output before GUI wiring.
Chart-ready data before chart rendering.
Scenario comparison before recommendation AI.
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
visible capacity-gate chart
```

The next step is:

```text
compare what happens when one business parameter changes.
```

The first business parameter is:

```text
DC_KANTO weekly S capacity.
```

---

## 3. Scope Control

### 3.1 In scope

Implement pure helper functions for:

```text
capacity override dataset
Base vs Capacity-up comparison
comparison summary text
optional small GUI comparison text section
focused tests
```

The comparison should be deterministic and based on the existing capacity-gate chart dataset.

### 3.2 Out of scope

Do not implement:

```text
full scenario editor
CSV master mutation
database scenario persistence
full planner re-run
multi-gate capacity flow
leadtime-aware propagation
cost / profit impact
optimization
recommendation AI
existing cockpit integration
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
tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
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

## 5. Business Scenario Definition

### 5.1 Base scenario

The base scenario is the current Japanese Rice first runner result.

```text
scenario_label = Base
capacity_node = DC_KANTO
capacity_type = S
capacity = 90 lots / week
```

Base weekly rows:

```text
2027-W40 requested = 80,  capacity = 90, accepted = 80, blocked = 0
2027-W41 requested = 95,  capacity = 90, accepted = 90, blocked = 5
2027-W42 requested = 110, capacity = 90, accepted = 90, blocked = 20
```

Base totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 5.2 Capacity-up scenario

The first scenario variation is:

```text
scenario_label = Capacity-up
capacity_node = DC_KANTO
capacity_type = S
capacity = 100 lots / week
```

Requested values remain unchanged:

```text
2027-W40 requested = 80
2027-W41 requested = 95
2027-W42 requested = 110
```

Capacity-up weekly rows should be:

```text
2027-W40 requested = 80,  capacity = 100, accepted = 80,  blocked = 0
2027-W41 requested = 95,  capacity = 100, accepted = 95,  blocked = 0
2027-W42 requested = 110, capacity = 100, accepted = 100, blocked = 10
```

Capacity-up totals:

```text
requested = 285
capacity = 300
accepted = 275
blocked = 10
```

### 5.3 Delta

Base to Capacity-up delta:

```text
capacity: +30
accepted: +15
blocked:  -15
```

Blocked reduction:

```text
25 -> 10
reduction = 15 lots
reduction ratio = 15 / 25 = 60.0%
```

---

## 6. Calculation Rule

For this vertical slice, use the same simple same-week capacity gate rule:

```text
accepted = min(requested, capacity)
blocked = max(requested - capacity, 0)
shortage = blocked
unused_capacity = max(capacity - accepted, 0)
capacity_usage_ratio = accepted / capacity if capacity > 0 else 0
blocked_ratio = blocked / requested if requested > 0 else 0
capacity_usage_pct = capacity_usage_ratio * 100
blocked_pct = blocked_ratio * 100
```

This is intentionally simple.

Do not introduce leadtime-aware propagation.

Do not introduce inventory carry-over.

Do not introduce full PSI engine mutation.

---

## 7. Required Helper: Capacity Override Dataset

Add a helper to:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Recommended name:

```python
build_capacity_override_chart_dataset(
    base_dataset: dict,
    *,
    capacity_value: int,
    scenario_label: str = "Capacity-up",
) -> dict
```

Expected behavior:

```text
consume base_dataset["rows"]
use each row's requested value
replace capacity with capacity_value
recalculate accepted / blocked / shortage / unused_capacity / ratios
return a chart-dataset-like object
```

The helper should preserve:

```text
week order
unit
x_key
series
chart_hint
```

Recommended returned metadata:

```python
{
    "title": "Japanese Rice DC_KANTO capacity gate - Capacity-up",
    "scenario_label": "Capacity-up",
    "capacity_override": 100,
    "unit": "lot",
    "x_key": "week",
    "series": ["requested", "capacity", "accepted", "blocked"],
    "rows": [...],
    "totals": {...},
    "chart_hint": "line_or_grouped_bar",
}
```

---

## 8. Required Helper: Scenario Comparison

Add:

```python
build_capacity_gate_scenario_comparison(
    base_dataset: dict,
    variant_dataset: dict,
    *,
    base_label: str = "Base",
    variant_label: str = "Capacity-up",
) -> dict
```

Expected return:

```python
{
    "title": "Japanese Rice DC_KANTO capacity scenario comparison",
    "base_label": "Base",
    "variant_label": "Capacity-up",
    "rows": [...],
    "totals": {...},
    "management_message": "...",
}
```

---

## 9. Required Comparison Rows

Comparison rows should contain:

```text
week
base_requested
base_capacity
base_accepted
base_blocked
variant_requested
variant_capacity
variant_accepted
variant_blocked
delta_capacity
delta_accepted
delta_blocked
```

Expected comparison rows:

```text
2027-W40:
  base_requested = 80
  base_capacity = 90
  base_accepted = 80
  base_blocked = 0
  variant_requested = 80
  variant_capacity = 100
  variant_accepted = 80
  variant_blocked = 0
  delta_capacity = 10
  delta_accepted = 0
  delta_blocked = 0

2027-W41:
  base_requested = 95
  base_capacity = 90
  base_accepted = 90
  base_blocked = 5
  variant_requested = 95
  variant_capacity = 100
  variant_accepted = 95
  variant_blocked = 0
  delta_capacity = 10
  delta_accepted = 5
  delta_blocked = -5

2027-W42:
  base_requested = 110
  base_capacity = 90
  base_accepted = 90
  base_blocked = 20
  variant_requested = 110
  variant_capacity = 100
  variant_accepted = 100
  variant_blocked = 10
  delta_capacity = 10
  delta_accepted = 10
  delta_blocked = -10
```

---

## 10. Required Comparison Totals

Comparison totals should include:

```python
{
    "base": {
        "requested": 285,
        "capacity": 270,
        "accepted": 260,
        "blocked": 25,
    },
    "variant": {
        "requested": 285,
        "capacity": 300,
        "accepted": 275,
        "blocked": 10,
    },
    "delta": {
        "capacity": 30,
        "accepted": 15,
        "blocked": -15,
    },
    "blocked_reduction": 15,
    "blocked_reduction_ratio": 0.6,
    "blocked_reduction_pct": 60.0,
}
```

Use approximate float assertions for ratios and percentages.

---

## 11. Required Helper: Comparison Summary Text

Add:

```python
format_capacity_gate_scenario_comparison_text(comparison: dict) -> str
```

Expected text should include:

```text
Base
Capacity-up
DC_KANTO
90
100
blocked lots: 25 -> 10
blocked reduction: 15 lots
blocked reduction: 60.0%
accepted lots: 260 -> 275
```

The exact wording may vary, but the focused tests should check key terms and values.

---

## 12. Optional GUI Display

Optionally extend the independent GUI wrapper to show a small comparison section.

If implemented, show something like:

```text
Scenario variation:
  Base DC_KANTO capacity: 90
  Capacity-up capacity: 100
  Accepted lots: 260 -> 275
  Blocked lots: 25 -> 10
  Blocked reduction: 15 lots / 60.0%
```

This section can appear below the current management message.

Keep it simple.

Do not add a full scenario editor.

Do not add comparison chart rendering in this slice.

---

## 13. Test File

Add focused test:

```text
tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
```

---

## 14. Required Tests

### 14.1 Variant dataset test

Build base and variant:

```python
result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
model = extract_japanese_rice_first_runner_gui_model(result)
base_dataset = build_japanese_rice_capacity_gate_chart_dataset(model)
variant_dataset = build_capacity_override_chart_dataset(
    base_dataset,
    capacity_value=100,
    scenario_label="Capacity-up",
)
```

Assert variant rows:

```text
W40 requested=80 capacity=100 accepted=80 blocked=0
W41 requested=95 capacity=100 accepted=95 blocked=0
W42 requested=110 capacity=100 accepted=100 blocked=10
```

Assert variant totals:

```text
requested=285
capacity=300
accepted=275
blocked=10
```

Assert derived values are safe and numeric.

### 14.2 Comparison test

Build comparison:

```python
comparison = build_capacity_gate_scenario_comparison(base_dataset, variant_dataset)
```

Assert totals:

```text
comparison["totals"]["base"]["accepted"] == 260
comparison["totals"]["base"]["blocked"] == 25
comparison["totals"]["variant"]["accepted"] == 275
comparison["totals"]["variant"]["blocked"] == 10
comparison["totals"]["delta"]["accepted"] == 15
comparison["totals"]["delta"]["blocked"] == -15
comparison["totals"]["blocked_reduction"] == 15
comparison["totals"]["blocked_reduction_pct"] == 60.0
```

Assert rows:

```text
W41 delta_accepted=5, delta_blocked=-5
W42 delta_accepted=10, delta_blocked=-10
```

### 14.3 Summary text test

Call:

```python
text = format_capacity_gate_scenario_comparison_text(comparison)
```

Assert text includes:

```text
Base
Capacity-up
25 -> 10
15 lots
60.0%
260 -> 275
```

### 14.4 Empty dataset safety

Use empty datasets:

```python
base_dataset = {"rows": [], "totals": {}}
variant_dataset = {"rows": [], "totals": {}}
comparison = build_capacity_gate_scenario_comparison(base_dataset, variant_dataset)
```

Assert:

```text
comparison["rows"] == []
comparison["totals"] is safe
```

### 14.5 Import safety

Import:

```python
pysi.gui.japanese_rice_first_runner_view
```

Assert import does not open a GUI window.

---

## 15. Test Commands

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

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
```

---

## 16. Safety Boundaries

Expected modified file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Expected new test file:

```text
tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
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

Do not add scenario comparison chart rendering in this slice.

---

## 17. Acceptance Criteria

This request is complete when:

```text
build_capacity_override_chart_dataset(...) exists
build_capacity_gate_scenario_comparison(...) exists
format_capacity_gate_scenario_comparison_text(...) exists
Capacity-up 100 rows are deterministic
variant accepted / blocked rows are correct
comparison deltas are correct
blocked reduction 25 -> 10 is shown
blocked reduction 15 lots / 60.0% is shown
focused scenario variation tests pass
existing chart view tests pass
existing chart dataset tests pass
existing GUI wrapper tests pass
existing output contract tests pass
existing Japanese Rice tests pass
capacity integration tests pass
compileall passes
planner behavior unchanged
existing cockpit files unchanged
scenario master CSV files unchanged
NetworkX untouched
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where were the scenario variation helpers implemented?
What test file was added?
Does build_capacity_override_chart_dataset(...) exist?
Does build_capacity_gate_scenario_comparison(...) exist?
Does format_capacity_gate_scenario_comparison_text(...) exist?
Does Capacity-up 100 produce W40 80/100/80/0?
Does Capacity-up 100 produce W41 95/100/95/0?
Does Capacity-up 100 produce W42 110/100/100/10?
Does variant totals show requested=285, capacity=300, accepted=275, blocked=10?
Does comparison show base blocked=25 and variant blocked=10?
Does comparison show blocked reduction=15 and 60.0%?
Was a GUI comparison section added?
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
full scenario editor
scenario persistence
CSV master mutation
database scenario save
scenario comparison chart
cost / profit impact
multi-gate capacity flow
leadtime-aware PSI
full cockpit integration
note article generation
```

This request only implements the first deterministic scenario variation and comparison.

---

## 20. Development Meaning

Before this request:

```text
The Japanese Rice GUI shows one scenario.
```

After this request:

```text
The Japanese Rice GUI model can compare Base vs Capacity-up.
```

This is the first step from:

```text
visualization
```

to:

```text
management evaluation
```

The key management statement is:

```text
Increasing DC_KANTO weekly capacity from 90 to 100 reduces blocked lots from 25 to 10.
```

In simple terms:

```text
The chart showed the bottleneck.
This request shows what happens if we loosen it.
```
