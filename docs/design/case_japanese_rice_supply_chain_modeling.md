# Japanese Rice Supply Chain Modeling Design Memo

**Version:** v0r2 revised for 3-year crop-cycle horizon  
**Date:** 2026-05-15  
**Status:** Design memo  
**Target path:** `docs/design/case_japanese_rice_supply_chain_modeling.md`

---

## 1. Purpose

This memo defines how to model the **Japanese Rice Supply Chain** as a WOM case study.

This revision changes the time design from a 52-week single-year view to a **3-year crop-cycle view**.

```text
planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027
```

This makes it possible to observe:

```text
2027-W01 to 2027-W40:
    consumption of 2026 crop inventory

2027-W40:
    old-crop / new-crop boundary

2027-W41 to 2027-W52:
    initial consumption of 2027 crop
```

---

## 2. Modeling Position

The Rice Case is a comprehensive WOM case because it includes:

```text
seasonal supply concentration
annual inventory drawdown
old-crop / new-crop transition
storage capacity
milling / processing
logistics
price and cost structure
policy and institutional factors
scenario planning
```

The Rice Case is different from the COVID Vaccine Case.

```text
COVID Vaccine Case:
    Forward PUSH with Capacity demonstration
    focus = deliver and administer available lots under capacity constraints

Rice Case:
    full WOM Modeling Process demonstration
    focus = annual PSI synchronization, crop-year inventory, cost, price, and scenario evaluation
```

---

## 3. Scope

### 3.1 Phase 1 Scope

Target flow:

```text
Producer Region
    ↓
Collection / JA / Aggregator
    ↓
Brown Rice Storage
    ↓
Milling
    ↓
Packaging
    ↓
Wholesaler
    ↓
Retail / Food Service
    ↓
Final Demand
```

Phase 1 should include:

```text
3-year planning horizon
main evaluation year = 2027
weekly buckets
old-crop carryover inventory
seasonal harvest supply
annual demand
inventory accumulation and drawdown by crop year
storage capacity
milling capacity
transport capacity
basic cost / price evaluation
AS IS / TO BE / CAN BE / WILL BE / LET IT BE scenarios
```

---

## 4. Network Definition

Initial node set:

```text
PRODUCER_NIIGATA
COLLECTION_NIIGATA
BROWN_STORAGE_EAST
MILL_EAST
PACKAGING_EAST
WHOLESALER_EAST
RETAIL_TOKYO
FOOD_SERVICE_TOKYO
DEMAND_HOUSEHOLD_TOKYO
DEMAND_FOOD_SERVICE_TOKYO
```

Initial lanes:

```text
PRODUCER_NIIGATA → COLLECTION_NIIGATA
COLLECTION_NIIGATA → BROWN_STORAGE_EAST
BROWN_STORAGE_EAST → MILL_EAST
MILL_EAST → PACKAGING_EAST
PACKAGING_EAST → WHOLESALER_EAST
WHOLESALER_EAST → RETAIL_TOKYO
WHOLESALER_EAST → FOOD_SERVICE_TOKYO
RETAIL_TOKYO → DEMAND_HOUSEHOLD_TOKYO
FOOD_SERVICE_TOKYO → DEMAND_FOOD_SERVICE_TOKYO
```

---

## 5. Product and Lot Definition

Initial product classes:

```text
BROWN_RICE_STANDARD
MILLED_RICE_STANDARD
PACKAGED_RICE_STANDARD
PACKAGED_RICE_PREMIUM
```

Simplified transformation chain:

```text
BROWN_RICE_STANDARD
    ↓ milling
MILLED_RICE_STANDARD
    ↓ packaging
PACKAGED_RICE_STANDARD
    ↓ retail / food service demand
CONSUMED_RICE
```

New-crop lot header:

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

Old-crop carryover lot header:

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

## 6. PSI Definition

The most important Rice PSI pattern is:

```text
Before new harvest:
    S consumes old-crop inventory

Harvest weeks:
    P increases sharply
    I increases sharply

After harvest:
    S continues weekly
    I declines gradually
```

Rice Case should track inventory by crop year.

```text
I_total
I_2025_crop
I_2026_crop
I_2027_crop
```

---

## 7. Time Structure

### 7.1 Planning horizon

```text
2026-W01 to 2028-W52
```

### 7.2 Main evaluation year

```text
2027
```

### 7.3 Crop cohort cycles

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

## 8. Capacity Definition

Initial capacity candidates:

```text
storage_capacity:
    I capacity

milling_capacity:
    P capacity or processing capacity

packaging_capacity:
    P / S capacity

transport_capacity:
    S capacity / flow capacity

market_absorption_capacity:
    S demand / sales capacity
```

---

## 9. Cost and Price Model

Initial cost categories:

```text
purchase_cost
drying_adjustment_cost
storage_cost_per_lot_week
milling_cost_per_lot
packaging_cost_per_lot
transport_cost_per_lot
inventory_holding_cost
quality_loss_cost
old_crop_discount_cost
```

Initial price categories:

```text
producer_price
wholesale_price
retail_price
food_service_price
premium_brand_price
old_crop_discount_price
new_crop_premium_price
```

---

## 10. Scenario Definitions

Use the five-view scenario framework.

```text
AS IS:
    current inventory, cost, revenue, and price structure

TO BE:
    premium brand strategy, higher selling price, export opportunity

CAN BE:
    storage cost reduction, milling capacity improvement, demand smoothing

WILL BE:
    demand decline, price decline, inventory overhang, cash pressure

LET IT BE:
    government reserve, minimum access rice, food security constraints
```

---

## 11. KPI and Visualization

Key KPIs:

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

Most important chart:

```text
stacked inventory by crop year:
    2025 crop
    2026 crop
    2027 crop
```

This chart should show the 2027 transition from 2026 crop to 2027 crop.

---

## 12. Initial MVP Model

```text
planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027

crop cycles:
    2025 carryover → 2026-W01 to 2026-W40
    2026 harvest → 2026-W40 to 2026-W44
    2026 consumption → 2026-W41 to 2027-W40
    2027 harvest → 2027-W40 to 2027-W44
    2027 consumption → 2027-W41 to 2028-W40
```

Minimal nodes:

```text
PRODUCER_NIIGATA
COLLECTION_NIIGATA
BROWN_STORAGE_EAST
MILL_EAST
PACKAGING_EAST
WHOLESALER_EAST
RETAIL_TOKYO
FOOD_SERVICE_TOKYO
DEMAND_HOUSEHOLD_TOKYO
DEMAND_FOOD_SERVICE_TOKYO
```

MVP evaluation:

```text
old-crop drawdown
new-crop harvest spike
inventory by crop year
storage utilization
storage cost
gross profit
scenario delta vs AS IS
```

---

## 13. Implementation Roadmap

```text
Phase 1:
    update Rice smoke runner to 3-year crop-cycle horizon

Phase 2:
    add inventory by crop year

Phase 3:
    add cost / price evaluation by crop year

Phase 4:
    add AS IS / CAN BE / WILL BE scenario comparison

Phase 5:
    draft follow-up note article
```

---

## 14. Summary

The Japanese Rice Supply Chain Case is a core WOM modeling case.

The key message is:

```text
Rice is not only a production quantity problem.

It is a crop-year PSI synchronization problem
between harvest concentration, old-crop carryover,
new-crop transition, storage capacity,
processing capacity, demand, price, cost, and policy constraints.
```
