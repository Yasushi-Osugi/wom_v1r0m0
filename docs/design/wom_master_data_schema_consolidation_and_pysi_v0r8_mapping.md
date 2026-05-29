# WOM Master Data Schema Consolidation and PySI V0R8 Mapping

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md`  
**Related memo:** `docs/design/wom_scenario_package_control_model.md`  
**Primary intent:** Consolidate existing PySI V0R8 master data assets and map them into WOM canonical master schema, scenario package, planning context, and runtime diagnostic layers.

---

## 1. Purpose

This memo defines the master data architecture direction for WOM after confirming that the PySI V0R8-derived implementation assets are preserved in the `WOM_V0R1M0_github` lineage.

The purpose is not to invent a new master schema from zero.

The purpose is to:

```text
recognize PySI V0R8 master files and loaders as existing proven assets
    ↓
consolidate scattered existing schema discussions
    ↓
define canonical WOM master domains
    ↓
map PySI V0R8 master files into canonical WOM schema
    ↓
prepare scenario-package-driven execution
    ↓
preserve compatibility with existing local / public V0R8-derived implementations
```

This memo is also intended to prevent repeated redefinition of the same master schema concepts, especially capacity master definitions.

---

## 2. Core Position

The core position of this memo is:

```text
PySI V0R8 original master data and loader are not obsolete trash.
They are the current proven input spine.
```

WOM V1 / Scenario Package architecture should not discard PySI V0R8.

Instead, it should preserve and map it.

The target direction is:

```text
PySI V0R8 original master CSVs
    ↓
legacy loader / current loader
    ↓
mapping adapter layer
    ↓
WOM canonical master rows
    ↓
WOMPlanningContext / runtime env / scenario package
    ↓
PSI planning engine / money evaluation / cockpit / diagnostics
```

---

## 3. Important Correction: Physical Layer and Planning Layer Already Exist

This memo does not introduce the physical/planning layer separation.

That separation already exists in the PySI V0R8-derived WOM implementation lineage.

### 3.1 Physical layer

The physical layer describes the supply chain as a real-world or logical network.

It includes:

```text
nodes
edges / flows
locations / geo coordinates
lead time
safety stock
calendar
physical or operational resource meaning
MOM / DAD / supply_point roles
```

In the existing implementation, this layer is represented through files and runtime structures such as:

```text
node_geo.csv
product_tree_outbound.csv
product_tree_inbound.csv
network / tree modules
GUI network / world map views
```

### 3.2 Planning layer

The planning layer is the product-specific and scenario-specific expansion of the physical layer.

It includes:

```text
product-specific inbound / outbound planning trees
weekly PSI buckets
lot_ID lists
demand-side PSI
supply-side PSI
planning horizon
scenario
capacity context
money evaluation context
```

The existing PySI V0R8 core concept is:

```text
dual-tree + weekly PSI buckets + lot_ID lists
```

For each product, WOM maintains two planning trees:

```text
OUTBOUND:
    demand / distribution / sales side

INBOUND:
    supply / production / procurement side
```

Each planning node holds weekly PSI buckets:

```python
psi4demand[w] = [S_ids, CO_ids, I_ids, P_ids]
psi4supply[w] = [S_ids, CO_ids, I_ids, P_ids]
```

Quantity is derived from:

```python
len(lot_id_list)
```

not from `(lot_id, qty)` pairs.

### 3.3 Meaning for this memo

Therefore, this memo does not ask:

```text
Should WOM distinguish physical layer and planning layer?
```

It asks:

```text
How should the existing PySI V0R8 physical/planning separation be mapped into
canonical master schema, scenario package, runtime context, and event/diagnostic layers?
```

---

## 4. Relationship to Scenario Package Control Model

The related design memo:

```text
docs/design/wom_scenario_package_control_model.md
```

defines WOM as a generic scenario-package-driven weekly PSI planning platform.

The target execution pattern is:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/iphone_case/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/tesla/as_is.yaml
```

This memo defines how existing master files should map into that scenario package structure.

The key architectural rule is:

```text
A case is not a custom program.
A case is a scenario package.
```

---

## 5. Existing PySI V0R8 Master Assets

The following files are representative PySI V0R8-derived master data assets.

Actual filenames may differ slightly between local versions, but the domain structure is stable.

### 5.1 Network / physical structure

```text
product_tree_outbound.csv
product_tree_inbound.csv
node_geo.csv
node_geo4import.csv
node_geo4export.csv
```

### 5.2 Demand input

```text
sku_S_month_data.csv
S_month_data.csv
```

### 5.3 Capacity / capability input

```text
sku_P_month_data.csv
Cap_month equivalent
Cap_week equivalent
```

### 5.4 Cost / price / money input

```text
sku_cost_table_inbound.csv
sku_cost_table_outbound.csv
offering_price_ASIS_TOBE.csv
tariff_table.csv
```

### 5.5 SQL / intermediate assets

```text
pysi.sqlite3
schema.sql
schema_psi_v1.sql
calendar_iso tables
node_product / product_edge related tables
```

### 5.6 Runtime and output

```text
out/
out_*/
plan_data/psi_state/
kpi.csv
series.csv
psi_df.csv
psi_events.parquet
```

---

## 6. Canonical WOM Master Domains

WOM V1-oriented canonical master domains should be organized as follows.

```text
1. Scenario Master
2. Network Master
3. Node Master
4. Edge / Flow Master
5. Product Master
6. Demand Master
7. Capacity Master
8. Money Master
9. Calendar Master
10. Scenario Control Master
```

These are canonical domains, not necessarily one-to-one CSV files.

A single legacy CSV may map to multiple canonical domains.

A single canonical domain may be populated from multiple legacy CSVs.

---

## 7. Scenario Master

### 7.1 Purpose

Defines the scenario identity and run-level metadata.

### 7.2 Canonical fields

```text
scenario_id
case_id
scenario_name
description
planning_start_week
planning_horizon_weeks
week_domain
base_currency
lot_unit
engine_profile
enable_capacity
enable_money
enable_diagnostics
```

### 7.3 PySI V0R8 mapping

Current PySI V0R8 execution often uses:

```text
--scenario Baseline
CSV directory path
runtime config
scenario preload plugin
```

Mapping:

```text
CLI --scenario / scenario JSON / preload data
    → Scenario Master
```

### 7.4 Scenario package target

Example:

```yaml
scenario:
  scenario_id: RICE_AS_IS
  case_id: japanese_rice
  planning_start_week: 2027-W40
  planning_horizon_weeks: 52
  week_domain: business_week_label
```

---

## 8. Network Master

### 8.1 Purpose

Defines the physical and logical supply chain structure.

### 8.2 Canonical fields

```text
network_id
bound
tree_side
from_node
to_node
edge_type
leadtime_days
transport_mode
active
comment
```

### 8.3 PySI V0R8 mapping

Representative inputs:

```text
product_tree_outbound.csv
product_tree_inbound.csv
```

Mapping:

```text
product_tree_outbound.csv
    → OUTBOUND network / demand-side planning tree

product_tree_inbound.csv
    → INBOUND network / supply-side planning tree
```

### 8.4 Important rule

The two-tree structure should be preserved.

```text
OUTBOUND tree:
    supply_point → DAD nodes → market / customer / leaf nodes

INBOUND tree:
    supply_point → MOM nodes → upstream / supply / procurement nodes
```

The `supply_point` is the connection point between outbound and inbound planning.

---

## 9. Node Master

### 9.1 Purpose

Defines node identity, physical attributes, planning attributes, and role interpretation.

### 9.2 Canonical fields

```text
node_id
node_name
node_role
node_character
bound
parent_node
lat
lon
leadtime_days
safety_stock_days
calendar_id
long_vacation_weeks
tags
active
comment
```

### 9.3 PySI V0R8 mapping

Representative inputs:

```text
node_geo.csv
product_tree_outbound.csv
product_tree_inbound.csv
```

Mapping:

```text
node_geo.csv
    → physical node identity / geo / map

product_tree_*.csv
    → planning node relation / product-specific tree membership
```

### 9.4 Reserved node roles

Existing role conventions should be preserved:

```text
supply_point
    production office / inbound-outbound connection

MOMxxxx
    Mother Of Manufacturing / supply-side starting node

DADyyyy
    Demand Aggregation on Distribution / demand-side aggregation node

BUFFER
    decoupling / inventory buffer node

LEAF
    market / customer / terminal node
```

---

## 10. Edge / Flow Master

### 10.1 Purpose

Defines movement or planning relationship between nodes.

### 10.2 Canonical fields

```text
from_node
to_node
bound
tree_side
product_id
edge_type
leadtime_days
capacity_reference
cost_reference
calendar_id
active
comment
```

### 10.3 PySI V0R8 mapping

Representative inputs:

```text
product_tree_outbound.csv
product_tree_inbound.csv
```

Mapping:

```text
parent / child relation in product_tree_*.csv
    → Edge / Flow Master
```

### 10.4 Future direction

In the scenario package form, edge definitions may become clearer as:

```text
edge_master.csv
```

However, for compatibility, existing product-tree files should continue to work.

---

## 11. Product Master

### 11.1 Purpose

Defines products planned by WOM.

### 11.2 Canonical fields

```text
product_id
product_name
product_group
lot_size
unit
lifecycle_stage
active
comment
```

### 11.3 PySI V0R8 mapping

Product identity is currently distributed across:

```text
product_tree_outbound.csv
product_tree_inbound.csv
sku_S_month_data.csv
sku_P_month_data.csv
sku_cost_table_inbound.csv
sku_cost_table_outbound.csv
offering_price_ASIS_TOBE.csv
```

Mapping rule:

```text
any product appearing in network / demand / capacity / cost / price inputs
    → Product Master candidate
```

### 11.4 Important rule

Product master should eventually be explicit.

However, the adapter should support legacy implicit product discovery.

---

## 12. Demand Master

### 12.1 Purpose

Defines market or leaf-node demand input.

### 12.2 Canonical fields

```text
scenario_id
product_id
node_id
week
demand_qty
demand_type
priority
unit
source_granularity
source_id
comment
```

### 12.3 PySI V0R8 mapping

Representative inputs:

```text
sku_S_month_data.csv
S_month_data.csv
```

Mapping:

```text
sku_S_month_data.csv
    → product-specific demand input

S_month_data.csv
    → generic or aggregate demand input
```

### 12.4 Canonical intermediate

Recommended canonical row:

```text
DemandPlanRow
```

Candidate fields:

```text
scenario_id
product_id
demand_node_id
week
demand_qty
demand_signal_type
source_granularity
source_file
priority
comment
```

### 12.5 Runtime mapping

Demand master should initialize:

```text
demand-side PSI
leaf node S / demand requirement
Demand Anchored Lot seed
```

### 12.6 Future scenario package files

```text
demand_plan.csv
demand_variability_policy.yaml
```

---

## 13. Capacity Master

### 13.1 Purpose

Defines supply, production, shipment, and inventory capacity / capability.

Capacity is not an isolated model.

It connects:

```text
physical resource
    ↓
product / scenario / week
    ↓
planning capacity context
    ↓
capacity-aware PSI planning
    ↓
diagnostics / KPI / issue generation
```

### 13.2 Existing PySI V0R8 input

Representative inputs:

```text
sku_P_month_data.csv
Cap_month equivalent
Cap_week equivalent
```

Historically, this file expresses production or capability input for MOM-side nodes.

### 13.3 Existing design documents to consolidate

Existing related specs include:

```text
docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md
docs/design/wom_capacity_input_granularity_adapter.md
docs/design/capacity_input_granularity_adapter_v0r1_completion.md
docs/design/capacity_provider_monthly_csv_adapter_v0r2.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
```

This memo treats those as existing design layers, not as unrelated fragments.

### 13.4 Formal capacity master candidate

A direct capacity master candidate has already been defined with fields similar to:

```text
scenario_id
tree_side
node_name
product_name
week
capacity_type
capacity_qty
cap_mode
unit
priority
calendar_id
comment
```

This should be treated as the formal consolidated capacity master candidate for near-term V1 alignment.

### 13.5 Canonical intermediate row

The capacity granularity adapter direction defines a canonical weekly row such as:

```text
WeeklyCapacityRow
```

Candidate fields:

```text
scenario_id
product_id
capacity_owner_type
capacity_owner_id
week
capacity_type
capacity_qty
cap_mode
unit
source_granularity
source_id
comment
```

### 13.6 Runtime mapping

Capacity master rows may map to several runtime contexts:

```text
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
```

Current explicit pipeline runtime shape should be treated as a runtime contract, not as the only master-file contract.

### 13.7 Future scenario package files

Recommended canonical scenario package capacity files:

```text
capacity_resource_master.csv
capacity_calendar.csv
product_capacity_consumption.csv
capacity_policy.csv
scenario_capacity_override.csv
```

### 13.8 Mapping relation

```text
PySI V0R8 sku_P_month_data.csv
    ↓
MonthlyCapacityInputRow
    ↓
WeeklyCapacityRow
    ↓
CapacityMasterRecord / canonical capacity rows
    ↓
runtime capacity context
    ↓
capacity-aware planning / diagnostics
```

### 13.9 Important policy

Do not silently hide mismatch.

Even after adapter implementation, WOM should retain diagnostics for:

```text
selected product mismatch
node mismatch
week-domain mismatch
shape mismatch
capacity present but not applied
capacity absent and treated as unlimited
capacity applied and blocking
```

---

## 14. Money Master

### 14.1 Purpose

Defines product/node cost, selling price, tariff, and price/profit simulation input.

### 14.2 PySI V0R8 input

Representative inputs:

```text
sku_cost_table_inbound.csv
sku_cost_table_outbound.csv
offering_price_ASIS_TOBE.csv
tariff_table.csv
```

### 14.3 Canonical master rows

Candidate canonical rows:

```text
ProductNodeCostRow
ProductLeafPriceRow
TariffPolicyRow
CostStructureRow
```

### 14.4 Candidate fields: ProductNodeCostRow

```text
scenario_id
product_id
node_id
bound
cost_type
cost_component
cost_amount
currency
unit
effective_from_week
effective_to_week
source_id
comment
```

### 14.5 Candidate fields: ProductLeafPriceRow

```text
scenario_id
product_id
leaf_node_id
price_type
price_amount
currency
effective_from_week
effective_to_week
comment
```

### 14.6 Candidate fields: TariffPolicyRow

```text
scenario_id
from_node
to_node
product_id
tariff_rate
tariff_amount
currency
policy_id
effective_from_week
effective_to_week
comment
```

### 14.7 Runtime mapping

Money master should feed:

```text
cost evaluation
price evaluation
revenue
profit
margin
cashflow / waterfall
Management Cockpit
```

### 14.8 Design boundary

WOM should not become a full product costing system.

WOM should connect quantity PSI to management-oriented price/profit simulation.

Detailed product costing may remain external.

---

## 15. Calendar Master

### 15.1 Purpose

Defines week mapping and operation calendars.

### 15.2 Canonical fields

```text
calendar_id
week_label
week_index
start_date
end_date
working_days
holiday_flag
long_vacation_flag
comment
```

### 15.3 PySI V0R8 mapping

Existing assets include:

```text
calendar445.py
calendar_iso.py
calendar_iso_generate.py
calendar_sync.py
long_vacation_weeks in node data
```

### 15.4 Week domain policy

Master data and scenario package should prefer business-readable week labels:

```text
2027-W40
```

Engine internals may use integer indexes:

```text
0, 1, 2, ...
```

A week-domain adapter should map:

```text
business week label ↔ engine week index
```

---

## 16. Scenario Control Master

### 16.1 Purpose

Defines how the scenario absorbs demand and supply variability.

### 16.2 Policy domains

The scenario control model should include:

```text
Demand-Supply Balance Policy
Demand Variability Policy
Buffer Policy
Capacity Flex Policy
Early Build Policy
Allocation Policy
```

### 16.3 PySI V0R8 mapping

Some of these behaviors currently exist as:

```text
plugins
hook behavior
scenario preload
capacity_clip
demand_wave
alloc_urgency
urgency_tickets
diagnostics
```

### 16.4 Future scenario package files

```text
demand_supply_balance_policy.yaml
demand_variability_policy.yaml
buffer_policy.yaml
capacity_flex_policy.yaml
early_build_policy.yaml
allocation_policy.yaml
```

---

## 17. Runtime Context Mapping

The canonical master data should initialize runtime structures used by the current WOM engine and cockpit.

### 17.1 Physical/runtime objects

```text
physical network
node maps
geo lookup
networkx graph / map view
```

### 17.2 Planning/runtime objects

```text
prod_tree_dict_OT
prod_tree_dict_IN
root_node_outbound_byprod
root_node_inbound_byprod
psi4demand
psi4supply
lot_pool
scheduled events
```

### 17.3 Capacity runtime objects

```text
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
capacity usage
capacity violation
capacity applicability diagnostic
```

### 17.4 Money runtime objects

```text
cost tables
price tables
tariff tables
profit summary
cost waterfall
node money evaluation
product money summary
```

### 17.5 Diagnostic runtime objects

```text
explicit_pipeline_capacity_scenario_alignment_diagnostic
kpi messages
management issues
replan candidates
```

---

## 18. Legacy Loader Policy

The legacy PySI V0R8 loader should remain valid.

Policy:

```text
Do not break existing CSV loading.
Do not discard PySI V0R8 input files.
Do not require immediate migration to new scenario package schema.
Add adapter layers around existing loaders.
```

Near-term target:

```text
existing PySI V0R8 CSV loader
    ↓
canonical row extraction
    ↓
diagnostic validation
    ↓
scenario package-compatible context
```

---

## 19. Scenario Package Policy

A scenario package should eventually contain:

```text
scenario.yaml
masters/
  node_master.csv
  edge_master.csv
  product_master.csv
  demand_plan.csv
  capacity_master.csv
  money_master.csv
  calendar_master.csv
policies/
  demand_supply_balance_policy.yaml
  demand_variability_policy.yaml
  buffer_policy.yaml
  capacity_flex_policy.yaml
  early_build_policy.yaml
  allocation_policy.yaml
```

However, migration should allow a transitional package:

```text
scenario.yaml
legacy_pysi_v0r8_csv_dir: data/
```

This permits:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

while still reading legacy PySI V0R8 CSV files.

---

## 20. Master Schema Consolidation Table

| Domain | PySI V0R8 source | Canonical target | Runtime target | Future scenario package |
|---|---|---|---|---|
| Scenario | CLI args / scenario preload | ScenarioMaster | env.scenario_id | scenario.yaml |
| Network | product_tree_outbound/inbound | Network / Edge rows | product trees / graphs | edge_master.csv |
| Node | node_geo / product_tree | NodeMaster | node map / plan nodes | node_master.csv |
| Product | product names in all masters | ProductMaster | product selection | product_master.csv |
| Demand | sku_S_month_data / S_month_data | DemandPlanRow | demand PSI / lots | demand_plan.csv |
| Capacity | sku_P_month_data / cap inputs | WeeklyCapacityRow / CapacityMasterRecord | weekly_capability / explicit capacity context | capacity_master.csv |
| Cost | sku_cost_table_in/out | ProductNodeCostRow | cost evaluation | money_master.csv |
| Price | offering_price_ASIS_TOBE | ProductLeafPriceRow | revenue / margin | price_master.csv |
| Tariff | tariff_table | TariffPolicyRow | landed cost / profit | tariff_policy.csv |
| Calendar | calendar modules / node calendars | CalendarMaster | week adapter | calendar_master.csv |
| Policy | plugins / hooks | ScenarioControlPolicy | behavior modifiers | policies/*.yaml |

---

## 21. Migration Roadmap

### Phase M1: Inventory current master files

Codex or manual inspection should list:

```text
current CSV files
required columns
optional columns
current loaders
current runtime destinations
test coverage
```

### Phase M2: Define canonical row dataclasses

Candidate dataclasses:

```text
ScenarioMasterRow
NodeMasterRow
EdgeMasterRow
ProductMasterRow
DemandPlanRow
WeeklyCapacityRow
ProductNodeCostRow
ProductLeafPriceRow
TariffPolicyRow
CalendarMasterRow
```

### Phase M3: Build legacy-to-canonical adapters

Adapters should read current PySI V0R8 files and emit canonical rows.

### Phase M4: Build canonical-to-runtime adapters

Adapters should build:

```text
planning trees
PSI initial state
capacity context
money context
diagnostic context
```

### Phase M5: Add scenario package loader

`scenario.yaml` should specify either:

```text
legacy CSV directory
```

or:

```text
canonical master files
```

### Phase M6: Introduce run_wom_scenario

Target:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

### Phase M7: Preserve legacy runner

Existing command should remain valid:

```bat
python main.py --backend mvp --skip-orchestrate --csv data --scenario Baseline --ui cockpit
```

---

## 22. Design Rules

### Rule 1: Do not break existing working demo

The existing WOM V0R1M0 / PySI V0R8-derived cockpit startup is a valuable working asset.

It should remain executable.

### Rule 2: Do not re-invent capacity schema repeatedly

Capacity schema already exists across multiple design docs.

The next task is consolidation, not reinvention.

### Rule 3: Keep master schema and runtime context separate

Master file layout is not the same as runtime shape.

Example:

```text
capacity_master.csv
    is master data

env.explicit_pipeline_forward_weekly_capacity
    is runtime context
```

### Rule 4: Keep physical layer and planning layer explicit

Do not collapse:

```text
physical network
```

into:

```text
product-specific planning tree
```

They are related but not identical.

### Rule 5: Preserve diagnostics

Adapters should not silently hide mismatch.

Diagnostics should remain visible.

---

## 23. Acceptance Criteria for This Design Direction

This design direction is accepted when the team agrees that:

```text
1. PySI V0R8 master data is the current proven input spine.
2. WOM canonical schema should be layered on top, not substituted abruptly.
3. Legacy loader compatibility is required.
4. Scenario package is the future execution contract.
5. Physical layer and planning layer already exist and must be preserved.
6. Capacity master must be consolidated from existing specs.
7. Money and demand masters must be treated as first-class, not afterthoughts.
8. run_wom_scenario should eventually load either legacy or canonical scenario packages.
```

---

## 24. Recommended Next Documents

After this memo, recommended next documents are:

```text
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_scenario_package_loader.md
docs/codex_requests/wom_master_data_schema_inventory_request.md
```

Recommended order:

```text
1. wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
2. wom_capacity_master_schema_consolidation.md
3. wom_master_data_schema_inventory_request.md
4. wom_scenario_package_loader.md
```

---

## 25. Summary

WOM should not discard PySI V0R8.

WOM should preserve it, map it, and extend it.

The master data architecture should be:

```text
PySI V0R8 original CSVs
    ↓
legacy loader
    ↓
legacy-to-canonical adapter
    ↓
WOM canonical master rows
    ↓
canonical-to-runtime adapter
    ↓
WOM Planning Context / env / cockpit / diagnostics
```

Capacity master is important, but it is only one part of the larger master data architecture.

The correct next step is not to re-create another isolated capacity schema.

The correct next step is to consolidate the master data schema landscape and define the mapping from PySI V0R8 to WOM canonical scenario packages.

In short:

```text
The WOM master data future should grow from the PySI V0R8 roots.
Do not cut the roots.
Map them.
```
