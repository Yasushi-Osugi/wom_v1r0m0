# Codex Request: Japanese Rice Capacity-Constrained First Flow Vertical Slice

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_capacity_constrained_first_flow_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

**Related implementation files already present:**

```text
pysi/plan/plan_node_tree_instantiation.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/network/network_master_loader.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/capacity/capacity_weekly_rows_source.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice capacity-constrained first flow vertical slice.

This request should add a small, deterministic, lot-level capacity gate flow.

The flow must use the actual ProductPlanNode tree produced by the previous slice.

Source demand lots must be read from:

```python
MARKET_TOKYO.psi4demand[week][0]
```

Capacity gate:

```text
DC_KANTO
capacity_type = S
capacity_qty = 90 lots/week
```

Expected lot-level result:

```text
2027-W40:
  requested 80
  accepted 80
  blocked 0

2027-W41:
  requested 95
  accepted 90
  blocked 5

2027-W42:
  requested 110
  accepted 90
  blocked 20

Total:
  requested 285
  accepted 260
  blocked 25
```

This is not a full PSI planner.

This is not GUI wiring.

This is the first capacity gate applied to actual demand lot IDs on actual plan_nodes.

---

## 2. Strategic Context

Japanese Rice Case has now completed the following milestones:

```text
Capacity master:
  capacity_master.csv

Demand master:
  demand_master.csv

Network master:
  node_master.csv / network_master.csv

First PSI smoke:
  run_japanese_rice_first_psi_vslice(...)

Actual planning-layer tree:
  ProductPlanNode trees

Demand lot attachment:
  MARKET_TOKYO.psi4demand[week][0]
```

The next step is to split actual lot IDs into:

```text
accepted_lot_ids
blocked_lot_ids
```

at the first capacity gate.

Selected first capacity gate:

```text
DC_KANTO -> MARKET_TOKYO
```

Reason:

```text
DC_KANTO is the first visible restriction in the same-week smoke balance.
```

---

## 3. Scope Control

### 3.1 In scope

Implement a pure helper and focused test to:

```text
instantiate actual ProductPlanNode trees
attach demand lots to actual MARKET_TOKYO plan_node
read demand lots from MARKET_TOKYO.psi4demand[week][0]
load capacity rows
select DC_KANTO S capacity by week
split lots into accepted / blocked
compute capacity usage, shortage, unused capacity
return deterministic flow diagnostic
verify lot ID consistency
```

### 3.2 Out of scope

Do not implement:

```text
full canonical PSI planning
leadtime-shifted propagation
inventory carry-over
CO / backlog calculation
multi-node propagation
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
cost / profit simulation
GUI wiring
NetworkX retirement
optimization
scenario runner integration beyond isolated helper
```

Do not modify existing planner behavior.

Do not modify GUI files.

---

## 4. Expected Changed / Added Files

Recommended new implementation file:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Recommended focused test file:

```text
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Optional package export:

```text
pysi/plan/__init__.py
```

Only update package export if it is low risk and consistent with project style.

---

## 5. Existing Functions to Reuse

Reuse existing code. Do not duplicate CSV parsing.

### 5.1 Plan node tree

Use:

```python
instantiate_product_plan_node_trees(...)
attach_demand_lots_to_actual_plan_node_psi4demand(...)
```

from:

```text
pysi/plan/plan_node_tree_instantiation.py
```

If there is a convenience helper that loads Japanese Rice plan_node tree with demand attached, reuse it.

### 5.2 Demand

Use:

```python
load_weekly_demand_master_csv(...)
generate_demand_anchored_lots(...)
```

from:

```text
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
```

### 5.3 Network

Use:

```python
load_network_master_package(...)
```

from:

```text
pysi/network/network_master_loader.py
```

### 5.4 Capacity

Use:

```python
load_capacity_weekly_rows_to_env(...)
```

from:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

or existing canonical capacity loader via that path.

Do not duplicate capacity CSV parsing.

---

## 6. Scenario Constants

Use:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
scenario_root = examples/scenarios/japanese_rice_vslice_001
```

Weeks:

```text
2027-W40
2027-W41
2027-W42
```

Demand node:

```text
MARKET_TOKYO
```

Capacity gate node:

```text
DC_KANTO
```

Capacity type:

```text
S
```

Expected capacity:

```text
90 lots/week
```

---

## 7. Core Algorithm

Given:

```python
demand_lot_ids = market_tokyo.psi4demand[week][0]
capacity_qty = dc_kanto_s_capacity_by_week[week]
```

Compute:

```python
accepted_lot_ids = demand_lot_ids[:capacity_qty]
blocked_lot_ids = demand_lot_ids[capacity_qty:]
```

Then:

```python
requested = len(demand_lot_ids)
accepted = len(accepted_lot_ids)
blocked = len(blocked_lot_ids)
capacity_usage = accepted
unused_capacity = max(capacity_qty - accepted, 0)
shortage = blocked
```

Preserve lot order.

Do not sort unless existing lot generator already guarantees deterministic order.

The expected default behavior is FIFO by generated lot ID list order.

---

## 8. Required Public Functions

Implement:

```python
split_lots_by_capacity(
    lot_ids: list[str],
    capacity_qty: int,
) -> dict
```

Expected result shape:

```python
{
    "requested": len(lot_ids),
    "capacity": capacity_qty,
    "accepted": ...,
    "blocked": ...,
    "capacity_usage": ...,
    "unused_capacity": ...,
    "shortage": ...,
    "accepted_lot_ids": [...],
    "blocked_lot_ids": [...],
}
```

Implement:

```python
compute_capacity_gate_flow_by_week(
    *,
    demand_lots_by_week: dict[str, list[str]],
    capacity_by_week: dict[str, int],
    capacity_node: str,
    demand_node: str,
    capacity_type: str = "S",
) -> dict
```

Implement:

```python
run_japanese_rice_capacity_constrained_first_flow(
    scenario_root: str | Path,
) -> dict
```

Keep functions pure.

Do not mutate global state.

---

## 9. Capacity Row Selection Rule

Select capacity rows matching:

```text
node_name = DC_KANTO
product_name = JAPANESE_RICE_STANDARD
capacity_type = S
week = target week
```

Expected capacity by week:

```text
2027-W40 = 90
2027-W41 = 90
2027-W42 = 90
```

If multiple matching rows exist, recommended behavior is:

```text
sum matching capacity_qty
```

For this vertical slice, current data has one matching row per week.

---

## 10. Demand Lot Source Rule

The demand lots must come from the actual plan_node:

```python
MARKET_TOKYO.psi4demand[week][0]
```

Do not compute requested counts directly from `demand_master.csv` for the flow.

This is critical because this slice must prove the previous plan_node instantiation slice is being used.

The diagnostic should include a field such as:

```python
"demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]"
```

or equivalent.

---

## 11. Expected Weekly Results

### 11.1 Week 2027-W40

```text
requested = 80
capacity = 90
accepted = 80
blocked = 0
capacity_usage = 80
unused_capacity = 10
shortage = 0
```

### 11.2 Week 2027-W41

```text
requested = 95
capacity = 90
accepted = 90
blocked = 5
capacity_usage = 90
unused_capacity = 0
shortage = 5
```

### 11.3 Week 2027-W42

```text
requested = 110
capacity = 90
accepted = 90
blocked = 20
capacity_usage = 90
unused_capacity = 0
shortage = 20
```

### 11.4 Totals

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
capacity_usage = 260
unused_capacity = 10
shortage = 25
```

---

## 12. Expected Diagnostic Shape

Recommended return shape:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "run_mode": "capacity_constrained_first_flow",
    "full_psi_plan": False,
    "available": True,
    "flow": {
        "capacity_node": "DC_KANTO",
        "demand_node": "MARKET_TOKYO",
        "capacity_type": "S",
        "unit": "lot",
        "demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]",
    },
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],
    "weekly": {
        "2027-W40": {
            "requested": 80,
            "capacity": 90,
            "accepted": 80,
            "blocked": 0,
            "capacity_usage": 80,
            "unused_capacity": 10,
            "shortage": 0,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [],
        },
        "2027-W41": {
            "requested": 95,
            "capacity": 90,
            "accepted": 90,
            "blocked": 5,
            "capacity_usage": 90,
            "unused_capacity": 0,
            "shortage": 5,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [...],
        },
        "2027-W42": {
            "requested": 110,
            "capacity": 90,
            "accepted": 90,
            "blocked": 20,
            "capacity_usage": 90,
            "unused_capacity": 0,
            "shortage": 20,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [...],
        },
    },
    "totals": {
        "requested": 285,
        "capacity": 270,
        "accepted": 260,
        "blocked": 25,
        "capacity_usage": 260,
        "unused_capacity": 10,
        "shortage": 25,
    },
    "messages": [
        "Japanese Rice capacity-constrained first flow: actual plan_node tree loaded.",
        "Japanese Rice capacity-constrained first flow: demand lots read from MARKET_TOKYO.psi4demand[week][0].",
        "Japanese Rice capacity-constrained first flow: DC_KANTO S capacity applied.",
        "Japanese Rice capacity-constrained first flow: accepted / blocked lots computed.",
    ],
}
```

The exact shape may vary, but focused tests must verify the same facts.

---

## 13. Optional ProductPlanNode Result Attachment

It is acceptable to only return accepted / blocked lists in the diagnostic.

Optional, if clean:

```python
dc_kanto.capacity_flow_results[week] = {...}
```

or:

```python
market_tokyo.capacity_gate_results[week] = {...}
```

Do not make this optional attachment a reason to increase scope.

The required result is the deterministic diagnostic.

---

## 14. Required Tests

Add:

```text
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

### 14.1 Runner mode

Assert:

```text
result["run_mode"] == "capacity_constrained_first_flow"
result["full_psi_plan"] is False
result["available"] is True
```

### 14.2 Demand lot source

Assert:

```text
result["flow"]["demand_node"] == "MARKET_TOKYO"
result["flow"]["capacity_node"] == "DC_KANTO"
result["flow"]["capacity_type"] == "S"
result["flow"]["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"
```

### 14.3 Week 2027-W40

Assert:

```text
requested = 80
capacity = 90
accepted = 80
blocked = 0
capacity_usage = 80
unused_capacity = 10
shortage = 0
```

### 14.4 Week 2027-W41

Assert:

```text
requested = 95
capacity = 90
accepted = 90
blocked = 5
capacity_usage = 90
unused_capacity = 0
shortage = 5
```

### 14.5 Week 2027-W42

Assert:

```text
requested = 110
capacity = 90
accepted = 90
blocked = 20
capacity_usage = 90
unused_capacity = 0
shortage = 20
```

### 14.6 Totals

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
capacity_usage = 260
unused_capacity = 10
shortage = 25
```

### 14.7 Lot ID set consistency

For each week, assert:

```text
accepted_lot_ids and blocked_lot_ids are disjoint
accepted + blocked count equals requested
len(accepted_lot_ids) == accepted
len(blocked_lot_ids) == blocked
```

If the runner exposes original demand lot IDs by week, assert:

```text
set(accepted_lot_ids) | set(blocked_lot_ids)
  == set(original_demand_lot_ids)
```

If not exposed, counts and disjointness are sufficient for this first slice.

### 14.8 Split helper standalone behavior

Add a simple unit test for:

```python
split_lots_by_capacity(["L1", "L2", "L3"], 2)
```

Expected:

```text
accepted_lot_ids = ["L1", "L2"]
blocked_lot_ids = ["L3"]
```

Also test capacity greater than request:

```python
split_lots_by_capacity(["L1", "L2"], 5)
```

Expected:

```text
accepted = 2
blocked = 0
unused_capacity = 3
```

### 14.9 Existing tests still pass

Run at minimum:

```text
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
tests/test_japanese_rice_network_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

---

## 15. Test Commands

Focused test:

```bat
python -m pytest tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Existing Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile check:

```bat
python -m compileall -q pysi/plan/capacity_constrained_first_flow.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

---

## 16. Safety Boundaries

Expected changed / added files:

```text
pysi/plan/capacity_constrained_first_flow.py
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Optional:

```text
pysi/plan/__init__.py
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

Do not wire into GUI.

Do not claim full PSI planning.

Do not change scenario master CSV files unless a clear typo blocks the test.

---

## 17. Acceptance Criteria

This request is complete when:

```text
capacity_constrained_first_flow helper is added
Japanese Rice first flow runner is added
focused first flow test is added
actual ProductPlanNode tree is instantiated
MARKET_TOKYO.psi4demand[week][0] is used as demand lot source
DC_KANTO S capacity rows are used as capacity gate
W40 accepted/blocked = 80/0
W41 accepted/blocked = 90/5
W42 accepted/blocked = 90/20
total accepted/blocked = 260/25
lot ID sets are deterministic and internally consistent
run result marks full_psi_plan = False
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
existing Japanese Rice tests still pass
capacity integration tests still pass
compileall passes
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the capacity-constrained first flow helper implemented?
What test file was added?
Does the runner use actual ProductPlanNode tree?
Does it read demand lots from MARKET_TOKYO.psi4demand[week][0]?
Does it apply DC_KANTO S capacity as the first gate?
What are the W40 accepted/blocked counts?
What are the W41 accepted/blocked counts?
What are the W42 accepted/blocked counts?
What are the total accepted/blocked counts?
Does the result mark full_psi_plan = False?
Did you change planner behavior?
Did you change GUI layout?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 19. Development Meaning

This request is the first true lot-level capacity gate for Japanese Rice Case.

Previous milestone:

```text
Demand lots are loaded onto the actual MARKET_TOKYO ProductPlanNode.
```

This milestone:

```text
Demand lots reach DC_KANTO capacity gate and split into accepted / blocked lots.
```

At DC_KANTO:

```text
W40 passes fully.
W41 blocks 5 lots.
W42 blocks 20 lots.
```

This is the first real transition from:

```text
data loading and structural correctness
```

to:

```text
operational constraint behavior at lot level
```

In simple terms:

```text
The rice bags are on the WOM vehicle.
Now the vehicle reaches the DC_KANTO capacity gate.
Some bags pass.
Some bags wait.
```
