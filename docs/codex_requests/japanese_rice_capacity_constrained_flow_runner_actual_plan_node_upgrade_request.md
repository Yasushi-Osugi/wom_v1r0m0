# Codex Request: Japanese Rice Capacity-Constrained Flow Runner Actual PlanNode Upgrade

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade.md
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

**Related implementation files already present:**

```text
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

Please upgrade the existing Japanese Rice first PSI smoke runner:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

so that its returned diagnostic includes the two newer Japanese Rice vertical-slice results:

```text
1. actual ProductPlanNode tree evidence
2. DC_KANTO capacity-constrained first flow result
```

The upgraded runner should still be a diagnostic-first PSI smoke runner.

It must not become a full PSI planner.

It must not modify GUI files.

It must not modify existing planner engine behavior.

It must not remove or modify NetworkX.

---

## 2. Strategic Context

The Japanese Rice Case has completed these milestones:

```text
Capacity:
  capacity_master.csv
  WeeklyCapacityRow source
  capacity runtime attachment

Demand:
  demand_master.csv
  WeeklyDemandRow
  DemandAnchoredLot

Network:
  node_master.csv
  network_master.csv
  WOM E2E hammock structure

First PSI smoke:
  run_japanese_rice_first_psi_vslice(...)

Actual ProductPlanNode tree:
  MARKET_TOKYO.psi4demand[week][0]

Capacity-constrained first flow:
  DC_KANTO S capacity gate
  accepted_lot_ids / blocked_lot_ids
```

The first PSI smoke runner is the natural entry point for demos and diagnostics.

The newer actual plan_node tree and first capacity gate result should now be visible from that runner.

---

## 3. Current Situation

### 3.1 Existing runner

Current runner:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

It already returns a diagnostic-first smoke result with:

```text
master counts
demand lot counts
network path verification
capacity runtime attachment
simple weekly balance
full_psi_plan = False
```

### 3.2 Actual ProductPlanNode tree

Implemented in:

```text
pysi/plan/plan_node_tree_instantiation.py
```

Key verified result:

```text
actual outbound MARKET_TOKYO ProductPlanNode

MARKET_TOKYO.psi4demand["2027-W40"][0] = 80 lot IDs
MARKET_TOKYO.psi4demand["2027-W41"][0] = 95 lot IDs
MARKET_TOKYO.psi4demand["2027-W42"][0] = 110 lot IDs
```

### 3.3 Capacity-constrained first flow

Implemented in:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Key verified result:

```text
DC_KANTO S capacity gate

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

## 4. Goal of This Request

Upgrade the existing runner so that a single call:

```python
run_japanese_rice_first_psi_vslice(Path("examples/scenarios/japanese_rice_vslice_001"))
```

returns not only the earlier smoke diagnostic, but also:

```text
actual_plan_node_tree
capacity_constrained_first_flow
```

This makes the runner a more useful Japanese Rice diagnostic entry point.

It should show:

```text
masters loaded
actual plan_node tree instantiated
MARKET_TOKYO.psi4demand[week][0] verified
DC_KANTO capacity gate applied
accepted / blocked lots visible
```

---

## 5. Scope Control

### 5.1 In scope

Modify:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Add:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

The implementation should:

```text
reuse existing actual ProductPlanNode helper
reuse existing capacity-constrained first flow helper
add actual_plan_node_tree diagnostic section
add capacity_constrained_first_flow diagnostic section
preserve existing runner fields
preserve run_mode = diagnostic_first_psi_smoke
preserve full_psi_plan = False
add focused tests
```

### 5.2 Out of scope

Do not implement:

```text
full canonical PSI planner
leadtime-aware propagation
inventory carry-over
CO / backlog calculation
multi-gate capacity flow
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
GUI wiring
NetworkX retirement
cost / profit integration
optimization
```

Do not modify GUI files.

Do not modify existing planner engine files.

Do not change scenario master CSV files.

---

## 6. Expected Changed / Added Files

Expected modified file:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Expected new test file:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Optional only if absolutely necessary:

```text
pysi/runners/__init__.py
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

## 7. Existing Functions to Reuse

### 7.1 ProductPlanNode tree

Reuse existing helper from:

```text
pysi/plan/plan_node_tree_instantiation.py
```

Expected helper:

```python
instantiate_japanese_rice_plan_node_tree_and_attach_demand(...)
```

or equivalent existing function.

It should provide:

```text
actual ProductPlanNode trees
actual outbound MARKET_TOKYO ProductPlanNode
MARKET_TOKYO.psi4demand[week][0]
```

### 7.2 Capacity-constrained first flow

Reuse existing runner/helper from:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Expected public function:

```python
run_japanese_rice_capacity_constrained_first_flow(...)
```

or equivalent.

It should provide:

```text
DC_KANTO capacity gate
weekly accepted / blocked
totals
full_psi_plan = False
```

Do not duplicate first-flow logic inside the first PSI runner.

---

## 8. Diagnostic Section: actual_plan_node_tree

Add a new section to the returned diagnostic:

```python
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
}
```

Field names may vary slightly, but tests must verify the same facts.

The important point is that the first PSI runner now proves actual plan_node demand attachment, not only compatibility-shape attachment.

---

## 9. Diagnostic Section: capacity_constrained_first_flow

Add a new section to the returned diagnostic:

```python
"capacity_constrained_first_flow": {
    "available": True,
    "run_mode": "capacity_constrained_first_flow",
    "full_psi_plan": False,
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
}
```

The exact field nesting may vary.

The tests must verify the core facts.

---

## 10. Preserve Existing Runner Contract

Existing result fields must remain available.

Preserve:

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
run_mode
full_psi_plan
```

In particular, preserve existing master counts:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

Preserve:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

If current field names differ, preserve the current names and add the new sections around them.

Do not break existing test expectations.

---

## 11. Message Stream

Append deterministic messages such as:

```text
Japanese Rice first PSI vertical slice: actual ProductPlanNode tree instantiated.
Japanese Rice first PSI vertical slice: MARKET_TOKYO.psi4demand[week][0] verified.
Japanese Rice first PSI vertical slice: DC_KANTO capacity-constrained first flow attached.
```

Do not remove existing useful messages unless tests require a controlled adjustment.

---

## 12. Testing Requirements

Add focused test:

```text
tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

### 12.1 Runner remains diagnostic smoke

Assert:

```text
result["run_mode"] == "diagnostic_first_psi_smoke"
result["full_psi_plan"] is False
```

### 12.2 Existing master counts still exist

Assert:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

### 12.3 actual_plan_node_tree section exists

Assert:

```text
actual_plan_node_tree.available is True
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

### 12.4 actual plan_node S-slot counts are visible

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

### 12.5 capacity_constrained_first_flow section exists

Assert:

```text
capacity_constrained_first_flow.available is True
capacity_node = DC_KANTO
demand_node = MARKET_TOKYO
capacity_type = S
full_psi_plan = False
```

### 12.6 Weekly accepted / blocked values

Assert:

```text
2027-W40 accepted / blocked = 80 / 0
2027-W41 accepted / blocked = 90 / 5
2027-W42 accepted / blocked = 90 / 20
```

### 12.7 Totals

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 12.8 Messages

Assert messages include deterministic phrases indicating:

```text
actual ProductPlanNode tree instantiated
MARKET_TOKYO.psi4demand[week][0] verified
DC_KANTO capacity-constrained first flow attached
```

---

## 13. Test Commands

Run focused upgrade test:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

Run existing Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Run capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py
```

---

## 14. Safety Boundaries

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

Do not rename or remove `run_japanese_rice_first_psi_vslice(...)`.

Do not claim full PSI planning.

---

## 15. Acceptance Criteria

This request is complete when:

```text
run_japanese_rice_first_psi_vslice(...) includes actual_plan_node_tree section
run_japanese_rice_first_psi_vslice(...) includes capacity_constrained_first_flow section
actual_plan_node_tree reports inbound_node_count = 5
actual_plan_node_tree reports outbound_node_count = 5
actual_plan_node_tree reports MARKET_TOKYO S-slot counts 80 / 95 / 110
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
compileall passes
```

---

## 16. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the runner upgraded?
What test file was added?
Does the runner still return run_mode = diagnostic_first_psi_smoke?
Does the runner still return full_psi_plan = False?
Does the runner include actual_plan_node_tree?
Does actual_plan_node_tree report inbound/outbound node counts 5/5?
Does actual_plan_node_tree report MARKET_TOKYO S-slot counts 80/95/110?
Does the runner include capacity_constrained_first_flow?
Does capacity_constrained_first_flow report DC_KANTO as capacity node?
Does capacity_constrained_first_flow report accepted/blocked 80/0, 90/5, 90/20?
Does capacity_constrained_first_flow report total accepted/blocked 260/25?
Did you preserve existing first PSI smoke fields?
Did you change planner behavior?
Did you change GUI layout?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 17. Non-Goals

This request does not implement:

```text
multi-gate capacity flow
RICE_MILL_A clipping
FARM_REGION_A clipping
leadtime-aware PSI propagation
inventory calculation
CO / backlog
GUI visualization
cost / profit integration
optimization
NetworkX retirement
```

This request only upgrades the diagnostic first PSI runner to include the already implemented actual plan_node and first capacity gate evidence.

---

## 18. Development Meaning

Before this upgrade:

```text
The first PSI smoke runner showed master integration.
The capacity-constrained first flow separately showed DC_KANTO accepted / blocked lots.
```

After this upgrade:

```text
The first PSI smoke runner itself shows:
  master integration
  actual ProductPlanNode evidence
  MARKET_TOKYO lot attachment
  DC_KANTO accepted / blocked lots
```

This makes the runner much stronger as a demo and diagnostic entry point.

In simple terms:

```text
The Japanese Rice runner will no longer only say:
  the case loads.

It will also say:
  the rice bags are on the actual WOM vehicle,
  260 bags pass DC_KANTO,
  and 25 bags wait.
```
