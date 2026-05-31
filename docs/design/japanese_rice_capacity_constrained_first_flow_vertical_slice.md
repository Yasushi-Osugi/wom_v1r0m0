# Japanese Rice Capacity-Constrained First Flow Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-05-31  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice.md`

**Strategic role:** First lot-level capacity gate after actual ProductPlanNode instantiation  
**Primary case:** Japanese Rice Case  
**Initial execution target:** split MARKET_TOKYO demand lots into accepted / blocked lots at the first outbound capacity gate, DC_KANTO

---

## 1. Purpose

This memo defines the next Japanese Rice Case vertical slice after the plan node tree instantiation milestone.

The current Japanese Rice Case has reached the following state:

```text
Capacity
Demand
Network
First PSI smoke runner
Actual product-specific ProductPlanNode tree
DemandAnchoredLot attachment to actual MARKET_TOKYO plan_node
```

The current plan node tree instantiation slice proves:

```python
MARKET_TOKYO.psi4demand["2027-W40"][0] contains 80 lot IDs
MARKET_TOKYO.psi4demand["2027-W41"][0] contains 95 lot IDs
MARKET_TOKYO.psi4demand["2027-W42"][0] contains 110 lot IDs
```

The next required step is to pass these lots through the first capacity gate.

For the first minimal flow, the selected gate is:

```text
DC_KANTO
```

because the first PSI smoke diagnostic already showed that DC_KANTO is the first visible restriction:

```text
DC_KANTO S capacity:
  90 lots/week

MARKET_TOKYO demand:
  2027-W40 = 80
  2027-W41 = 95
  2027-W42 = 110

Expected same-week shortage:
  0 / 5 / 20
```

This slice should convert that simple balance signal into actual lot-level accepted / blocked results.

---

## 2. Current Completed Foundations

### 2.1 Capacity master

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Relevant capacity rows:

```text
DC_KANTO S capacity = 90 lots/week
RICE_MILL_A P capacity = 100 lots/week
FARM_REGION_A P capacity = 120 lots/week
```

Weeks:

```text
2027-W40
2027-W41
2027-W42
```

### 2.2 Demand master

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

Relevant demand:

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

### 2.3 Network master

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

Relevant outbound path:

```text
demand_side_root
  -> supply_point
    -> DC_KANTO
      -> MARKET_TOKYO
        -> Global_Sales_Office
```

Relevant node roles:

```text
DC_KANTO:
  node_character = DAD
  partner_key = RICE_CORE

MARKET_TOKYO:
  node_character = MARKET_LEAF
```

### 2.4 Actual plan_node tree

Completed by the previous vertical slice:

```text
ProductPlanNode trees
    ↓
actual outbound MARKET_TOKYO ProductPlanNode
    ↓
MARKET_TOKYO.psi4demand[week][0]
```

---

## 3. Problem Statement

The previous slice proves that demand lots sit on actual product-specific plan_nodes.

However, these lots have not yet passed through any actual capacity constraint.

Current state:

```text
MARKET_TOKYO demand lots exist by week.
```

Needed next state:

```text
At DC_KANTO capacity gate:
  accepted lots
  blocked lots
  capacity usage
  shortage
  deterministic lot-level result
```

This is the first transition from:

```text
balance diagnostic
```

to:

```text
lot-level capacity flow
```

---

## 4. First Flow Choice: DC_KANTO -> MARKET_TOKYO

The first capacity-constrained flow should focus on the outbound DAD-to-market segment:

```text
DC_KANTO -> MARKET_TOKYO
```

Reason:

```text
1. MARKET_TOKYO already has actual demand lot IDs in psi4demand[week][0].
2. DC_KANTO has weekly S capacity rows.
3. The simple smoke balance already shows visible shortages.
4. The expected accepted / blocked counts are deterministic.
5. This is smaller and safer than trying to implement full inbound/outbound PSI propagation.
```

This is the first capacity gate, not the whole network.

---

## 5. Scope of This Vertical Slice

### 5.1 In scope

```text
reuse actual ProductPlanNode tree instantiation
reuse demand lot generation and attachment
load capacity rows
select DC_KANTO S capacity by week
read MARKET_TOKYO.psi4demand[week][0]
split lot IDs into accepted / blocked by week
attach or return accepted / blocked lot IDs
compute capacity usage
compute shortage
return deterministic flow diagnostic
add focused tests
```

### 5.2 Out of scope

```text
full canonical PSI planning
leadtime-shifted propagation
inventory carry-over
CO / backlog calculation
multi-node propagation
inbound MOM capacity clipping
supply generation
cost / profit simulation
GUI wiring
NetworkX retirement
optimization
```

This is a one-gate lot-level flow.

It should stay deliberately small.

---

## 6. Proposed Implementation Files

Recommended implementation file:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Recommended focused test file:

```text
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

Optional package export:

```text
pysi/plan/__init__.py
```

Only update package export if project style supports it and the change is low risk.

Do not modify GUI files.

Do not modify existing planner engine files.

---

## 7. Existing Functions to Reuse

Reuse previous work.

### 7.1 Plan node tree instantiation

```python
instantiate_product_plan_node_trees(...)
attach_demand_lots_to_actual_plan_node_psi4demand(...)
```

from:

```text
pysi/plan/plan_node_tree_instantiation.py
```

### 7.2 Demand

```python
load_weekly_demand_master_csv(...)
generate_demand_anchored_lots(...)
```

from:

```text
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
```

### 7.3 Network

```python
load_network_master_package(...)
```

from:

```text
pysi/network/network_master_loader.py
```

### 7.4 Capacity

```python
load_capacity_weekly_rows_to_env(...)
```

from:

```text
pysi/capacity/capacity_weekly_rows_source.py
```

If easier, the capacity rows may be loaded directly via existing canonical capacity loader path, but do not duplicate CSV parsing.

---

## 8. Core Flow Concept

Input by week:

```text
demand_lot_ids = MARKET_TOKYO.psi4demand[week][0]
capacity_qty = DC_KANTO S capacity for that week
```

Algorithm:

```python
accepted_lot_ids = demand_lot_ids[:capacity_qty]
blocked_lot_ids = demand_lot_ids[capacity_qty:]
```

Summary:

```python
requested = len(demand_lot_ids)
accepted = len(accepted_lot_ids)
blocked = len(blocked_lot_ids)
capacity = capacity_qty
capacity_usage = accepted
shortage = blocked
```

The split should be deterministic.

Default ordering:

```text
preserve lot ID order produced by demand lot generation
```

This gives stable tests.

---

## 9. Expected Weekly Results

### 9.1 2027-W40

Demand:

```text
80 lots
```

Capacity:

```text
90 lots
```

Expected:

```text
requested = 80
capacity = 90
accepted = 80
blocked = 0
capacity_usage = 80
unused_capacity = 10
shortage = 0
```

### 9.2 2027-W41

Demand:

```text
95 lots
```

Capacity:

```text
90 lots
```

Expected:

```text
requested = 95
capacity = 90
accepted = 90
blocked = 5
capacity_usage = 90
unused_capacity = 0
shortage = 5
```

### 9.3 2027-W42

Demand:

```text
110 lots
```

Capacity:

```text
90 lots
```

Expected:

```text
requested = 110
capacity = 90
accepted = 90
blocked = 20
capacity_usage = 90
unused_capacity = 0
shortage = 20
```

Total:

```text
requested = 285
accepted = 260
blocked = 25
```

This total result is the first lot-level capacity gate result.

---

## 10. Result Object / Diagnostic Shape

Recommended function:

```python
run_japanese_rice_capacity_constrained_first_flow(
    scenario_root: str | Path,
) -> dict
```

Recommended returned diagnostic:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "run_mode": "capacity_constrained_first_flow",
    "full_psi_plan": False,
    "available": True,
    "flow": {
        "capacity_node": "DC_KANTO",
        "demand_node": "MARKET_TOKYO",
        "capacity_type": "S",
        "unit": "lot",
    },
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],
    "weekly": {
        "2027-W40": {
            "requested": 80,
            "capacity": 90,
            "accepted": 80,
            "blocked": 0,
            "capacity_usage": 80,
            "unused_capacity": 10,
            "shortage": 0,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [],
        },
        "2027-W41": {
            "requested": 95,
            "capacity": 90,
            "accepted": 90,
            "blocked": 5,
            "capacity_usage": 90,
            "unused_capacity": 0,
            "shortage": 5,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [...],
        },
        "2027-W42": {
            "requested": 110,
            "capacity": 90,
            "accepted": 90,
            "blocked": 20,
            "capacity_usage": 90,
            "unused_capacity": 0,
            "shortage": 20,
            "accepted_lot_ids": [...],
            "blocked_lot_ids": [...],
        },
    },
    "totals": {
        "requested": 285,
        "capacity": 270,
        "accepted": 260,
        "blocked": 25,
        "shortage": 25,
        "unused_capacity": 10,
    },
    "messages": [
        "Japanese Rice capacity-constrained first flow: actual plan_node tree loaded.",
        "Japanese Rice capacity-constrained first flow: demand lots read from MARKET_TOKYO.psi4demand[week][0].",
        "Japanese Rice capacity-constrained first flow: DC_KANTO S capacity applied.",
        "Japanese Rice capacity-constrained first flow: accepted / blocked lots computed.",
    ],
}
```

The exact field names may vary, but focused tests must verify the core facts.

---

## 11. Optional PlanNode Attachment

The first implementation may simply return accepted / blocked lists in the diagnostic.

However, it may also attach results to the relevant plan_nodes if implemented cleanly.

Possible fields:

```python
dc_kanto.capacity_flow_results[week] = {
    "accepted_lot_ids": [...],
    "blocked_lot_ids": [...],
}
```

or:

```python
market_tokyo.capacity_gate_result[week] = {...}
```

For this first slice, this is optional.

Acceptance should focus on the returned diagnostic and deterministic lot splits.

---

## 12. Capacity Row Selection Rule

The capacity gate must select:

```text
node_name = DC_KANTO
capacity_type = S
product_name = JAPANESE_RICE_STANDARD
week = target week
```

The expected capacity quantity is:

```text
90
```

for all three weeks.

If the helper sees multiple matching rows, it should either:

```text
sum them
```

or:

```text
raise deterministic error
```

For this slice, since the master has one row per node/product/type/week, the happy path is enough.

Recommended behavior for future-proofing:

```text
sum matching rows
```

but tests should only depend on current single-row values.

---

## 13. Demand Lot Source Rule

The demand lots must come from the actual plan_node:

```python
market_tokyo.psi4demand[week][0]
```

Not from a separately recomputed demand count.

This is important.

The flow should prove that the previous slice is actually used.

Correct:

```text
Read lot IDs from actual MARKET_TOKYO ProductPlanNode.
```

Avoid:

```text
Read demand_qty directly from demand_master.csv and skip the plan_node.
```

The design purpose is to move lot IDs through actual plan_node structures.

---

## 14. Deterministic Lot Ordering

The split must preserve deterministic lot ordering.

Expected:

```text
accepted_lot_ids = first N lot IDs
blocked_lot_ids = remaining lot IDs
```

where N is capacity.

For example:

```text
W41:
  95 requested
  90 accepted
  5 blocked
```

The blocked lots should be the last 5 in the generated week-specific lot order.

Tests can verify counts and uniqueness.

They do not need to hard-code every lot ID unless existing lot ID generation already has stable first/last IDs.

---

## 15. Test Strategy

Recommended focused test:

```text
tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py
```

### 15.1 Runner returns expected mode

Assert:

```text
run_mode = capacity_constrained_first_flow
full_psi_plan = False
available = True
```

### 15.2 It uses actual plan_node demand lots

Assert result indicates or proves:

```text
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

If a source field is returned:

```text
result["flow"]["demand_lot_source"] == "MARKET_TOKYO.psi4demand[week][0]"
```

### 15.3 Weekly W40 result

Assert:

```text
requested = 80
capacity = 90
accepted = 80
blocked = 0
unused_capacity = 10
shortage = 0
```

### 15.4 Weekly W41 result

Assert:

```text
requested = 95
capacity = 90
accepted = 90
blocked = 5
unused_capacity = 0
shortage = 5
```

### 15.5 Weekly W42 result

Assert:

```text
requested = 110
capacity = 90
accepted = 90
blocked = 20
unused_capacity = 0
shortage = 20
```

### 15.6 Total result

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
shortage = 25
unused_capacity = 10
```

### 15.7 Lot ID consistency

Assert:

```text
accepted_lot_ids and blocked_lot_ids are disjoint
accepted + blocked count equals requested
all blocked lots come from original MARKET_TOKYO S-slot lot list
```

For each week:

```text
set(accepted_lot_ids) union set(blocked_lot_ids)
  == set(MARKET_TOKYO.psi4demand[week][0])
```

### 15.8 Existing tests still pass

Run:

```text
tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
tests/test_japanese_rice_network_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

---

## 16. Suggested Implementation Functions

Recommended file:

```text
pysi/plan/capacity_constrained_first_flow.py
```

Recommended functions:

```python
split_lots_by_capacity(
    lot_ids: list[str],
    capacity_qty: int,
) -> dict
```

```python
compute_capacity_gate_flow_by_week(
    *,
    demand_lots_by_week: dict[str, list[str]],
    capacity_by_week: dict[str, int],
    capacity_node: str,
    demand_node: str,
    capacity_type: str = "S",
) -> dict
```

```python
run_japanese_rice_capacity_constrained_first_flow(
    scenario_root: str | Path,
) -> dict
```

Optional helper:

```python
load_japanese_rice_actual_plan_node_tree_with_demand(
    scenario_root: str | Path,
) -> dict
```

if not already provided by the plan_node instantiation helper.

Keep these pure.

Do not mutate global state.

---

## 17. Acceptance Criteria for Future Codex Request

The implementation is complete when:

```text
capacity-constrained first flow helper is added
Japanese Rice first flow runner is added
focused test is added
actual ProductPlanNode tree is instantiated
MARKET_TOKYO.psi4demand[week][0] is used as demand lot source
DC_KANTO S capacity rows are used as capacity gate
W40 accepted/blocked = 80/0
W41 accepted/blocked = 90/5
W42 accepted/blocked = 90/20
total accepted/blocked = 260/25
lot ID sets are consistent and deterministic
run result marks full_psi_plan = False
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
existing Japanese Rice tests still pass
```

---

## 18. Non-Goals

This slice does not implement:

```text
multi-stage propagation
RICE_MILL_A capacity clipping
FARM_REGION_A capacity clipping
leadtime shifting
inventory carry-over
backlog / CO
supply plan generation
cost / profit
GUI display
optimization
NetworkX changes
```

Those are future steps.

This slice is only:

```text
one capacity gate
lot-level accepted / blocked split
DC_KANTO -> MARKET_TOKYO
```

---

## 19. Relationship to Future PSI Planning

This slice is not full PSI planning, but it is a key building block.

It provides:

```text
lot-level capacity clipping
accepted / blocked lots
weekly capacity usage
weekly shortage
```

These are needed for future:

```text
capacity-constrained PSI propagation
MOM balance line visualization
blocked lot diagnostics
management cockpit issue detection
```

After this slice, the next natural steps are:

```text
1. Extend capacity gate to RICE_MILL_A.
2. Add leadtime-aware lot movement.
3. Propagate accepted lots through outbound tree.
4. Add blocked lot diagnostics.
5. Add MOM/DAD weekly balance line.
```

---

## 20. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_capacity_constrained_first_flow_vertical_slice_request.md
```

Scope:

```text
add capacity_constrained_first_flow helper
add Japanese Rice first flow runner
use actual ProductPlanNode tree
read demand lots from MARKET_TOKYO.psi4demand[week][0]
apply DC_KANTO S capacity
split accepted / blocked lots
add focused tests
do not modify GUI
do not modify existing planner behavior
do not remove NetworkX
do not claim full PSI planning
```

---

## 21. Development Meaning

This slice is the first true capacity gate.

Previous milestone:

```text
Demand lots are loaded onto the actual WOM planning-layer vehicle.
```

This milestone:

```text
The vehicle reaches the first capacity gate.
```

At DC_KANTO:

```text
W40 passes.
W41 partially blocks.
W42 blocks more.
```

This is the first moment where the Japanese Rice Case moves from:

```text
data loading and structural correctness
```

to:

```text
lot-level operational constraint behavior
```

In simple terms:

```text
The rice bags are now on the WOM vehicle.
The next question is how many can pass the DC_KANTO gate each week.
