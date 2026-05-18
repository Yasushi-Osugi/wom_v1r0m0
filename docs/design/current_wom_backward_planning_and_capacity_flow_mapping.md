# Current WOM Backward Planning and Capacity Flow Mapping

**Version:** v0r1 draft  
**Date:** 2026-05-18  
**Status:** Design / implementation mapping memo  
**Target path:** `docs/design/current_wom_backward_planning_and_capacity_flow_mapping.md`

---

## 1. Purpose

This memo maps the current WOM / PySI V0R8 planning flow around:

- Backward Planning
- `supply_point` connection
- MOM allocation
- MOM capacity leveling
- demand-to-supply bridge candidates
- future placement of With Capacity Forward PUSH Planning

The goal is to clarify existing implementation before changing the next bridge or capacity-aware forward planning functions.

---

## 2. Why This Mapping Is Needed

Recent Rice Case work verified this path:

```text
Rice weekly input
    ↓
WeeklyPlanRow
    ↓
LotHeader
    ↓
PsiSeedRecord
    ↓
PlanNode.psi4demand seed
    ↓
Backward Planning smoke
```

Before moving to:

```text
psi4demand
    ↓
psi4supply
```

or to:

```text
With Capacity Forward PUSH Planning
```

we need to understand the existing engine sequence.

Current WOM already contains several bridge-like and planning-like functions:

```text
outbound backward planning
outbound-to-inbound bridge
market-to-MOM allocation
MOM capacity leveling
demand-to-supply bridge
forward PUSH / PULL processing
```

Therefore, the next step is not to create a new bridge blindly.

The next step is to map the current engine.

---

## 3. High-Level Current Flow Hypothesis

```text
Run Full Plan
    ↓
_run_planning_sequence(...)
    ↓
outbound_backward_leaf_to_MOM(...)
    ↓
outbound → inbound connection
    ↓
MOM allocation
    ↓
inbound backward planning by MOM subtree
    ↓
MOM capacity leveling
    ↓
demand-to-supply bridge
    ↓
forward supply planning / PUSH-PULL
```

The exact runtime order should be confirmed by tracing `_run_planning_sequence(...)`.

---

## 4. Run Full Plan Entry Point

The GUI button calls:

```python
ttk.Button(action_row, text="Run Full Plan", command=self.run_full_plan)
```

`run_full_plan()` delegates the actual planning sequence to:

```python
self._run_planning_sequence(use_selected_decouples=True)
```

The planning sequence resolves:

```text
out_root = env.prod_tree_dict_OT[prod]
in_root  = env.prod_tree_dict_IN[prod]
```

with fallbacks to:

```text
env.root_node_outbound
env.root_node_inbound
```

This confirms that the planning target is the product-specific PlanNode world.

---

## 5. Product-Specific PlanNode Roots

WOM has two node worlds.

```text
Physical layer:
    product-independent GUI / map / NetworkX node world

Planning layer:
    product-specific PlanNode tree world
```

The target roots are:

```text
prod_tree_dict_OT[product_name] → outbound planning tree
prod_tree_dict_IN[product_name] → inbound planning tree
```

The current mapping work and future bridge work should target these PlanNode trees, not physical GUI nodes.

---

## 6. Current Step 1: Outbound Backward Planning

Current function:

```python
outbound_backward_leaf_to_MOM(out_root, in_root, layer="demand")
```

Current behavior:

```python
for n in _iter_postorder(out_root):
    if hasattr(n, "aggregate_children_P_into_parent_S"):
        n.aggregate_children_P_into_parent_S(layer=layer)
    if hasattr(n, "calcS2P"):
        n.calcS2P()
```

Meaning:

```text
market / leaf demand
    ↓
DAD nodes
    ↓
supply_point
```

This is current outbound-side Backward Planning / Demand Allocation.

It should be treated as an existing V0R8 engine asset.

---

## 7. `supply_point` Connection Model

`supply_point` is the conceptual connection node between outbound and inbound planning trees.

```text
OUTBOUND:
    supply_point → DADxxx → market / leaf

INBOUND:
    supply_point → MOMxxx → upstream / leaf
```

However, implementation must avoid blindly propagating the same demand from `supply_point` into all MOM branches.

Existing inbound logic already recognizes this risk and processes MOM subtrees separately.

---

## 8. Outbound-to-Inbound Connection

Current bridge candidate:

```python
connect_outbound2inbound(out_root, in_root)
```

It appears inside:

```python
inbound_backward_MOM_to_leaf(...)
```

Conceptually:

```text
outbound-side accumulated demand
    ↓
inbound-side demand context
```

Open questions:

```text
1. Does it copy supply_point demand?
2. Does it copy root-level PSI?
3. Does it preserve Lot_IDs?
4. Which buckets are copied?
5. Does it target psi4demand or psi4supply?
```

---

## 9. Processing A: Market-to-MOM Allocation

Current function:

```python
allocate_markets_to_moms(...)
```

Current behavior:

```text
1. collect source lots
2. extract market_key from lot_id
3. select assigned MOM using policy dictionary
4. append lot to selected MOM.psi4demand[w][S]
```

This is current WOM's rule-based MOM allocation.

It is not yet a full optimization model.

### Future direction

This can later become an OR / optimization model.

Possible objectives:

```text
service level
market priority compliance
profit / margin contribution
capacity utilization balance
transport cost
leadtime
strategic priority
```

Possible constraints:

```text
MOM capacity
market demand
leadtime
lane availability
product capability
allocation policy
```

---

## 10. Inbound Backward Planning by MOM Subtree

Current function:

```python
inbound_backward_MOM_to_leaf(...)
```

This identifies MOM nodes:

```python
mom_list = _find_nodes_by_prefix(in_root, "MOM_")
```

and then runs inbound Backward Planning per MOM subtree:

```python
calc_all_psiS2P2childS_preorder(a_mom)
```

Meaning:

```text
MOM.psi4demand[w][S]
    ↓
MOM subtree backward planning
    ↓
upstream / inbound leaf demand allocation
```

This structure avoids propagating identical demand into all MOM branches from `supply_point`.

---

## 11. Processing B: MOM Capacity Leveling

Current legacy / simple function:

```python
inbound_MOM_leveling_vs_capacity(...)
```

This inspects:

```python
mom.psi4demand[w][3]
```

where bucket `3` is `P`.

If P lots exceed capacity, overflow lots are shifted earlier.

Conceptual logic:

```text
MOM.psi4demand[w][P] exceeds capacity
    ↓
keep lots within capacity in week w
    ↓
overflow lots move to w-1, w-2, ...
```

Capacity source priority:

```text
1. env.weekly_capability[product][mom_name][w]
2. env.weekly_capability[mom_name][w]
3. mom.nx_capacity
```

This corresponds to capacity-constrained backward leveling / advance production.

---

## 12. P_month Plan vs P_capacity Month

The term `P_month` can mean different things.

These concepts should be separated:

```text
P_month plan:
    production requirement / planned production quantity

P_capacity_month:
    production capacity limit for MOM / production node

S_month supply:
    supply / shipment / sales quantity depending on context
```

The legacy `sku_P_month_data.csv` may represent production plan or demand/plan input, not necessarily capacity.

MOM capacity should have a clearer capacity input model such as:

```text
mom_P_capacity_month.csv
P_capacity_month.csv
capacity_P_month.csv
```

---

## 13. P_month CSV and weekly_capability Open Issue

Current confirmed behavior:

```text
inbound_MOM_leveling_vs_capacity(...)
    can consume env.weekly_capability
```

Open issue:

```text
It is not yet confirmed that current WOM loads P_month capacity data into env.weekly_capability.
```

Required investigation:

```bat
git grep -n "P_month"
git grep -n "weekly_capability"
git grep -n "capacity"
git grep -n "capability"
git grep -n "level_mom_demand_with_capacity"
git grep -n "inbound_MOM_leveling_vs_capacity"
```

Questions:

```text
1. Which file loads P_month_data.csv?
2. Does P_month_data.csv represent plan or capacity?
3. Is there a dedicated capacity CSV?
4. Where is env.weekly_capability populated?
5. Is monthly capacity converted to weekly capacity?
6. Is 4-4-5 or ISO week used?
```

---

## 14. Demand-to-Supply Bridge Candidates

Current engine already has multiple bridge-like functions.

### 14.1 `bridge_inbound_demand_to_supply(root)`

This reads:

```text
node.psi4demand[w][S]
```

and sets:

```text
node.psi4supply[w] = [demand_s, [], [], []]
```

Meaning:

```text
demand S
    ↓
supply S seed
```

### 14.2 `copy_demand_to_supply_rec(node)`

Inside `inbound_backward_MOM_to_leaf(...)`, demand is cloned to supply for each MOM subtree.

Conceptual behavior:

```text
node.psi4supply = clone(node.psi4demand)
```

### 14.3 PUSH / PULL helpers

Existing functions include:

```text
copy_S_demand2supply(node)
copy_P_demand2supply(node)
PULL_process(node)
PUSH_process(node)
push_pull_all_psi2i_decouple4supply5(...)
```

These also perform demand-to-supply or supply-side actions.

### 14.4 Design implication

A new bridge should not be added until existing bridge candidates are mapped and a canonical bridge policy is selected.

---

## 15. With Capacity Forward PUSH Placement

Future **With Capacity Forward PUSH Planning** should be placed after the demand-to-supply bridge.

Conceptual position:

```text
Backward Planning:
    demand allocation
    MOM allocation
    MOM capacity leveling
        ↓
Demand-to-Supply Bridge:
    psi4demand → psi4supply
        ↓
Forward Planning:
    with Capacity Forward PUSH Planning
```

Meaning:

```text
psi4demand:
    where and when demand lots should be planned

psi4supply:
    how planned lots actually move under execution / capacity constraints
```

With Capacity Forward PUSH should not replace Backward Planning.

It should validate and simulate supply execution under capacity constraints.

---

## 16. Annual Capacity and ROI Interpretation

MOM capacity has a management-level meaning.

It is not only a weekly algorithmic constraint.

```text
annual demand
    ↓
annual production requirement
    ↓
weekly average production requirement
    ↓
peak weekly capacity requirement
    ↓
MOM capacity shortage / surplus
```

If weekly or seasonal demand repeatedly exceeds MOM capacity:

```text
capacity shortage
    ↓
advance production
    ↓
higher inventory
    ↓
storage / working capital cost
    ↓
potential service loss
    ↓
equipment investment question
```

WOM should eventually support:

```text
capacity increase scenario
investment cost
ROI proxy
capacity utilization
profit / cash impact
long-term sustainability
```

This belongs to Management Cockpit / E2E Evaluation, not to low-level PSI bucket operations alone.

---

## 17. Current Confirmed Implementation Map

Confirmed or strongly indicated current implementation:

```text
Run Full Plan:
    run_full_plan()
        ↓
    _run_planning_sequence(...)

Outbound Backward Planning:
    outbound_backward_leaf_to_MOM(...)

Outbound → Inbound connection:
    connect_outbound2inbound(...)

MOM Allocation:
    allocate_markets_to_moms(...)

Inbound Backward Planning:
    inbound_backward_MOM_to_leaf(...)
    calc_all_psiS2P2childS_preorder(...)

MOM Capacity Leveling:
    inbound_MOM_leveling_vs_capacity(...)

Demand-to-Supply bridge candidates:
    bridge_inbound_demand_to_supply(...)
    copy_demand_to_supply_rec(...)
    copy_S_demand2supply(...)
    copy_P_demand2supply(...)

Forward Planning:
    PUSH_process(...)
    PULL_process(...)
    push_pull_all_psi2i_decouple4supply5(...)
    inbound_forward_leaf_to_MOM(...)
```

---

## 18. Current Open Questions

The following must be clarified before designing the next bridge or capacity feature.

```text
1. What is the exact current _run_planning_sequence step order?
2. Is level_mom_demand_with_capacity implemented?
3. Is level_mom_demand_with_capacity called from Run Full Plan?
4. Is inbound_MOM_leveling_vs_capacity still active anywhere?
5. Where is env.weekly_capability populated?
6. Does P_month_data.csv mean production plan or production capacity?
7. Is there a dedicated MOM capacity CSV?
8. Which bridge function should become canonical?
9. Where should With Capacity Forward PUSH be inserted?
10. How should capacity investment / ROI scenario connect to KPI evaluation?
```

---

## 19. Recommended Next Investigation

### 19.1 Search commands

Run:

```bat
git grep -n "def _run_planning_sequence"
git grep -n "outbound_backward_leaf_to_MOM"
git grep -n "connect_outbound2inbound"
git grep -n "allocate_markets_to_moms"
git grep -n "level_mom_demand_with_capacity"
git grep -n "inbound_MOM_leveling_vs_capacity"
git grep -n "weekly_capability"
git grep -n "P_month"
git grep -n "bridge_inbound_demand_to_supply"
git grep -n "copy_demand_to_supply"
git grep -n "push_pull"
```

### 19.2 Mapping output to produce

Create an updated implementation map showing:

```text
function
file
called by
input
output
PSI layer touched
capacity source
status
```

---

## 20. Recommended Design Sequence

Recommended next sequence:

```text
1. Complete current implementation mapping.
2. Identify canonical demand-to-supply bridge.
3. Confirm weekly_capability loading path.
4. Design WOM capacity input granularity adapter.
5. Design canonical demand-to-supply bridge.
6. Design with Capacity Forward PUSH placement.
7. Design annual capacity / ROI evaluation.
```

---

## 21. Summary

Before adding a new demand-to-supply bridge or extending With Capacity Forward PUSH, WOM should first map its existing engine flow.

Key understanding:

```text
Outbound Backward Planning already exists.
MOM allocation already exists as a policy-based function.
MOM capacity leveling already exists in a legacy/simple form.
Demand-to-supply bridge candidates already exist.
Forward PUSH/PULL functions already exist.
```

Therefore, the next step is not to invent a new bridge from scratch.

The next step is to:

```text
map the current engine,
identify canonical functions,
separate plan vs capacity inputs,
and then insert With Capacity Forward PUSH at the correct location.
```

This mapping protects existing WOM implementation assets and prevents duplicate planning logic.
