# Codex Request: WOM Master Data Loading and Runtime Model Map Source Audit

**Version:** v0r1  
**Date:** 2026-06-03  
**Status:** Codex source-audit request  
**Target path:** `docs/codex_requests/wom_master_data_loading_and_runtime_model_map_source_audit_request.md`

**Parent design doc:**

```text
docs/design/wom_master_data_loading_and_runtime_model_map.md
```

**Preceding design doc:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

**Request type:** Source-code audit / documentation update  
**Important:** This request is primarily for inspection and documentation. Do not change planner behavior.

---

## 1. Request Summary

Please perform a source-code audit of the current WOM repository to verify how master data CSV files are loaded and where their values are set in the runtime model.

The parent design memo defines the intended high-level flow:

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

This request should inspect the actual current source code and produce a source-audit appendix / updated documentation that maps:

```text
CSV file
  ↓
loader function / module
  ↓
intermediate row object / dict
  ↓
runtime object / attribute
  ↓
planner / evaluator / visualization usage
```

The goal is to turn the conceptual master data map into an implementation-grounded wiring map.

---

## 2. Why This Audit Is Needed

The current WOM codebase has accumulated several implementation generations:

```text
legacy v0r8 CSV-based WOM logic
current Japanese Rice vertical slices
capacity diagnostic and runtime attachment modules
management cockpit / cash-flow visualization code
cost / money evaluation experiments
pipeline / plugin related utilities
```

Before connecting `Run Full Plan` to the graph panel, cost evaluation, tariff simulation, and rule-based planning, we need to understand the real current source-code wiring.

This is especially important for:

```text
capacity master
cost master
price / offering price master
tariff master
runtime plan node setting
psi4demand / psi4supply buckets
visualization dataset generation
```

---

## 3. Scope

### 3.1 In scope

Please inspect and document:

```text
scenario root discovery
master CSV file names
master CSV directories
network / node / edge master loading
demand master loading
demand lot generation
capacity master loading
capacity runtime attachment
cost master loading
price / offering price loading
tariff master status
product / SKU master status
calendar / week master status
lane / logistics master status
runtime model instantiation
ProductPlanNode setting
Node / legacy Node setting
psi4demand / psi4supply bucket setting
cash-flow / money visualization data sources
visualization dataset helpers
```

### 3.2 Out of scope

Do not implement new planner behavior.

Do not modify GUI layout.

Do not modify scenario master CSV files.

Do not remove or modify NetworkX.

Do not refactor large modules.

Do not implement tariff simulation in this request.

Do not implement Run Full Plan graph adapter in this request.

This is a source audit and documentation request.

---

## 4. Expected Output File

Please add a new source-audit memo:

```text
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
```

This file should be a companion to:

```text
docs/design/wom_master_data_loading_and_runtime_model_map.md
```

It should record what is actually found in the current source code.

Do not overwrite the parent design memo unless a very small correction is clearly necessary.

Preferred output:

```text
new source-audit memo only
```

---

## 5. Recommended Search Areas

Please inspect at least these directories and files where present:

```text
pysi/
pysi/network/
pysi/demand/
pysi/capacity/
pysi/plan/
pysi/runners/
pysi/gui/
pysi/reporting/
pysi/master_data/
examples/scenarios/
tests/
docs/design/
docs/codex_requests/
```

Search for terms such as:

```text
load_
read_csv
csv
master
capacity
weekly_capability
cost
money
cash
tariff
offering
price
node_master
product_tree
sku
demand
lot
psi4demand
psi4supply
ProductPlanNode
Node
runtime_attachment
scenario_root
```

---

## 6. Required Audit Sections

The audit memo should include the following sections.

### 6.1 Executive Summary

Summarize:

```text
which master categories are clearly implemented
which are partially implemented
which are missing or not yet connected
which source files are central
which findings are important for the next Run Full Plan graph adapter design
```

### 6.2 Master File Inventory

Create a table:

```text
Category | File path / pattern | Example scenario | Status | Notes
```

Categories:

```text
scenario config
network / node / edge
demand
capacity
cost
price / offering price
tariff
product / SKU
calendar / week
lane / logistics
```

Status values should be:

```text
implemented
partial
legacy
diagnostic-only
not found
unclear
```

### 6.3 Loader Function Inventory

Create a table:

```text
Category | Module | Function / class | Input | Output | Status | Notes
```

Please include exact module and function/class names where found.

Examples to verify:

```text
pysi/network/network_master_loader.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/capacity/capacity_weekly_rows_source.py
pysi/plan/plan_node_tree_instantiation.py
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Also inspect legacy and reporting modules.

### 6.4 Runtime Setting Map

Create a table:

```text
Source | Loader output | Runtime object | Attribute / index | Set by | Used by | Notes
```

Important targets:

```text
ProductPlanNode.parent
ProductPlanNode.children
ProductPlanNode.partner_key
ProductPlanNode.node_character
ProductPlanNode.psi4demand[week][0]
ProductPlanNode.psi4supply
DemandAnchoredLot.lot_id
capacity rows / env.weekly_capability
node.nx_capacity
cost index / money rows
price assumptions
tariff assumptions
visualization datasets
```

### 6.5 Japanese Rice Current Path

Document the actual current Japanese Rice path from source code:

```text
scenario root
  ↓
network master load
  ↓
ProductPlanNode tree
  ↓
demand master load
  ↓
DemandAnchoredLot generation
  ↓
MARKET_TOKYO.psi4demand[week][0]
  ↓
capacity master load
  ↓
DC_KANTO capacity gate
  ↓
runner output contract
  ↓
GUI model
  ↓
chart dataset
  ↓
chart view
  ↓
scenario variation
```

For each step, include exact source file and function names.

### 6.6 Capacity Master Audit

This section is especially important.

Please document:

```text
where capacity master CSV rows are loaded
what columns are expected
how rows are normalized
where capacity is attached at runtime
whether env.weekly_capability is used
whether ProductPlanNode stores capacity directly
whether legacy Node.nx_capacity is used
what precedence rules exist
which tests assert capacity behavior
```

Please explicitly audit these known/possible concepts:

```text
load_capacity_weekly_rows_to_env
runtime_attachment_applied
input_row_count
weekly_capability[product][mom_name]
weekly_capability[mom_name]
mom.nx_capacity
capacity gate accepted / blocked
```

If any of these are not found or only exist in a specific module, say so.

### 6.7 Cost / Money / Cash Flow Audit

Please document:

```text
which cost master files exist
which cost loader functions exist
which cost rows / dicts are created
where money / cash-flow data is calculated
how current cockpit / reporting code obtains cost or money values
whether cost master is connected to Japanese Rice
whether cost master is connected to Run Full Plan
whether cost is still legacy / experimental / partial
```

Search likely areas:

```text
pysi/reporting/
pysi/gui/
pysi/master_data/
pysi/plan/
tests/
```

Include exact source references.

### 6.8 Price / Offering Price Audit

Please document:

```text
whether offering price files exist
where they are loaded
how price is used for revenue / margin / money evaluation
whether price is scenario-specific
whether price is connected to current GUI / reporting outputs
```

### 6.9 Tariff Audit

Please document:

```text
whether tariff master files exist
whether tariff loader exists
whether tariff is used in any current calculation
whether tariff is only data / placeholder / not connected
which tests mention tariff
what is missing for future tariff cost simulation
```

Do not implement tariff logic.

Just audit.

### 6.10 Visualization Dataset Audit

Please document:

```text
which current helpers build chart datasets
which current helpers build GUI models
which current reporting modules export flat datasets
which GUI modules read runner output directly
which GUI modules already use adapter-like patterns
```

Include Japanese Rice helpers such as:

```text
extract_japanese_rice_first_runner_gui_model
build_japanese_rice_capacity_gate_chart_dataset
build_japanese_rice_capacity_gate_chart_series
build_capacity_override_chart_dataset
build_capacity_gate_scenario_comparison
```

Also inspect cash-flow visualization and management cockpit code for similar adapter patterns.

### 6.11 Test Coverage Map

Create a table:

```text
Area | Test file | What it verifies | Gaps
```

Include at least:

```text
Japanese Rice network master tests
Japanese Rice demand master tests
Japanese Rice capacity master tests
plan node tree instantiation tests
first PSI runner tests
capacity constrained first flow tests
chart dataset / chart view / scenario variation tests
capacity runtime attachment tests
cost / money / reporting tests if found
tariff-related tests if found
```

### 6.12 Gaps and Risks

List gaps such as:

```text
cost master not fully mapped
tariff not connected
multiple capacity representations
legacy Node vs ProductPlanNode ambiguity
GUI modules reading runner-specific output
lack of unified MasterLoadResult
lack of unified WomRuntimeModel
lack of unified FullPlanResult
```

Be specific and grounded in source findings.

### 6.13 Recommended Next Design Actions

Recommend the next design / implementation requests.

Likely candidates:

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_full_plan_result_contract.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
docs/design/wom_tariff_cost_simulation_model_vertical_slice.md
```

Explain which should come next based on the audit.

---

## 7. Evidence Requirements

For each important finding, include:

```text
file path
function / class name
short explanation of what it does
status
```

Example style:

```text
pysi/plan/plan_node_tree_instantiation.py
  - ProductPlanNode
  - instantiate_product_plan_node_trees(...)
  - sets parent/children and psi4demand buckets for product-specific runtime nodes
  - status: implemented for Japanese Rice vertical slice
```

Do not make broad claims without pointing to source files.

---

## 8. Safety Rules

Do not change planner behavior.

Do not change GUI behavior.

Do not change scenario master CSV files.

Do not refactor source code.

Do not delete or rename modules.

Do not remove NetworkX.

Do not modify large implementation files unless absolutely necessary for documentation import checks.

Preferred changed file:

```text
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
```

Optional minor changed file:

```text
docs/design/wom_master_data_loading_and_runtime_model_map.md
```

Only if a small cross-reference is useful.

No production Python changes are expected.

---

## 9. Optional Verification Commands

Since this is a documentation / audit request, full pytest may not be necessary, but please run at least:

```bat
git diff --check
```

If a markdown checker is available, run it.

If no markdown checker exists, that is fine.

Do not run expensive or unrelated test suites unless you changed code unexpectedly.

If any Python code is changed unexpectedly, stop and explain why.

---

## 10. Acceptance Criteria

This request is complete when:

```text
source-audit memo is added at docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
audit includes master file inventory
audit includes loader function inventory
audit includes runtime setting map
audit includes Japanese Rice current path with exact source files/functions
audit includes capacity master audit
audit includes cost / money / cash-flow audit
audit includes price / offering price audit
audit includes tariff audit
audit includes visualization dataset audit
audit includes test coverage map
audit includes gaps and risks
audit includes recommended next design actions
no planner behavior is changed
no GUI behavior is changed
no scenario master CSV files are changed
NetworkX is untouched
git diff --check passes
```

---

## 11. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
What source-audit file was added?
Which master categories are clearly implemented?
Which master categories are partial or missing?
Which source files are central to network loading?
Which source files are central to demand loading?
Which source files are central to capacity loading?
Where are ProductPlanNode and psi4demand set?
Where is capacity attached or evaluated?
What did you find about cost / money / cash-flow handling?
What did you find about price / offering price handling?
What did you find about tariff handling?
What did you find about visualization dataset adapters?
What tests or checks did you run?
Did you change planner behavior?
Did you change GUI behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
What are the recommended next design actions?
```

---

## 12. Development Meaning

Before this request:

```text
WOM has a conceptual master data loading map.
```

After this request:

```text
WOM has a source-code-grounded master data loading map.
```

This is necessary before building:

```text
Run Full Plan result contract
Graph Panel Adapter
Cost / Tariff Simulation
Rule Based Planning System
```

In simple terms:

```text
The design map says where the cables should go.
This source audit confirms where the cables actually go today.
```
