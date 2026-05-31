# Japanese Rice First PSI Run Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_psi_run_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_first_psi_run_vertical_slice_request.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice first PSI run vertical slice.

This phase implemented the first deterministic integrated smoke runner for the Japanese Rice Case.

The runner integrates:

```text
Capacity
Demand
Network
```

and returns a diagnostic-first PSI smoke result.

This is not a full canonical PSI planner.

This is the first successful integration test showing that the Japanese Rice Case can load all three foundational model entrances and compute a deterministic weekly balance signal.

---

## 2. Key Commit

Implementation commit:

```text
6998529 Add Japanese rice first PSI smoke runner
```

Related preceding commits:

```text
442d9ad Add Japanese Rice first PSI run vertical slice Codex request
91317ee Add Japanese Rice first PSI run vertical slice design
88e2da9 Add Japanese Rice network master vertical slice completion memo
e710bc5 Add Japanese rice network vertical slice
6d5e11f Add Japanese Rice network master vertical slice Codex request
e072ee0 Revise Japanese Rice network master vertical slice design for WOM hammock layout semantics
018df04 Add Japanese Rice demand master vertical slice completion memo
a6334e4 Add Japanese rice demand vertical slice
0598d53 Clarify demand lot leaf plan node anchor in Japanese Rice request
```

---

## 3. Files Added

This implementation added:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

The commit created:

```text
2 files changed
375 insertions
```

No GUI file was changed.

No planner behavior was changed.

No NetworkX dependency was removed or modified.

No full PSI planner run was claimed.

---

## 4. Implemented Runner

Implemented runner:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Primary API:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

Purpose:

```text
Run a deterministic diagnostic-first PSI smoke integration for the Japanese Rice Case.
```

The runner:

```text
loads network masters
loads demand master
generates DemandAnchoredLots
attaches demand lots to MARKET_TOKYO leaf psi4demand compatibility shape
loads capacity rows
applies capacity runtime attachment preflight
validates demand / capacity / network alignment
validates MOM/DAD partner_key alignment
validates inbound / outbound WOM hammock paths
computes deterministic same-week balance summary
returns a diagnostic dictionary
```

---

## 5. Explicit Run Mode

The returned result explicitly marks the run as:

```text
diagnostic_first_psi_smoke
```

and explicitly states:

```text
full_psi_plan = False
```

This is important.

The implementation does not present itself as a completed full PSI planner.

It is a first integrated smoke diagnostic.

Correct interpretation:

```text
Capacity, demand, and network have been integrated into a deterministic first PSI smoke diagnostic.
```

Incorrect interpretation:

```text
Full canonical PSI planning is complete.
```

---

## 6. Loaded Master Inputs

The runner integrates the following Japanese Rice scenario masters.

### 6.1 Capacity

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Expected and verified:

```text
capacity rows = 9
```

Capacity facts used by the smoke balance:

```text
FARM_REGION_A P capacity = 120 lots/week
RICE_MILL_A P capacity = 100 lots/week
DC_KANTO S capacity = 90 lots/week
```

### 6.2 Demand

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

Expected and verified:

```text
demand rows = 3
demand lots = 285
```

Demand facts:

```text
MARKET_TOKYO demand:
  2027-W40 = 80 lots
  2027-W41 = 95 lots
  2027-W42 = 110 lots
```

### 6.3 Network

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

Expected and verified:

```text
network nodes = 9
network edges = 8
```

Network facts:

```text
RICE_MILL_A = MOM
DC_KANTO = DAD
FARM_REGION_A = SUPPLIER_LEAF
MARKET_TOKYO = MARKET_LEAF
supply_point = SUPPLY_POINT
```

MOM/DAD alignment:

```text
RICE_MILL_A.partner_key = RICE_CORE
DC_KANTO.partner_key = RICE_CORE
```

---

## 7. Demand Lot Attachment Confirmed

The runner confirms that generated demand lots attach to the MARKET_TOKYO leaf compatibility shape.

Expected structure:

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

This preserves the WOM principle:

```text
DemandAnchoredLot is born at final demand.
```

And the legacy-compatible PSI meaning:

```python
MARKET_TOKYO.plan_node.psi4demand[week]["S"] = list[lot_ID]
```

or:

```python
MARKET_TOKYO.plan_node.psi4demand[week][0] = list[lot_ID]
```

---

## 8. Capacity Runtime Attachment Confirmed

The runner applies the existing capacity runtime attachment preflight.

Expected and verified:

```text
runtime_attachment_applied = True
input_row_count = 9
```

This uses the existing capacity runtime helper path.

The runner does not change capacity enforcement behavior.

The runner does not implement new capacity planning logic.

It only consumes existing capacity rows and runtime attachment diagnostics for this first smoke run.

---

## 9. Network Hammock Paths Confirmed

The runner verifies the inbound and outbound WOM hammock paths.

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

The runner also verifies:

```text
mom_node = RICE_MILL_A
dad_node = DC_KANTO
partner_key = RICE_CORE
market_leaf = MARKET_TOKYO
supply_point = supply_point
```

This confirms that the Japanese Rice Case is now using the WOM E2E hammock structure.

---

## 10. Simple Weekly Balance Summary

The first PSI smoke computes a deterministic same-week balance.

This is not final PSI.

It does not yet apply:

```text
leadtime shift
inventory carry-over
backlog / CO calculation
optimization
capacity-constrained lot propagation
```

It is a smoke diagnostic.

### 10.1 DC_KANTO

Capacity:

```text
90 lots/week
```

Balance:

```text
2027-W40:
  demand = 80
  capacity = 90
  balance = +10
  shortage = 0

2027-W41:
  demand = 95
  capacity = 90
  balance = -5
  shortage = 5

2027-W42:
  demand = 110
  capacity = 90
  balance = -20
  shortage = 20
```

### 10.2 RICE_MILL_A

Capacity:

```text
100 lots/week
```

Balance:

```text
2027-W40:
  demand = 80
  capacity = 100
  balance = +20
  shortage = 0

2027-W41:
  demand = 95
  capacity = 100
  balance = +5
  shortage = 0

2027-W42:
  demand = 110
  capacity = 100
  balance = -10
  shortage = 10
```

### 10.3 FARM_REGION_A

Capacity:

```text
120 lots/week
```

Balance:

```text
2027-W40:
  demand = 80
  capacity = 120
  balance = +40
  shortage = 0

2027-W41:
  demand = 95
  capacity = 120
  balance = +25
  shortage = 0

2027-W42:
  demand = 110
  capacity = 120
  balance = +10
  shortage = 0
```

---

## 11. First Bottleneck Signal

The smoke balance shows a useful first bottleneck signal.

Initial same-week interpretation:

```text
DC_KANTO becomes short in W41 and W42.
RICE_MILL_A becomes short in W42.
FARM_REGION_A remains sufficient in all three weeks.
```

This suggests:

```text
DC_KANTO distribution capacity is the first visible restriction in this simple smoke diagnostic.
```

This is not yet a final planning conclusion.

It is a first integrated signal.

---

## 12. Tests Added

Focused test file:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

The tests cover:

```text
master counts
285 demand lots
MARKET_TOKYO leaf attachment
capacity preflight
network path verification
MOM/DAD partner alignment
weekly balance for DC_KANTO
weekly balance for RICE_MILL_A
weekly balance for FARM_REGION_A
deterministic messages
diagnostic-smoke marker
full_psi_plan = False
```

---

## 13. Tests Executed

Focused first PSI smoke test:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Observed result:

```text
9 passed
```

Japanese Rice vertical slice tests:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py
```

Observed result:

```text
22 passed
```

Capacity source / runtime / diagnostic integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
40 passed
```

Capacity regression tests:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
28 passed
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_psi_run_vertical_slice.py
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
GUI layout
NetworkX dependency
full PSI planner behavior
capacity enforcement behavior
original PySI monthly demand behavior
inventory calculation
backlog / CO calculation
cost / price / profit calculation
```

This phase added only:

```text
a pure Japanese Rice first PSI smoke runner
a focused test file
```

---

## 15. Current Japanese Rice Case State

The Japanese Rice Case has now reached this state:

```text
Capacity + Demand + Network
    ↓
diagnostic-first PSI smoke runner
    ↓
simple weekly balance diagnostic
```

This is the first time the case behaves like a runnable WOM scenario, even though it is not yet a full canonical PSI plan.

In practical terms:

```text
The rice demand lots exist.
The WOM hammock network exists.
The capacity rows exist.
The demand lots can be associated with the market leaf.
Capacity and demand can be compared by week.
The first simple balance signal is produced.
```

---

## 16. Development Meaning

This is a major milestone.

Before this phase:

```text
Capacity, Demand, and Network existed as separate vertical slices.
```

After this phase:

```text
Capacity, Demand, and Network are integrated into one deterministic PSI smoke diagnostic.
```

This is the first successful engine-start test for the Japanese Rice Case.

It confirms:

```text
The scenario can be loaded.
The master data align.
Demand lots can be generated.
Demand lots can be attached to the leaf demand node.
Capacity can be attached to runtime context.
Network hammock paths are valid.
Weekly balance can be computed.
```

The case has moved from static master definition to first runnable diagnostic behavior.

---

## 17. Still Deferred

The following remain intentionally deferred.

### 17.1 Full PSI planning

Not yet implemented:

```text
leadtime-shifted demand propagation
supply propagation
inventory calculation
CO / backlog calculation
accepted / blocked lot propagation
```

### 17.2 Product-specific plan_node instantiation

Not yet implemented:

```text
actual inbound/outbound plan_node tree objects generated from network_master
actual lot insertion into real PlanNode instances
```

Current demand attachment remains a compatibility shape.

### 17.3 Capacity-constrained lot planning

Not yet implemented:

```text
real capacity clipping across the network
blocked lot IDs by node/week from this runner
capacity-aware flow execution
```

### 17.4 GUI visualization

Not yet implemented:

```text
MOM weekly balance line chart
DC/Kanto balance chart
Cockpit display
NetworkX retirement
```

### 17.5 Cost / profit integration

Not yet implemented:

```text
cost profile
price simulation
profit / margin
tariff impact
cash / AR / AP effects
```

---

## 18. Recommended Next Step

The next design should probably move from smoke diagnostic to the first actual planning structure.

Recommended next design:

```text
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice.md
```

Purpose:

```text
Build product-specific inbound/outbound plan_node trees from node_master and network_master.
```

Why this should come next:

```text
The current runner uses compatibility structures.
The next step should instantiate actual planning-layer nodes.
Once actual plan_nodes exist, demand lots can be attached to real leaf nodes,
and later PSI propagation can operate on the actual WOM structure.
```

Alternative next design:

```text
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice.md
```

Purpose:

```text
Move from simple same-week balance to capacity-constrained lot acceptance/blocking.
```

Recommended order:

```text
1. Plan-node tree instantiation vertical slice
2. Demand lot attachment to actual MARKET_TOKYO plan_node
3. Capacity-constrained first flow vertical slice
4. MOM weekly balance line diagnostic
5. GUI visualization
```

---

## 19. Future MOM Weekly Balance Line

The current smoke balance already hints at the future visualization.

For example:

```text
DC_KANTO:
  capacity = 90
  demand = 80 / 95 / 110
  balance = +10 / -5 / -20

RICE_MILL_A:
  capacity = 100
  demand pressure = 80 / 95 / 110
  balance = +20 / +5 / -10
```

These are exactly the kind of time-series signals that can later become:

```text
MOM weekly demand-supply balance line
```

Future design:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

The visualization should wait until computed weekly series are produced by a more complete planning run.

---

## 20. Completion Summary

Completed:

```text
Japanese Rice first PSI smoke runner added
focused first PSI smoke test added
capacity / demand / network masters loaded together
285 demand lots generated
MARKET_TOKYO leaf compatibility attachment verified
capacity runtime attachment preflight applied
inbound hammock path verified
outbound hammock path verified
MOM/DAD partner_key alignment verified
simple weekly balance computed
DC_KANTO balance = +10 / -5 / -20
RICE_MILL_A balance = +20 / +5 / -10
FARM_REGION_A balance = +40 / +25 / +10
diagnostic_first_psi_smoke marker added
full_psi_plan = False
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
focused tests passed
vertical slice tests passed
capacity diagnostics tests passed
capacity regression tests passed
compileall passed
```

Current milestone:

```text
Japanese Rice Case has passed its first engine-start smoke test.
```

Next recommended milestone:

```text
Plan-node tree instantiation from Japanese Rice network master.
```

In simple terms:

```text
The rice bags, demand, road network, and first engine-start diagnostic are now in the repo.
The next step is to build the real planning-layer vehicle that will carry the lots.
```
