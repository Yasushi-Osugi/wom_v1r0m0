# Japanese Rice Capacity-Constrained Flow Runner Actual PlanNode Upgrade Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_request.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice_completion.md
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice capacity-constrained flow runner actual ProductPlanNode upgrade.

This phase upgraded the existing Japanese Rice first PSI smoke runner:

```python
run_japanese_rice_first_psi_vslice(...)
```

so that the runner now exposes two additional diagnostic sections:

```text
actual_plan_node_tree
capacity_constrained_first_flow
```

The runner now shows not only that the Japanese Rice master data can be loaded and aligned, but also that:

```text
actual ProductPlanNode trees are available
MARKET_TOKYO.psi4demand[week][0] contains demand lot IDs
DC_KANTO capacity gate splits lots into accepted / blocked groups
```

This remains a diagnostic-first PSI smoke runner. It is not a full canonical PSI planner.

---

## 2. Key Commit

Implementation commit:

```text
5b5b286 Upgrade Japanese rice first PSI runner diagnostics
```

Related preceding commits:

```text
5993533 Add Japanese Rice first PSI runner actual plan node upgrade Codex request
8034ee9 Add Japanese Rice first PSI runner actual plan node upgrade design
d039e60 Add Japanese Rice capacity constrained first flow completion memo
febc28e Add Japanese rice capacity constrained first flow
8fa29e4 Add Japanese Rice capacity constrained first flow Codex request
392b8d7 Add Japanese Rice capacity constrained first flow vertical slice design
5e380ee Add Japanese Rice plan node tree instantiation completion memo
19d0303 Add Japanese rice plan node tree instantiation
87b04a8 Add Japanese Rice plan node tree instantiation vertical slice Codex request
```

---

## 3. Files Changed / Added

This implementation changed:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

This implementation added:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

The commit created:

```text
2 files changed
153 insertions
```

No GUI files were changed.

No planner engine files were changed.

No NetworkX dependency was removed or modified.

No full PSI planning was claimed.

---

## 4. Runner Upgraded

The upgraded runner remains:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

The runner still returns:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

The runner still preserves existing first PSI smoke fields, including:

```text
scenario_id
product_name
available
masters
weeks
demand
network
capacity
balance
messages
```

The important upgrade is that the runner now also includes:

```text
actual_plan_node_tree
capacity_constrained_first_flow
```

This makes the runner a stronger diagnostic and future demo entry point.

---

## 5. actual_plan_node_tree Section Added

The upgraded runner now exposes actual ProductPlanNode evidence.

Confirmed facts:

```text
available = True
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

The runner reports the actual MARKET_TOKYO S-slot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

This means the runner no longer only shows that demand lots can be generated.

It now shows that those lots are attached to the actual ProductPlanNode structure.

---

## 6. capacity_constrained_first_flow Section Added

The upgraded runner now exposes the DC_KANTO first capacity gate result.

Confirmed facts:

```text
available = True
capacity_node = DC_KANTO
demand_node = MARKET_TOKYO
capacity_type = S
full_psi_plan = False
```

The runner reports weekly accepted / blocked counts:

```text
2027-W40:
  accepted = 80
  blocked = 0

2027-W41:
  accepted = 90
  blocked = 5

2027-W42:
  accepted = 90
  blocked = 20
```

Total result:

```text
accepted = 260
blocked = 25
```

This turns the first PSI smoke runner into a direct diagnostic view of the first lot-level capacity constraint.

---

## 7. Existing Smoke Runner Contract Preserved

The implementation preserves the existing first PSI smoke contract.

Confirmed:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

Existing master counts remain available:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

Existing top-level smoke diagnostic fields remain present.

This is important because the runner can now be used both for earlier smoke checks and newer capacity-gate checks.

---

## 8. Message Stream Extended

The runner now appends deterministic upgrade messages indicating:

```text
actual ProductPlanNode tree instantiated
MARKET_TOKYO.psi4demand[week][0] verified
DC_KANTO capacity-constrained first flow attached
```

These messages provide human-readable confirmation that the runner includes the actual plan_node and capacity gate upgrade.

---

## 9. Tests Added

Focused upgrade test file:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

The tests verify:

```text
runner still reports diagnostic_first_psi_smoke
runner still reports full_psi_plan = False
existing master counts remain available
actual_plan_node_tree section exists
actual_plan_node_tree reports inbound/outbound counts 5/5
actual_plan_node_tree reports MARKET_TOKYO S-slot counts 80/95/110
capacity_constrained_first_flow section exists
capacity_constrained_first_flow reports DC_KANTO
capacity_constrained_first_flow reports MARKET_TOKYO
capacity_constrained_first_flow reports accepted/blocked 80/0, 90/5, 90/20
capacity_constrained_first_flow reports total accepted/blocked 260/25
messages include the new upgrade markers
```

---

## 10. Tests Executed

Focused upgrade test:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Observed result:

```text
7 passed
```

Existing Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
48 passed
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
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Observed result:

```text
compileall completed successfully
```

---

## 11. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
GUI layout
NetworkX dependency
scenario master CSV files
full PSI planner behavior
capacity enforcement engine behavior
inventory calculation
CO / backlog calculation
cost / price / profit behavior
```

This phase only upgraded the diagnostic runner by composing existing helper outputs.

It reused existing implementations:

```text
ProductPlanNode tree helper
capacity-constrained first flow helper
```

It did not duplicate major logic.

---

## 12. Current Japanese Rice Case State

The Japanese Rice Case now has:

```text
Capacity
Demand
Network
Actual ProductPlanNode tree
DemandAnchoredLot attachment to MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted_lot_ids / blocked_lot_ids
first PSI smoke runner exposing all of the above
```

The current runner-level diagnostic chain is:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
masters loaded
    ↓
actual ProductPlanNode tree visible
    ↓
MARKET_TOKYO.psi4demand[week][0] visible
    ↓
DC_KANTO capacity gate visible
    ↓
accepted / blocked lots visible
```

This is a major improvement for demo readiness.

---

## 13. Development Meaning

This is a major milestone.

Before this upgrade:

```text
The first PSI smoke runner showed master integration and simple weekly balance.
The capacity-constrained first flow separately showed accepted / blocked lots.
```

After this upgrade:

```text
The first PSI smoke runner itself shows:
  master integration
  actual ProductPlanNode evidence
  MARKET_TOKYO lot attachment
  DC_KANTO accepted / blocked lots
```

This turns the runner into a much stronger diagnostic entry point.

It is no longer just:

```text
The Japanese Rice Case can be loaded.
```

It is now:

```text
The Japanese Rice Case can be loaded.
Demand lots are on actual ProductPlanNodes.
DC_KANTO capacity gate accepts 260 lots and blocks 25 lots.
```

---

## 14. Still Deferred

The following remain intentionally deferred.

### 14.1 Multi-gate capacity flow

Not yet implemented:

```text
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
multi-stage accepted / blocked propagation
```

### 14.2 Leadtime-aware PSI propagation

Not yet implemented:

```text
leadtime shifting
week-shifted P/S timing
long vacation handling
```

### 14.3 Inventory and backlog

Not yet implemented:

```text
inventory carry-over
CO / backlog calculation
blocked demand carry-forward
```

### 14.4 GUI and visualization

Not yet implemented:

```text
weekly balance line chart
accepted / blocked chart
cockpit issue visibility
NetworkX retirement
```

### 14.5 Financial evaluation

Not yet implemented:

```text
cost profile
price / profit simulation
tariff impact
cash / AR / AP impact
```

---

## 15. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke.md
```

Purpose:

```text
Define a stable, CLI-friendly output contract for run_japanese_rice_first_psi_vslice(...)
so that the runner can be called from command line or GUI wrapper and display a compact demo summary.
```

Why this is recommended:

```text
The runner now contains enough meaningful diagnostic information for a demo.
Before extending to multi-gate flow, it is useful to make the output stable and easy to show.
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
1. Runner output contract / CLI smoke
2. Multi-gate capacity flow
3. Leadtime-aware PSI propagation
4. MOM/DAD weekly balance line diagnostic
5. GUI visualization
```

---

## 16. Future Demo Meaning

The upgraded runner can support a simple demo statement:

```text
Japanese Rice Case loads capacity, demand, and network masters.
It creates actual ProductPlanNode trees.
It places Tokyo demand lots into MARKET_TOKYO.psi4demand.
It applies DC_KANTO capacity.
It reports 260 accepted lots and 25 blocked lots.
```

This is much stronger than simply showing CSV loading.

It begins to communicate the WOM concept:

```text
Lot-level operational constraints can be simulated and diagnosed by week.
```

---

## 17. Completion Summary

Completed:

```text
run_japanese_rice_first_psi_vslice(...) upgraded
actual_plan_node_tree diagnostic section added
capacity_constrained_first_flow diagnostic section added
actual_plan_node_tree reports inbound/outbound node counts 5/5
actual_plan_node_tree reports MARKET_TOKYO S-slot counts 80/95/110
capacity_constrained_first_flow reports DC_KANTO as capacity node
capacity_constrained_first_flow reports MARKET_TOKYO as demand node
capacity_constrained_first_flow reports W40 accepted / blocked = 80 / 0
capacity_constrained_first_flow reports W41 accepted / blocked = 90 / 5
capacity_constrained_first_flow reports W42 accepted / blocked = 90 / 20
capacity_constrained_first_flow reports total accepted / blocked = 260 / 25
existing first PSI smoke fields preserved
run_mode remains diagnostic_first_psi_smoke
full_psi_plan remains False
existing Japanese Rice tests passed
capacity integration tests passed
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
compileall passed
```

Current milestone:

```text
Japanese Rice first PSI smoke runner now exposes actual ProductPlanNode evidence and DC_KANTO accepted / blocked flow.
```

In simple terms:

```text
The runner no longer only says the rice case can be loaded.
It now shows that the rice bags are on the actual WOM vehicle,
260 bags pass the DC_KANTO gate,
and 25 bags wait.
```
