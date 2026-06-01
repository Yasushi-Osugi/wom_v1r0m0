# Japanese Rice First Runner Scenario Variation Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md`

**Strategic role:** Move the Japanese Rice first runner from one-scenario visualization to simple scenario comparison  
**Primary case:** Japanese Rice Case  
**Current north star:** Management-visible simulation before recommendation AI  
**Immediate goal:** Compare Base capacity 90 vs Capacity-up 100 and show how blocked lots change

---

## 1. Purpose

This memo defines the next vertical slice after the Japanese Rice first runner chart view.

The current Japanese Rice GUI wrapper can show one scenario:

```text
requested
capacity
accepted
blocked
```

by week.

The chart now makes the first supply-demand balance pattern visible.

The next step is to change one business parameter and compare the result.

The first scenario variation should be intentionally small:

```text
Base:
  DC_KANTO S capacity = 90 lots / week

Capacity-up:
  DC_KANTO S capacity = 100 lots / week
```

The purpose is to move from:

```text
visualization
```

to:

```text
comparison evaluation
```

This is still not full optimization.

This is still not recommendation AI.

This is still not cost / profit simulation.

This is the first controlled scenario variation for the Japanese Rice first runner.

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
weekly table
  ↓
chart-ready dataset
  ↓
visible capacity-gate chart
```

Latest key implementation:

```text
b8bd68d Add Japanese Rice first runner chart view
```

Latest completion memo:

```text
docs/design/japanese_rice_first_runner_chart_view_vertical_slice_completion.md
```

Current GUI wrapper file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Current chart dataset helper:

```python
build_japanese_rice_capacity_gate_chart_dataset(...)
```

Current chart series helper:

```python
build_japanese_rice_capacity_gate_chart_series(...)
```

Current chart view test file:

```text
tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py
```

---

## 3. Why Scenario Variation Comes Next

The current chart answers:

```text
What happens in the base case?
```

The next management question is:

```text
What if capacity changes?
```

A visible chart becomes much more useful when the user can compare:

```text
before
after
delta
```

For the current Japanese Rice Case, the simplest useful business question is:

```text
If DC_KANTO weekly S capacity increases from 90 to 100,
how much blocked demand is reduced?
```

This question is simple, deterministic, and management-relevant.

It is the first practical step from:

```text
seeing the problem
```

to:

```text
evaluating a possible action
```

---

## 4. Scope of This Vertical Slice

### 4.1 In scope

Define a simple scenario variation contract.

The first variation is:

```text
DC_KANTO S capacity 90 -> 100
```

The implementation should:

```text
keep the current base result
derive a variation result using changed capacity
compare accepted / blocked by week
compare totals
prepare comparison-ready rows
optionally display comparison text/table in independent GUI
optionally prepare comparison chart dataset
```

### 4.2 Out of scope

Do not implement yet:

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

This slice is about a controlled first variation only.

---

## 5. Business Scenario Definition

### 5.1 Base scenario

```text
scenario_label = Base
capacity_node = DC_KANTO
capacity_type = S
capacity = 90 lots / week
```

Base requested values:

```text
2027-W40 requested = 80
2027-W41 requested = 95
2027-W42 requested = 110
```

Base accepted / blocked:

```text
2027-W40 accepted = 80, blocked = 0
2027-W41 accepted = 90, blocked = 5
2027-W42 accepted = 90, blocked = 20
```

Base totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 5.2 Capacity-up scenario

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

Capacity-up accepted / blocked:

```text
2027-W40 accepted = 80, blocked = 0
2027-W41 accepted = 95, blocked = 0
2027-W42 accepted = 100, blocked = 10
```

Capacity-up totals:

```text
requested = 285
capacity = 300
accepted = 275
blocked = 10
```

### 5.3 Delta

Delta from Base to Capacity-up:

```text
accepted: +15
blocked:  -15
capacity: +30
```

Blocked reduction:

```text
25 -> 10
reduction = 15 lots
reduction ratio = 15 / 25 = 60%
```

This is the first visible management effect.

---

## 6. Calculation Rule

For this vertical slice, use a simple same-week capacity gate rule:

```text
accepted = min(requested, capacity)
blocked = max(requested - capacity, 0)
unused_capacity = max(capacity - accepted, 0)
```

This is intentionally the same conceptual rule used in the current first runner capacity-gate smoke.

Do not introduce leadtime-aware propagation in this slice.

Do not introduce inventory carry-over in this slice.

Do not introduce full PSI engine mutation in this slice.

---

## 7. Recommended Data Contract

### 7.1 Scenario variation row

Recommended row shape:

```python
{
    "week": "2027-W41",
    "scenario_label": "Capacity-up",
    "requested": 95,
    "capacity": 100,
    "accepted": 95,
    "blocked": 0,
    "shortage": 0,
    "unused_capacity": 5,
    "capacity_usage_ratio": 0.95,
    "blocked_ratio": 0.0,
}
```

### 7.2 Comparison row

Recommended row shape:

```python
{
    "week": "2027-W41",
    "base_requested": 95,
    "base_capacity": 90,
    "base_accepted": 90,
    "base_blocked": 5,
    "variant_requested": 95,
    "variant_capacity": 100,
    "variant_accepted": 95,
    "variant_blocked": 0,
    "delta_capacity": 10,
    "delta_accepted": 5,
    "delta_blocked": -5,
}
```

### 7.3 Comparison totals

Recommended totals shape:

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

---

## 8. Recommended Helper Functions

Add helpers to:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

or, if the module becomes too large, create:

```text
pysi/gui/japanese_rice_first_runner_scenario_variation.py
```

Recommended first approach:

```text
keep helper in pysi/gui/japanese_rice_first_runner_view.py
```

Reason:

```text
current scope is small
avoids premature module split
keeps the vertical slice easy to inspect
```

### 8.1 Capacity override helper

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
use each base row's requested value
replace capacity with capacity_value
recalculate accepted / blocked / shortage / unused_capacity / ratios
return chart dataset with the same dataset contract
```

### 8.2 Scenario comparison helper

```python
build_capacity_gate_scenario_comparison(
    base_dataset: dict,
    variant_dataset: dict,
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

### 8.3 Summary text helper

```python
format_capacity_gate_scenario_comparison_text(comparison: dict) -> str
```

Expected output includes:

```text
Base capacity: 90 lots/week
Capacity-up: 100 lots/week
Blocked lots: 25 -> 10
Blocked reduction: 15 lots
Blocked reduction ratio: 60.0%
```

---

## 9. Expected Base Dataset

The base dataset already exists through:

```python
build_japanese_rice_capacity_gate_chart_dataset(...)
```

Expected base rows:

```text
2027-W40 requested=80,  capacity=90, accepted=80, blocked=0
2027-W41 requested=95,  capacity=90, accepted=90, blocked=5
2027-W42 requested=110, capacity=90, accepted=90, blocked=20
```

Expected base totals:

```text
requested=285
capacity=270
accepted=260
blocked=25
```

---

## 10. Expected Variant Dataset

For `capacity_value=100`, expected rows:

```text
2027-W40 requested=80,  capacity=100, accepted=80,  blocked=0
2027-W41 requested=95,  capacity=100, accepted=95,  blocked=0
2027-W42 requested=110, capacity=100, accepted=100, blocked=10
```

Expected variant totals:

```text
requested=285
capacity=300
accepted=275
blocked=10
```

Expected derived totals:

```text
shortage=10
unused_capacity=25
capacity_usage_ratio=275/300
blocked_ratio=10/285
```

---

## 11. Expected Comparison Rows

Expected comparison rows:

```text
2027-W40:
  base_capacity=90
  variant_capacity=100
  base_accepted=80
  variant_accepted=80
  base_blocked=0
  variant_blocked=0
  delta_accepted=0
  delta_blocked=0

2027-W41:
  base_capacity=90
  variant_capacity=100
  base_accepted=90
  variant_accepted=95
  base_blocked=5
  variant_blocked=0
  delta_accepted=5
  delta_blocked=-5

2027-W42:
  base_capacity=90
  variant_capacity=100
  base_accepted=90
  variant_accepted=100
  base_blocked=20
  variant_blocked=10
  delta_accepted=10
  delta_blocked=-10
```

Expected totals:

```text
delta_capacity=30
delta_accepted=15
delta_blocked=-15
blocked_reduction=15
blocked_reduction_pct=60.0
```

---

## 12. Chart Direction

The first comparison chart should not be implemented in this design unless the implementation slice decides to include a very small visual extension.

The preferred next chart after this slice would be:

```text
Base blocked vs Variant blocked by week
```

or:

```text
Base accepted vs Variant accepted by week
```

But this design focuses on:

```text
scenario variation data and comparison text
```

Chart rendering can remain a later slice.

---

## 13. GUI Display Direction

The independent GUI wrapper can optionally add a small comparison section:

```text
Scenario variation:
  Base DC_KANTO capacity: 90
  Capacity-up: 100
  Blocked lots: 25 -> 10
  Reduction: 15 lots, 60.0%
```

The GUI table and chart for the base scenario should remain unchanged.

The variation section can be displayed under the current management message.

Do not make the GUI complicated.

---

## 14. Test Strategy

Add focused test:

```text
tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
```

Tests should avoid opening a GUI.

Focus on pure helper functions.

### 14.1 Variant dataset test

Use current runner:

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

### 14.2 Comparison test

Build comparison:

```python
comparison = build_capacity_gate_scenario_comparison(base_dataset, variant_dataset)
```

Assert:

```text
delta_capacity=30
delta_accepted=15
delta_blocked=-15
blocked_reduction=15
blocked_reduction_pct=60.0
```

Assert rows:

```text
W41 delta_accepted=5, delta_blocked=-5
W42 delta_accepted=10, delta_blocked=-10
```

### 14.3 Summary text test

Assert text includes:

```text
Base
Capacity-up
90
100
25 -> 10
15 lots
60.0%
```

### 14.4 Safety test

Use artificial dataset with empty rows.

Assert helper returns safe empty comparison.

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

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py
```

---

## 16. Acceptance Criteria

This design is ready for implementation when the Codex request can require:

```text
capacity override dataset helper exists
scenario comparison helper exists
summary text helper exists
Base 90 vs Capacity-up 100 comparison is deterministic
variant accepted / blocked rows are correct
comparison deltas are correct
blocked reduction 25 -> 10 is shown
blocked reduction 15 lots / 60.0% is shown
focused tests pass
existing chart view tests pass
existing chart dataset tests pass
existing GUI wrapper tests pass
existing output contract tests pass
existing Japanese Rice tests pass
compileall passes
planner behavior unchanged
existing cockpit files unchanged
scenario master CSV files unchanged
NetworkX untouched
```

---

## 17. Safety Boundaries

Do not change:

```text
run_japanese_rice_first_psi_vslice(...)
runner output contract
scenario master CSV files
existing cockpit files
planner behavior
NetworkX dependency
```

Do not implement:

```text
full planner scenario rerun
database scenario persistence
scenario editor
cost / profit logic
recommendation AI
```

This is a pure deterministic first scenario variation.

---

## 18. Future Codex Request Name

Recommended next Codex request:

```text
docs/codex_requests/japanese_rice_first_runner_scenario_variation_vertical_slice_request.md
```

Scope:

```text
add capacity override dataset helper
add scenario comparison helper
add comparison summary text helper
add focused tests
optionally show a small comparison text section in the independent GUI wrapper
do not modify existing cockpit
do not change planner behavior
do not mutate scenario masters
```

---

## 19. Development Meaning

Before this slice:

```text
The Japanese Rice GUI shows one scenario.
```

After this slice:

```text
The Japanese Rice GUI can compare a simple capacity-change scenario.
```

This is the first step from:

```text
visualization
```

to:

```text
management evaluation
```

The key management message becomes:

```text
Increasing DC_KANTO weekly capacity from 90 to 100 reduces blocked lots from 25 to 10.
```

This is the first small but concrete WOM business evaluation.

---

## 20. Recommended Next-Next Step

After this variation slice, the next natural step is:

```text
docs/design/japanese_rice_first_runner_scenario_comparison_chart_vertical_slice.md
```

Purpose:

```text
Show Base vs Capacity-up blocked lots in a comparison chart.
```

That would make the improvement visually clear:

```text
Base blocked:       0, 5, 20
Capacity-up blocked: 0, 0, 10
```

But first, define and test the comparison data.

Data first.

Chart second.

---

## 21. Completion Target

This vertical slice is complete when the following management question can be answered deterministically:

```text
What happens if DC_KANTO capacity increases from 90 to 100?
```

Expected answer:

```text
accepted lots increase from 260 to 275
blocked lots decrease from 25 to 10
blocked lots are reduced by 15
blocked reduction ratio is 60.0%
```

This is the first concrete scenario comparison for the Japanese Rice Case.
