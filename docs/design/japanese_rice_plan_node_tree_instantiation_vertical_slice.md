# Japanese Rice Plan Node Tree Instantiation Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-05-31  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice.md`

**Strategic role:** Bridge from master-data compatibility shapes to actual product-specific planning-layer node trees  
**Primary case:** Japanese Rice Case  
**Initial execution target:** instantiate inbound / outbound plan_node trees from Japanese Rice node_master.csv and network_master.csv, then attach DemandAnchoredLots to the actual MARKET_TOKYO outbound leaf plan_node

---

## 1. Purpose

This memo defines the next Japanese Rice Case vertical slice after the first PSI smoke runner.

The current Japanese Rice first PSI smoke runner successfully proves:

```text
Capacity + Demand + Network
    ↓
diagnostic-first PSI smoke runner
    ↓
simple weekly balance diagnostic
```

However, the current demand lot attachment is still a compatibility shape.

The next required step is:

```text
node_master.csv / network_master.csv
    ↓
product-specific inbound / outbound plan_node trees
    ↓
actual MARKET_TOKYO outbound leaf plan_node
    ↓
plan_node.psi4demand[week][0] = list[lot_ID]
```

This is the bridge from static master loading and diagnostic smoke to actual WOM planning-layer structure.

---

## 2. Current State

### 2.1 Completed Capacity

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
capacity runtime attachment
```

Key facts:

```text
FARM_REGION_A P capacity = 120 lots/week
RICE_MILL_A P capacity = 100 lots/week
DC_KANTO S capacity = 90 lots/week
```

### 2.2 Completed Demand

```text
demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO leaf compatibility shape
```

Key facts:

```text
MARKET_TOKYO demand:
  2027-W40 = 80 lots
  2027-W41 = 95 lots
  2027-W42 = 110 lots

Total lots:
  285
```

### 2.3 Completed Network

```text
node_master.csv
network_master.csv
    ↓
WOM E2E hammock structure
```

Inbound:

```text
supply_side_root
  -> supply_point
    -> RICE_MILL_A
      -> FARM_REGION_A
        -> Procurement_Center
```

Outbound:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

### 2.4 Completed First PSI Smoke

```text
run_japanese_rice_first_psi_vslice(...)
```

It proves:

```text
masters load
demand lots generate
capacity runtime context attaches
network paths exist
simple weekly balance computes
```

But it does not yet instantiate real product-specific plan_node trees.

---

## 3. Problem Statement

The current runner proves that demand lots can be placed into a compatibility representation.

However, the next planning phase needs actual planning-layer node objects.

Current shape:

```text
MARKET_TOKYO leaf compatibility structure
  psi4demand[week]["S"] = list[lot_ID]
```

Needed next shape:

```python
market_tokyo_plan_node.psi4demand[week][0] = list[lot_ID]
```

or equivalent legacy-compatible access.

This is important because existing WOM / PySI planning logic historically expects node instances with PSI arrays or lists.

The next slice must create product-specific plan_node trees from the network master and then attach demand lots to the actual outbound leaf plan_node.

---

## 4. Scope of This Vertical Slice

### 4.1 In scope

```text
load Japanese Rice node_master.csv
load Japanese Rice network_master.csv
instantiate product-specific inbound plan_node tree
instantiate product-specific outbound plan_node tree
preserve node_character / partner_key / tree_side / product_name
link parent / children relationships
initialize psi4demand structure on plan_nodes
find MARKET_TOKYO outbound leaf plan_node
generate DemandAnchoredLots from demand_master.csv
attach demand lot IDs to MARKET_TOKYO.plan_node.psi4demand[week][0]
optionally expose symbolic S-slot adapter
verify capacity nodes exist in instantiated plan_node trees
add focused tests
```

### 4.2 Out of scope

```text
full PSI planner execution
leadtime-shifted propagation
inventory calculation
CO / backlog calculation
capacity-constrained accepted / blocked lot movement
GUI wiring
NetworkX refactoring
cost / profit calculation
monthly S_month_data compatibility
scenario runner wiring
```

This slice creates the planning-layer vehicle.

It does not yet drive the full route.

---

## 5. Design Principle: Physical Node vs Plan Node

The physical node and plan_node must be separated.

### 5.1 Physical node

Example:

```text
MARKET_TOKYO
DC_KANTO
RICE_MILL_A
FARM_REGION_A
```

These represent business locations or logical business nodes.

### 5.2 Plan node

A plan_node is product-specific and tree-side-specific.

Plan node key:

```text
(scenario_id, product_name, tree_side, node_name)
```

Example:

```text
(JAPANESE_RICE_VSLICE_001, JAPANESE_RICE_STANDARD, outbound, MARKET_TOKYO)
```

This represents the actual planning-layer leaf node for Japanese Rice demand in Tokyo.

### 5.3 Why this matters

The same physical node name may appear in multiple products or views.

Therefore, plan_node identity must not be only:

```text
node_name
```

It should be:

```text
product_name + tree_side + node_name
```

---

## 6. Product-Specific Tree Instantiation

The first implementation should instantiate two trees.

### 6.1 Inbound plan_node tree

Root:

```text
supply_side_root
```

Tree side:

```text
inbound
```

Product:

```text
JAPANESE_RICE_STANDARD
```

Expected path:

```text
supply_side_root
  -> supply_point
    -> RICE_MILL_A
      -> FARM_REGION_A
        -> Procurement_Center
```

### 6.2 Outbound plan_node tree

Root:

```text
demand_side_root
```

Tree side:

```text
outbound
```

Product:

```text
JAPANESE_RICE_STANDARD
```

Expected path:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

### 6.3 supply_point handling

`supply_point` appears in both trees.

For plan_node identity, the first slice should treat them as tree-side-specific plan nodes:

```text
inbound supply_point plan_node
outbound supply_point plan_node
```

They share the same physical node name and node_character, but are different plan_node instances because their tree_side differs.

Future logic may bridge them explicitly.

---

## 7. Proposed PlanNode Runtime Object

If no suitable existing plan_node class can be safely reused, implement a minimal runtime object.

Recommended name:

```text
ProductPlanNode
```

Possible location:

```text
pysi/plan/plan_node_tree_instantiation.py
```

Alternative location:

```text
pysi/network/plan_node_tree_instantiation.py
```

Recommended dataclass:

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
    is_leaf: bool = False
    is_mom: bool = False
    is_dad: bool = False
    is_supply_point: bool = False
    psi4demand: dict[str, list[list[str]]] = field(default_factory=dict)
    psi4supply: dict[str, list[list[str]]] = field(default_factory=dict)
```

The exact type of `psi4demand` can be adjusted to match existing conventions.

The critical requirement is:

```python
plan_node.psi4demand[week][0] == list_of_lot_IDs_for_S
```

---

## 8. PSI Slot Contract

The legacy PSI slot order is:

```text
0 = S
1 = CO
2 = I
3 = P
```

For demand attachment, this slice must prove:

```python
market_tokyo_plan_node.psi4demand["2027-W40"][0] has 80 lot IDs
market_tokyo_plan_node.psi4demand["2027-W41"][0] has 95 lot IDs
market_tokyo_plan_node.psi4demand["2027-W42"][0] has 110 lot IDs
```

Recommended helper:

```python
ensure_psi_week_slots(plan_node, week)
```

which initializes:

```python
plan_node.psi4demand[week] = [[], [], [], []]
```

if missing.

Optional symbolic adapter:

```python
get_psi_s_lots(plan_node, week) -> list[str]
```

But the test must verify the legacy access pattern:

```python
psi4demand[week][0]
```

---

## 9. Demand Lot Attachment to Actual PlanNode

The existing demand lot generator should be reused:

```text
load_weekly_demand_master_csv(...)
generate_demand_anchored_lots(...)
```

The new slice should add or reuse a function such as:

```python
attach_demand_lots_to_actual_plan_node_psi4demand(
    plan_node: ProductPlanNode,
    lots: list[DemandAnchoredLot],
) -> dict
```

It should:

```text
group lots by week
initialize psi4demand[week] as [S, CO, I, P]
place lot IDs in psi4demand[week][0]
return summary
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

---

## 10. Network Master to PlanNode Tree Builder

Recommended builder API:

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
    "product_name": "JAPANESE_RICE_STANDARD",
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "inbound": {
        "root": ProductPlanNode(...supply_side_root...),
        "nodes": {
            "supply_side_root": ProductPlanNode(...),
            "supply_point": ProductPlanNode(...),
            "RICE_MILL_A": ProductPlanNode(...),
            "FARM_REGION_A": ProductPlanNode(...),
            "Procurement_Center": ProductPlanNode(...),
        },
    },
    "outbound": {
        "root": ProductPlanNode(...demand_side_root...),
        "nodes": {
            "demand_side_root": ProductPlanNode(...),
            "supply_point": ProductPlanNode(...),
            "DC_KANTO": ProductPlanNode(...),
            "MARKET_TOKYO": ProductPlanNode(...),
            "Global_Sales_Office": ProductPlanNode(...),
        },
    },
    "summary": {...},
}
```

The exact return shape may vary, but tests must verify the core facts.

---

## 11. Node Character Preservation

PlanNode instances must preserve node character.

Expected:

```text
outbound MARKET_TOKYO:
  node_character = MARKET_LEAF
  is_leaf = true

outbound DC_KANTO:
  node_character = DAD
  is_dad = true
  partner_key = RICE_CORE

inbound RICE_MILL_A:
  node_character = MOM
  is_mom = true
  partner_key = RICE_CORE

inbound FARM_REGION_A:
  node_character = SUPPLIER_LEAF
```

This continues the policy:

```text
MOM/DAD are defined by node_character, not node_name prefix.
```

---

## 12. Capacity Node Alignment

This slice does not perform capacity-constrained planning.

However, it should verify that capacity nodes exist in the instantiated plan_node trees.

Expected mapping:

```text
FARM_REGION_A:
  exists in inbound plan_node tree

RICE_MILL_A:
  exists in inbound plan_node tree

DC_KANTO:
  exists in outbound plan_node tree
```

Optional future extension:

```text
attach capacity_by_week_type metadata to plan_node
```

But this should be optional in this slice.

The required point is alignment, not capacity execution.

---

## 13. Relationship to First PSI Smoke Runner

The first PSI smoke runner currently uses compatibility shapes.

After this slice, the runner can be improved to use actual plan_node tree objects.

Possible future update:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
instantiate_product_plan_node_trees(...)
    ↓
attach demand lots to actual MARKET_TOKYO plan_node
    ↓
compute same smoke balance
```

But the first implementation of this slice may add a new focused helper and test without rewriting the existing runner immediately.

Recommended safety approach:

```text
1. Implement tree instantiation helper.
2. Add focused tests.
3. Do not change first PSI smoke runner yet.
4. Later revise the smoke runner to consume the actual plan_node tree.
```

This avoids destabilizing the successful first PSI smoke runner.

---

## 14. Suggested Implementation Files

Recommended future implementation files:

```text
pysi/plan/plan_node_tree_instantiation.py
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

Optional package export:

```text
pysi/plan/__init__.py
```

If the project style avoids adding to `pysi/plan`, use:

```text
pysi/network/plan_node_tree_instantiation.py
```

But conceptually this belongs to the planning layer.

---

## 15. Required Tests

Recommended focused test:

```text
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
```

### 15.1 Instantiate inbound / outbound plan_node trees

Assert:

```text
inbound root = supply_side_root
outbound root = demand_side_root
inbound node count = 5
outbound node count = 5
```

### 15.2 Verify inbound path

Assert:

```text
supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center
```

using actual parent / children links.

### 15.3 Verify outbound path

Assert:

```text
demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office
```

using actual parent / children links.

### 15.4 Verify node_character and partner_key

Assert:

```text
RICE_MILL_A.node_character == "MOM"
RICE_MILL_A.partner_key == "RICE_CORE"

DC_KANTO.node_character == "DAD"
DC_KANTO.partner_key == "RICE_CORE"
```

### 15.5 Verify MARKET_TOKYO as actual outbound demand leaf plan_node

Assert:

```text
MARKET_TOKYO exists in outbound tree
MARKET_TOKYO.node_character == "MARKET_LEAF"
MARKET_TOKYO.is_leaf is True
```

Important nuance:

In the WOM hammock structure, `MARKET_TOKYO` may have a control endpoint child:

```text
Global_Sales_Office
```

Therefore, business demand leaf and graph terminal are not always identical.

For demand anchoring:

```text
MARKET_TOKYO is the final demand leaf by node_character = MARKET_LEAF.
```

Even if `Global_Sales_Office` exists as a control endpoint after it.

### 15.6 Attach demand lots to actual MARKET_TOKYO plan_node

Assert:

```python
market_tokyo.psi4demand["2027-W40"][0] has length 80
market_tokyo.psi4demand["2027-W41"][0] has length 95
market_tokyo.psi4demand["2027-W42"][0] has length 110
```

Assert total:

```text
285 lot IDs
```

Assert lot IDs are unique.

### 15.7 Verify legacy slot semantics

Assert:

```text
slot index 0 means S
```

If helper exposes slot names, assert:

```text
S slot and index 0 refer to same lot list
```

### 15.8 Capacity node alignment

Assert:

```text
FARM_REGION_A exists in inbound tree
RICE_MILL_A exists in inbound tree
DC_KANTO exists in outbound tree
```

### 15.9 No planner / GUI side effects

Assert or document:

```text
no full PSI run is executed
no GUI files are changed
NetworkX is not used
```

---

## 16. Acceptance Criteria for Future Codex Request

The implementation is complete when:

```text
ProductPlanNode or equivalent plan_node runtime object is implemented
inbound product-specific plan_node tree is instantiated
outbound product-specific plan_node tree is instantiated
parent / children links are created
node_character is preserved
partner_key is preserved
MARKET_TOKYO actual outbound plan_node is found
285 DemandAnchoredLots are generated
MARKET_TOKYO.psi4demand[2027-W40][0] has 80 lot IDs
MARKET_TOKYO.psi4demand[2027-W41][0] has 95 lot IDs
MARKET_TOKYO.psi4demand[2027-W42][0] has 110 lot IDs
capacity nodes align with instantiated trees
focused tests pass
Japanese Rice first PSI smoke test still passes
capacity / demand / network vertical slice tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
```

---

## 17. Non-Goals

This slice does not implement:

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
```

This slice only builds the real planning-layer tree and attaches demand lots to the real outbound leaf plan_node.

---

## 18. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_plan_node_tree_instantiation_vertical_slice_request.md
```

Scope:

```text
add plan_node tree instantiation helper
add ProductPlanNode or equivalent runtime class
instantiate inbound / outbound plan_node trees from Japanese Rice network master
generate demand lots
attach lots to actual MARKET_TOKYO outbound plan_node.psi4demand[week][0]
add focused tests
do not modify GUI
do not modify planner behavior
do not remove NetworkX
do not run full PSI
```

---

## 19. Development Meaning

This slice is the transition from:

```text
compatibility shape
```

to:

```text
actual product-specific planning-layer node tree
```

In the previous smoke runner, the system proved that the engine can start.

In this slice, WOM begins building the actual vehicle that will carry lots through the planning network.

Current metaphor:

```text
Rice bags exist.
Demand exists.
Road network exists.
The engine starts.
```

This slice adds:

```text
The actual planning-layer vehicle frame that can carry the rice lots.
```

After this, WOM can move toward:

```text
capacity-constrained first flow
leadtime-aware PSI propagation
MOM weekly balance line visualization
GUI demonstration
```
