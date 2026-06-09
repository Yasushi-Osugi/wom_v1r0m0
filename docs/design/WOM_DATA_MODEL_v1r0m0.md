# WOM_DATA_MODEL v1r0m0

Canonical Data Model for WOM (Weekly Operation Model) — Version 1.0

**Revision history**
- Kernel v1 (2026-03-13): Event/Flow-centric base model established
- v1r0m0 (2026-06-07): Tree/Table dual-structure redesign (260604 re-definition)

---

## 1. Core Design Principle

> **Flow/Event = source of truth.  
> State = derived view.**

This principle from Kernel v1 is preserved.  
The v1r0m0 revision adds a second structural principle:

> **Tree = for simulation (PSI + PPC).  
> Table = for evaluation (Profit/Cost).**

These two structures serve fundamentally different computational purposes and must not be conflated.

---

## 2. The Two-Structure Model

### 2-A. Tree Model — for network simulation

The Tree model handles anything that requires traversing an E2E supply chain network.  
It answers: *what flows where, when, in what quantity and at what price.*

Two tree directions:

```
Inbound Tree  :  Supply Point → DC → Market (push side)
Outbound Tree :  Market → DC → Supply Point (demand pull side)
```

Tree-dependent simulations:

- **PSI Simulator** — Planned Ship Quantity (数量シミュレーション)
- **PPC Simulator** — Planned Sales Price (単価・利益シミュレーション)

Both PSI and PPC require network traversal because outcomes at one node
depend on relationships with upstream/downstream nodes.

### 2-B. Table Model — for evaluation

The Table model handles anything that can be evaluated as a flat aggregation
after the Tree simulation has produced its results.

Dimensions: `product × node × week × scenario`

Table-dependent evaluation:

- **C: Profit/Cost Evaluator**

```
Revenue   = Ship_Qty  × Sales_Price
Cost      = Ship_Qty  × Unit_Cost
Profit    = Revenue - Cost - Fee - Adjustment
```

This is ordinary spreadsheet arithmetic. No network traversal is needed.  
Pulling Profit/Cost evaluation into the Tree structure over-complicates it.

---

## 3. PSI Simulator (Tree-based, Quantity)

### Definition

```
PSI: Production/Procurement · Ship/Sales · Inventory
     Quantity Simulation
```

| Side        | Characteristic                                     |
|-------------|----------------------------------------------------|
| Supply side | Rate-limited by bottleneck capacity                |
| Demand side | Demand fluctuation absorbed by inventory           |

### PSI List Structure

```python
psi4demand[week][S, CO, I, P, CapSoft, CapHard]
psi4supply[week][S, CO, I, P, CapSoft, CapHard]
```

Index mapping:

| Index | Field    | Description                          |
|-------|----------|--------------------------------------|
| 0     | S        | Ship / Sales quantity                |
| 1     | CO       | Customer Order (accepted demand)     |
| 2     | I        | Inventory                            |
| 3     | P        | Production / Procurement             |
| 4     | CapSoft  | Soft capacity (shift/overtime-based) |
| 5     | CapHard  | Hard capacity (physical equipment)   |

Capacity is modelled as a constraint embedded directly in the PSI list.  
`CapHard` = physical ceiling (immovable).  
`CapSoft` = operational ceiling (adjustable via shift policy).

### Core Simulation Loop

```
DemandEvent (market)
  ↓  [LT shift]
ProductionNeed (supply point)
  ↓  [CapHard / CapSoft clip]
AcceptedLots / BlockedLots
  ↓  [allocation rule]
Ship_Qty per node per week
  ↓
Inventory update
  ↓
Next week
```

### Allocation rules (Plugin-injectable)

- `urgency_first` — priority by stockout risk
- `market_share` — fixed ratio allocation
- `buffer_maintain` — preserve safety stock threshold
- custom rules via Hook/Plugin

---

## 4. PPC Simulator (Tree-based, Unit Price)

### Definition

```
PPC: Price · Profit · Cost
     Unit Price Simulation
```

PPC is not a post-processing step after PSI.  
It is a **parallel, independent simulation** that determines:

- What sales price should be set at the Leaf node (market front)
- Where profit is generated in the supply chain
- How brand protection rules constrain discounting

### Why Tree traversal is needed

Sales price at a Leaf node is not determined locally.  
It depends on:

```
HQ supply cost
  + Transport / logistics cost per lane
  + DC handling cost
  + Leaf margin target
  = Leaf floor price
```

Lane changes, geopolitical cost shifts, or HQ pricing policy changes
propagate through the tree and change Leaf pricing.

### Price Policy (per product × market node)

```csv
product_id, market_node, base_price, target_margin_rate,
minimum_margin_rate, max_discount_rate, brand_floor_price,
campaign_budget_rate, competitor_follow_flag
```

Key policy rules:

- **Cost accumulation**: minimum cost is accumulated from HQ to Leaf
- **Leaf-controlled margin**: final margin is set at the market front
- **Brand floor protection**: discount cannot go below `brand_floor_price`
- **Competitor follow = OFF** by default — brand differentiation is preferred
  over price matching

### Profit Center model

Two standard patterns:

| Pattern | Profit Center       | Cost Centers              |
|---------|---------------------|---------------------------|
| A       | Leaf node (market)  | HQ, factory, DC           |
| B       | HQ supply point     | Factory, DC, Leaf         |

Pattern B applies when Brand Usage Fee or Affiliated Parts Lane pricing
captures margin centrally at HQ.

---

## 5. Profit/Cost Evaluator (Table-based)

### Inputs (from PSI + PPC outputs)

- `ship_qty[product][node][week]` — from PSI Simulator
- `sales_price[product][node][week]` — from PPC Simulator
- `unit_cost[product][node]` — from Cost Master

### Calculation

```python
Revenue[p][n][w] = ship_qty[p][n][w] * sales_price[p][n][w]
Cost[p][n][w]    = ship_qty[p][n][w] * unit_cost[p][n]
Profit[p][n][w]  = Revenue[p][n][w] - Cost[p][n][w] - Fee[p][n] - Adj[p][n][w]
```

All operations are flat table arithmetic — no network traversal.

### Cost Master structure (business-character model)

Rather than a full product costing system (SAP CO-PC level),
WOM uses a **cost ratio model** that captures the business character
of each node:

```csv
product_id, node_id, business_unit,
sales_price,
material_cost_ratio,
labor_cost_ratio,
facility_fixed_cost_ratio,
logistics_cost_ratio,
indirect_cost_ratio,
profit_ratio
```

This is intentionally simplified.  
It enables scenario simulation without requiring a full ERP cost rollup.  
Detailed product costing can be connected later as an external interface.

---

## 6. Core Runtime Entities (from Kernel v1, preserved)

### Lot

```python
@dataclass(frozen=True)
class Lot:
    lot_id: str
    product_id: str
    origin_node: str
    destination_node: Optional[str]
    quantity_cpu: float          # CPU = Common Planning Unit
    created_time_bucket: str     # ISO week: YYYYWW
    attributes: Optional[dict] = None
```

### Event

```python
@dataclass(frozen=True)
class Event:
    event_id: str
    lot_id: str
    event_type: str              # production / shipment / arrival / sale
    product_id: str
    node_id: str
    time_bucket: str
    quantity_cpu: float
    source: Optional[str] = None
    metadata: Optional[dict] = None
```

### State (derived)

```python
@dataclass(frozen=True)
class State:
    inventory_by_node_product_time: dict
    demand_by_market_product_time: dict
    supply_by_node_product_time: dict
    backlog_by_market_product_time: dict
    capacity_usage_by_resource_time: dict
    financial_summary: Optional[dict] = None
```

State is always recomputed from Events. Never mutated directly.

### TrustEvent

```python
@dataclass(frozen=True)
class TrustEvent:
    trust_event_id: str
    event_type: str              # E_STOCKOUT_RISK / E_CAPACITY_OVERLOAD / ...
    severity: float
    node_id: Optional[str]
    product_id: Optional[str]
    time_bucket: str
    message: str
    evidence: Optional[dict] = None
```

### Operator

```python
@dataclass(frozen=True)
class Operator:
    operator_id: str
    operator_type: str           # increase_production / shift_shipment / ...
    target: dict
    parameters: dict
    rationale: Optional[str] = None
```

---

## 7. Time Representation

Canonical time bucket format: `YYYYWW` (ISO week)

Examples: `202601`, `202652`, `202701`

Rules:
- All events use ISO week buckets
- Time ordering is deterministic
- Monthly views are derived from weekly aggregation

---

## 8. Data Flow: Full Pipeline

```
DemandEvent (market)
  ↓
Lot (CPU-based supply unit)
  ↓
PSI Simulation (Tree: Inbound + Outbound)
  ├─ ship_qty [product][node][week]
  └─ accepted / blocked lots

PPC Simulation (Tree: cost accumulation + price policy)
  └─ sales_price [product][node][week]

                ↓  both outputs feed into ↓

Profit/Cost Evaluation (Table: product × node × week)
  ├─ Revenue
  ├─ Cost
  ├─ Profit
  └─ KPI (service rate, CCC, inventory level, profit ratio)

                ↓

State Snapshot → TrustEvent → Operator → re-simulation
```

---

## 9. Serialisation Artifacts

| File                           | Content                              |
|--------------------------------|--------------------------------------|
| `demand_events.json`           | DemandEvent records                  |
| `flow_events.json`             | FlowEvent / Event records            |
| `state_view.json`              | Derived State snapshot               |
| `trust_events.json`            | TrustEvent records                   |
| `operator_candidates.json`     | Candidate Operators                  |
| `operator_spec.json`           | Applied Operator spec                |
| `evaluation_results.json`      | EvaluationResult records             |
| `product_price_policy.csv`     | PPC price policy master              |
| `node_cost_master.csv`         | Cost ratio by product × node         |
| `visual_capacity_gate_weekly.csv` | Capacity gate visualisation       |
| `full_plan_result.json`        | Full plan result contract            |

---

## 10. Design Rules (mandatory)

| # | Rule                                                                 |
|---|----------------------------------------------------------------------|
| 1 | Events and Flows are the only primary source of truth                |
| 2 | State must always be derived — never mutated directly                |
| 3 | Operators modify Event/Flow structures only                          |
| 4 | Tree is for network simulation (PSI, PPC); Table is for evaluation   |
| 5 | PSI and PPC are parallel simulators — neither is a post-process of the other |
| 6 | Core runtime entities are immutable (frozen dataclasses)             |
| 7 | IDs must be stable and reproducible                                  |
| 8 | Time buckets use ISO week format (YYYYWW) throughout                 |

---

*End of WOM_DATA_MODEL v1r0m0*
