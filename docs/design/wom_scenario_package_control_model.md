# WOM Scenario Package and Control Model

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_scenario_package_control_model.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the design direction for WOM Scenario Package and Scenario Control Model.

The purpose is to clarify that WOM should not become a collection of case-specific runners.

Instead, WOM should be presented and implemented as a generic scenario-based weekly PSI planning platform.

The target execution style is:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/iphone_case/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/tesla/as_is.yaml
```

This means:

```text
same runner
same WOM engine
same PSI planning framework
same Management Cockpit
different scenario packages
```

The public demo should therefore demonstrate WOM genericity by switching scenario packages, not by introducing case-specific execution logic.

---

## 2. Core Principle

The core principle is:

```text
A case is not a custom program.
A case is a scenario package.
```

Japanese Rice, iPhone, Tesla, vaccine distribution, or any other supply chain case should be represented as data and policies loaded by the generic WOM runner.

Therefore:

```text
WOM Engine:
    generic

WOM Runner:
    generic

Scenario Package:
    case-specific

Master Data:
    case-specific but schema-generic

Control Model:
    case-specific but schema-generic
```

A public demo should make this visible.

The important message is:

```text
WOM can model multiple supply chains by changing scenario package definitions.
```

---

## 3. What This Memo Corrects

A previous possible direction was:

```bat
python -m pysi.runners.run_japanese_rice_case_smoke
```

as a convenience entry point for the Japanese Rice Case.

This memo does not completely prohibit such a shortcut, but it repositions it as non-essential.

For public demo and architectural clarity, the preferred direction is:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

A case-specific runner may hide the true value of WOM.

A generic scenario runner demonstrates the true value of WOM.

---

## 4. Public Demo Concept

The public demo should show at least one scenario package, and ideally multiple scenario packages.

Candidate cases:

```text
1. Japanese Rice Case
2. iPhone Case
3. Tesla Case
```

The public demo message should be:

```text
WOM is not a rice simulator.
WOM is not an iPhone simulator.
WOM is not an EV simulator.
WOM is a weekly PSI scenario modeling platform.
```

The common demo pattern should be:

```text
run_wom_scenario
    ↓
load scenario package
    ↓
load network / demand / capacity / money / control policies
    ↓
run generic PSI planning
    ↓
evaluate quantity and money
    ↓
show Management Cockpit and diagnostics
```

---

## 5. Scenario Package Concept

A Scenario Package is the complete set of definitions needed to run one WOM planning scenario.

Recommended directory shape:

```text
scenarios/
  japanese_rice/
    as_is.yaml
    masters/
      node_master.csv
      edge_master.csv
      product_master.csv
      demand_plan.csv
      money_master.csv
      capacity_resource_master.csv
      capacity_calendar.csv
      product_capacity_consumption.csv
      capacity_policy.csv
    policies/
      demand_supply_balance_policy.yaml
      demand_variability_policy.yaml
      buffer_policy.yaml
      capacity_flex_policy.yaml
      early_build_policy.yaml
      allocation_policy.yaml

  iphone_case/
    as_is.yaml
    masters/
      ...
    policies/
      ...

  tesla/
    as_is.yaml
    masters/
      ...
    policies/
      ...
```

The exact folder structure may evolve, but the architectural point is fixed:

```text
scenario package = master data + control policies + run metadata
```

---

## 6. Generic Scenario Runner

The generic runner should be:

```text
pysi.runners.run_wom_scenario
```

Target command:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

The runner should:

```text
1. Load scenario yaml
2. Resolve relative paths
3. Load generic WOM master data
4. Load capacity master data
5. Load scenario control policies
6. Build WOMPlanningContext
7. Run generic PSI planning pipeline
8. Run money evaluation if enabled
9. Run diagnostics if enabled
10. Export outputs
11. Optionally open or refresh GUI / cockpit
```

The runner should not contain Japanese Rice specific logic.

The runner should not contain iPhone specific logic.

The runner should not contain Tesla specific logic.

All case specificity should come from the scenario package.

---

## 7. Scenario YAML Contract

A scenario yaml should describe the scenario package at a high level.

Conceptual example:

```yaml
scenario:
  scenario_id: RICE_AS_IS
  case_id: japanese_rice
  title: Japanese Rice Supply Chain As-Is
  description: Weekly PSI scenario package for Japanese rice distribution.
  planning_start_week: 2027-W40
  planning_horizon_weeks: 52
  week_domain: business_week_label

runner:
  engine_profile: generic_weekly_psi
  enable_capacity: true
  enable_money: true
  enable_management_cockpit: true
  enable_diagnostics: true

masters:
  node_master: masters/node_master.csv
  edge_master: masters/edge_master.csv
  product_master: masters/product_master.csv
  demand_plan: masters/demand_plan.csv
  money_master: masters/money_master.csv
  capacity_resource_master: masters/capacity_resource_master.csv
  capacity_calendar: masters/capacity_calendar.csv
  product_capacity_consumption: masters/product_capacity_consumption.csv
  capacity_policy: masters/capacity_policy.csv

policies:
  demand_supply_balance: policies/demand_supply_balance_policy.yaml
  demand_variability: policies/demand_variability_policy.yaml
  buffer: policies/buffer_policy.yaml
  capacity_flex: policies/capacity_flex_policy.yaml
  early_build: policies/early_build_policy.yaml
  allocation: policies/allocation_policy.yaml

outputs:
  output_dir: outputs/scenarios/japanese_rice/as_is
```

This yaml is not meant to be final syntax yet.

It is a scenario package contract candidate.

---

## 8. Scenario Control Model

The Scenario Control Model defines how WOM should absorb demand and supply variability.

This is the upper-level model above raw node / edge / PSI / capacity data.

It answers questions such as:

```text
How should total demand and total supply be balanced?
How should demand variability be represented?
Where should buffer inventory absorb variability?
How flexible is production capacity?
How much early build is allowed?
How should scarce supply be allocated?
```

The Scenario Control Model should include:

```text
1. Demand-Supply Balance Policy
2. Demand Variability Policy
3. Buffer Policy
4. Capacity Flex Policy
5. Early Build Policy
6. Allocation Policy
```

These policies should be scenario-specific but schema-generic.

---

## 9. Demand-Supply Balance Policy

This policy defines how WOM compares and balances total demand and total supply.

It should answer:

```text
Is the scenario demand-anchored or supply-anchored?
At what level is demand/supply balance evaluated?
How are shortages handled?
How are surpluses handled?
Which demand classes are prioritized?
```

Conceptual example:

```yaml
demand_supply_balance_policy:
  planning_mode: demand_anchored
  balance_level: total_network
  shortage_handling: backlog_or_lost_sales
  surplus_handling: inventory_buffer
  priority:
    - committed_demand
    - forecast_demand
    - strategic_stock
```

Candidate values:

```text
planning_mode:
    demand_anchored
    supply_anchored
    balanced_reconciliation

balance_level:
    total_network
    region
    product
    node
    product_region

shortage_handling:
    backlog
    lost_sales
    allocation_cut
    service_risk_warning

surplus_handling:
    inventory_buffer
    production_slowdown
    reallocation
    disposal_or_discount
```

---

## 10. Demand Variability Policy

This policy defines the nature of demand variability in the scenario.

Different cases have different demand behavior.

Examples:

```text
Japanese Rice:
    relatively stable demand
    seasonal behavior
    crop-year and regional characteristics

iPhone:
    new product launch peak
    region allocation
    promotional wave
    product lifecycle

Tesla:
    order volatility
    production ramp-up
    regional delivery waves
    capacity-constrained fulfillment
```

Conceptual example:

```yaml
demand_variability_policy:
  pattern: seasonal_stable
  volatility_level: low
  demand_signal_type: forecast_plus_committed
  shock_scenarios:
    - name: demand_spike
      week: 2027-W42
      multiplier: 1.2
```

Candidate values:

```text
pattern:
    stable
    seasonal_stable
    launch_peak
    ramp_up
    promotion_wave
    disruption_shock

volatility_level:
    low
    medium
    high

demand_signal_type:
    committed_order
    forecast
    forecast_plus_committed
    market_scenario
```

---

## 11. Buffer Policy

This policy defines where and how inventory buffers absorb demand/supply variability.

It should answer:

```text
Which nodes can hold buffer inventory?
How many weeks of buffer should be targeted?
Is overflow allowed?
How should buffer inventory be consumed?
```

Conceptual example:

```yaml
buffer_policy:
  buffer_nodes:
    - WH_TOKYO
    - REGIONAL_DC_EAST
  target_buffer_weeks: 2
  buffer_absorption_mode: inventory_first
  overflow_policy: warning
```

Candidate values:

```text
buffer_absorption_mode:
    inventory_first
    capacity_first
    balanced
    market_priority

overflow_policy:
    warning
    hard_limit
    emergency_storage
    reallocation
```

---

## 12. Capacity Flex Policy

This policy defines how flexible capacity is.

It should answer:

```text
Is capacity a hard constraint or soft constraint?
Is overtime allowed?
Is outsourcing allowed?
What is the cost penalty for capacity flex?
How much temporary capacity can be added?
```

Conceptual example:

```yaml
capacity_flex_policy:
  default_mode: hard
  allowed_flex:
    MILL_EAST:
      capacity_type: P
      max_overtime_ratio: 0.2
      flex_cost_multiplier: 1.5
```

Candidate values:

```text
default_mode:
    hard
    soft
    flex_with_penalty

flex_type:
    overtime
    outsourcing
    subcontracting
    temporary_shift
    no_flex
```

This policy should not replace the capacity master.

It controls how the capacity master is interpreted.

---

## 13. Early Build Policy

This policy defines whether WOM can build supply before the actual demand week.

It should answer:

```text
Is early build allowed?
How many weeks early?
At which nodes?
What inventory cost or obsolescence penalty applies?
```

Conceptual example:

```yaml
early_build_policy:
  enabled: true
  max_early_build_weeks: 4
  allowed_nodes:
    - MILL_EAST
    - FACTORY_ASIA
  inventory_cost_penalty: medium
```

Candidate values:

```text
enabled:
    true
    false

inventory_cost_penalty:
    low
    medium
    high

obsolescence_risk:
    none
    low
    medium
    high
```

This is especially important for launch products, seasonal demand, and capacity-constrained supply chains.

---

## 14. Allocation Policy

This policy defines how scarce supply is allocated.

It should answer:

```text
Which markets or customers receive priority?
Is allocation based on demand due week, margin, strategic importance, or fairness?
How are ties resolved?
```

Conceptual example:

```yaml
allocation_policy:
  rule: priority_by_market
  priority_markets:
    - JP
    - US
    - EU
  tie_breaker: margin_priority
```

Candidate values:

```text
rule:
    first_due_first_served
    priority_by_market
    priority_by_customer
    margin_priority
    service_level_priority
    proportional_allocation

tie_breaker:
    due_week
    margin_priority
    strategic_priority
    equal_split
```

---

## 15. Capacity Master Generic Definition

Capacity should be defined as generic master data, not as case-specific code.

Recommended minimum capacity master set:

```text
capacity_resource_master.csv
capacity_calendar.csv
product_capacity_consumption.csv
capacity_policy.csv
scenario_capacity_override.csv
```

The minimum public demo may omit `scenario_capacity_override.csv`, but the model should allow it.

---

## 16. Capacity Resource Master

Defines physical or logical capacity resources.

Example:

```csv
resource_id,node_id,capacity_type,resource_name,unit,base_capacity,active
MILL_EAST_P,MILL_EAST,P,East mill processing capacity,lot,100,1
MILL_EAST_I,MILL_EAST,I,East mill storage capacity,lot,500,1
WH_TOKYO_S,WH_TOKYO,S,Tokyo warehouse shipping capacity,lot,80,1
```

Recommended fields:

```text
resource_id
node_id
capacity_type
resource_name
unit
base_capacity
active
```

Recommended capacity types:

```text
P = production / processing / purchase capacity
S = shipment / sales / outbound capacity
I = inventory / storage capacity
```

---

## 17. Capacity Calendar

Defines weekly available capacity by resource.

Example:

```csv
scenario_id,resource_id,week,available_capacity,unit,source,note
RICE_AS_IS,MILL_EAST_P,2027-W40,5,lot,rice_case,weekly milling capacity
RICE_AS_IS,MILL_EAST_P,2027-W41,6,lot,rice_case,weekly milling capacity
```

Recommended fields:

```text
scenario_id
resource_id
week
available_capacity
unit
source
note
```

Important rule:

```text
Master data should use business week labels such as 2027-W40.
Engine internals may use integer week indexes.
A week-domain adapter should map between them.
```

---

## 18. Product Capacity Consumption

Defines how much capacity one lot consumes.

Example:

```csv
product_id,node_id,capacity_type,resource_id,capacity_per_lot,unit
PACKAGED_RICE_STANDARD,MILL_EAST,P,MILL_EAST_P,1,lot
PACKAGED_RICE_STANDARD,WH_TOKYO,S,WH_TOKYO_S,1,lot
```

Recommended fields:

```text
product_id
node_id
capacity_type
resource_id
capacity_per_lot
unit
```

MVP assumption:

```text
1 lot consumes 1 capacity lot
```

Future extension:

```text
kg
ton
pallet
case
machine_hour
labor_hour
line_hour
```

---

## 19. Capacity Policy Master

Defines hard/soft interpretation of capacity.

Example:

```csv
scenario_id,node_id,capacity_type,policy,severity,allocation_rule
RICE_AS_IS,MILL_EAST,P,hard,blocked,priority_by_due_week
RICE_AS_IS,WH_TOKYO,I,soft,warning,allow_overflow
```

Recommended fields:

```text
scenario_id
node_id
capacity_type
policy
severity
allocation_rule
```

Candidate policies:

```text
hard
soft
flex_with_penalty
unlimited_for_demo
```

---

## 20. Scenario Capacity Override

Defines scenario-specific changes to base capacity.

Example:

```csv
scenario_id,resource_id,week,override_capacity,reason
RICE_TO_BE,MILL_EAST_P,2027-W40,8,new milling shift
RICE_DISRUPTION,MILL_EAST_P,2027-W40,2,machine_failure
```

This enables scenario planning:

```text
As-Is
To-Be
Disruption
Recovery
Expansion
```

---

## 21. Week Domain Contract

WOM should distinguish:

```text
business week label:
    2027-W40

engine week index:
    0, 1, 2
```

Recommended contract:

```text
scenario package / master data / reporting:
    use business week labels

planning engine internal arrays:
    may use integer index

adapter:
    converts business week label to integer index and back
```

This prevents user-facing master data from becoming engine-internal and unreadable.

It also preserves engine efficiency.

---

## 22. Forward Capacity Shape Contract

Current diagnostic has identified a shape mismatch:

```text
producer:
    product -> node -> capacity_type -> week_label -> capacity_lots

current consumer expectation:
    product -> node -> capacity_type -> list[index] -> capacity_lots
```

This memo does not decide the final fix.

Candidate fixes:

```text
A. Convert week-label map to list-indexed capacity before engine execution.
B. Revise forward capacity consumer to accept week-label maps.
C. Support both with explicit shape_version and adapter.
```

Recommended direction:

```text
Keep master data and scenario context label-week based.
Use adapter at the planning engine boundary.
Preserve diagnostics that report shape version and effective applicability.
```

---

## 23. Scenario Package Examples

### 23.1 Japanese Rice Case

Public message:

```text
Stable seasonal demand, regional distribution, milling capacity, inventory buffer.
```

Key control model characteristics:

```text
demand pattern:
    seasonal_stable

capacity:
    milling capacity at MILL_EAST

buffer:
    warehouse / regional inventory buffer

planning issue:
    crop-year / seasonal supply-demand balance
```

Command:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

---

### 23.2 iPhone Case

Public message:

```text
Global new-product launch, assembly capacity, regional allocation, sales peak.
```

Key control model characteristics:

```text
demand pattern:
    launch_peak

capacity:
    final assembly / logistics capacity

buffer:
    pre-launch inventory buffer

planning issue:
    launch-week supply allocation and service risk
```

Command:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/iphone_case/as_is.yaml
```

---

### 23.3 Tesla Case

Public message:

```text
Production ramp-up, regional delivery waves, capacity-constrained fulfillment.
```

Key control model characteristics:

```text
demand pattern:
    ramp_up / order volatility

capacity:
    factory output / shipping / delivery capacity

buffer:
    finished vehicle inventory or in-transit buffer

planning issue:
    production ramp and regional delivery allocation
```

Command:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/tesla/as_is.yaml
```

---

## 24. Public Demo Strategy

The public demo should show that the same runner can execute different supply chain scenarios.

Recommended note article structure:

```text
1. WOM is a scenario-based weekly PSI planning platform.
2. A scenario package defines network, demand, capacity, money, and control policies.
3. The same runner executes multiple cases.
4. Japanese Rice demonstrates stable seasonal supply chain planning.
5. iPhone demonstrates launch peak and global allocation.
6. Tesla demonstrates ramp-up and capacity constrained fulfillment.
7. WOM Management Cockpit shows quantity, money, issues, and diagnostics.
```

This is more powerful than presenting only one dedicated Japanese Rice demo.

---

## 25. Relationship to Existing Capacity Diagnostics

The recently added Capacity Scenario Alignment Diagnostic is directly relevant.

It already detects:

```text
selected product mismatch
node mismatch
week-domain mismatch
forward capacity shape mismatch
backward capability product mismatch
```

Those diagnostics are signs that WOM needs a clearer scenario package contract.

This memo defines that upper-level contract.

The diagnostic should remain even after adapters are implemented.

Future diagnostics should explain:

```text
scenario package loaded
capacity master loaded
week-domain adapter applied
forward capacity shape converted
capacity effectively applied
```

---

## 26. Safety Boundaries

This memo is a design memo only.

It does not request immediate implementation.

When implemented, the following safety boundaries should apply:

```text
do not hard-code Japanese Rice logic into WOM engine
do not hard-code iPhone logic into WOM engine
do not hard-code Tesla logic into WOM engine
do not replace generic master loading with case-specific code
do not hide scenario mismatch by silent conversion
do not remove diagnostic visibility
```

---

## 27. Recommended Development Phases

### Phase S1: Scenario Package Design

Create scenario package schema and minimal yaml loader design.

Target:

```text
docs/design/wom_scenario_package_loader.md
```

### Phase S2: Generic Scenario Runner

Implement or define:

```text
pysi.runners.run_wom_scenario
```

Target command:

```bat
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
```

### Phase S3: Capacity Master Generic Adapter

Define and implement adapters from generic capacity masters to current runtime capacity context.

Inputs:

```text
capacity_resource_master.csv
capacity_calendar.csv
product_capacity_consumption.csv
capacity_policy.csv
```

Outputs:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

### Phase S4: Week Domain Adapter

Define conversion:

```text
business week label -> engine week index
engine week index -> business week label
```

### Phase S5: Public Demo Scenario Packages

Prepare:

```text
scenarios/japanese_rice/as_is.yaml
scenarios/iphone_case/as_is.yaml
scenarios/tesla/as_is.yaml
```

At least Japanese Rice should be complete enough for first publication.

### Phase S6: Management Cockpit Scenario Identity

Make cockpit show:

```text
scenario_id
case_id
selected product
week domain
capacity shape version
diagnostic status
```

---

## 28. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_scenario_package_loader.md
```

or, if capacity should be prioritized first:

```text
docs/design/wom_capacity_master_generic_schema.md
```

Decision point:

```text
Should WOM first define the scenario package loader,
or should it first define generic capacity master schema?
```

Recommended order:

```text
1. Scenario package control model
2. Generic capacity master schema
3. Scenario package loader
4. run_wom_scenario runner
5. Japanese Rice public scenario package
```

---

## 29. Summary

This memo defines WOM as a generic scenario package driven planning platform.

The key design decision is:

```text
Do not build case-specific runners as the primary demo path.
Build a generic run_wom_scenario runner and switch scenario packages.
```

The public demo should show:

```text
python -m pysi.runners.run_wom_scenario --scenario scenarios/japanese_rice/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/iphone_case/as_is.yaml
python -m pysi.runners.run_wom_scenario --scenario scenarios/tesla/as_is.yaml
```

This demonstrates WOM's genericity.

The necessary upper-level model is the Scenario Control Model:

```text
Demand-Supply Balance
Demand Variability
Buffer Policy
Capacity Flex
Early Build
Allocation Policy
```

The necessary master data extension is generic capacity master definition:

```text
Capacity Resource Master
Capacity Calendar
Product Capacity Consumption
Capacity Policy
Scenario Capacity Override
```

In short:

```text
WOM should not be a collection of case programs.
WOM should be a generic weekly PSI planning platform whose worlds are switched by scenario packages.
```
