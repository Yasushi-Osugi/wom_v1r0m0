# Codex Request: Japanese Rice Plan Node Tree Instantiation Vertical Slice

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_plan_node_tree_instantiation_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice.md
```

**Related design / completion docs:**

```text
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

**Related implementation files already present:**

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/network/network_master_loader.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/capacity/capacity_weekly_rows_source.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice plan node tree instantiation vertical slice.

The purpose of this request is to move from the current demand attachment compatibility shape to actual product-specific planning-layer node objects.

Current state:

```text
demand_master.csv
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO leaf compatibility shape
    ↓
psi4demand[week]["S"] = list[lot_ID]
```

Requested next state:

```text
node_master.csv / network_master.csv
    ↓
product-specific inbound / outbound plan_node trees
    ↓
actual MARKET_TOKYO outbound plan_node
    ↓
MARKET_TOKYO.psi4demand[week][0] = list[lot_ID]
```

This is not a full PSI planner run.

This is not GUI wiring.

This is the planning-layer tree instantiation bridge.

---

## 2. Strategic Context

The Japanese Rice Case already has:

```text
Capacity:
  capacity_master.csv

Demand:
  demand_master.csv

Network:
  node_master.csv / network_master.csv

First PSI smoke:
  run_japanese_rice_first_psi_vslice(...)
```

The first PSI smoke runner successfully integrates masters and computes a simple weekly balance, but its demand attachment is still compatibility-oriented.

This request creates the actual product-specific planning-layer node tree structure that later PSI propagation can use.

In simple terms:

```text
The previous slice started the engine.
This slice builds the planning-layer vehicle frame that carries the lots.
```

---

## 3. Scope Control

### 3.1 In scope

Add a focused implementation and tests to:

```text
instantiate inbound product-specific plan_node tree
instantiate outbound product-specific plan_node tree
preserve node_character / partner_key / tree_side / product_name
create parent / children links
initialize psi4demand structures
find actual MARKET_TOKYO outbound plan_node
generate 285 DemandAnchoredLots from demand_master.csv
attach lot IDs to MARKET_TOKYO.psi4demand[week][0]
verify capacity nodes exist in instantiated trees
verify legacy slot index 0 means S
```

### 3.2 Out of scope

Do not implement:

```text
full PSI planning
leadtime propagation
inventory calculation
CO / backlog calculation
capacity clipping
accepted / blocked lot movement
cost / profit evaluation
GUI display
MOM weekly balance line chart
NetworkX retirement
main runner / GUI wiring
```

This slice should be pure, testable, and non-invasive.

---

## 4. Expected Changed / Added Files

Recommended files to add:

```text
pysi/plan/plan_node_tree_instantiation.py
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

Optional package export if project style supports it:

```text
pysi/plan/__init__.py
```

If `pysi/plan/__init__.py` does not exist or changing it is risky, do not force an export.

Do not modify GUI files.

Do not modify planner engine files.

Do not remove or modify NetworkX.

---

## 5. Existing Functions to Reuse

Reuse existing loaders and generators.

### Network

```python
load_network_master_package(...)
load_network_node_master_csv(...)
load_network_edge_master_csv(...)
find_node(...)
has_path(...)
derive_tree_depths(...)
```

from:

```text
pysi/network/network_master_loader.py
```

### Demand

```python
load_weekly_demand_master_csv(...)
generate_demand_anchored_lots(...)
```

from:

```text
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
```

Do not duplicate CSV parsing logic.

---

## 6. Scenario Constants

Use:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
scenario_root = examples/scenarios/japanese_rice_vslice_001
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

Expected demand node:

```text
MARKET_TOKYO
```

Expected MOM node:

```text
RICE_MILL_A
```

Expected DAD node:

```text
DC_KANTO
```

Expected supplier node:

```text
FARM_REGION_A
```

Expected partner key:

```text
RICE_CORE
```

---

## 7. ProductPlanNode Runtime Object

If no suitable existing plan node class can be safely reused, implement a minimal runtime dataclass:

```python
@dataclass
class ProductPlanNode:
    scenario_id: str
    product_name: str
    tree_side: str
    node_name: str
    node_character: str
    node_role: str | None = None
    parent: "ProductPlanNode | None" = None
    children: list["ProductPlanNode"] = field(default_factory=list)
    partner_key: str | None = None
    position_group: str | None = None
    depth: int | None = None
    is_root: bool = False
    is_leaf: bool = False
    is_mom: bool = False
    is_dad: bool = False
    is_supply_point: bool = False
    is_supplier_leaf: bool = False
    is_market_leaf: bool = False
    is_procurement_center: bool = False
    is_global_sales_office: bool = False
    psi4demand: dict[str, list[list[str]]] = field(default_factory=dict)
    psi4supply: dict[str, list[list[str]]] = field(default_factory=dict)
```

The exact field list may be adjusted slightly, but tests must verify the essential behavior.

Important identity rule:

```text
plan_node identity = scenario_id + product_name + tree_side + node_name
```

Do not treat `node_name` alone as globally unique across planning views.

---

## 8. Tree-Side Specific supply_point Rule

`supply_point` appears in both inbound and outbound network views.

For this slice, instantiate two different plan_node objects:

```text
inbound supply_point plan_node
outbound supply_point plan_node
```

They share:

```text
node_name = supply_point
node_character = SUPPLY_POINT
```

but differ by:

```text
tree_side = inbound / outbound
```

The test should verify that inbound and outbound supply_point are distinct objects if object identity is accessible.

---

## 9. Inbound Plan Node Tree

Instantiate this inbound plan_node tree:

```text
supply_side_root
  -> supply_point
    -> RICE_MILL_A
      -> FARM_REGION_A
        -> Procurement_Center
```

Expected inbound node count:

```text
5
```

Expected inbound nodes:

```text
supply_side_root
supply_point
RICE_MILL_A
FARM_REGION_A
Procurement_Center
```

Expected node roles:

```text
RICE_MILL_A.node_character = MOM
RICE_MILL_A.is_mom = True
RICE_MILL_A.partner_key = RICE_CORE

FARM_REGION_A.node_character = SUPPLIER_LEAF
FARM_REGION_A.is_supplier_leaf = True
```

---

## 10. Outbound Plan Node Tree

Instantiate this outbound plan_node tree:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

Expected outbound node count:

```text
5
```

Expected outbound nodes:

```text
demand_side_root
supply_point
DC_KANTO
MARKET_TOKYO
Global_Sales_Office
```

Expected node roles:

```text
DC_KANTO.node_character = DAD
DC_KANTO.is_dad = True
DC_KANTO.partner_key = RICE_CORE

MARKET_TOKYO.node_character = MARKET_LEAF
MARKET_TOKYO.is_market_leaf = True
MARKET_TOKYO.is_leaf = True
```

Important nuance:

```text
MARKET_TOKYO may have Global_Sales_Office as a control endpoint child.
Therefore, demand leaf should be identified by node_character = MARKET_LEAF / is_market_leaf,
not only by graph terminal status.
```

---

## 11. Tree Builder API

Implement:

```python
instantiate_product_plan_node_trees(
    *,
    scenario_id: str,
    product_name: str,
    nodes: list[NetworkNodeRow],
    edges: list[NetworkEdgeRow],
) -> dict
```

Recommended return shape:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "inbound": {
        "root": ProductPlanNode(...),
        "nodes": {
            "supply_side_root": ProductPlanNode(...),
            "supply_point": ProductPlanNode(...),
            "RICE_MILL_A": ProductPlanNode(...),
            "FARM_REGION_A": ProductPlanNode(...),
            "Procurement_Center": ProductPlanNode(...),
        },
    },
    "outbound": {
        "root": ProductPlanNode(...),
        "nodes": {
            "demand_side_root": ProductPlanNode(...),
            "supply_point": ProductPlanNode(...),
            "DC_KANTO": ProductPlanNode(...),
            "MARKET_TOKYO": ProductPlanNode(...),
            "Global_Sales_Office": ProductPlanNode(...),
        },
    },
    "summary": {
        "inbound_node_count": 5,
        "outbound_node_count": 5,
        "product_name": "JAPANESE_RICE_STANDARD",
    },
}
```

The exact dictionary can vary, but tests should confirm the same facts.

---

## 12. PSI Slot Initialization

Legacy PSI demand slot order is:

```text
0 = S
1 = CO
2 = I
3 = P
```

Implement or reuse:

```python
ensure_psi_week_slots(plan_node, week, *, psi_attr="psi4demand") -> list[list[str]]
```

Expected behavior:

```python
if week not in plan_node.psi4demand:
    plan_node.psi4demand[week] = [[], [], [], []]
```

It should return the 4-slot list.

The test must verify:

```python
len(plan_node.psi4demand[week]) == 4
```

and:

```python
plan_node.psi4demand[week][0] is the S slot
```

---

## 13. Demand Lot Attachment API

Implement:

```python
attach_demand_lots_to_actual_plan_node_psi4demand(
    plan_node: ProductPlanNode,
    lots: list[DemandAnchoredLot],
) -> dict
```

Expected behavior:

```text
filter or group lots by anchor_node / demand_node / week
initialize psi4demand[week] as [S, CO, I, P]
place lot IDs in psi4demand[week][0]
return deterministic summary
```

For this slice, lots should all target:

```text
MARKET_TOKYO
```

Expected summary:

```python
{
    "attached": True,
    "node_name": "MARKET_TOKYO",
    "product_name": "JAPANESE_RICE_STANDARD",
    "tree_side": "outbound",
    "total_lots": 285,
    "weekly_lot_counts": {
        "2027-W40": 80,
        "2027-W41": 95,
        "2027-W42": 110,
    },
    "psi_slot": "S",
    "legacy_slot_index": 0,
}
```

If the function receives lots for a different node, it may ignore them or raise.

For this happy-path slice, deterministic behavior is enough.

---

## 14. Optional Convenience Helper

A convenience helper may be useful:

```python
instantiate_japanese_rice_plan_node_tree_and_attach_demand(
    scenario_root: str | Path,
) -> dict
```

It can:

```text
load network package
instantiate plan_node trees
load demand master
generate lots
find MARKET_TOKYO outbound plan_node
attach lots
return summary
```

This helper is optional.

If implemented, tests may use it.

Do not wire it into `run_japanese_rice_first_psi_vslice(...)` in this request unless the change is tiny and non-breaking.

Safer approach:

```text
Add new helper and focused tests first.
Leave existing first PSI smoke runner unchanged.
```

---

## 15. Required Tests

Add:

```text
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

### 15.1 Instantiate inbound and outbound trees

Assert:

```text
inbound root = supply_side_root
outbound root = demand_side_root
inbound node count = 5
outbound node count = 5
```

### 15.2 Verify inbound parent / children links

Assert path through actual objects:

```text
supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center
```

Use `children` and `parent` links, not only edge helper path checks.

### 15.3 Verify outbound parent / children links

Assert path through actual objects:

```text
demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office
```

Use `children` and `parent` links.

### 15.4 Verify node_character and partner_key preservation

Assert:

```text
RICE_MILL_A.node_character == MOM
RICE_MILL_A.is_mom is True
RICE_MILL_A.partner_key == RICE_CORE

DC_KANTO.node_character == DAD
DC_KANTO.is_dad is True
DC_KANTO.partner_key == RICE_CORE
```

### 15.5 Verify supply_point tree-side-specific instances

Assert:

```text
inbound["nodes"]["supply_point"].tree_side == inbound
outbound["nodes"]["supply_point"].tree_side == outbound
```

If object identity is available:

```text
inbound supply_point is not outbound supply_point
```

### 15.6 Verify MARKET_TOKYO as actual outbound demand leaf plan_node

Assert:

```text
MARKET_TOKYO exists in outbound tree
MARKET_TOKYO.node_character == MARKET_LEAF
MARKET_TOKYO.is_market_leaf is True
MARKET_TOKYO.is_leaf is True
```

Do not require MARKET_TOKYO to be graph terminal because Global_Sales_Office may be a control endpoint child.

### 15.7 Attach demand lots to actual MARKET_TOKYO plan_node

Load demand master and generate lots.

Attach them to the actual outbound MARKET_TOKYO plan_node.

Assert:

```python
len(market_tokyo.psi4demand["2027-W40"][0]) == 80
len(market_tokyo.psi4demand["2027-W41"][0]) == 95
len(market_tokyo.psi4demand["2027-W42"][0]) == 110
```

Assert total:

```text
285
```

Assert lot IDs are unique.

### 15.8 Verify legacy PSI slot semantics

Assert:

```text
psi4demand[week] has exactly 4 slots
slot index 0 contains S lot IDs
slots 1, 2, 3 remain lists
```

If a symbolic S adapter is implemented, assert index 0 and symbolic S refer to the same list.

### 15.9 Capacity node alignment

Assert:

```text
FARM_REGION_A exists in inbound plan_node tree
RICE_MILL_A exists in inbound plan_node tree
DC_KANTO exists in outbound plan_node tree
```

No capacity planning is required.

### 15.10 Existing tests still pass

At minimum, the following tests must still pass:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
tests/test_japanese_rice_network_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

---

## 16. Test Commands

Run focused test:

```bat
python -m pytest tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

Run existing Japanese Rice vertical slice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Run capacity integration tests if touched dependencies require confidence:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Run compile check:

```bat
python -m compileall -q pysi/plan/plan_node_tree_instantiation.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

If implementation file is placed elsewhere, adjust the compile command accordingly.

---

## 17. Safety Boundaries

Expected changed / added files:

```text
pysi/plan/plan_node_tree_instantiation.py
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
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

Do not run full PSI.

Do not change scenario master CSV files unless a clear typo blocks the test.

Do not change first PSI smoke runner unless absolutely necessary.

---

## 18. Acceptance Criteria

This request is complete when:

```text
ProductPlanNode or equivalent runtime object is implemented
inbound product-specific plan_node tree is instantiated
outbound product-specific plan_node tree is instantiated
parent / children links are created
node_character is preserved
partner_key is preserved
inbound and outbound supply_point are tree-side-specific plan_nodes
MARKET_TOKYO actual outbound plan_node is found
285 DemandAnchoredLots are generated
MARKET_TOKYO.psi4demand[2027-W40][0] has 80 lot IDs
MARKET_TOKYO.psi4demand[2027-W41][0] has 95 lot IDs
MARKET_TOKYO.psi4demand[2027-W42][0] has 110 lot IDs
legacy PSI slot index 0 is verified as S
capacity nodes align with instantiated trees
focused test passes
Japanese Rice first PSI smoke test still passes
capacity / demand / network vertical slice tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
```

---

## 19. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was ProductPlanNode or equivalent implemented?
Where was the tree instantiation helper implemented?
What test file was added?
Does it instantiate inbound and outbound product-specific plan_node trees?
How many inbound and outbound plan_nodes are created?
Does it preserve parent / children links?
Does it preserve node_character?
Does it preserve RICE_MILL_A / DC_KANTO partner_key = RICE_CORE?
Are inbound and outbound supply_point distinct tree-side-specific plan_nodes?
Does MARKET_TOKYO exist as the actual outbound demand leaf plan_node?
Does MARKET_TOKYO.psi4demand[2027-W40][0] contain 80 lot IDs?
Does MARKET_TOKYO.psi4demand[2027-W41][0] contain 95 lot IDs?
Does MARKET_TOKYO.psi4demand[2027-W42][0] contain 110 lot IDs?
Does the implementation verify legacy PSI slot index 0 as S?
Does it change planner behavior?
Does it change GUI layout?
Does it remove or modify NetworkX?
Which tests passed?
```

---

## 20. Development Meaning

This request moves Japanese Rice Case from:

```text
compatibility shape
```

to:

```text
actual product-specific planning-layer node tree
```

This is the missing bridge before real PSI propagation.

The next phase after this can move toward:

```text
capacity-constrained first flow
leadtime-aware PSI propagation
MOM weekly balance line diagnostic
GUI visualization
```

This request should stay focused.

In simple terms:

```text
The rice bags exist.
The demand exists.
The road network exists.
The engine starts.
Now build the actual planning-layer vehicle frame and load the rice lots onto MARKET_TOKYO.
```
