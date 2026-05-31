# Japanese Rice Capacity-Constrained Flow Runner Actual PlanNode Upgrade

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade.md`

**Strategic role:** Upgrade the existing Japanese Rice first PSI smoke runner to consume actual ProductPlanNode trees and include the DC_KANTO accepted / blocked lot flow result  
**Primary case:** Japanese Rice Case  
**Initial execution target:** extend `run_japanese_rice_first_psi_vslice(...)` diagnostic output without changing GUI or full planner behavior

---

## 1. Purpose

This memo defines the next Japanese Rice Case vertical slice after the successful capacity-constrained first flow.

The current Japanese Rice Case now has:

```text
Capacity
Demand
Network
First PSI smoke runner
Actual ProductPlanNode tree
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted_lot_ids / blocked_lot_ids
```

However, the existing first PSI smoke runner still represents the earlier integration milestone.

The purpose of this slice is to upgrade the first PSI smoke runner so that its returned diagnostic includes:

```text
actual ProductPlanNode tree evidence
MARKET_TOKYO.psi4demand[week][0] evidence
DC_KANTO capacity-constrained first flow result
accepted_lot_ids / blocked_lot_ids summary
```

This upgrade should keep the runner as a diagnostic-first smoke runner.

It must not become a full PSI planner.

---

## 2. Current Completed Foundations

### 2.1 First PSI smoke runner

Existing runner:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Existing public API:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

Existing role:

```text
Load capacity, demand, and network masters.
Generate demand lots.
Verify network paths.
Attach capacity runtime context.
Compute simple weekly balance.
Return deterministic diagnostic.
```

### 2.2 Actual ProductPlanNode tree

Implemented in:

```text
pysi/plan/plan_node_tree_instantiation.py
```

Key capability:

```text
node_master.csv / network_master.csv
    ↓
ProductPlanNode trees
    ↓
actual MARKET_TOKYO outbound ProductPlanNode
    ↓
MARKET_TOKYO.psi4demand[week][0]
```

Confirmed attachment:

```text
2027-W40 = 80 lot IDs
2027-W41 = 95 lot IDs
2027-W42 = 110 lot IDs
```

### 2.3 Capacity-constrained first flow

Implemented in:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Key capability:

```text
MARKET_TOKYO.psi4demand[week][0]
    ↓
DC_KANTO S capacity gate
    ↓
accepted_lot_ids / blocked_lot_ids
```

Confirmed first flow result:

```text
2027-W40:
  accepted 80 / blocked 0

2027-W41:
  accepted 90 / blocked 5

2027-W42:
  accepted 90 / blocked 20

Total:
  accepted 260 / blocked 25
```

---

## 3. Problem Statement

The project now has two useful but separate diagnostic layers:

```text
1. First PSI smoke runner
2. Capacity-constrained first flow runner
```

The first PSI smoke runner is the natural entry point for the Japanese Rice demonstration.

The capacity-constrained first flow is the first true lot-level operational behavior.

They should now be aligned.

The upgraded runner should answer:

```text
Can Japanese Rice masters be loaded?
Can actual ProductPlanNode trees be instantiated?
Can demand lots be attached to actual MARKET_TOKYO ProductPlanNode?
Can DC_KANTO capacity gate split those lot IDs into accepted / blocked groups?
Can the runner report this as a diagnostic-first PSI smoke, not a full PSI plan?
```

---

## 4. Design Goal

Upgrade:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

so that it still returns existing information, but additionally includes:

```text
plan_node_tree
capacity_constrained_first_flow
accepted / blocked lots summary
```

The upgrade should preserve backward compatibility as much as practical.

Existing tests should continue to pass.

New tests should assert the new diagnostic sections.

---

## 5. Scope of This Vertical Slice

### 5.1 In scope

```text
reuse actual ProductPlanNode tree helper
reuse capacity-constrained first flow helper
extend first PSI smoke runner output
add diagnostic section for actual plan_node tree
add diagnostic section for capacity_constrained_first_flow
preserve existing simple weekly balance section
preserve run_mode / full_psi_plan semantics
add focused tests
```

### 5.2 Out of scope

```text
full PSI planner
leadtime-aware propagation
inventory carry-over
CO / backlog
multi-gate capacity flow
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
GUI wiring
NetworkX retirement
cost / profit integration
optimization
```

This slice should upgrade the diagnostic runner, not introduce a full planning engine.

---

## 6. Recommended Implementation Target

Primary file to modify:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Likely import from:

```text
pysi/plan/plan_node_tree_instantiation.py
pysi/plan/capacity_constrained_first_flow.py
```

Recommended focused test:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Do not modify GUI files.

Do not modify existing planner engine files.

---

## 7. Existing Functions to Reuse

### 7.1 From plan node instantiation

Use:

```python
instantiate_japanese_rice_plan_node_tree_and_attach_demand(...)
```

or equivalent helper from:

```text
pysi/plan/plan_node_tree_instantiation.py
```

This should provide:

```text
ProductPlanNode trees
actual MARKET_TOKYO plan_node
MARKET_TOKYO.psi4demand[week][0]
```

### 7.2 From capacity-constrained first flow

Use:

```python
run_japanese_rice_capacity_constrained_first_flow(...)
```

or lower-level helpers from:

```text
pysi/plan/capacity_constrained_first_flow.py
```

This should provide:

```text
DC_KANTO accepted / blocked lots by week
total accepted / blocked
full_psi_plan = False
```

### 7.3 Existing first PSI smoke logic

Preserve existing:

```text
capacity / demand / network master counts
simple weekly balance
network path verification
capacity runtime preflight summary
messages
```

The upgrade should add sections, not remove the useful existing summary.

---

## 8. Proposed Upgraded Diagnostic Shape

Current result should be extended with new fields.

Recommended additions:

```python
{
    "run_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    ...
    "actual_plan_node_tree": {
        "available": True,
        "product_name": "JAPANESE_RICE_STANDARD",
        "inbound_node_count": 5,
        "outbound_node_count": 5,
        "demand_node": "MARKET_TOKYO",
        "demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]",
        "weekly_s_slot_counts": {
            "2027-W40": 80,
            "2027-W41": 95,
            "2027-W42": 110,
        },
    },
    "capacity_constrained_first_flow": {
        "available": True,
        "run_mode": "capacity_constrained_first_flow",
        "capacity_node": "DC_KANTO",
        "demand_node": "MARKET_TOKYO",
        "capacity_type": "S",
        "weekly": {
            "2027-W40": {
                "requested": 80,
                "capacity": 90,
                "accepted": 80,
                "blocked": 0,
                "capacity_usage": 80,
                "unused_capacity": 10,
                "shortage": 0,
            },
            "2027-W41": {
                "requested": 95,
                "capacity": 90,
                "accepted": 90,
                "blocked": 5,
                "capacity_usage": 90,
                "unused_capacity": 0,
                "shortage": 5,
            },
            "2027-W42": {
                "requested": 110,
                "capacity": 90,
                "accepted": 90,
                "blocked": 20,
                "capacity_usage": 90,
                "unused_capacity": 0,
                "shortage": 20,
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
    },
}
```

The exact field names may vary, but tests must verify the core facts.

---

## 9. Preserve Existing Runner Meaning

The upgraded runner must still make clear:

```text
This is diagnostic-first PSI smoke.
This is not full canonical PSI planning.
```

Required markers:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

The new first flow section should also preserve:

```text
capacity_constrained_first_flow.full_psi_plan = False
```

if that field is included.

Correct interpretation:

```text
The first PSI smoke runner now includes actual plan_node evidence and first capacity gate result.
```

Incorrect interpretation:

```text
Full PSI planning is complete.
```

---

## 10. Expected Values to Preserve

### 10.1 Master counts

Existing expected counts should remain:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

### 10.2 Demand lots

Expected actual plan_node demand slot counts:

```text
MARKET_TOKYO.psi4demand["2027-W40"][0] = 80
MARKET_TOKYO.psi4demand["2027-W41"][0] = 95
MARKET_TOKYO.psi4demand["2027-W42"][0] = 110
```

### 10.3 Capacity-constrained first flow

Expected flow result:

```text
2027-W40:
  requested 80
  capacity 90
  accepted 80
  blocked 0

2027-W41:
  requested 95
  capacity 90
  accepted 90
  blocked 5

2027-W42:
  requested 110
  capacity 90
  accepted 90
  blocked 20
```

Expected totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

---

## 11. Message Stream

The runner should append deterministic messages such as:

```text
Japanese Rice first PSI vertical slice: actual ProductPlanNode tree instantiated.
Japanese Rice first PSI vertical slice: MARKET_TOKYO.psi4demand[week][0] verified.
Japanese Rice first PSI vertical slice: DC_KANTO capacity-constrained first flow attached.
```

Existing messages should not be removed unless tests require a minor wording update.

---

## 12. Backward Compatibility

Existing test:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

should continue to pass.

If this test asserts exact dictionary equality, revise it carefully to assert only stable contract fields.

Recommended approach:

```text
Add new fields.
Keep old fields.
Avoid breaking old field names.
```

Add a new focused test for the new sections rather than overloading the old test too much.

---

## 13. Required Tests

Add:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

### 13.1 Runner still reports diagnostic smoke mode

Assert:

```text
result["run_mode"] == "diagnostic_first_psi_smoke"
result["full_psi_plan"] is False
```

### 13.2 Actual plan_node tree section exists

Assert:

```text
result["actual_plan_node_tree"]["available"] is True
inbound_node_count == 5
outbound_node_count == 5
demand_node == MARKET_TOKYO
demand_lot_source == MARKET_TOKYO.psi4demand[week][0]
```

### 13.3 MARKET_TOKYO S-slot counts are visible

Assert:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

from:

```text
actual_plan_node_tree.weekly_s_slot_counts
```

### 13.4 Capacity-constrained first flow section exists

Assert:

```text
result["capacity_constrained_first_flow"]["available"] is True
capacity_node == DC_KANTO
demand_node == MARKET_TOKYO
capacity_type == S
```

### 13.5 Weekly accepted / blocked counts

Assert:

```text
2027-W40 accepted / blocked = 80 / 0
2027-W41 accepted / blocked = 90 / 5
2027-W42 accepted / blocked = 90 / 20
```

### 13.6 Totals

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 13.7 Existing fields still available

Assert old master counts still exist:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

### 13.8 Existing tests still pass

Run:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
tests/test_japanese_rice_network_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

---

## 14. Suggested Test Commands

Focused upgrade test:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Existing Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

---

## 15. Safety Boundaries

Expected changed / added files:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
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

Do not change the public name of `run_japanese_rice_first_psi_vslice(...)`.

Do not claim full PSI planning.

---

## 16. Acceptance Criteria for Future Codex Request

The implementation is complete when:

```text
run_japanese_rice_first_psi_vslice(...) includes actual_plan_node_tree section
run_japanese_rice_first_psi_vslice(...) includes capacity_constrained_first_flow section
actual_plan_node_tree reports inbound_node_count = 5
actual_plan_node_tree reports outbound_node_count = 5
actual_plan_node_tree reports MARKET_TOKYO psi4demand S-slot counts 80 / 95 / 110
capacity_constrained_first_flow reports DC_KANTO as capacity node
capacity_constrained_first_flow reports MARKET_TOKYO as demand node
capacity_constrained_first_flow reports W40 accepted / blocked = 80 / 0
capacity_constrained_first_flow reports W41 accepted / blocked = 90 / 5
capacity_constrained_first_flow reports W42 accepted / blocked = 90 / 20
capacity_constrained_first_flow reports total accepted / blocked = 260 / 25
existing first PSI smoke fields remain available
run_mode remains diagnostic_first_psi_smoke
full_psi_plan remains False
existing Japanese Rice tests still pass
capacity integration tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
```

---

## 17. Non-Goals

This slice does not implement:

```text
multi-gate flow
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
leadtime-aware PSI propagation
inventory calculation
backlog / CO calculation
GUI visualization
cost / profit integration
optimization
NetworkX retirement
```

This slice only upgrades the existing first PSI smoke runner to include the actual plan_node and first capacity gate results.

---

## 18. Development Meaning

Before this upgrade:

```text
The first PSI smoke runner showed that Capacity + Demand + Network could be integrated.
The capacity-constrained first flow separately showed accepted / blocked lots at DC_KANTO.
```

After this upgrade:

```text
The first PSI smoke runner itself will show actual plan_node demand lot attachment and DC_KANTO accepted / blocked results.
```

This makes the runner a stronger demonstration entry point.

It gives one command-level diagnostic view of:

```text
masters loaded
actual plan_node tree instantiated
demand lots attached to MARKET_TOKYO
DC_KANTO capacity gate applied
accepted / blocked lots computed
```

This is useful for future:

```text
public demo
GUI cockpit wiring
weekly balance line visualization
scenario explanation
```

---

## 19. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_request.md
```

Scope:

```text
upgrade run_japanese_rice_first_psi_vslice(...)
add actual_plan_node_tree diagnostic section
add capacity_constrained_first_flow diagnostic section
add focused tests
preserve existing fields
do not modify GUI
do not modify planner behavior
do not remove NetworkX
do not claim full PSI planning
```

---

## 20. Summary

This design upgrades the Japanese Rice first PSI smoke runner from:

```text
integration smoke diagnostic
```

to:

```text
integration smoke diagnostic with actual plan_node tree and first capacity gate result
```

It keeps the same safe boundary:

```text
full_psi_plan = False
```

but makes the runner much more valuable.

In simple terms:

```text
The runner no longer only says the rice case can be loaded.
It will also show that the rice lots are on the actual WOM vehicle,
and that 260 lots pass the DC_KANTO gate while 25 lots wait.
```
