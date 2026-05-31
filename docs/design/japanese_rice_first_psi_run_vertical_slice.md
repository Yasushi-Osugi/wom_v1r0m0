# Japanese Rice First PSI Run Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-05-31  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_first_psi_run_vertical_slice.md`

**Strategic role:** First integrated PSI run design for Japanese Rice Case  
**Primary case:** Japanese Rice Case  
**Initial execution target:** diagnostic-first PSI smoke run using capacity, demand, and network vertical slices

---

## 1. Purpose

This memo defines the first PSI run vertical slice for the Japanese Rice Case.

The previous vertical slices established the three foundational inputs:

```text
Capacity:
  examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv

Demand:
  examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv

Network:
  examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
  examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

The next step is to connect these three pieces into the first minimal PSI run.

This should be done carefully.

The first PSI run should be:

```text
diagnostic-first
small
deterministic
testable
non-GUI
non-invasive to existing planner behavior
```

The initial goal is not to implement full WOM.

The initial goal is to prove that:

```text
Japanese Rice demand lots can be loaded,
anchored at MARKET_TOKYO,
recognized as demand pressure on the WOM E2E network,
and compared with weekly capacity rows at the relevant nodes.
```

---

## 2. Current Completed Foundations

### 2.1 Capacity vertical slice

Completed:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
    ↓
capacity runtime attachment
    ↓
capacity diagnostics
```

Key nodes:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
```

Key weeks:

```text
2027-W40
2027-W41
2027-W42
```

### 2.2 Demand vertical slice

Completed:

```text
demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO outbound leaf plan_node compatibility shape
    ↓
psi4demand[week]["S"]
```

Key demand:

```text
MARKET_TOKYO
JAPANESE_RICE_STANDARD
2027-W40 = 80 lots
2027-W41 = 95 lots
2027-W42 = 110 lots
```

Total demand lots:

```text
285
```

### 2.3 Network vertical slice

Completed:

```text
node_master.csv
network_master.csv
    ↓
WOM E2E hammock structure
```

Inbound path:

```text
supply_side_root
  -> supply_point
    -> RICE_MILL_A
      -> FARM_REGION_A
        -> Procurement_Center
```

Outbound path:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

MOM-DAD alignment:

```text
RICE_MILL_A:
  node_character = MOM
  partner_key = RICE_CORE

DC_KANTO:
  node_character = DAD
  partner_key = RICE_CORE
```

---

## 3. First PSI Run Definition

The first PSI run should not be a full production run.

It should be a vertical integration smoke run.

Recommended name:

```text
Japanese Rice first PSI run vertical slice
```

Recommended technical interpretation:

```text
load all Japanese Rice masters
validate cross-master alignment
generate demand lots
attach demand lots to MARKET_TOKYO leaf plan_node compatibility shape
load capacity rows
attach capacity runtime contexts
derive network paths
produce minimal weekly PSI/balance diagnostic
```

This is a first integrated run, not yet full canonical PSI propagation.

---

## 4. Important Scope Control

The first PSI run must avoid overreach.

### 4.1 In scope

```text
load capacity_master.csv
load demand_master.csv
load node_master.csv
load network_master.csv
generate DemandAnchoredLot records
attach demand lots to MARKET_TOKYO leaf psi4demand S slot compatibility shape
load WeeklyCapacityRow records into env.capacity_weekly_rows
apply capacity runtime attachment preflight
verify demand node exists as network market leaf
verify capacity nodes exist in network
verify inbound / outbound hammock paths exist
compute simple weekly balance series
return deterministic run summary / diagnostic
add focused tests
```

### 4.2 Out of scope

```text
full WOM planner rewrite
full original PySI V0R8 monthly demand compatibility
GUI wiring
NetworkX dependency retirement
optimization
cost / profit simulation
tariff calculation
inventory propagation
leadtime-shifted full PSI plan
MOM weekly balance graph rendering
scenario runner integration
```

This slice should produce data and diagnostics.

It should not yet draw the chart.

---

## 5. Why Diagnostic-First

A diagnostic-first PSI run is safer than immediately wiring into the full planner.

Reason:

```text
The Japanese Rice Case has just acquired capacity, demand, and network masters.
Before running full PSI logic, WOM should prove that these masters align.
```

The first run should answer:

```text
Can the system load all masters?
Do products match?
Do weeks match?
Do demand nodes exist in the network?
Do capacity nodes exist in the network?
Can demand lots sit at the correct outbound market leaf?
Can capacity rows be read by the runtime capacity context?
Can a simple weekly demand-capacity comparison be produced?
```

This is like a test drive in a parking lot before entering the highway.

---

## 6. Proposed First Runner

Recommended implementation target for a future Codex request:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

or, if project style prefers package helpers:

```text
pysi/scenarios/japanese_rice_first_psi_run.py
```

Recommended focused test:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Recommended scenario root:

```text
examples/scenarios/japanese_rice_vslice_001
```

The runner should be pure and callable from tests.

It should not require GUI.

It should not require a full command-line interface in the first slice.

---

## 7. Proposed API

Recommended function:

```python
run_japanese_rice_first_psi_vslice(
    scenario_root: str | Path,
) -> dict
```

Alternative generic function:

```python
run_first_psi_vslice(
    scenario_root: str | Path,
    *,
    scenario_id: str,
    product_name: str,
) -> dict
```

For first implementation, a Japanese Rice-specific runner is acceptable if it keeps scope small.

A generic helper can be extracted later.

---

## 8. Loading Sequence

Recommended loading sequence:

```text
1. Load network node master.
2. Load network edge master.
3. Load demand master.
4. Generate demand anchored lots.
5. Attach demand lots to MARKET_TOKYO leaf plan_node compatibility shape.
6. Load capacity master to env.capacity_weekly_rows.
7. Apply capacity runtime attachment preflight.
8. Validate cross-master alignment.
9. Compute simple weekly balance summary.
10. Return run diagnostic.
```

This sequence ensures the network is present before interpreting demand and capacity alignment.

---

## 9. Expected Master Inputs

### 9.1 Capacity input

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Expected capacity facts:

```text
FARM_REGION_A P capacity = 120 lots/week
RICE_MILL_A P capacity = 100 lots/week
DC_KANTO S capacity = 90 lots/week
weeks = 2027-W40, 2027-W41, 2027-W42
```

### 9.2 Demand input

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

Expected demand facts:

```text
MARKET_TOKYO demand = 80 / 95 / 110 lots
weeks = 2027-W40, 2027-W41, 2027-W42
total lots = 285
```

### 9.3 Network input

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

Expected network facts:

```text
RICE_MILL_A = MOM
DC_KANTO = DAD
MARKET_TOKYO = MARKET_LEAF
FARM_REGION_A = SUPPLIER_LEAF
supply_point = SUPPLY_POINT
RICE_MILL_A.partner_key = RICE_CORE
DC_KANTO.partner_key = RICE_CORE
```

---

## 10. Product and Scenario Contract

The first PSI run should use:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
```

All capacity, demand, and network rows should align to this product/scenario.

If a row uses a different product or scenario, the diagnostic should report mismatch.

For first implementation, tests can simply assert that all loaded rows match the expected product/scenario.

---

## 11. Demand Attachment Contract

Demand lots must remain anchored at:

```text
MARKET_TOKYO
```

Meaning:

```text
MARKET_TOKYO is the outbound market leaf plan_node.
```

The first PSI run should reuse the existing demand adapter:

```text
attach_demand_lots_to_leaf_plan_node_psi4demand(...)
```

Expected demand PSI compatibility shape:

```text
JAPANESE_RICE_STANDARD
  MARKET_TOKYO
    psi4demand
      2027-W40
        S = 80 lot IDs
      2027-W41
        S = 95 lot IDs
      2027-W42
        S = 110 lot IDs
```

This confirms that:

```text
DemandAnchoredLot is born at final demand.
```

---

## 12. Capacity Attachment Contract

The first PSI run should reuse the completed capacity source and runtime attachment helpers.

Relevant functions already implemented:

```text
load_capacity_weekly_rows_to_env(...)
apply_capacity_runtime_attachment_preflight(...)
build_capacity_runtime_attachment_diagnostic(...)
build_capacity_weekly_rows_source_diagnostic(...)
```

Expected env fields:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_load_summary
env.capacity_runtime_attachment_summary
env.capacity_runtime_attachment_preflight_result
```

The first run should not change capacity enforcement behavior.

It should only consume the existing capacity runtime context for diagnostic purposes.

---

## 13. Network Alignment Contract

The runner should verify:

```text
MARKET_TOKYO exists in node_master
MARKET_TOKYO.node_character = MARKET_LEAF
MARKET_TOKYO.tree_side = outbound
MARKET_TOKYO.is_leaf = true

FARM_REGION_A exists in node_master
RICE_MILL_A exists in node_master
DC_KANTO exists in node_master

RICE_MILL_A.node_character = MOM
DC_KANTO.node_character = DAD
RICE_MILL_A.partner_key = DC_KANTO.partner_key = RICE_CORE
```

It should also verify paths:

```text
inbound:
  supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center

outbound:
  demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office
```

---

## 14. Minimal Weekly Balance Summary

The first PSI run should compute a simple weekly balance summary.

This is not yet the final MOM balance chart.

It is a deterministic smoke diagnostic.

### 14.1 Demand series

From demand lots:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

### 14.2 DC_KANTO capacity series

From capacity rows:

```text
DC_KANTO S capacity = 90 / 90 / 90
```

Expected simple balance:

```text
2027-W40:
  demand = 80
  DC capacity = 90
  balance = +10
  shortage = 0

2027-W41:
  demand = 95
  DC capacity = 90
  balance = -5
  shortage = 5

2027-W42:
  demand = 110
  DC capacity = 90
  balance = -20
  shortage = 20
```

### 14.3 RICE_MILL_A capacity series

From capacity rows:

```text
RICE_MILL_A P capacity = 100 / 100 / 100
```

If using the same demand pressure as first smoke approximation:

```text
2027-W40:
  demand pressure = 80
  capacity = 100
  balance = +20

2027-W41:
  demand pressure = 95
  capacity = 100
  balance = +5

2027-W42:
  demand pressure = 110
  capacity = 100
  balance = -10
  shortage = 10
```

This is only a first diagnostic approximation.

It does not yet apply leadtime, inventory, or full PSI logic.

### 14.4 FARM_REGION_A capacity series

From capacity rows:

```text
FARM_REGION_A P capacity = 120 / 120 / 120
```

Using same demand pressure approximation:

```text
2027-W40:
  balance = +40

2027-W41:
  balance = +25

2027-W42:
  balance = +10
```

This shows the initial bottleneck tendency:

```text
DC_KANTO distribution capacity is most restrictive in W41/W42.
RICE_MILL_A becomes short only in W42 under the simple same-week approximation.
FARM_REGION_A is sufficient in all three weeks.
```

Again, this is not a final planning result.

It is a smoke diagnostic.

---

## 15. Expected Run Diagnostic Shape

Recommended returned dictionary:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "available": True,
    "masters": {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    },
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],
    "demand": {
        "node": "MARKET_TOKYO",
        "weekly_lot_counts": {
            "2027-W40": 80,
            "2027-W41": 95,
            "2027-W42": 110,
        },
        "total_lots": 285,
    },
    "network": {
        "inbound_path_exists": True,
        "outbound_path_exists": True,
        "mom_node": "RICE_MILL_A",
        "dad_node": "DC_KANTO",
        "partner_key": "RICE_CORE",
        "market_leaf": "MARKET_TOKYO",
        "supply_point": "supply_point",
    },
    "capacity": {
        "runtime_attachment_applied": True,
        "input_row_count": 9,
    },
    "balance": {
        "DC_KANTO": {
            "2027-W40": {"demand": 80, "capacity": 90, "balance": 10, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 90, "balance": -5, "shortage": 5},
            "2027-W42": {"demand": 110, "capacity": 90, "balance": -20, "shortage": 20},
        },
        "RICE_MILL_A": {
            "2027-W40": {"demand": 80, "capacity": 100, "balance": 20, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 100, "balance": 5, "shortage": 0},
            "2027-W42": {"demand": 110, "capacity": 100, "balance": -10, "shortage": 10},
        },
        "FARM_REGION_A": {
            "2027-W40": {"demand": 80, "capacity": 120, "balance": 40, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 120, "balance": 25, "shortage": 0},
            "2027-W42": {"demand": 110, "capacity": 120, "balance": 10, "shortage": 0},
        },
    },
    "messages": [
        "Japanese Rice first PSI vertical slice: masters loaded.",
        "Japanese Rice first PSI vertical slice: demand lots attached to MARKET_TOKYO leaf.",
        "Japanese Rice first PSI vertical slice: capacity runtime context attached.",
        "Japanese Rice first PSI vertical slice: network hammock paths verified.",
        "Japanese Rice first PSI vertical slice: simple weekly balance computed.",
    ],
}
```

The exact field names can be adjusted, but tests should verify the core facts.

---

## 16. Terminology: PSI Run vs PSI Smoke

This slice can be called a PSI run only in a limited sense.

Recommended wording:

```text
first PSI vertical slice
diagnostic-first PSI smoke run
```

Avoid claiming:

```text
full PSI planning completed
inventory plan completed
leadtime-adjusted plan completed
optimized plan completed
```

The correct statement is:

```text
Capacity, demand, and network have been integrated into a first deterministic PSI smoke diagnostic.
```

---

## 17. Suggested Implementation Scope for Codex

A future Codex request should likely add:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Possibly add:

```text
pysi/runners/__init__.py
```

if needed.

Do not add GUI files.

Do not add NetworkX changes.

Do not add CLI integration unless trivial and clearly isolated.

---

## 18. Test Strategy

Recommended test file:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Tests should verify:

```text
runner loads scenario root
capacity rows = 9
demand rows = 3
demand lots = 285
network nodes = 9
network edges = 8
weeks = 2027-W40 / W41 / W42
MARKET_TOKYO demand lot counts = 80 / 95 / 110
inbound path exists
outbound path exists
RICE_MILL_A is MOM
DC_KANTO is DAD
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
capacity runtime attachment applied
DC_KANTO simple balance = +10 / -5 / -20
RICE_MILL_A simple balance = +20 / +5 / -10
FARM_REGION_A simple balance = +40 / +25 / +10
messages include deterministic run status
```

Also run existing vertical slice tests:

```text
tests/test_japanese_rice_capacity_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_network_master_vertical_slice.py
```

---

## 19. Acceptance Criteria for Future Codex Request

The first PSI run vertical slice is complete when:

```text
Japanese Rice first PSI runner is added
runner loads capacity / demand / network masters
runner generates 285 demand lots
runner attaches demand lots to MARKET_TOKYO leaf compatibility structure
runner attaches capacity runtime context
runner verifies inbound / outbound hammock paths
runner verifies MOM/DAD partner_key alignment
runner computes deterministic simple weekly balance summary
focused test passes
capacity vertical slice test still passes
demand vertical slice test still passes
network vertical slice test still passes
capacity diagnostics tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
full PSI run not claimed
```

---

## 20. Non-Goals

This design does not implement:

```text
full canonical PSI planner
full PySI V0R8 monthly demand compatibility
leadtime-shifted PSI propagation
inventory carry-over calculation
backlog / CO calculation
optimized allocation
capacity enforcement beyond simple comparison
GUI cockpit view
MOM balance line chart
NetworkX removal
cost / price / profit simulation
```

These are future phases.

---

## 21. Future Work After This Slice

After the first PSI run smoke succeeds, recommended next steps are:

### 21.1 Plan-node tree instantiation

```text
Build actual product-specific inbound / outbound plan_node trees from node_master and network_master.
```

### 21.2 Leadtime-aware PSI propagation

```text
Use leadtime from network_master / node_plan_parameter_master to shift demand and supply by week.
```

### 21.3 Capacity-constrained run

```text
Use WeeklyCapacityRow runtime contexts to accept/block lots by week and node.
```

### 21.4 Integrated diagnostics

```text
diagnostic["japanese_rice_first_psi_run"]
diagnostic["demand_network_alignment"]
diagnostic["capacity_network_alignment"]
diagnostic["weekly_balance"]
```

### 21.5 MOM weekly balance line visualization

```text
Render weekly demand pressure, capacity, accepted lots, blocked lots, and balance gap.
```

This future visualization should be based on computed weekly series after PSI execution.

---

## 22. Relationship to MOM Weekly Balance Line

The simple weekly balance summary in this slice is the data seed for the future visualization.

Future chart idea:

```text
x-axis:
  week

series:
  demand pressure
  available capacity
  accepted lots
  blocked lots
  balance gap
```

For Japanese Rice:

```text
RICE_MILL_A:
  milling capacity vs demand pressure

DC_KANTO:
  distribution capacity vs Tokyo demand pressure
```

The first PSI smoke should produce enough deterministic data to make this future chart credible, but the chart itself is out of scope.

Recommended future design:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

---

## 23. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_first_psi_run_vertical_slice_request.md
```

Scope:

```text
add a pure Japanese Rice first PSI smoke runner
add focused tests
load capacity / demand / network masters
generate demand lots
attach demand lots to MARKET_TOKYO leaf compatibility shape
attach capacity runtime context
verify network paths
compute simple weekly balance
do not modify planner
do not modify GUI
do not remove NetworkX
do not claim full PSI planning
```

---

## 24. Summary

Japanese Rice Case now has:

```text
Capacity
Demand
Network
```

The next step is the first deterministic integration run:

```text
Capacity + Demand + Network
    ↓
first PSI smoke diagnostic
```

This first run should prove:

```text
The rice demand lots exist.
The WOM hammock network exists.
The capacity rows exist.
The demand lots can be associated with the market leaf.
Capacity and demand can be compared by week.
The first simple balance signal can be produced.
```

This will be the first moment when Japanese Rice Case starts to behave like a runnable WOM scenario.

In simple terms:

```text
The rice bags, the demand, and the road network are ready.
The next slice starts the engine.
```
