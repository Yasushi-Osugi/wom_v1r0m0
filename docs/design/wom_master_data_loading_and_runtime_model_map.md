# WOM Master Data Loading and Runtime Model Map

**Version:** v0r1 draft  
**Date:** 2026-06-03  
**Status:** Design memo  
**Target path:** `docs/design/wom_master_data_loading_and_runtime_model_map.md`

**Parent / preceding design doc:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
```

**Strategic role:** Define how WOM master data enters the pipeline and where it is set in the runtime model  
**Primary scope:** Master CSV files, loaders, intermediate rows, runtime model objects, planning/evaluation/visualization usage  
**Current north star:** Management-visible simulation before recommendation AI  
**Development principle:** Trace every input cable before connecting the main cockpit

---

## 1. Purpose

This memo defines the master data loading and runtime model map for WOM.

The immediate reason for this memo is that WOM is moving from isolated Japanese Rice vertical slices toward a real `Run Full Plan` pipeline.

Before connecting GUI graph panels, cost evaluation, tariff simulation, and rule-based planning to the WOM main pipeline, we need to understand:

```text
which master CSV files exist
which loader reads each file
which intermediate row object or dict is created
which runtime object receives the data
which attribute is set
which planner / evaluator / visualization module uses it
which parts are already implemented
which parts are still TOBE / TBD
```

In simple terms:

```text
This memo labels the input cables before connecting the cockpit.
```

---

## 2. Relationship to WOM Top Routine

The previous design memo defined the Top Routine as the orchestration layer.

```text
Scenario Root / Config
  ↓
Top Routine / Pipeline Core
  ↓
Master Data Loading
  ↓
Runtime Model Instantiation
  ↓
PSI Planning
  ↓
Evaluation
  ↓
Visualization Dataset Adapter
  ↓
GUI / CSV / pandas / SQL / BI
```

This memo focuses on the early stages:

```text
Scenario Root / Config
  ↓
Master Data Loading
  ↓
Runtime Model Instantiation
```

The master data map is the input-side wiring diagram for the Top Routine.

---

## 3. Scope

### 3.1 In scope

This memo covers master data categories such as:

```text
scenario config
network / node / edge master
demand master
capacity master
cost master
price / offering price master
tariff master
calendar / week master
product / SKU / tree master
lane / logistics master
```

It also covers how those master data should become runtime objects such as:

```text
MasterLoadResult
WomRuntimeModel
ProductPlanNode
DemandAnchoredLot
capacity index
cost index
tariff index
price index
visualization datasets
```

### 3.2 Out of scope

This memo does not implement code.

This memo does not finalize every existing legacy CSV format.

This memo does not guarantee that every TOBE loader already exists.

This memo does not change planner behavior.

This memo does not change GUI behavior.

This memo does not define a full DB schema.

---

## 4. Important Note on Current vs TOBE

WOM has accumulated multiple generations of implementation.

Some functionality exists in:

```text
legacy v0r8 CSV loaders
current Japanese Rice vertical slice loaders
management cockpit / cash-flow visualization modules
capacity diagnostic modules
cost / money evaluation experiments
```

Therefore, this memo intentionally separates:

```text
Current known implementation
TOBE target design
Need source-code verification
```

This memo should be treated as the first master-data map, not the final exhaustive source-code audit.

A later Codex request should inspect the actual repository and update this map with precise function names, file paths, and column mappings.

---

## 5. Recommended Master Loading Principle

Master loading should be centralized as a pipeline stage.

Recommended flow:

```text
scenario_root
  ↓
discover master files
  ↓
load master CSV rows
  ↓
normalize rows
  ↓
validate rows
  ↓
build MasterLoadResult
  ↓
instantiate WomRuntimeModel
```

GUI code should not directly load arbitrary master CSVs.

Planner code should not repeatedly parse CSVs.

A single master-loading stage should own:

```text
file discovery
CSV reading
column normalization
schema validation
row typing
diagnostic messages
```

---

## 6. Scenario Root

A WOM scenario should be identified by:

```text
scenario_root
scenario_id
product scope
week range
run mode
```

Example from Japanese Rice vertical slices:

```text
examples/scenarios/japanese_rice_vslice_001
```

Expected scenario-root contents may include:

```text
network master
demand master
capacity master
cost master
price master
tariff master
scenario config
output directory
```

The exact physical file names may differ by scenario generation.

The Top Routine should not assume one hard-coded file name unless the scenario contract says so.

---

## 7. MasterLoadResult Concept

The output of master loading should be a typed or structured result.

Recommended conceptual structure:

```text
MasterLoadResult
  scenario_root
  scenario_id
  loaded_files
  network_rows
  node_rows
  edge_rows
  demand_rows
  capacity_rows
  cost_rows
  price_rows
  tariff_rows
  calendar_rows
  product_rows
  validation_messages
  warnings
  diagnostics
```

This object is the handoff from master loading to runtime model instantiation.

---

## 8. WomRuntimeModel Concept

The runtime model should be the structured in-memory model used by planners and evaluators.

Recommended conceptual structure:

```text
WomRuntimeModel
  scenario_id
  scenario_root
  product_index
  plan_node_trees
  node_index
  edge_index
  lot_index
  capacity_index
  cost_index
  price_index
  tariff_index
  calendar_index
  lane_index
  diagnostics
```

The GUI should not depend directly on every internal runtime object.

The GUI should consume visualization datasets created by adapters.

---

## 9. Master Data Category Map

The high-level map is:

```text
Network / Node / Edge Master
  → ProductPlanNode tree / node_index / edge_index

Demand Master
  → DemandAnchoredLot / market leaf psi4demand[S]

Capacity Master
  → capacity rows / capacity index / env.weekly capability / capacity gate

Cost Master
  → cost profile index / node-product cost structure / money evaluation

Price Master
  → product-node price assumptions / revenue evaluation

Tariff Master
  → tariff rate index / post-plan tariff cost simulation

Product / SKU Master
  → product index / lot generation / cost and price lookup

Calendar Master
  → week index / ISO week mapping / planning horizon

Lane / Logistics Master
  → lane index / leadtime / transport capacity / logistics cost
```

---

## 10. Network / Node / Edge Master

### 10.1 Purpose

Network master defines the physical / planning topology.

It answers:

```text
which nodes exist
which tree side they belong to
which edges connect them
which node is market / DC / MOM / farm / supply point
which partner keys align inbound and outbound
which node metadata is needed for planning
```

### 10.2 Current Japanese Rice implementation pattern

The Japanese Rice vertical slices introduced a network master loader and plan-node instantiation helper.

Current known implementation path:

```text
network master rows
  ↓
pysi/network/network_master_loader.py
  ↓
network row structures
  ↓
pysi/plan/plan_node_tree_instantiation.py
  ↓
ProductPlanNode tree
```

Current runtime target:

```text
ProductPlanNode
  scenario_id
  product_name
  tree_side
  node_name
  node_character
  parent
  children
  partner_key
  role flags
  psi4demand
  psi4supply
```

### 10.3 Important runtime setting

The plan-node tree builder should preserve:

```text
node_name
tree_side
parent / children object links
node_character
role flags
partner_key
supply_point separation between inbound and outbound
```

### 10.4 Known Japanese Rice examples

```text
MARKET_TOKYO
DC_KANTO
RICE_MILL_A
FARM_REGION_A
supply_point
```

Partner-key alignment:

```text
RICE_MILL_A.partner_key == RICE_CORE
DC_KANTO.partner_key == RICE_CORE
```

### 10.5 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| network node rows | network loader | node rows | ProductPlanNode | node_name, node_character, role flags | planning / GUI |
| network edge rows | network loader | edge rows | ProductPlanNode links | parent, children | traversal / planning |
| partner key | network loader | node metadata | ProductPlanNode | partner_key | inbound/outbound alignment |
| tree side | network loader | node metadata | ProductPlanNode | tree_side | inbound/outbound separation |

---

## 11. Demand Master

### 11.1 Purpose

Demand master defines market demand by product and week.

It answers:

```text
what product is demanded
which market or leaf node demands it
which week
how many units / lots
which scenario
```

### 11.2 Current Japanese Rice implementation pattern

The Japanese Rice vertical slices use demand master loading and lot generation.

Current known flow:

```text
demand master rows
  ↓
demand loader
  ↓
demand lot generator
  ↓
DemandAnchoredLot
  ↓
MARKET_TOKYO.psi4demand[week][0]
```

### 11.3 Runtime setting

The most important current setting is:

```python
plan_node.psi4demand[week][0] = list[lot_ids]
```

Legacy PSI slot order:

```text
index 0 = S
index 1 = CO
index 2 = I
index 3 = P
```

For the Japanese Rice first runner:

```text
2027-W40: 80 lot IDs in MARKET_TOKYO.psi4demand["2027-W40"][0]
2027-W41: 95 lot IDs in MARKET_TOKYO.psi4demand["2027-W41"][0]
2027-W42: 110 lot IDs in MARKET_TOKYO.psi4demand["2027-W42"][0]
```

### 11.4 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| demand rows | demand loader | demand rows | DemandAnchoredLot | lot_id, product, demand_week, market | lot generation |
| demand quantity | demand loader | demand row | lot generator | number of lots | lot generation |
| market node | demand loader | demand row | ProductPlanNode | psi4demand[week][S] | planning |
| product | demand loader | demand row / lot | lot_index | product_name | planning / cost / GUI |

### 11.5 Design rule

Demand should be transformed into lots before planning.

Demand should not remain only as aggregate quantity if the WOM model is lot-based.

---

## 12. Capacity Master

### 12.1 Purpose

Capacity master defines the processing capacity of nodes, lanes, or operations by product and week.

It answers:

```text
which node has capacity
which product
which week
which capacity type
how much capacity
which source / scenario
```

### 12.2 Current Japanese Rice implementation pattern

Current known flow:

```text
capacity master rows
  ↓
pysi/capacity/capacity_weekly_rows_source.py
  ↓
load_capacity_weekly_rows_to_env(...)
  ↓
capacity runtime attachment / preflight
  ↓
capacity gate helper
  ↓
accepted / blocked
```

Current Japanese Rice smoke gate:

```text
DC_KANTO
capacity_type = S
capacity = 90 lots/week
```

Base result:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

Scenario variation:

```text
capacity override 100
accepted 260 -> 275
blocked 25 -> 10
```

### 12.3 Runtime setting

Capacity may currently exist as:

```text
capacity rows
env.weekly_capability
node.nx_capacity
capacity gate dataset
```

The exact current precedence should be verified in code.

A recent capacity-aware inbound backward planning summary mentioned deterministic effective MOM capacity resolution in this order:

```text
weekly_capability[product][mom_name]
direct weekly_capability[mom_name]
mom.nx_capacity
zero fallback
```

This should be verified and mapped in source code before being treated as a universal WOM contract.

### 12.4 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| capacity rows | capacity loader | weekly capacity rows | capacity_index | product/node/week/capacity_type | planning |
| capacity rows | capacity loader | env rows | env.weekly_capability | product/node/week | capacity-aware planner |
| node capacity | node/network loader | node metadata | ProductPlanNode or Node | nx_capacity / capacity attrs | fallback / diagnostics |
| capacity gate output | planner/adapter | accepted-blocked rows | visual dataset | requested/capacity/accepted/blocked | GUI / KPI |

### 12.5 Design rule

Capacity master should be normalized into an explicit capacity index.

The planner should not depend on raw CSV rows.

The visualization adapter should not recalculate capacity logic unless it is a diagnostic / scenario variation helper.

---

## 13. Cost Master

### 13.1 Purpose

Cost master defines the economic character of product-node or business-unit activity.

It answers:

```text
what cost structure applies
which node
which product
which week or period
which cost component
what ratio or unit cost
what currency
```

### 13.2 Current status

Cost / money / cash-flow functions exist in the broader WOM codebase.

However, the current Japanese Rice smoke GUI does not yet use a full cost master.

Therefore, cost master mapping should be treated as:

```text
partially implemented / needs source-code audit
```

### 13.3 TOBE cost model direction

The WOM TOBE image treats cost/profit structure as business character.

Recommended early cost master shape:

```text
scenario_id
product_name
node_name
business_unit
week_or_period
sales_price
material_cost_ratio
labor_cost_ratio
facility_fixed_cost_ratio
logistics_cost_ratio
indirect_cost_ratio
profit_ratio
currency
```

Alternative / more granular shape:

```text
scenario_id
product_name
node_name
cost_component
cost_basis
value
currency
effective_from_week
effective_to_week
```

### 13.4 Runtime target

Recommended runtime target:

```text
cost_index
  key: scenario_id / product_name / node_name / week / cost_component
  value: cost parameter
```

Evaluation result:

```text
MoneyResult
  revenue
  cogs
  gross_profit
  logistics_cost
  tariff_cost
  inventory_value
  cash_in
  cash_out
```

### 13.5 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| cost master | cost loader | cost rows | cost_index | node/product/component | money evaluation |
| cost ratio | cost loader | cost row | cost profile | ratio | cost structure simulation |
| unit cost | cost loader | cost row | cost profile | unit_cost | COGS / inventory value |
| fixed cost | cost loader | cost row | cost profile | fixed_cost | profitability evaluation |

### 13.6 Design rule

Cost should be evaluated after PSI quantity planning.

The PSI engine should not embed detailed product costing.

---

## 14. Price / Offering Price Master

### 14.1 Purpose

Price master defines sales or transfer price assumptions.

It answers:

```text
which product
which market or node
which scenario
which week or period
what price
which currency
```

### 14.2 Runtime target

Recommended runtime target:

```text
price_index
  key: scenario_id / product_name / node_name / week
  value: price assumption
```

Used by:

```text
revenue calculation
margin calculation
scenario comparison
price simulation
```

### 14.3 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| offering price | price loader | price rows | price_index | product/node/week | revenue evaluation |
| transfer price | price loader | price rows | price_index | source/destination/product | money evaluation |
| scenario price | price loader | price rows | price_index | scenario-specific price | scenario comparison |

---

## 15. Tariff Master

### 15.1 Purpose

Tariff master defines trade duty assumptions.

It answers:

```text
which origin
which destination
which product or HS code
which lane
which effective period
what tariff rate
what basis
```

### 15.2 Recommended position

Tariff simulation should be outside the PSI engine.

Recommended flow:

```text
PsiPlanningResult / Lot Flow Dataset
  ↓
Tariff Cost Evaluator
  ↓
TariffCostResult
  ↓
MoneyResult
  ↓
Visualization Dataset
```

### 15.3 Recommended tariff master shape

```text
scenario_id
product_name
hs_code
origin_country
destination_country
export_node
import_node
lane_id
effective_from_week
effective_to_week
tariff_rate
tariff_basis
currency
comment
```

### 15.4 Runtime target

Recommended runtime target:

```text
tariff_index
  key: scenario_id / product_name / origin / destination / week / lane
  value: tariff rule
```

### 15.5 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| tariff master | tariff loader | tariff rows | tariff_index | product/origin/destination/week | tariff evaluation |
| tariff rate | tariff loader | tariff row | tariff rule | tariff_rate | tariff cost |
| HS code | tariff loader | tariff row | tariff rule | hs_code | trade rule matching |
| effective period | tariff loader | tariff row | tariff rule | from/to week | scenario evaluation |

### 15.6 Design rule

Tariff should first be post-plan evaluation.

Future phases may feed tariff into sourcing/lane optimization.

---

## 16. Product / SKU Master

### 16.1 Purpose

Product master defines product identity and lot generation assumptions.

It answers:

```text
product name
SKU
lot size
unit
product family
cost/price lookup keys
HS code
shelf life if needed
```

### 16.2 Runtime target

Recommended runtime target:

```text
product_index
  product_name
  sku
  lot_size
  unit
  product_family
  hs_code
```

### 16.3 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| product master | product loader | product rows | product_index | product_name / sku | planning / cost |
| lot size | product loader | product row | lot generator | lot_size | demand lot generation |
| HS code | product loader | product row | product_index | hs_code | tariff matching |

---

## 17. Calendar / Week Master

### 17.1 Purpose

Calendar master defines week buckets and planning horizon.

It answers:

```text
which weeks exist
ISO week labels
start/end dates
fiscal period mapping
month mapping
year mapping
```

### 17.2 Runtime target

Recommended runtime target:

```text
calendar_index
  week
  start_date
  end_date
  fiscal_month
  fiscal_quarter
  fiscal_year
```

Used by:

```text
planning horizon
weekly PSI arrays
monthly/weekly conversion
GUI x-axis
report aggregation
```

### 17.3 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| calendar master | calendar loader | calendar rows | calendar_index | week label | planning / GUI |
| fiscal period | calendar loader | calendar row | calendar_index | month / quarter / year | reporting |
| date range | calendar loader | calendar row | calendar_index | start/end date | output formatting |

---

## 18. Lane / Logistics Master

### 18.1 Purpose

Lane master defines movement between nodes.

It answers:

```text
source node
destination node
leadtime
transport capacity
transport cost
risk
mode
lane availability
```

### 18.2 Runtime target

Recommended runtime target:

```text
lane_index
  source_node
  destination_node
  product_name
  leadtime
  transport_capacity
  logistics_cost
  lane_status
```

Used by:

```text
forward shipment
arrival timing
lane selection
transport bottleneck
logistics cost
tariff origin/destination matching
```

### 18.3 TOBE runtime map

| CSV / master area | Loader | Intermediate | Runtime target | Attribute / index | Used by |
|---|---|---|---|---|---|
| lane master | lane loader | lane rows | lane_index | source/destination/product | planning |
| leadtime | lane loader | lane row | lane_index | leadtime | PSI timing |
| transport cost | lane loader | lane row | lane_index | logistics_cost | money evaluation |
| lane capacity | lane loader | lane row | capacity_index | capacity_type=transport | capacity gate |

---

## 19. Runtime Setting Map Summary

The most important runtime setting points are:

```text
ProductPlanNode.parent
ProductPlanNode.children
ProductPlanNode.partner_key
ProductPlanNode.node_character
ProductPlanNode.psi4demand[week][S]
ProductPlanNode.psi4supply[week][S/CO/I/P]
DemandAnchoredLot.lot_id
DemandAnchoredLot.product_name
capacity_index[node/product/week/type]
cost_index[node/product/week/component]
price_index[node/product/week]
tariff_index[origin/destination/product/week]
visualization_datasets[dataset_name]
```

These are the places where master data becomes executable WOM structure.

---

## 20. Flat Visualization Dataset Relationship

Visualization should not read raw master CSVs.

Visualization should read datasets created after planning.

Recommended datasets:

```text
wom_visual_capacity_gate_weekly
wom_visual_psi_weekly
wom_visual_money_weekly
wom_kpi_summary
wom_event_trace
```

The master data map supports these datasets by clarifying where the values originate.

Example for capacity-gate visual dataset:

```text
demand master
  → demand lots
  → requested

capacity master
  → capacity index
  → capacity

capacity gate / planner
  → accepted / blocked

visualization adapter
  → requested / capacity / accepted / blocked chart dataset
```

---

## 21. Current Japanese Rice Mapping

The current Japanese Rice smoke path can be summarized as:

```text
network master
  ↓
ProductPlanNode tree

demand master
  ↓
DemandAnchoredLots
  ↓
MARKET_TOKYO.psi4demand[week][0]

capacity master
  ↓
capacity weekly rows
  ↓
DC_KANTO S capacity gate

capacity gate result
  ↓
requested / capacity / accepted / blocked
  ↓
GUI table
  ↓
chart dataset
  ↓
chart view
  ↓
scenario variation
```

This is the first concrete realization of the master-data-to-visualization chain.

---

## 22. Known Gaps / Need Source-Code Verification

The following should be verified by a later source-code inspection request:

```text
exact scenario_root file discovery rules
exact current CSV file names for each master category
exact loader function names for legacy v0r8 masters
exact cost master loader and runtime setting
exact price master loader and runtime setting
exact tariff master status
exact calendar / week master status
exact product / SKU master status
exact lane / logistics master status
relationship between env.weekly_capability and ProductPlanNode capacity fields
relationship between current cockpit cash-flow visualization and money datasets
```

This memo intentionally does not pretend that all of these are already confirmed.

---

## 23. Recommended Next Codex Request

The next Codex request should not implement new logic immediately.

It should inspect and document actual source code.

Recommended request:

```text
docs/codex_requests/wom_master_data_loading_and_runtime_model_map_source_audit_request.md
```

Expected Codex work:

```text
search source tree for master loaders
identify CSV file names and loader functions
identify runtime object setting points
identify cost / capacity / tariff / price handling
produce an updated mapping memo or source-audit appendix
do not change planner behavior
do not modify GUI
do not modify master CSV
```

This is a documentation / audit request.

---

## 24. Relationship to Future Implementation

After this map is verified, the next implementation flow can be:

```text
MasterLoadResult contract
  ↓
WomRuntimeModel contract
  ↓
FullPlanResult contract
  ↓
Visualization Dataset Adapter
  ↓
Run Full Plan Graph Panel
```

This is safer than connecting GUI directly to internal planner objects.

---

## 25. Acceptance Criteria for This Design

This memo is useful if it clarifies:

```text
which master categories exist
where master data should enter the Top Routine
how master data becomes runtime model data
where demand lots are attached
where capacity should be indexed
where cost / price / tariff should be evaluated
why visualization should consume flat datasets
which parts are current and which need source audit
```

This memo is not a final implementation specification.

It is the first wiring map.

---

## 26. Completion Summary

WOM master data should flow as:

```text
Scenario Root
  ↓
Master Loaders
  ↓
MasterLoadResult
  ↓
Runtime Model Builder
  ↓
WomRuntimeModel
  ↓
Planning / Evaluation
  ↓
Visualization Dataset Adapter
  ↓
GUI / CSV / pandas / SQL / BI
```

The key design rule is:

```text
Do not let GUI and reports depend directly on raw master CSVs or deep planner internals.
```

The immediate next step is to audit the source code and confirm the actual current loader and runtime setting paths.

That audit will turn this design map into an accurate implementation map.
