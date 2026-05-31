# Japanese Rice Network Master Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_network_master_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_network_master_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_network_master_vertical_slice_request.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice Case network master vertical slice.

This phase added the WOM E2E hammock network skeleton for Japanese Rice Case:

```text
Inbound:
  supply_side_root
    -> supply_point
      -> RICE_MILL_A
        -> FARM_REGION_A
          -> Procurement_Center

Outbound:
  demand_side_root
    -> supply_point
      -> DC_KANTO
        -> MARKET_TOKYO
          -> Global_Sales_Office
```

The completed network slice proves that Japanese Rice Case now has:

```text
Capacity:
  supply capability entrance

Demand:
  final demand lot source

Network:
  WOM E2E hammock structure
```

This is a major milestone because the Japanese Rice Case now has the three base elements required for a future PSI run:

```text
Demand
Capacity
Network
```

This phase does not execute a full PSI run.

It does not change planner behavior.

It does not change GUI layout.

It does not remove or modify NetworkX.

---

## 2. Key Commits

Implementation commit:

```text
e710bc5 Add Japanese rice network vertical slice
```

Related preceding commits:

```text
6d5e11f Add Japanese Rice network master vertical slice Codex request
e072ee0 Revise Japanese Rice network master vertical slice design for WOM hammock layout semantics
018df04 Add Japanese Rice demand master vertical slice completion memo
a6334e4 Add Japanese rice demand vertical slice
0598d53 Clarify demand lot leaf plan node anchor in Japanese Rice request
3ffd0e5 Revise Japanese Rice demand master vertical slice Codex request
45f172e Add Japanese Rice demand master vertical slice design
920d98d Add Japanese Rice capacity master vertical slice completion memo
d017bc1 Add Japanese rice capacity vertical slice
```

---

## 3. Files Added / Changed

This implementation added or updated:

```text
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
pysi/network/__init__.py
pysi/network/network_master_loader.py
tests/test_japanese_rice_network_master_vertical_slice.py
```

The commit created:

```text
5 files changed
552 insertions
```

New scenario master files:

```text
network_master.csv
node_master.csv
```

New implementation file:

```text
pysi/network/network_master_loader.py
```

New focused test file:

```text
tests/test_japanese_rice_network_master_vertical_slice.py
```

Existing package export updated:

```text
pysi/network/__init__.py
```

---

## 4. Added node_master.csv

New file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
```

It contains:

```text
9 nodes
```

Primary nodes:

```text
supply_side_root
demand_side_root
supply_point
RICE_MILL_A
FARM_REGION_A
Procurement_Center
DC_KANTO
MARKET_TOKYO
Global_Sales_Office
```

Key WOM node_character assignments:

```text
supply_point:
  SUPPLY_POINT

RICE_MILL_A:
  MOM

DC_KANTO:
  DAD

FARM_REGION_A:
  SUPPLIER_LEAF

MARKET_TOKYO:
  MARKET_LEAF

Procurement_Center:
  PROCUREMENT_CENTER

Global_Sales_Office:
  GLOBAL_SALES_OFFICE
```

---

## 5. Added network_master.csv

New file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

It contains:

```text
8 parent-child edges
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

This structure encodes the WOM E2E hammock model for the Japanese Rice Case.

---

## 6. Implemented Network Loader

Implemented in:

```text
pysi/network/network_master_loader.py
```

Implemented row types:

```text
NetworkNodeRow
NetworkEdgeRow
```

Implemented loader functions:

```text
load_network_node_master_csv(...)
load_network_edge_master_csv(...)
load_network_master_package(...)
```

Implemented helper functions:

```text
find_node(...)
edges_by_tree_side(...)
has_path(...)
derive_tree_depths(...)
```

Exported from:

```text
pysi/network/__init__.py
```

---

## 7. Important Semantic Achievement: MOM/DAD Without Name Prefix

A key achievement of this slice is that MOM and DAD are no longer detected from node_name prefix.

The new structure proves:

```text
RICE_MILL_A:
  node_character = MOM

DC_KANTO:
  node_character = DAD
```

Neither node name starts with:

```text
MOM
DAD
```

This means the new WOM master definition supports arbitrary business node names while preserving WOM roles.

This is important for generalizing WOM to many industries and scenarios.

---

## 8. Important Semantic Achievement: partner_key Alignment

The network slice also proves MOM/DAD alignment through `partner_key`.

For Japanese Rice Case:

```text
RICE_MILL_A:
  node_character = MOM
  partner_key = RICE_CORE

DC_KANTO:
  node_character = DAD
  partner_key = RICE_CORE
```

This means:

```text
RICE_MILL_A and DC_KANTO form an aligned MOM-DAD pair in the E2E hammock model.
```

This is more than a layout hint.

It is an E2E alignment semantic.

It allows future WOM logic and visualization to identify corresponding MOM and DAD roles without depending on naming conventions.

---

## 9. Layout Principle Confirmed

The implementation confirms that default layout depth can be derived from parent-child tree structure.

This supports the revised design principle:

```text
tree parent-child mapping is the primary layout source
```

and:

```text
position_group is optional
e2e_stage is optional / override only
```

The focused test confirms that layout depth can be derived from:

```text
network_master.csv parent_node / child_node relationships
```

without requiring NetworkX.

This preserves the original PySI V0R8 spirit:

```text
Map the tree parent-child structure directly,
then adjust same-depth spacing for visual readability.
```

---

## 10. NetworkX Boundary Preserved

This implementation did not remove or modify NetworkX.

That is correct.

NetworkX retirement is a future GUI / layout-engine concern, not part of the network master vertical slice.

Current decision:

```text
Network master:
  should be independent of NetworkX

NetworkX:
  may remain as an optional rendering adapter during migration
```

Future possible design docs:

```text
docs/design/wom_networkx_dependency_retirement.md
docs/design/wom_e2e_network_layout_engine_without_networkx.md
```

---

## 11. Tests Added

Focused test file:

```text
tests/test_japanese_rice_network_master_vertical_slice.py
```

The tests verify:

```text
node_master.csv exists
network_master.csv exists
9 nodes load
8 edges load
RICE_MILL_A has node_character = MOM
DC_KANTO has node_character = DAD
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
supply_point has node_character = SUPPLY_POINT
MARKET_TOKYO has node_character = MARKET_LEAF and is_leaf = true
FARM_REGION_A has node_character = SUPPLIER_LEAF
Procurement_Center exists
Global_Sales_Office exists
inbound hammock path exists
outbound hammock path exists
default layout depth can be derived from parent-child tree structure
position_group and e2e_stage remain optional
capacity nodes exist in network
demand node exists as outbound leaf
```

---

## 12. Tests Executed

Focused network vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_network_master_vertical_slice.py
```

Observed result:

```text
10 passed
```

Japanese Rice capacity vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
5 passed
```

Japanese Rice demand vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_demand_master_vertical_slice.py
```

Observed result:

```text
7 passed
```

Capacity weekly rows source helper test:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Observed result:

```text
8 passed
```

Capacity source Explicit KPI preflight wiring test:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Observed result:

```text
6 passed
```

Capacity weekly rows source diagnostic test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

Observed result:

```text
9 passed
```

Runtime attachment diagnostic integration test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Observed result:

```text
6 passed
```

Explicit pipeline capacity scenario alignment test:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
11 passed
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
python -m compileall pysi/network tests/test_japanese_rice_network_master_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

---

## 13. Current Japanese Rice Case State

The Japanese Rice Case now has the three foundational modeling entrances.

### 13.1 Capacity

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
capacity runtime diagnostic
```

### 13.2 Demand

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO outbound leaf plan_node compatibility shape
    ↓
psi4demand[week]["S"]
```

### 13.3 Network

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
    ↓
WOM E2E hammock structure
    ↓
inbound / outbound paths
    ↓
MOM-DAD partner_key alignment
```

This is a major milestone.

---

## 14. Relationship to WOM E2E Hammock Model

The completed network slice represents the WOM hammock model:

```text
Inbound:
  supply_side_root
    -> supply_point
      -> RICE_MILL_A
        -> FARM_REGION_A
          -> Procurement_Center

Outbound:
  demand_side_root
    -> supply_point
      -> DC_KANTO
        -> MARKET_TOKYO
          -> Global_Sales_Office
```

This gives Japanese Rice Case a real WOM network skeleton.

It is not only a physical chain.

It is a product-specific planning network with explicit WOM roles.

---

## 15. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
GUI layout
NetworkX dependency
full PSI run behavior
capacity enforcement
demand lot generation behavior
monthly S_month_data compatibility
cost / tariff / price loaders
scenario runner behavior
```

This phase only added:

```text
Japanese Rice node master
Japanese Rice network master
minimal pure network loader
network helper functions
focused tests
```

---

## 16. Legacy PySI V0R8 Compatibility Direction

This slice does not migrate all PySI V0R8 master attributes.

However, it preserves the design path to do so.

The revised design already documents how the following V0R8 attributes should be preserved later:

```text
lot_size
leadtime
process_capa
long_vacation_weeks
LT_boat
LT_air
LT_qourier
weeks_year
SS_days
TAX_currency_condition
HS_code
customs_tariff_rate
price_elasticity
cost_standard_flag
AR_lead_time
AP_lead_time
PSI_graph_flag
buffering_stock_flag
```

This avoids losing important V0R8 semantics while keeping this slice focused.

---

## 17. Why This Milestone Matters

Before this phase, Japanese Rice Case had:

```text
what supply can do
what the final market wants
```

After this phase, it also has:

```text
how the WOM E2E network connects them
```

This means the case now has:

```text
Capacity
Demand
Network
```

which are the three basic inputs required before attempting a first PSI run.

In practical terms:

```text
The rice supply capability exists.
The Tokyo market demand lots exist.
The WOM hammock road network now exists.
```

The next step can now be about making lots move.

---

## 18. Still Deferred

The following remain intentionally deferred.

### 18.1 Full PSI run

Not yet implemented:

```text
end-to-end PSI execution
lot propagation through network
capacity-constrained accepted / blocked lot behavior
```

### 18.2 Network-to-plan-node integration

Not yet implemented:

```text
actual product-specific plan_node tree instantiation from node_master / network_master
actual attachment of DemandAnchoredLot to instantiated MARKET_TOKYO plan_node
```

### 18.3 Demand / capacity / network integrated diagnostics

Not yet implemented:

```text
diagnostic["network_source"]
diagnostic["demand_network_alignment"]
diagnostic["capacity_network_alignment"]
```

### 18.4 MOM weekly balance visualization

Not yet implemented:

```text
weekly demand-supply balance line at RICE_MILL_A
MOM/DAD balance chart
GUI / cockpit time-series visualization
```

### 18.5 NetworkX retirement

Not yet implemented:

```text
pure WOM layout engine replacing NetworkX rendering dependency
```

---

## 19. Recommended Next Step

The recommended next design is:

```text
docs/design/japanese_rice_first_psi_run_vertical_slice.md
```

Purpose:

```text
Connect capacity, demand, and network vertical slices into the first minimal Japanese Rice PSI run.
```

The next request should be careful.

It should not try to implement full WOM.

It should first prove:

```text
1. Load Japanese Rice capacity, demand, and network masters.
2. Build or represent minimal product-specific planning network.
3. Verify MARKET_TOKYO demand lots can be associated with the network leaf.
4. Verify capacity nodes align with the network nodes.
5. Produce a minimal diagnostic or smoke result.
```

The first PSI run can be incremental.

Recommended first run target:

```text
diagnostic-first PSI run
```

rather than a full GUI demonstration.

---

## 20. Future Visualization Theme

A high-value future visualization remains:

```text
MOM weekly demand-supply balance line
```

For Japanese Rice Case, this would likely focus on:

```text
RICE_MILL_A:
  weekly milling capacity
  demand pressure
  accepted lots
  blocked lots
  balance gap

DC_KANTO:
  weekly distribution capacity
  market demand pressure
  shipment gap
```

This should be implemented after the first PSI run generates weekly time-series data.

Recommended future design:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

---

## 21. Completion Summary

Completed:

```text
Japanese Rice node_master.csv added
Japanese Rice network_master.csv added
NetworkNodeRow implemented
NetworkEdgeRow implemented
network master loader implemented
find_node helper implemented
edges_by_tree_side helper implemented
has_path helper implemented
derive_tree_depths helper implemented
9 nodes loaded
8 edges loaded
RICE_MILL_A node_character = MOM
DC_KANTO node_character = DAD
MOM/DAD detected without node_name prefix
RICE_MILL_A and DC_KANTO partner_key = RICE_CORE
supply_point node_character = SUPPLY_POINT
MARKET_TOKYO node_character = MARKET_LEAF
inbound hammock path verified
outbound hammock path verified
layout depth derived from parent-child tree
position_group remains optional
e2e_stage remains optional
planner behavior unchanged
GUI layout unchanged
NetworkX dependency untouched
full PSI run not required
focused tests passed
capacity and demand tests passed
capacity regression tests passed
compileall passed
```

Current milestone:

```text
Japanese Rice Case now has:
  Demand
  Capacity
  Network
```

This is the structural starting point for the next phase:

```text
Japanese Rice first PSI run vertical slice
```
