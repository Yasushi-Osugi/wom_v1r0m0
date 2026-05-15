# Japanese Rice Supply Chain AS-IS Research Memo

**Version:** v0r2 revised for 3-year crop-cycle horizon  
**Date:** 2026-05-15  
**Status:** Research memo / modeling preparation  
**Target path:** `docs/design/case_japanese_rice_supply_chain_as_is_research.md`

---

## 1. Purpose

This memo defines the AS-IS research framework for modeling the Japanese rice supply chain as a WOM case study.

This revision adds an important rice-specific modeling principle:

> Rice should be modeled by **crop year / harvest cohort**, not only by a single calendar year.

The intended modeling flow is:

```text
real-world rice supply chain
    ↓
AS-IS research memo
    ↓
WOM Case Modeling Base Dataset
    ↓
Adapter
    ↓
WOM Planning Engine
    ↓
PSI / Capacity / Cost / KPI outputs
    ↓
Visualization
    ↓
Management Issue
```

The final goal is to answer the next-step promise from the earlier Rice Case note article:

```text
How should the rice supply chain scenario be simulated in WOM / PSI Planner?
How should parameters be set?
How should cost and price sensitivity be evaluated?
How should scenarios be compared and prioritized?
```

---

## 2. Scope

The initial AS-IS research should focus on the Japanese domestic rice supply chain.

Target flow:

```text
Producer / farm
    ↓
collection / drying / adjustment
    ↓
brown rice storage
    ↓
milling
    ↓
packaging
    ↓
wholesale
    ↓
retail / food service
    ↓
final consumption
```

The focus is on:

- harvested rice
- brown rice
- milled rice
- packaged rice
- domestic distribution
- inventory and storage
- crop-year inventory carryover
- old-crop / new-crop transition
- cost and price structure
- demand and consumption
- scenario planning

Out of scope for the first AS-IS memo:

- individual farmer-level operations
- detailed crop cultivation process
- detailed subsidy / policy mechanism
- full global rice trade network
- exact government reserve release mechanics
- all varieties and grades

---

## 3. Key Characteristics of Rice Supply Chain

### 3.1 Seasonal supply concentration

Rice production is highly seasonal.

```text
P increases sharply around harvest season
I increases after harvest
S continues through the year
I decreases gradually as demand is fulfilled
```

### 3.2 Crop-year inventory carryover

Rice supply and consumption cross calendar-year boundaries.

A crop harvested in `2026-W40` is not fully consumed by the end of calendar year 2026.

A more realistic cycle is:

```text
2026 crop:
    harvested: 2026-W40 to 2026-W44
    consumed mainly: 2026-W41 to 2027-W40
```

Therefore, evaluating only `2026-W01 to 2026-W52` is misleading.

WOM should distinguish:

```text
calendar year:
    Jan-Dec style reporting period

crop year / harvest cohort:
    harvest-to-next-harvest consumption cycle
```

### 3.3 Inventory-heavy structure

Rice must be stored across the year.

Important modeling concepts:

```text
inventory_qty
inventory_value
storage_capacity
storage_cost
inventory_age
crop_year
quality deterioration risk
```

### 3.4 Product transformation

Typical forms:

```text
paddy rice
brown rice
milled rice
packaged rice
cooked rice / food-service demand
```

Initial WOM modeling may simplify this into:

```text
brown rice
milled rice
packaged rice
```

### 3.5 Cost and price structure

Important cost / price elements:

```text
purchase price
drying / adjustment cost
storage cost
milling cost
packaging cost
transport cost
wholesale margin
retail price
food-service selling price
inventory holding cost
cash conversion pressure
quality deterioration cost
old crop discount risk
new crop premium opportunity
```

---

## 4. Time Structure

### 4.1 Weekly bucket

WOM uses weekly buckets. Rice case should also be modeled weekly.

### 4.2 Three-year planning horizon

Recommended horizon:

```text
2026-W01 to 2028-W52
```

This allows WOM to see:

```text
2026:
    consumption of 2025 crop carryover and 2026 crop harvest

2027:
    full evaluation year showing old-crop consumption and new-crop transition

2028:
    tail observation of 2027 crop consumption
```

### 4.3 Main evaluation year

Recommended main evaluation year:

```text
2027
```

Reason:

```text
2027-W01 to 2027-W40:
    consumption of 2026 crop inventory

2027-W40:
    boundary week between 2026 crop and 2027 crop

2027-W41 to 2027-W52:
    early consumption of 2027 crop
```

### 4.4 Crop cohort cycles

Recommended initial crop cohort definition:

```text
2025 crop inventory:
    consumed during 2026-W01 to 2026-W40

2026 crop:
    harvested during 2026-W40 to 2026-W44
    consumed mainly during 2026-W41 to 2027-W40

2027 crop:
    harvested during 2027-W40 to 2027-W44
    consumed mainly during 2027-W41 to 2028-W40
```

Boundary convention:

```text
W40:
    old crop consumption final week
    new crop harvest start week

W41:
    new crop consumption start week
```

---

## 5. WOM Modeling Implications

### 5.1 Node candidates

```text
PRODUCER_REGION
COLLECTION_CENTER
BROWN_RICE_STORAGE
MILLING_NODE
PACKAGING_NODE
WHOLESALER
RETAIL_MARKET
FOOD_SERVICE_MARKET
DEMAND_MARKET
```

### 5.2 Lane candidates

```text
producer → collection
collection → storage
storage → milling
milling → packaging
packaging → wholesaler
wholesaler → retail
wholesaler → food_service
retail → demand
```

### 5.3 Product candidates

```text
BROWN_RICE_STANDARD
MILLED_RICE_STANDARD
MILLED_RICE_PREMIUM
PACKAGED_RICE_STANDARD
PACKAGED_RICE_PREMIUM
RESERVE_RICE
IMPORTED_RICE
```

### 5.4 Lot candidates

Candidate new-crop lot header:

```python
lot = {
    "lot_id": "RICE-JP-2026W40-000001",
    "product_id": "BROWN_RICE_STANDARD",
    "crop_year": "2026",
    "origin_region": "NIIGATA",
    "harvest_week": "2026-W40",
    "available_week": "2026-W41",
    "expected_consumption_start_week": "2026-W41",
    "expected_consumption_end_week": "2027-W40",
    "quality_limit_week": "2027-W40",
    "current_node": "COLLECTION_NIIGATA",
    "quality_grade": "standard",
    "brand_class": "domestic_standard",
    "quantity_kg": 1000,
}
```

Candidate old-crop carryover lot header:

```python
lot = {
    "lot_id": "RICE-JP-2025-CARRYOVER-000001",
    "product_id": "BROWN_RICE_STANDARD",
    "crop_year": "2025",
    "harvest_week": "2025-W40",
    "available_week": "2026-W01",
    "expected_consumption_start_week": "2026-W01",
    "expected_consumption_end_week": "2026-W40",
    "quality_limit_week": "2026-W40",
    "current_node": "BROWN_STORAGE_EAST",
    "quality_grade": "standard",
    "brand_class": "domestic_standard",
    "quantity_kg": 1000,
}
```

---

## 6. PSI Interpretation for Rice

### 6.1 Producer / Collection Node

```text
P:
    harvested / collected rice lots

S:
    lots shipped to storage / mill / wholesaler

I:
    rice inventory at producer / collection node
```

### 6.2 Storage Node

```text
P:
    lots received into storage

S:
    lots released to milling / downstream distribution

I:
    stored rice inventory
```

### 6.3 Milling Node

```text
P:
    milling output or processed lots

S:
    lots shipped to packaging / wholesaler

I:
    milled rice inventory
```

### 6.4 Retail / Market Node

```text
P:
    lots received into retail / market node

S:
    lots sold / consumed

I:
    retail inventory
```

### 6.5 Crop-year inventory view

Rice Case should track inventory by crop year.

```text
I_total
I_2025_crop
I_2026_crop
I_2027_crop
```

---

## 7. Capacity / Cost / KPI Candidates

Capacity candidates:

```text
storage capacity:
    I capacity

milling capacity:
    P capacity or processing capacity

packaging capacity:
    P / S capacity

transport capacity:
    S capacity / flow capacity

market absorption capacity:
    S demand / sales capacity
```

KPI candidates:

```text
ending_inventory_qty_by_crop_year
inventory_value_by_crop_year
storage_utilization
milling_utilization
transport_utilization
gross_profit
profit_margin
cash_conversion_pressure
inventory_soundness_score
producer_sustainability_score
```

---

## 8. Open Assumptions for Initial Model

```text
three-year planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027

weekly bucket

initial old-crop inventory:
    2025 crop carryover inventory

crop cycles:
    2025 crop consumed during 2026-W01 to 2026-W40
    2026 crop harvested during 2026-W40 to 2026-W44
    2026 crop consumed mainly during 2026-W41 to 2027-W40
    2027 crop harvested during 2027-W40 to 2027-W44
    2027 crop consumed mainly during 2027-W41 to 2028-W40
```

---

## 9. Summary

Japanese rice supply chain is a strong WOM case because it combines:

```text
seasonal supply concentration
annual inventory drawdown
old-crop / new-crop transition
storage burden
processing / milling
distribution
price and cost structure
policy constraints
scenario planning
```

The most important modeling insight is:

```text
Rice is not only a production quantity problem.

It is a crop-year PSI synchronization problem
between harvest concentration, old-crop carryover,
new-crop transition, storage capacity,
processing capacity, demand, price, cost, and policy constraints.
```

The next related documents to update are:

```text
docs/design/case_japanese_rice_supply_chain_modeling.md
docs/design/case_japanese_rice_master_dataset.md
docs/design/case_japanese_rice_simulation_plan.md
```
