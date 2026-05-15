# Japanese Rice Case Master Dataset Design Memo

**Version:** v0r2 revised for 3-year crop-cycle horizon  
**Date:** 2026-05-15  
**Status:** Design memo  
**Target path:** `docs/design/case_japanese_rice_master_dataset.md`

---

## 1. Purpose

This memo defines the master dataset for the Japanese Rice Supply Chain WOM case study.

This revision adds explicit support for:

```text
3-year planning horizon
main evaluation year = 2027
crop_year
harvest cohort
initial old-crop inventory
old-crop / new-crop transition
```

---

## 2. File Set Overview

The Rice Case Master Dataset should include:

```text
rice_scenario_master.csv
rice_node_master.csv
rice_lane_master.csv
rice_product_master.csv
rice_lot_master.csv
rice_supply_plan.csv
rice_demand_plan.csv
rice_capacity_master.csv
rice_cost_price_master.csv
rice_kpi_policy_master.csv
rice_scenario_parameter_master.csv
rice_assumption_log.csv
rice_adapter_mapping_master.csv
```

---

## 3. rice_scenario_master.csv

### Schema

```csv
scenario_id,scenario_name,baseline_scenario_id,description,start_week,end_week,main_evaluation_year,scenario_type,is_baseline,comment
```

### Sample Rows

```csv
scenario_id,scenario_name,baseline_scenario_id,description,start_week,end_week,main_evaluation_year,scenario_type,is_baseline,comment
RICE_AS_IS,Rice AS-IS,,Current simplified Japanese rice supply chain,2026-W01,2028-W52,2027,AS_IS,true,baseline scenario
RICE_TO_BE_PREMIUM,Rice TO-BE Premium Strategy,RICE_AS_IS,Premium rice price uplift and brand strengthening,2026-W01,2028-W52,2027,TO_BE,false,price uplift scenario
RICE_CAN_BE_STORAGE,Rice CAN-BE Storage Improvement,RICE_AS_IS,Storage cost reduction and inventory control,2026-W01,2028-W52,2027,CAN_BE,false,realistic improvement scenario
RICE_WILL_BE_DEMAND_DECLINE,Rice WILL-BE Demand Decline,RICE_AS_IS,Domestic demand decline and inventory overhang risk,2026-W01,2028-W52,2027,WILL_BE,false,risk scenario
```

---

## 4. rice_lot_master.csv

### Schema

```csv
scenario_id,lot_id,product_id,crop_year,quantity,current_node_id,target_node_id,target_region,harvest_week,available_week,expected_consumption_start_week,expected_consumption_end_week,quality_limit_week,quality_status,priority,comment
```

### Sample Rows

```csv
scenario_id,lot_id,product_id,crop_year,quantity,current_node_id,target_node_id,target_region,harvest_week,available_week,expected_consumption_start_week,expected_consumption_end_week,quality_limit_week,quality_status,priority,comment
RICE_AS_IS,RICE-JP-2025-CARRYOVER-000001,BROWN_RICE_STANDARD,2025,1000,BROWN_STORAGE_EAST,RETAIL_TOKYO,TOKYO,2025-W40,2026-W01,2026-W01,2026-W40,2026-W40,usable,100,old crop carryover lot
RICE_AS_IS,RICE-JP-2026W40-000001,BROWN_RICE_STANDARD,2026,1000,COLLECTION_NIIGATA,BROWN_STORAGE_EAST,EAST,2026-W40,2026-W41,2026-W41,2027-W40,2027-W40,usable,100,2026 harvest lot
RICE_AS_IS,RICE-JP-2027W40-000001,BROWN_RICE_STANDARD,2027,1000,COLLECTION_NIIGATA,BROWN_STORAGE_EAST,EAST,2027-W40,2027-W41,2027-W41,2028-W40,2028-W40,usable,100,2027 harvest lot
```

---

## 5. rice_supply_plan.csv

### Schema

```csv
scenario_id,node_id,product_id,crop_year,week,supply_qty,supply_type,source_type,comment
```

### Sample Rows

```csv
scenario_id,node_id,product_id,crop_year,week,supply_qty,supply_type,source_type,comment
RICE_AS_IS,BROWN_STORAGE_EAST,BROWN_RICE_STANDARD,2025,2026-W01,80,old_crop_carryover,initial_inventory,2025 crop carryover inventory
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026,2026-W40,20,harvest,internal,2026 harvest peak week 1
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026,2026-W41,30,harvest,internal,2026 harvest peak week 2
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026,2026-W42,30,harvest,internal,2026 harvest peak week 3
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026,2026-W43,15,harvest,internal,2026 harvest tail
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026,2026-W44,5,harvest,internal,2026 harvest tail
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2027,2027-W40,20,harvest,internal,2027 harvest peak week 1
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2027,2027-W41,30,harvest,internal,2027 harvest peak week 2
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2027,2027-W42,30,harvest,internal,2027 harvest peak week 3
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2027,2027-W43,15,harvest,internal,2027 harvest tail
RICE_AS_IS,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2027,2027-W44,5,harvest,internal,2027 harvest tail
```

---

## 6. rice_demand_plan.csv

### Schema

```csv
scenario_id,demand_node_id,region,product_id,week,demand_qty,demand_type,priority,comment
```

Demand should cover the full 3-year horizon.

### Sample Rows

```csv
scenario_id,demand_node_id,region,product_id,week,demand_qty,demand_type,priority,comment
RICE_AS_IS,DEMAND_HOUSEHOLD_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2026-W01,1.0,household,100,weekly household demand
RICE_AS_IS,DEMAND_FOOD_SERVICE_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2026-W01,0.6,food_service,100,weekly food service demand
RICE_AS_IS,DEMAND_HOUSEHOLD_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2027-W01,1.0,household,100,weekly household demand
RICE_AS_IS,DEMAND_FOOD_SERVICE_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2027-W01,0.6,food_service,100,weekly food service demand
RICE_AS_IS,DEMAND_HOUSEHOLD_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2028-W01,1.0,household,100,weekly household demand
RICE_AS_IS,DEMAND_FOOD_SERVICE_TOKYO,TOKYO,PACKAGED_RICE_STANDARD,2028-W01,0.6,food_service,100,weekly food service demand
```

MVP adapter may generate repeated weekly rows automatically.

---

## 7. rice_capacity_master.csv

Capacity rows may be expanded across 2026-W01 to 2028-W52 by adapter.

### Schema

```csv
scenario_id,capacity_owner_type,capacity_owner_id,product_id,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

### Sample Rows

```csv
scenario_id,capacity_owner_type,capacity_owner_id,product_id,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
RICE_AS_IS,node,BROWN_STORAGE_EAST,BROWN_RICE_STANDARD,2026-W01,I,100,hard,LOT,100,STD_CAL,brown rice storage capacity
RICE_AS_IS,node,MILL_EAST,BROWN_RICE_STANDARD,2026-W01,P,5,hard,LOT,100,STD_CAL,milling capacity
RICE_AS_IS,lane,LANE_PACKAGING_TO_WHOLESALER,PACKAGED_RICE_STANDARD,2026-W01,S,5,hard,LOT,100,STD_CAL,transport capacity
```

---

## 8. rice_cost_price_master.csv

### Schema

```csv
scenario_id,owner_type,owner_id,product_id,week,cost_price_type,unit_value,unit,currency,comment
```

### Sample Rows

```csv
scenario_id,owner_type,owner_id,product_id,week,cost_price_type,unit_value,unit,currency,comment
RICE_AS_IS,node,PRODUCER_NIIGATA,BROWN_RICE_STANDARD,2026-W40,purchase_price,250000,LOT,JPY,producer purchase price per lot
RICE_AS_IS,node,BROWN_STORAGE_EAST,BROWN_RICE_STANDARD,2026-W01,storage_cost_per_lot_week,5000,LOT,JPY,storage cost assumption
RICE_AS_IS,node,MILL_EAST,BROWN_RICE_STANDARD,2026-W01,milling_cost_per_lot,30000,LOT,JPY,milling cost assumption
RICE_AS_IS,lane,LANE_PACKAGING_TO_WHOLESALER,PACKAGED_RICE_STANDARD,2026-W01,transport_cost_per_lot,20000,LOT,JPY,transport cost assumption
RICE_AS_IS,node,RETAIL_TOKYO,PACKAGED_RICE_STANDARD,2026-W01,selling_price,500000,LOT,JPY,retail selling price per lot
```

---

## 9. rice_scenario_parameter_master.csv

Scenario parameters should support:

```text
premium price uplift
storage cost reduction
demand decline
old crop discount
new crop premium
```

Example:

```csv
scenario_id,parameter_id,target_type,target_id,product_id,week,value,unit,comment
RICE_TO_BE_PREMIUM,premium_price_increase,node,RETAIL_TOKYO,PACKAGED_RICE_PREMIUM,2027-W01,0.10,ratio,10 percent premium price uplift in evaluation year
RICE_CAN_BE_STORAGE,storage_cost_reduction,node,BROWN_STORAGE_EAST,BROWN_RICE_STANDARD,2027-W01,-0.15,ratio,15 percent storage cost reduction in evaluation year
RICE_WILL_BE_DEMAND_DECLINE,household_demand_decline,demand,DEMAND_HOUSEHOLD_TOKYO,PACKAGED_RICE_STANDARD,2027-W01,-0.10,ratio,10 percent demand decline in evaluation year
```

---

## 10. rice_assumption_log.csv

Add crop-cycle assumptions.

```csv
scenario_id,assumption_id,category,description,value,source,confidence,comment
RICE_AS_IS,ASSUMP_HORIZON,TIME,Planning horizon is 2026-W01 to 2028-W52,3 years,model assumption,high,needed to observe crop-year cycles
RICE_AS_IS,ASSUMP_EVAL_YEAR,TIME,Main evaluation year is 2027,2027,model assumption,high,2027 shows old-crop consumption and new-crop transition
RICE_AS_IS,ASSUMP_2025_CARRYOVER,TIME,2025 crop carryover is consumed during 2026-W01 to 2026-W40,W01-W40,model assumption,medium,boundary convention
RICE_AS_IS,ASSUMP_NEW_CROP_START,TIME,New crop is harvested from W40 and consumed from W41,W40 harvest W41 consumption,model assumption,medium,one-week availability lag
```

---

## 11. rice_adapter_mapping_master.csv

Adapter should map crop-year fields as well.

```csv
case_dataset,case_field,wom_target_file,wom_target_field,transform_rule,comment
rice_lot_master,crop_year,lot_header,crop_year,copy,crop-year tracking
rice_lot_master,quality_limit_week,lot_header,quality_limit_week,copy,quality limit
rice_supply_plan,crop_year,psi_seed,crop_year,copy,supply cohort tracking
rice_capacity_master,capacity_owner_id,capacity_master_sample.csv,node_name,pseudo_lane_if_owner_type_lane,lane capacity represented as pseudo node if needed
```

---

## 12. Summary

The most important revision is:

```text
Rice Case requires crop-year modeling.

A 52-week calendar-year horizon is not enough.

The recommended first model uses:
    2026-W01 to 2028-W52
with:
    2027 as main evaluation year
```

This enables WOM to represent:

```text
old-crop carryover
new-crop harvest
new-crop consumption
old-crop / new-crop transition
inventory by crop year
cost / price evaluation
scenario comparison
```
