# Japanese Rice Capacity-Constrained First Flow Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_capacity_constrained_first_flow_vertical_slice_request.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice capacity-constrained first flow vertical slice.

This phase implemented the first lot-level capacity gate for the Japanese Rice Case.

The previous milestone proved that DemandAnchoredLots could be attached to an actual ProductPlanNode:

```python
MARKET_TOKYO.psi4demand[week][0] = list[lot_ID]
```

This phase adds the first capacity-constrained flow:

```text
MARKET_TOKYO.psi4demand[week][0]
    ↓
DC_KANTO S capacity gate
    ↓
accepted_lot_ids / blocked_lot_ids
```

This is not a full PSI planner.

It is the first deterministic capacity gate behavior at the lot level.

---

## 2. Key Commit

Implementation commit:

```text
febc28e Add Japanese rice capacity constrained first flow
```

Related preceding commits:

```text
8fa29e4 Add Japanese Rice capacity constrained first flow Codex request
392b8d7 Add Japanese Rice capacity constrained first flow vertical slice design
5e380ee Add Japanese Rice plan node tree instantiation completion memo
19d0303 Add Japanese rice plan node tree instantiation
87b04a8 Add Japanese Rice plan node tree instantiation vertical slice Codex request
0c83b0f Add Japanese Rice plan node tree instantiation vertical slice design
e818935 Add Japanese Rice first PSI run vertical slice completion memo
6998529 Add Japanese rice first PSI smoke runner
442d9ad Add Japanese Rice first PSI run vertical slice Codex request
```

---

## 3. Files Added

This implementation added:

```text
pysi/plan/capacity_constrained_first_flow.py
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

The commit created:

```text
2 files changed
334 insertions
```

No GUI files were changed.

No existing planner engine files were changed.

No NetworkX dependency was removed or modified.

No full PSI planning was claimed.

---

## 4. Implemented First Flow Helper

Implemented in:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Public functions implemented:

```text
split_lots_by_capacity(...)
compute_capacity_gate_flow_by_week(...)
run_japanese_rice_capacity_constrained_first_flow(...)
```

The implementation uses the actual Japanese Rice ProductPlanNode tree created by the previous slice.

The runner uses:

```text
instantiate_japanese_rice_plan_node_tree_and_attach_demand(...)
```

and reads demand lot IDs from:

```python
MARKET_TOKYO.psi4demand[week][0]
```

This is critical because it proves the actual plan_node tree is now part of the flow, not merely a compatibility shape or direct demand count.

---

## 5. Capacity Gate

The first capacity gate is:

```text
capacity_node = DC_KANTO
capacity_type = S
unit = lot
```

Capacity source:

```text
capacity_master.csv
```

Capacity rows are loaded through:

```text
load_capacity_weekly_rows_to_env(...)
```

The selected gate values are:

```text
2027-W40 = 90 lots
2027-W41 = 90 lots
2027-W42 = 90 lots
```

This is the first operational gate where actual lot IDs are split into accepted and blocked groups.

---

## 6. Demand Lot Source

The demand lot source is:

```python
MARKET_TOKYO.psi4demand[week][0]
```

This is the actual outbound MARKET_TOKYO ProductPlanNode demand S slot.

Expected demand lots:

```text
2027-W40 = 80 lot IDs
2027-W41 = 95 lot IDs
2027-W42 = 110 lot IDs
```

Total demand lots:

```text
285
```

The flow does not compute demand directly from `demand_master.csv` for the final split.

It uses lot IDs already attached to the ProductPlanNode.

---

## 7. Split Logic

The capacity gate uses deterministic list-order splitting.

For each week:

```python
accepted_lot_ids = demand_lot_ids[:capacity_qty]
blocked_lot_ids = demand_lot_ids[capacity_qty:]
```

This means the first `capacity_qty` lots pass the gate, and the remaining lots are blocked.

The split preserves lot ordering.

This is intentionally simple and deterministic.

It is a first capacity gate, not an optimizer.

---

## 8. Weekly Results

### 8.1 Week 2027-W40

Input:

```text
requested = 80
capacity = 90
```

Result:

```text
accepted = 80
blocked = 0
capacity_usage = 80
unused_capacity = 10
shortage = 0
```

Interpretation:

```text
All W40 Tokyo demand lots pass the DC_KANTO gate.
```

### 8.2 Week 2027-W41

Input:

```text
requested = 95
capacity = 90
```

Result:

```text
accepted = 90
blocked = 5
capacity_usage = 90
unused_capacity = 0
shortage = 5
```

Interpretation:

```text
W41 exceeds DC_KANTO capacity by 5 lots.
```

### 8.3 Week 2027-W42

Input:

```text
requested = 110
capacity = 90
```

Result:

```text
accepted = 90
blocked = 20
capacity_usage = 90
unused_capacity = 0
shortage = 20
```

Interpretation:

```text
W42 exceeds DC_KANTO capacity by 20 lots.
```

---

## 9. Total Results

Total across target weeks:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
capacity_usage = 260
unused_capacity = 10
shortage = 25
```

This is the first lot-level constrained flow result for Japanese Rice Case.

---

## 10. Diagnostic Mode

The returned result explicitly remains an isolated vertical slice.

Expected diagnostic markers:

```text
run_mode = capacity_constrained_first_flow
full_psi_plan = False
available = True
```

This is important.

Correct interpretation:

```text
Japanese Rice Case now has a deterministic one-gate lot-level capacity split.
```

Incorrect interpretation:

```text
Full canonical PSI planning is complete.
```

This phase does not perform full PSI propagation.

---

## 11. Tests Added

Focused test file:

```text
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

The tests cover:

```text
split_lots_by_capacity standalone behavior
runner metadata
demand lot source
weekly W40 accepted / blocked result
weekly W41 accepted / blocked result
weekly W42 accepted / blocked result
total accepted / blocked result
lot ID consistency
full_psi_plan = False
```

---

## 12. Tests Executed

Focused test:

```bat
python -m pytest tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Observed result:

```text
7 passed
```

Existing Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
41 passed
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
python -m compileall -q pysi/plan/capacity_constrained_first_flow.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

---

## 13. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
GUI layout
NetworkX dependency
existing first PSI smoke runner behavior
full PSI planner behavior
capacity enforcement engine behavior
inventory calculation
CO / backlog calculation
cost / price / profit behavior
```

This phase only added:

```text
a pure capacity-constrained first flow helper
a Japanese Rice first flow runner
a focused test file
```

---

## 14. Current Japanese Rice Case State

The Japanese Rice Case now has:

```text
Capacity
Demand
Network
First PSI smoke runner
Actual ProductPlanNode tree
DemandAnchoredLot attachment to actual MARKET_TOKYO ProductPlanNode
Capacity-constrained first flow at DC_KANTO
```

The current operational chain is:

```text
demand_master.csv
    ↓
DemandAnchoredLots
    ↓
MARKET_TOKYO.psi4demand[week][0]
    ↓
DC_KANTO S capacity gate
    ↓
accepted_lot_ids / blocked_lot_ids
```

This is the first point where the case shows lot-level operational constraint behavior.

---

## 15. Development Meaning

This is a major milestone.

Before this phase:

```text
The Japanese Rice Case had lot IDs sitting on the actual MARKET_TOKYO ProductPlanNode.
```

After this phase:

```text
Those lot IDs pass through the first capacity gate and split into accepted / blocked lots.
```

The case has moved from:

```text
data loading and structural correctness
```

to:

```text
lot-level operational constraint behavior
```

This is highly aligned with WOM's purpose.

WOM is not only showing aggregate demand and capacity.

It is beginning to handle:

```text
which lots can pass
which lots must wait
where the bottleneck appears
```

---

## 16. Still Deferred

The following remain intentionally deferred.

### 16.1 Multi-stage propagation

Not yet implemented:

```text
DC_KANTO accepted lots moving further upstream
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
full outbound / inbound propagation
```

### 16.2 Leadtime-aware PSI

Not yet implemented:

```text
leadtime shift
week shifting
P-to-S / S-to-P timing logic
long vacation handling
```

### 16.3 Inventory and backlog

Not yet implemented:

```text
inventory carry-over
CO / backlog calculation
unfulfilled demand carry-forward
```

### 16.4 GUI and visualization

Not yet implemented:

```text
MOM weekly balance line chart
accepted / blocked lot visualization
cockpit issue visibility
NetworkX retirement
```

### 16.5 Financial evaluation

Not yet implemented:

```text
cost profile
price / profit simulation
tariff impact
cash / AR / AP impact
```

---

## 17. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade.md
```

Purpose:

```text
Upgrade the existing first PSI smoke runner to incorporate the actual ProductPlanNode tree and DC_KANTO accepted / blocked flow result.
```

Alternative next design:

```text
docs/design/japanese_rice_multi_gate_capacity_flow_vertical_slice.md
```

Purpose:

```text
Extend capacity-constrained flow from DC_KANTO to RICE_MILL_A and FARM_REGION_A.
```

Recommended order:

```text
1. First flow completion memo
2. Upgrade smoke runner to include first flow result
3. Multi-gate flow
4. Leadtime-aware PSI propagation
5. MOM/DAD weekly balance line diagnostic
6. GUI visualization
```

---

## 18. Future MOM/DAD Weekly Balance Line

The new accepted / blocked lot result prepares the future weekly balance line.

For DC_KANTO:

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
```

Future chart series can include:

```text
requested lots
accepted lots
blocked lots
capacity
shortage
unused capacity
```

This is the beginning of the visualization the project has been aiming for:

```text
weekly demand-supply balance line
```

---

## 19. Completion Summary

Completed:

```text
capacity_constrained_first_flow helper added
Japanese Rice first flow runner added
focused first flow test added
actual ProductPlanNode tree is used
MARKET_TOKYO.psi4demand[week][0] is used as demand lot source
DC_KANTO S capacity rows are used as the first capacity gate
W40 accepted / blocked = 80 / 0
W41 accepted / blocked = 90 / 5
W42 accepted / blocked = 90 / 20
total accepted / blocked = 260 / 25
lot ID sets are deterministic and internally consistent
run result marks full_psi_plan = False
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
existing Japanese Rice tests passed
capacity integration tests passed
compileall passed
```

Current milestone:

```text
Japanese Rice Case now has its first lot-level capacity gate.
```

Next recommended milestone:

```text
Upgrade the PSI smoke runner or extend to multi-gate capacity flow.
```

In simple terms:

```text
The rice bags are on the WOM vehicle.
They reached the DC_KANTO gate.
260 bags passed.
25 bags were held back.
WOM has started to behave like a constrained operation model.
