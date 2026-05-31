# Japanese Rice Plan Node Tree Instantiation Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_plan_node_tree_instantiation_vertical_slice_request.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice plan node tree instantiation vertical slice.

This phase moves the Japanese Rice Case from:

```text
MARKET_TOKYO leaf compatibility shape
```

to:

```text
actual MARKET_TOKYO outbound ProductPlanNode
```

and confirms that generated DemandAnchoredLots can be attached to the actual planning-layer node structure:

```python
MARKET_TOKYO.psi4demand[week][0] = list[lot_ID]
```

This is an important bridge from master-data diagnostics to real WOM planning-layer structure.

---

## 2. Key Commit

Implementation commit:

```text
19d0303 Add Japanese rice plan node tree instantiation
```

Related preceding commits:

```text
87b04a8 Add Japanese Rice plan node tree instantiation vertical slice Codex request
0c83b0f Add Japanese Rice plan node tree instantiation vertical slice design
e818935 Add Japanese Rice first PSI run vertical slice completion memo
6998529 Add Japanese rice first PSI smoke runner
442d9ad Add Japanese Rice first PSI run vertical slice Codex request
91317ee Add Japanese Rice first PSI run vertical slice design
88e2da9 Add Japanese Rice network master vertical slice completion memo
e710bc5 Add Japanese rice network vertical slice
6d5e11f Add Japanese Rice network master vertical slice Codex request
```

---

## 3. Files Added

This implementation added:

```text
pysi/plan/plan_node_tree_instantiation.py
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

The commit created:

```text
2 files changed
573 insertions
```

No GUI files were changed.

No planner engine files were changed.

No NetworkX dependency was removed or modified.

No full PSI run was executed or claimed.

---

## 4. Implemented ProductPlanNode

Implemented in:

```text
pysi/plan/plan_node_tree_instantiation.py
```

Implemented runtime object:

```text
ProductPlanNode
```

The object includes the key planning-layer identity dimensions:

```text
scenario_id
product_name
tree_side
node_name
```

This is important because a physical node name alone is not enough to identify a WOM planning-layer node.

Correct plan_node identity is:

```text
scenario_id + product_name + tree_side + node_name
```

This allows, for example:

```text
inbound supply_point plan_node
outbound supply_point plan_node
```

to exist as distinct runtime objects.

---

## 5. Implemented Tree Instantiation Helper

Implemented helper:

```text
instantiate_product_plan_node_trees(...)
```

The helper builds:

```text
product-specific inbound plan_node tree
product-specific outbound plan_node tree
```

from:

```text
node_master.csv
network_master.csv
```

using the already implemented network master loader.

The helper preserves:

```text
node_character
node_role
tree_side
product_name
partner_key
position_group
role flags
parent / children links
```

---

## 6. Inbound Plan Node Tree Confirmed

The implementation instantiates the inbound Japanese Rice plan_node tree:

```text
supply_side_root
  -> supply_point
    -> RICE_MILL_A
      -> FARM_REGION_A
        -> Procurement_Center
```

Expected and verified inbound node count:

```text
5
```

Key inbound nodes:

```text
supply_side_root
supply_point
RICE_MILL_A
FARM_REGION_A
Procurement_Center
```

Key role preservation:

```text
RICE_MILL_A:
  node_character = MOM
  is_mom = True
  partner_key = RICE_CORE

FARM_REGION_A:
  node_character = SUPPLIER_LEAF
  is_supplier_leaf = True
```

---

## 7. Outbound Plan Node Tree Confirmed

The implementation instantiates the outbound Japanese Rice plan_node tree:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

Expected and verified outbound node count:

```text
5
```

Key outbound nodes:

```text
demand_side_root
supply_point
DC_KANTO
MARKET_TOKYO
Global_Sales_Office
```

Key role preservation:

```text
DC_KANTO:
  node_character = DAD
  is_dad = True
  partner_key = RICE_CORE

MARKET_TOKYO:
  node_character = MARKET_LEAF
  is_market_leaf = True
  is_leaf = True
```

Important nuance:

```text
MARKET_TOKYO may have Global_Sales_Office as a control endpoint child.
Therefore, MARKET_TOKYO is identified as a final demand leaf by node_character = MARKET_LEAF / is_market_leaf,
not only by graph terminal status.
```

---

## 8. supply_point Tree-Side Separation Confirmed

The implementation confirms that `supply_point` is instantiated separately for inbound and outbound trees.

Expected and verified:

```text
inbound supply_point:
  tree_side = inbound

outbound supply_point:
  tree_side = outbound
```

They share:

```text
node_name = supply_point
node_character = SUPPLY_POINT
```

but they are distinct product-specific runtime plan_nodes because their `tree_side` differs.

This is correct for the current vertical slice.

Future bridge logic may explicitly connect them.

---

## 9. MOM/DAD Partner Alignment Preserved

The implementation preserves MOM/DAD partner alignment through `partner_key`.

Expected and verified:

```text
RICE_MILL_A.partner_key = RICE_CORE
DC_KANTO.partner_key = RICE_CORE
```

This continues the design decision:

```text
MOM/DAD are not detected by node_name prefix.
MOM/DAD roles are carried by node_character.
MOM/DAD correspondence is carried by partner_key.
```

This is a major step toward generic WOM model master definition.

---

## 10. DemandAnchoredLot Attachment to Actual PlanNode

The implementation confirms that generated demand lots can be attached to the actual outbound MARKET_TOKYO ProductPlanNode.

The target is no longer only:

```text
MARKET_TOKYO leaf compatibility shape
```

The target is now:

```text
actual outbound MARKET_TOKYO ProductPlanNode
```

Expected and verified:

```python
MARKET_TOKYO.psi4demand["2027-W40"][0] contains 80 lot IDs
MARKET_TOKYO.psi4demand["2027-W41"][0] contains 95 lot IDs
MARKET_TOKYO.psi4demand["2027-W42"][0] contains 110 lot IDs
```

Total attached demand lots:

```text
285
```

Lot IDs are verified as unique.

---

## 11. Legacy PSI Slot Semantics Confirmed

The implementation confirms the legacy PSI slot order:

```text
0 = S
1 = CO
2 = I
3 = P
```

For the actual MARKET_TOKYO plan_node:

```python
psi4demand[week][0]
```

is the demand S slot.

The tests verify:

```text
psi4demand[week] has exactly 4 slots
slot 0 contains demand S lot IDs
slots 1, 2, and 3 remain list containers
```

This preserves compatibility with existing PySI / WOM PSI semantics.

---

## 12. Capacity Node Alignment Confirmed

This slice does not perform capacity-constrained planning.

However, it verifies that the capacity nodes are present in the instantiated plan_node trees:

```text
FARM_REGION_A:
  exists in inbound plan_node tree

RICE_MILL_A:
  exists in inbound plan_node tree

DC_KANTO:
  exists in outbound plan_node tree
```

This prepares the next phase where capacity rows can be connected to actual plan_nodes.

---

## 13. Tests Added

Focused test file:

```text
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

The tests verify:

```text
inbound and outbound product-specific plan_node tree instantiation
5 inbound plan_nodes
5 outbound plan_nodes
actual parent / children object links
inbound path through object traversal
outbound path through object traversal
node_character preservation
partner_key preservation
tree-side-specific supply_point instances
MARKET_TOKYO as actual outbound demand leaf plan_node
DemandAnchoredLot attachment to MARKET_TOKYO.psi4demand[week][0]
legacy PSI slot semantics
capacity node alignment
```

---

## 14. Tests Executed

Focused test:

```bat
python -m pytest tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

Observed result:

```text
10 passed
```

Existing Japanese Rice vertical slice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
31 passed
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
python -m compileall -q pysi/plan/plan_node_tree_instantiation.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

---

## 15. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
GUI layout
NetworkX dependency
first PSI smoke runner behavior
capacity enforcement behavior
full PSI planner behavior
cost / price / profit behavior
monthly demand compatibility behavior
```

This phase only added:

```text
ProductPlanNode runtime object
plan_node tree instantiation helper
demand lot attachment to actual plan_node helper
focused tests
```

---

## 16. Current Japanese Rice Case State

The Japanese Rice Case now has:

```text
Capacity
Demand
Network
First PSI smoke runner
Actual product-specific plan_node tree
DemandAnchoredLot attachment to actual MARKET_TOKYO plan_node
```

The current state can be summarized as:

```text
capacity_master.csv
demand_master.csv
node_master.csv
network_master.csv
    ↓
ProductPlanNode trees
    ↓
MARKET_TOKYO.psi4demand[week][0]
    ↓
DemandAnchoredLot IDs attached
```

This is a substantial movement from static master definitions toward real WOM planning execution.

---

## 17. Development Meaning

This is a major milestone.

Before this phase:

```text
Demand lots could be attached to a compatibility shape.
```

After this phase:

```text
Demand lots can be attached to an actual product-specific planning-layer node.
```

The difference is important.

The previous structure proved:

```text
The data can be represented.
```

This structure proves:

```text
The data can be placed into the actual WOM planning-layer vehicle.
```

The Japanese Rice Case has now moved closer to executable PSI propagation.

---

## 18. Still Deferred

The following remain intentionally deferred.

### 18.1 Full PSI planning

Not yet implemented:

```text
leadtime-shifted demand propagation
supply propagation
inventory calculation
CO / backlog calculation
accepted / blocked lot propagation
```

### 18.2 Capacity-constrained first flow

Not yet implemented:

```text
capacity rows attached to actual plan_nodes
capacity clipping
accepted lots
blocked lots
blocked lot IDs by node/week
```

### 18.3 Leadtime-aware PSI propagation

Not yet implemented:

```text
P-to-S shifting
S-to-P backward propagation
week-shift by leadtime
long vacation handling
```

### 18.4 GUI visualization

Not yet implemented:

```text
MOM weekly balance line
DC_KANTO balance chart
cockpit visibility
NetworkX retirement
```

### 18.5 Cost / profit integration

Not yet implemented:

```text
price / profit simulation
cost profile
tariff impact
cash / AR / AP effects
```

---

## 19. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice.md
```

Purpose:

```text
Use actual product-specific plan_node trees and capacity rows to perform the first minimal capacity-constrained lot acceptance / blocking flow.
```

Recommended first target:

```text
MARKET_TOKYO demand lots
    ↓
DC_KANTO capacity check
    ↓
accepted / blocked lots by week
```

A small first flow could focus on the DAD / outbound side:

```text
DC_KANTO -> MARKET_TOKYO
```

using the already visible bottleneck signal:

```text
DC_KANTO capacity:
  90 lots/week

MARKET_TOKYO demand:
  80 / 95 / 110

Expected same-week shortage:
  0 / 5 / 20
```

This would turn the current smoke balance into actual lot-level accepted / blocked results.

---

## 20. Alternative Next Step

An alternative is:

```text
docs/design/japanese_rice_first_psi_smoke_runner_actual_plan_node_upgrade.md
```

Purpose:

```text
Revise run_japanese_rice_first_psi_vslice(...) to use actual ProductPlanNode trees instead of compatibility shapes.
```

Recommended order:

```text
1. Capacity-constrained first flow design
2. Then revise the first PSI smoke runner to consume actual ProductPlanNode tree
```

This keeps the current successful smoke runner stable until the next flow design is clear.

---

## 21. Future MOM Weekly Balance Line

The plan_node tree instantiation also prepares the future MOM weekly balance line.

Future visualization can use actual plan_nodes:

```text
RICE_MILL_A:
  actual inbound MOM plan_node

DC_KANTO:
  actual outbound DAD plan_node

MARKET_TOKYO:
  actual outbound demand leaf plan_node
```

Future chart series can include:

```text
demand pressure
capacity
accepted lots
blocked lots
balance gap
inventory / backlog
```

Recommended future design remains:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

---

## 22. Completion Summary

Completed:

```text
ProductPlanNode implemented
product-specific inbound plan_node tree instantiated
product-specific outbound plan_node tree instantiated
parent / children object links created
node_character preserved
partner_key preserved
inbound and outbound supply_point instantiated as separate tree-side-specific plan_nodes
MARKET_TOKYO actual outbound ProductPlanNode found
285 DemandAnchoredLots generated and attached
MARKET_TOKYO.psi4demand[2027-W40][0] has 80 lot IDs
MARKET_TOKYO.psi4demand[2027-W41][0] has 95 lot IDs
MARKET_TOKYO.psi4demand[2027-W42][0] has 110 lot IDs
legacy PSI slot index 0 verified as S
capacity nodes align with instantiated trees
focused tests passed
Japanese Rice first PSI smoke test still passes
capacity / demand / network vertical slice tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
compileall passed
```

Current milestone:

```text
Japanese Rice Case now has actual product-specific plan_node trees with demand lots attached to MARKET_TOKYO.psi4demand[week][0].
```

Next recommended milestone:

```text
Japanese Rice capacity-constrained first flow vertical slice.
```

In simple terms:

```text
The rice bags are no longer sitting on a temporary compatibility shelf.
They are now loaded onto the actual WOM planning-layer vehicle.
The next step is to move that vehicle through the first capacity gate.
```
