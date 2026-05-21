# MOM Allocation to Capacity-Aware Backward Planning Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-21  
**Status:** Design memo  
**Target path:** `docs/design/mom_allocation_to_capacity_aware_backward_planning.md`

**Related design documents:**

- `docs/design/wom_demand_layer_bridge_and_supply_execution_bridge.md`
- `docs/design/wom_outbound_to_inbound_demand_bridge.md`
- `docs/design/outbound_to_inbound_bridge_to_mom_allocation.md`
- `docs/design/outbound_to_inbound_bridge_to_mom_allocation_completion.md`
- `docs/design/current_wom_backward_planning_and_capacity_flow_mapping.md`
- `docs/design/wom_capacity_input_granularity_adapter.md`
- `docs/design/capacity_provider_monthly_csv_adapter_v0r2.md`
- `docs/design/rice_case_backward_planning_after_seed.md`
- `docs/design/rice_case_backward_planning_after_seed_completion.md`

---

## 1. Purpose

This memo defines the design boundary from **MOM Production Allocation** to **Capacity-Aware Inbound Backward Planning**.

The previous milestones completed the following demand-layer path:

```text
outbound supply_point.psi4demand[w][P]
    ↓
Bridge A: Outbound-to-Inbound Demand Bridge
    ↓
inbound supply_point.psi4demand[w][S]
    ↓
MOM Production Allocation
    ↓
MOMxxx.psi4demand[w][S]
```

The next controlled planning step is:

```text
MOMxxx.psi4demand[w][S]
    ↓
Capacity-Aware Inbound Backward Planning
    ↓
MOMxxx.psi4demand[w][P]
    ↓
capacity feasibility / advance production / overflow handling
```

The purpose is to define how WOM should handle MOM-assigned demand lots under MOM capacity constraints, while preserving V0R8 PSI bucket semantics.

---

## 2. Core Principle

The key principle is:

```text
MOM allocation decides which MOM should serve which market demand.

Capacity-aware backward planning decides when that MOM can feasibly satisfy the assigned demand.
```

These are different responsibilities.

```text
MOM Allocation:
    assignment problem

Capacity-Aware Backward Planning:
    timing and feasibility problem
```

This separation keeps WOM planning logic modular.

---

## 3. Position in the Overall Planning Flow

The recommended planning sequence is:

```text
[1] Plan Input Seed
    demand / supply / case_weekly input
        ↓
    PlanNode.psi4demand seed

[2] Outbound Backward Planning
    leaf demand
        ↓
    DAD
        ↓
    outbound supply_point

[3] Outbound-to-Inbound Demand Bridge
    outbound supply_point.psi4demand[w][P]
        ↓
    inbound supply_point.psi4demand[w][S]

[4] MOM Production Allocation
    inbound demand lots
        ↓
    MOMxxx.psi4demand[w][S]

[5] Capacity-Aware Inbound Backward Planning
    MOMxxx.psi4demand[w][S]
        ↓
    MOM subtree backward planning
        ↓
    MOMxxx.psi4demand[w][P]
        ↓
    capacity feasibility / week shifting

[6] Demand-to-Supply Execution Bridge
    finalized psi4demand
        ↓
    psi4supply

[7] Forward Supply Execution
    psi4supply
        ↓
    PUSH / PULL / With Capacity Forward PUSH
```

This memo focuses on step `[5]`.

---

## 4. Effective MOM Capacity Model

### 4.1 Motivation

The inbound tree can contain many possible bottleneck sources:

```text
supplier shortage
material shortage
component factory trouble
process capacity shortage
transport route closure
port / strait disruption
customs delay
yield loss
labor availability
```

Modeling all of these explicitly at every node and edge is possible, but it is not required for the first practical WOM MVP.

### 4.2 MVP assumption

For the MVP, inbound-side bottlenecks are represented as **effective MOM capacity**.

```text
inbound internal bottleneck
    ↓
effective MOM capacity
    ↓
MOM capacity-aware backward planning
```

This means:

```text
MOM nominal capacity
    - upstream bottleneck impact
    - material shortage impact
    - logistics disruption impact
    - process availability impact
    = effective MOM capacity
```

WOM consumes this as:

```python
env.weekly_capability[product][MOM_node][week]
```

or an equivalent `WeeklyCapacityRow`-derived runtime structure.

### 4.3 Practical meaning

If a component bottleneck reduces the actual feasible throughput of `MOM_ASIA` from 100 lots/week to 60 lots/week, WOM should plan using:

```text
effective MOM capacity = 60 lots/week
```

rather than the nominal installed capacity.

This makes the whole inbound operation synchronized to the current bottleneck.

---

## 5. Bottleneck Modeling Levels

WOM should support multiple levels of bottleneck modeling.

### 5.1 Level 1: Effective MOM Capacity Model

This is the recommended MVP.

```text
inbound internal bottleneck
    ↓
effective MOM capacity
```

Example:

```text
MOM_ASIA nominal capacity = 100
upstream bottleneck impact = -40
effective MOM capacity = 60
```

Runtime input:

```python
weekly_capability[product][MOM_ASIA][week] = 60
```

### 5.2 Level 2: Explicit Bottleneck Node / Lane Model

Future explicit modeling may represent bottleneck nodes and lanes directly.

Examples:

```text
supplier node capacity
material process capacity
subassembly factory capacity
transport lane capacity
port capacity
customs capacity
```

This allows WOM to identify:

```text
where the bottleneck is
which lots are blocked
how capacity propagates through the tree
```

### 5.3 Level 3: OR Optimization Model

Future optimization may model allocation and capacity usage as an OR problem.

Possible objectives:

```text
maximize service level
maximize profit
minimize total cost
balance MOM utilization
prioritize strategic markets
minimize delay
```

Possible constraints:

```text
MOM capacity
supplier capacity
lane capacity
leadtime
material availability
market demand
inventory availability
```

This is not part of the MVP.

---

## 6. Current Implementation Candidates

### 6.1 MOM allocation

Current function candidate:

```python
allocate_markets_to_moms(...)
```

Current role:

```text
policy-based MOM assignment
```

Current behavior:

```text
inbound supply_point demand lots
    ↓
market key extraction
    ↓
policy dict
    ↓
MOMxxx.psi4demand[w][S]
```

### 6.2 Capacity-aware backward planning

Relevant current functions:

```text
level_mom_demand_with_capacity(...)
inbound_MOM_leveling_vs_capacity(...)
inbound_backward_MOM_to_leaf(...)
```

Current known behavior:

```text
level_mom_demand_with_capacity exists and is called from Run Full Plan.

inbound_MOM_leveling_vs_capacity exists as a legacy/simple capacity leveling function.
```

### 6.3 Capacity input

Current capacity provider path:

```text
sku_P_month_data.csv
    ↓
capacity_provider_monthly_csv
    ↓
env.weekly_capability
```

The provider has been refactored to use the capacity input granularity adapter while preserving default `four_week_month` behavior.

---

## 7. Capacity-Aware Backward Planning Concept

### 7.1 Input

Input to this stage:

```text
MOMxxx.psi4demand[w][S]
effective MOM weekly capacity
routing / leadtime assumptions
allocation policy result
```

### 7.2 Process

Conceptual process:

```text
1. Read MOM-assigned demand lots from MOM.psi4demand[w][S].
2. Convert / propagate demand to MOM.psi4demand[w][P] through existing S→P logic.
3. Compare MOM.psi4demand[w][P] lot count with effective MOM capacity.
4. If within capacity:
       keep plan as-is.
5. If over capacity:
       move overflow lots to earlier feasible weeks.
6. Record capacity usage / overflow / shifted lots.
```

### 7.3 Output

Output:

```text
MOM.psi4demand[w][P] feasible under weekly capability
shifted lots if capacity over
overflow / backlog if no earlier capacity exists
capacity result summary
```

---

## 8. Effective Capacity Input

### 8.1 Capacity input source

Effective MOM capacity may come from:

```text
monthly capacity CSV
weekly capacity CSV
scenario override
external bottleneck model
manual input
simulation result
```

### 8.2 Canonical adapter path

Preferred path:

```text
P_capacity_month / P_capacity_week
    ↓
WeeklyCapacityRow
    ↓
env.weekly_capability
    ↓
level_mom_demand_with_capacity
```

### 8.3 Current runtime path

Current runtime path:

```text
capacity_provider_monthly_csv
    ↓
env.weekly_capability
```

This is now adapter-backed after v0r2 refactor.

---

## 9. Relationship to Forward PUSH with Capacity

Capacity-aware backward planning and Forward PUSH with Capacity are different.

### 9.1 Backward capacity

Backward capacity answers:

```text
Can the assigned demand be planned within MOM capacity?
```

It controls:

```text
production week
advance production
capacity feasibility
```

### 9.2 Forward capacity

Forward capacity answers:

```text
Can the planned supply actually move through the supply network?
```

It controls:

```text
shipment
transport
storage
delivery
execution feasibility
blocked lots
```

### 9.3 Correct placement

```text
MOM allocation
    ↓
capacity-aware backward planning
    ↓
demand-to-supply bridge
    ↓
Forward PUSH with Capacity
```

Forward PUSH with Capacity should not replace backward capacity planning.

---

## 10. Proposed MVP Integration Function

A future implementation may introduce:

```python
def run_mom_allocation_to_capacity_aware_backward_planning_smoke(
    *,
    out_root,
    in_root,
    product_name: str,
    policy: dict,
    weekly_capability: dict,
) -> MomCapacityBackwardPlanningResult:
    ...
```

Conceptual flow:

```text
1. assume Bridge A already populated inbound supply_point.psi4demand[w][S]
2. allocate bridged demand to MOM nodes
3. run capacity-aware MOM backward planning
4. validate PSI bucket invariants
5. summarize assigned / shifted / overflow lots
```

---

## 11. Suggested Result Object

```python
@dataclass
class MomCapacityBackwardPlanningResult:
    product_name: str
    assigned_lot_count: int = 0
    capacity_checked_lot_count: int = 0
    shifted_lot_count: int = 0
    overflow_lot_count: int = 0
    capacity_usage_by_mom_week: dict = field(default_factory=dict)
    shifted_lots: list[dict] = field(default_factory=list)
    overflow_lots: list[str] = field(default_factory=list)
    non_list_bucket_errors: list[dict] = field(default_factory=list)
    message: str = ""
```

---

## 12. Safety Invariants

The following invariants must be preserved.

```text
1. All psi4demand buckets remain lists.
2. All bucket items remain Lot_ID strings.
3. No numeric quantity values are inserted into PSI buckets.
4. Existing source demand lots are not silently lost.
5. Shifted lots remain traceable.
6. Capacity check does not write to psi4supply.
7. Forward Planning is not executed in this stage.
```

---

## 13. MVP Test Strategy

### 13.1 Test setup

Use a small inbound tree:

```text
supply_point
    ├── MOM_ASIA
    └── MOM_EURO
```

Seed bridged demand lots into:

```text
inbound supply_point.psi4demand[w][S]
```

Allocate to MOMs using policy.

Then run capacity-aware backward planning.

### 13.2 Capacity scenario

Example:

```text
MOM_ASIA capacity:
    week 10: 2 lots
    week 9:  2 lots

Demand:
    week 10: 3 lots
```

Expected:

```text
2 lots stay in week 10
1 lot shifts to week 9
```

### 13.3 Required tests

```text
1. MOM allocation produces MOM.psi4demand[w][S].
2. Capacity-aware backward planning runs.
3. MOM.psi4demand[w][P] does not exceed capacity.
4. Overflow lots are shifted earlier when possible.
5. PSI buckets remain Lot_ID lists.
6. No psi4supply mutation occurs.
7. W40 / W41 boundary remains valid.
```

---

## 14. Current Open Questions

Before implementation, confirm:

```text
1. Exact behavior of level_mom_demand_with_capacity(...)
2. Whether it consumes env.weekly_capability
3. Whether it expects MOM.psi4demand[w][S] or [P] as input
4. Whether it performs S→P internally or expects it already done
5. What capacity_result contains
6. Whether old inbound_MOM_leveling_vs_capacity should remain only legacy
```

---

## 15. Recommended Next Step

Before implementation, inspect:

```text
pysi/plan/engines.py::level_mom_demand_with_capacity(...)
```

and confirm:

```text
input buckets
output buckets
capacity source
overflow handling
return value
```

Then write a focused Codex Request for:

```text
Bridge A → MOM allocation → capacity-aware backward planning smoke
```

---

## 16. Future Work

### 16.1 Demand-to-Supply Execution Bridge

After capacity-aware backward planning is validated:

```text
finalized psi4demand
    ↓
psi4supply
```

### 16.2 Forward PUSH with Capacity

After Bridge B:

```text
psi4supply
    ↓
Forward PUSH with Capacity
```

### 16.3 Capacity ROI evaluation

After capacity behavior is stable:

```text
capacity scenario
    ↓
inventory / service / cost / profit
    ↓
ROI / Management Issue
```

---

## 17. Summary

This memo defines the design boundary from MOM allocation to capacity-aware inbound backward planning.

The key MVP assumption is:

```text
Inbound-side bottlenecks are represented as effective MOM capacity.
```

The key planning flow is:

```text
Bridge A
    ↓
MOM allocation
    ↓
capacity-aware backward planning
    ↓
demand-to-supply bridge
    ↓
Forward execution
```

The current step should prove that:

```text
MOM-assigned demand lots can be planned under MOM effective capacity,
without violating V0R8 PSI bucket semantics.
```
