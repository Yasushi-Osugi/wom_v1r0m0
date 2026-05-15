# Japanese Rice Case Simulation Plan Design Memo

**Version:** v0r2 revised for 3-year crop-cycle horizon  
**Date:** 2026-05-15  
**Status:** Design memo  
**Target path:** `docs/design/case_japanese_rice_simulation_plan.md`

---

## 1. Purpose

This memo defines the simulation plan for the Japanese Rice Supply Chain WOM Case Study.

This revision updates the simulation horizon and rice-specific time logic.

Rice should not be simulated only as a single calendar year.

The first meaningful Rice Case simulation should use:

```text
planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027
```

This allows WOM to observe:

```text
2027-W01 to 2027-W40:
    consumption of 2026 crop inventory

2027-W40:
    boundary between old crop consumption and new crop harvest

2027-W41 to 2027-W52:
    initial consumption of 2027 crop
```

---

## 2. Simulation Philosophy

The intended flow is:

```text
Rice Supply Chain AS-IS Research
    ↓
Rice Case Master Dataset
    ↓
Adapter
    ↓
WOM Planning Engine
    ↓
Quantity PSI Simulation
    ↓
Cost / Price Evaluation
    ↓
KPI Delta vs Baseline
    ↓
Scenario Comparison
    ↓
Management Issue Generation
```

The key idea is:

```text
Rice is not only a production quantity problem.

It is a crop-year PSI synchronization problem
between harvest concentration, old-crop carryover,
new-crop transition, storage capacity, demand, price, and cost.
```

---

## 3. Simulation Scope

```text
planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027

products:
    PACKAGED_RICE_STANDARD

demand markets:
    household
    food service
```

Crop cohort cycles:

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

Boundary rule:

```text
W40:
    old crop consumption final week
    new crop harvest start week

W41:
    new crop consumption start week
```

---

## 4. Baseline Scenario: RICE_AS_IS

### Basic assumptions

```text
scenario_id:
    RICE_AS_IS

planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027

old crop carryover:
    2025 crop inventory available at 2026-W01

new crop harvest:
    2026 crop harvested W40-W44
    2027 crop harvested W40-W44

demand:
    stable weekly demand

product:
    PACKAGED_RICE_STANDARD
```

### Baseline parameters

```text
lot_size:
    1 lot = 1,000 kg

initial 2025 crop carryover:
    80 lots

2026 harvest supply:
    W40: 20 lots
    W41: 30 lots
    W42: 30 lots
    W43: 15 lots
    W44: 5 lots
    total: 100 lots

2027 harvest supply:
    W40: 20 lots
    W41: 30 lots
    W42: 30 lots
    W43: 15 lots
    W44: 5 lots
    total: 100 lots

weekly household demand:
    1.0 lot / week

weekly food-service demand:
    0.6 lot / week

weekly total demand:
    1.6 lots / week
```

### Expected behavior

```text
2026-W01 to 2026-W40:
    2025 crop carryover inventory is consumed

2026-W40 to 2026-W44:
    2026 crop harvest creates P spike

2026-W41 to 2027-W40:
    2026 crop inventory is consumed

2027-W40 to 2027-W44:
    2027 crop harvest creates P spike

2027-W41 to 2028-W40:
    2027 crop inventory is consumed
```

---

## 5. Scenario Framework

Use the five-view scenario framework.

```text
AS IS
TO BE
CAN BE
WILL BE
LET IT BE
```

### AS IS

Understand current inventory, cost, revenue, and price structure.

### TO BE

Premium rice / brand value strategy.

Example parameter changes:

```text
premium product mix increase
selling price +10%
packaging cost +3%
```

### CAN BE

Storage cost reduction and inventory control.

Example parameter changes:

```text
storage_cost_per_lot_week -15%
milling_capacity +10%
transport_cost -5%
```

### WILL BE

Domestic demand decline and inventory overhang.

Example parameter changes:

```text
household demand -10%
food-service demand -5%
selling price -5%
storage cost unchanged or +5%
```

### LET IT BE

Policy reserve / minimum access / food security constraints treated as external.

---

## 6. Parameter Setting

Parameter categories:

```text
supply parameters
demand parameters
crop-year parameters
capacity parameters
cost parameters
price parameters
scenario policy parameters
KPI weight parameters
```

Crop-year parameters:

```text
crop_year
harvest_start_week
harvest_end_week
available_start_week
consumption_start_week
consumption_end_week
quality_limit_week
initial_old_crop_inventory
```

---

## 7. Cost / Price Sensitivity Analysis

Recommended first sensitivity variables:

```text
selling_price
storage_cost
transport_cost
milling_cost
demand_qty
old_crop_discount_rate
new_crop_premium_rate
```

Simple sensitivity grid:

| Parameter | Low | Base | High |
|---|---:|---:|---:|
| selling_price | -10% | 0% | +10% |
| storage_cost | -15% | 0% | +15% |
| demand_qty | -10% | 0% | +10% |
| transport_cost | -10% | 0% | +10% |

Sensitivity output:

```text
gross_profit change
profit_margin change
inventory_value_by_crop_year change
cash_conversion_pressure change
storage_cost change
fill_rate change
```

---

## 8. Simulation Execution Flow

```text
load Rice Case Master Dataset
    ↓
apply scenario parameters
    ↓
adapter to current WOM input
    ↓
run WOM planning engine or smoke simulator
    ↓
generate PSI outputs
    ↓
calculate cost / price evaluation
    ↓
calculate KPIs
    ↓
compare against baseline
    ↓
generate management issues
```

---

## 9. Expected Output Files

Quantity outputs:

```text
rice_psi_summary.csv
rice_inventory_by_crop_year.csv
rice_supply_by_week.csv
rice_demand_by_week.csv
rice_capacity_usage.csv
rice_capacity_violation.csv
```

Money outputs:

```text
rice_cost_summary.csv
rice_revenue_summary.csv
rice_profit_summary.csv
rice_inventory_value_by_crop_year.csv
rice_cash_pressure.csv
```

KPI outputs:

```text
rice_kpi_summary.csv
rice_kpi_delta_vs_baseline.csv
rice_scenario_comparison.csv
```

Issue outputs:

```text
rice_management_issues.csv
rice_management_issues.json
```

---

## 10. Visualization Plan

### PSI Chart

Show weekly:

```text
P
S
I
```

### Inventory by Crop Year Chart

This is the most important chart for the revised Rice Case.

Show stacked inventory:

```text
2025 crop
2026 crop
2027 crop
```

The 2027 chart should show:

```text
2027-W01 to 2027-W40:
    2026 crop inventory declining

2027-W40 to 2027-W44:
    2027 crop harvest spike

2027-W41 onward:
    2027 crop inventory starts to be consumed
```

### Cost / Profit Chart

```text
revenue
purchase cost
storage cost
milling cost
transport cost
gross profit
profit margin
```

### Scenario Comparison Chart

Compare:

```text
AS IS
TO BE
CAN BE
WILL BE
LET IT BE
```

using key KPIs.

---

## 11. Minimum Smoke Scenario v2

### Smoke input

```text
planning horizon:
    2026-W01 to 2028-W52

main evaluation year:
    2027

initial old crop:
    2025 crop carryover = 80 lots

2026 harvest:
    W40: 20 lots
    W41: 30 lots
    W42: 30 lots
    W43: 15 lots
    W44: 5 lots

2027 harvest:
    W40: 20 lots
    W41: 30 lots
    W42: 30 lots
    W43: 15 lots
    W44: 5 lots

weekly demand:
    household: 1.0 lot/week
    food service: 0.6 lot/week

storage capacity:
    100 lots

milling capacity:
    5 lots/week

transport capacity:
    5 lots/week
```

### Expected smoke output

```text
old crop consumption:
    2025 crop inventory declines during 2026-W01 to 2026-W40

2026 crop:
    harvested during 2026-W40 to 2026-W44
    inventory consumed through 2027-W40

2027 evaluation year:
    first half consumes 2026 crop
    W40 begins 2027 harvest
    W41 begins 2027 crop consumption

inventory by crop year:
    visible for 2025 / 2026 / 2027
```

---

## 12. Management Issue Generation

Potential issues:

```text
INVENTORY_OVERHANG
OLD_CROP_REMAINING_RISK
STORAGE_CAPACITY_PRESSURE
PROFIT_MARGIN_DECLINE
DEMAND_DECLINE_RISK
CROP_YEAR_TRANSITION_RISK
```

---

## 13. Relationship with Note Article

This simulation plan should directly support the follow-up note article:

```text
米のサプライチェーンをWOMでシミュレーションする
――パラメータ設定、価格感度分析、シナリオ比較の実例
```

The article should explain:

```text
1. Why a 3-year planning horizon is needed
2. How old crop and new crop are modeled
3. How 2027 is used as the main evaluation year
4. How AS IS is simulated
5. How parameter changes create TO BE / CAN BE / WILL BE
6. How cost / price sensitivity is evaluated
7. How scenario priorities are identified
```

---

## 14. Implementation Roadmap

### Phase 1: Update Rice smoke runner to v2

```text
3-year horizon
crop-year inventory
main evaluation year 2027
inventory by crop year output
```

### Phase 2: Add cost / price evaluation by crop year

```text
inventory value by crop year
storage cost by crop year
old-crop discount
new-crop premium
```

### Phase 3: Add scenario comparison

```text
RICE_AS_IS
RICE_CAN_BE_STORAGE
RICE_WILL_BE_DEMAND_DECLINE
```

### Phase 4: Add note article charts

```text
PSI chart
inventory by crop year chart
cost / profit chart
scenario comparison chart
```

---

## 15. Summary

The most important revision is:

```text
Rice Case should use a 3-year planning horizon.

The main evaluation year should be 2027.

This allows WOM to visualize:
    old-crop consumption
    new-crop harvest
    old-crop / new-crop transition
    crop-year inventory
    cost and KPI impact
```

The next implementation step is:

```text
Rice Case smoke runner v2:
    3-year crop-cycle horizon
    crop-year inventory tracking
    2027 main evaluation summary
```
