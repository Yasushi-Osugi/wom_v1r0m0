# Plan with Capacity Context and Planning Story Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/plan_with_capacity_context_and_planning_story.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the upper-level planning story for **Plan with Capacity** in WOM.

The immediate trigger for this memo is the current Explicit KPI View diagnostic:

```text
explicit_pipeline_backward_weekly_capability
```

is missing.

However, this memo intentionally starts one level above that implementation detail.

The purpose is to clarify:

```text
1. What Plan with Capacity means in WOM
2. How Backward Plan with Capacity and Forward Plan with Capacity differ
3. How bottleneck capacity should be represented
4. How lot dwell / stagnation should be interpreted
5. How capacity planning connects to PSI monetary KPI evaluation
6. How explicit_pipeline_backward_weekly_capability should be positioned as an implementation context
```

This memo does not implement the capability context.

It defines the planning story that should guide the later implementation.

---

## 2. Key Clarification: Lot Dwell Time and Lot Value

A key design point is:

```text
Lot dwell is not merely an inventory increase.
Lot dwell is also a time-state attribute of the lot itself.
```

In WOM, a lot is the minimum economic object flowing through the supply chain.

Therefore, when a lot remains at a node or on a lane for additional weeks, the lot itself gains additional time attributes:

```text
lot age
dwell weeks at current node
total elapsed weeks since origin
remaining shelf life
quality state
commercial value state
```

For ordinary durable goods, dwell may mainly create:

```text
inventory holding cost
cash conversion delay
service delay
backlog
opportunity loss
```

For time-sensitive products, such as pharmacy cold chain products, food, vaccines, or other shelf-life-sensitive goods, dwell can change the lot's economic value itself.

Examples:

```text
quality deterioration
remaining shelf-life reduction
obsolescence risk
temperature-control cost
disposal loss
write-off cost
service penalty
```

Thus, the meaning of dwell is:

```text
The lot's position in time changes.
The lot's economic value may also change.
```

This is the basis for later waste-loss and quality-decay models.

---

## 3. Scope Separation

Plan with Capacity and PSI monetary evaluation must be separated.

They are related, but they are not the same layer.

```text
Plan with Capacity:
    quantity flow
    capacity constraint
    lot movement
    timing
    dwell
    bottleneck
    execution feasibility

PSI Monetary Evaluation:
    revenue
    cost
    margin
    profit
    penalty
    waste loss
    tariff impact
    business KPI
```

The planning engine should first determine:

```text
what moves
where it moves
when it moves
where it is delayed
where it accumulates
```

Then the monetary evaluation layer should calculate:

```text
what business impact those movements and delays create
```

Recommended separation:

```text
Planning Engine:
    lot movement / PSI / capacity / dwell

Evaluation Engine:
    revenue / cost / profit / penalty / disposal loss / KPI
```

---

## 4. Backward Plan with Capacity

Backward planning starts from demand.

Its purpose is to determine the required upstream supply position and timing needed to satisfy downstream demand.

In WOM terms:

```text
Final demand
    ↓
required shipment / allocation position
    ↓
required production / purchase timing
    ↓
required upstream material supply timing
```

In the idealized outbound tree:

```text
capacity is treated as infinite or sufficiently unconstrained
```

This allows the model to define the ideal demand allocation position without immediately being blocked by execution constraints.

In the inbound tree, capacity constraints create:

```text
pre-build requirement
demand allocation shift
production timing shift
material requirement shift
upstream lot position shift
```

A key planning story is:

```text
Inbound production may need to be pulled forward
because the downstream MOM node output / shipment speed is constrained.
```

---

## 5. MOM Node as Bottleneck Proxy

A practical MVP interpretation is:

```text
Inbound bottleneck process constraints can initially be represented as
MOM node finished-goods output / shipment capability.
```

In other words, even if the true bottleneck is an internal inbound process, the MVP can model it through the effective shipment or output speed of the MOM node.

This means that the first version of capacity context can be:

```text
MOM node
product
week
available finished-goods output capability
```

This avoids prematurely modeling every process, resource, shift, and machine.

Recommended MVP:

```text
weekly capability by MOM node / product / week
```

Future expansion:

```text
process-level capability
resource-level capability
shift calendar
line capacity
supplier capacity
cold-chain storage capacity
```

---

## 6. Forward Plan with Capacity

Forward planning starts from available supply and execution constraints.

Its purpose is to simulate what actually happens under capacity limits.

In WOM terms:

```text
available supply / planned input
    ↓
capacity-constrained execution
    ↓
actual movement
    ↓
bottleneck
    ↓
delay / dwell / backlog / inventory accumulation
```

Forward Plan with Capacity functions as:

```text
a supply chain execution simulator
```

If capacity is gradually reduced from infinite to constrained, the model should reveal:

```text
where lots accumulate
which node becomes the bottleneck
how much output is delayed
how downstream shipment is affected
how long it takes for accumulated inventory to clear
```

The forward planning story is therefore:

```text
Capacity constraints reveal physical execution feasibility.
```

---

## 7. Bottleneck and Upstream Throttling Story

A key WOM planning story is:

```text
If a downstream MOM node is capacity-constrained,
then upstream inbound supply should be throttled in advance.
```

Without upstream throttling:

```text
upstream materials continue flowing
    ↓
MOM bottleneck cannot process/output fast enough
    ↓
lots accumulate before the bottleneck
    ↓
inventory, dwell, and cost increase
```

With upstream throttling:

```text
MOM output capability is recognized
    ↓
inbound material release is reduced or shifted
    ↓
unnecessary upstream production is avoided
    ↓
excess dwell and inventory are reduced
```

This is an important design concept for WOM:

```text
Plan with Capacity is not only about detecting bottlenecks.
It is also about preventing avoidable upstream accumulation.
```

---

## 8. Outbound Tree Waiting Story

In the outbound tree, if final customers can wait, delayed supply may still be sold later.

In that case:

```text
demand is not lost immediately
    ↓
shipment is delayed
    ↓
outbound inventory / backlog is gradually cleared
    ↓
time resolves the imbalance
```

This planning story applies to durable goods and products with flexible customer tolerance.

Relevant quantity-side indicators:

```text
backlog
delayed shipment
outbound dwell
service delay weeks
inventory clearing time
```

Relevant monetary-side indicators:

```text
delayed revenue
inventory holding cost
cash conversion delay
service penalty
opportunity cost
```

---

## 9. Perishable / Cold Chain Story

For products that deteriorate over time, waiting is not neutral.

Examples:

```text
pharmacy cold chain
vaccines
temperature-controlled medical products
fresh food
chemical materials
seasonal products
short-life consumer goods
```

In these cases:

```text
dwell time changes the value of the lot itself
```

A lot may require:

```text
maximum dwell weeks
shelf life
quality decay rule
cold storage requirement
disposal rule
write-off cost
```

A simple future rule could be:

```text
if lot.dwell_weeks > max_dwell_weeks:
    disposal_loss = lot_quantity * unit_cost
```

A more advanced future rule could be:

```text
remaining_value = original_value * quality_decay_factor(age_weeks)
```

This connects Forward Plan with Capacity to PSI monetary evaluation.

---

## 10. Lot Time-State Attributes

To support dwell and quality evaluation, lots may need time-state attributes.

Potential attributes:

```text
lot_id
product
current_node
current_week
origin_week
age_weeks
dwell_weeks_at_current_node
total_elapsed_weeks
max_dwell_weeks
remaining_shelf_life_weeks
quality_state
value_state
cold_chain_required
disposal_required
```

Not all attributes are required for MVP.

Recommended MVP:

```text
lot_id
product
current_node
current_week
dwell_weeks_at_current_node
```

Future extensions:

```text
shelf life
quality decay
temperature condition
disposal loss
```

---

## 11. Connection to PSI Monetary Evaluation

Plan with Capacity produces quantity and time facts.

Examples:

```text
lot delayed by 2 weeks
lot stayed at node A for 3 weeks
MOM node capacity short by 20 lots
outbound shipment delayed
inbound production shifted earlier
```

PSI monetary evaluation converts these into business impact.

Examples:

```text
inventory holding cost
capacity shortage penalty
overtime cost
lost sales
delayed revenue
service penalty
disposal loss
quality deterioration loss
```

Therefore, monetary evaluation should consume planning results, not replace planning.

Recommended relationship:

```text
Forward Plan with Capacity
    ↓
event / lot / PSI result
    ↓
Monetary KPI Evaluation
    ↓
Cockpit KPI View
```

---

## 12. Position of explicit_pipeline_backward_weekly_capability

The missing context key:

```text
explicit_pipeline_backward_weekly_capability
```

should be interpreted as the explicit pipeline's weekly capability context for backward planning.

Its MVP meaning should be:

```text
For each constrained MOM node / product / week,
how many lots can be output or shipped.
```

Recommended conceptual structure:

```python
{
    "MOM_NODE_ID": {
        "PRODUCT_NAME": {
            "YYYYWW": capability_lot_count
        }
    }
}
```

Alternative flat format:

```python
[
    {
        "node": "MOM_NODE_ID",
        "product": "PRODUCT_NAME",
        "week": "YYYYWW",
        "capability_lots": 100,
    }
]
```

The engine-facing structure should be decided in a later implementation memo.

This memo only defines the planning meaning.

---

## 13. Master Data Candidates

Plan with Capacity may require master data such as:

```text
node master
product master
node-product-week capability master
route / lane master
lead time master
calendar master
lot size master
process capability master
storage capability master
shelf-life master
```

For the current MVP, the most important candidate is:

```text
weekly capability master by node / product / week
```

This master can later be converted by an adapter into:

```text
explicit_pipeline_backward_weekly_capability
```

---

## 14. Original Master and Latest WOM Master

WOM currently has two master orientations:

```text
1. PySI V0R8 / WOM original master
2. latest WOM master
```

The latest WOM master may be transformed by adapters into the original / canonical master format.

Recommended architecture:

```text
User-facing WOM Master
    ↓
Adapter / Normalizer
    ↓
Canonical Engine Input
    ↓
Planning Engine
```

The planning engine should not directly depend on every user-facing master variation.

The adapter should translate:

```text
latest WOM capability master
```

into:

```text
explicit_pipeline_backward_weekly_capability
```

or other canonical context objects.

---

## 15. Planning Story Examples

### 15.1 Capacity Infinite Baseline

```text
all nodes have sufficient capacity
    ↓
demand allocation positions are ideal
    ↓
no significant dwell
    ↓
no bottleneck accumulation
```

This scenario is useful as a baseline.

### 15.2 MOM Capacity Constrained

```text
MOM node output capability is lower than demand
    ↓
MOM becomes bottleneck
    ↓
inbound lots accumulate before MOM
    ↓
outbound shipment is delayed
```

This scenario reveals the bottleneck.

### 15.3 Upstream Throttling

```text
MOM output speed is known
    ↓
inbound leaf material production is reduced / shifted
    ↓
unnecessary accumulation is reduced
```

This scenario supports better planning.

### 15.4 Customer Can Wait

```text
outbound delay occurs
    ↓
customer demand remains valid
    ↓
delayed lots are shipped later
    ↓
revenue is delayed but not lost
```

### 15.5 Cold Chain

```text
lot dwell exceeds allowed time
    ↓
quality deteriorates
    ↓
disposal loss or value reduction occurs
```

This scenario connects capacity planning to monetary loss evaluation.

---

## 16. KPI Implications

Plan with Capacity supports the following quantity-side KPIs:

```text
capacity usage
capacity shortage
accepted lots
blocked lots
delayed lots
dwell weeks
backlog
bottleneck node
clearing time
```

It also supports monetary evaluation KPIs:

```text
delayed revenue
lost sales
inventory holding cost
capacity shortage cost
overtime cost
service penalty
disposal loss
quality deterioration loss
```

The monetary KPIs should be calculated in a separate PSI monetary evaluation layer.

---

## 17. Design Principles

The following principles should guide implementation.

### 17.1 Separate planning and evaluation

```text
Planning determines what happens.
Evaluation determines what it means financially.
```

### 17.2 Start with MOM capability MVP

```text
Do not model every process first.
Represent bottleneck through MOM node weekly output capability first.
```

### 17.3 Treat dwell as lot time-state

```text
Dwell is not only inventory.
Dwell changes the lot's time-state and may change economic value.
```

### 17.4 Keep adapters explicit

```text
User-facing master formats should be translated to canonical engine contexts.
```

### 17.5 Keep guard behavior

```text
If capability context is missing, the cockpit should not crash.
It should show diagnostic reason.
```

---

## 18. Recommended Next Design

After this planning story memo, the next implementation-oriented memo should be:

```text
docs/design/explicit_pipeline_backward_weekly_capability_context.md
```

That memo should define:

```text
exact context schema
master CSV schema
adapter behavior
env attach timing
test cases
manual GUI validation flow
```

This upper-level memo should serve as the conceptual basis for that implementation memo.

---

## 19. Later Design: PSI Monetary KPI Evaluation

A separate design should cover:

```text
docs/design/psi_monetary_kpi_evaluation_master_context.md
```

That memo should define:

```text
KPI definitions
price master
cost structure master
tariff scenario master
cost behavior
Lot/MEO monetary evaluation
Price-Cost-Profit propagation
```

This should remain separate from Plan with Capacity.

---

## 20. Summary

Plan with Capacity should be treated as a planning and execution simulation layer.

Backward Plan with Capacity:

```text
defines required positions and timing from demand
```

Forward Plan with Capacity:

```text
simulates actual movement under capacity constraints
```

MOM node weekly output capability is the recommended MVP bottleneck proxy.

Lot dwell should be treated as a time-state of the lot itself.

This allows later monetary evaluation of:

```text
inventory cost
delay cost
service penalty
quality deterioration
disposal loss
```

The current missing key:

```text
explicit_pipeline_backward_weekly_capability
```

is the first concrete implementation context needed to move from diagnostic unavailable state to capacity-aware planning output.

This memo defines the story.

The next memo should define the concrete context.
