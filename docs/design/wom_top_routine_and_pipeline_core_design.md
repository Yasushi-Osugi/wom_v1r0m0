# WOM Top Routine and Pipeline Core Design

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/wom_top_routine_and_pipeline_core_design.md`

**Strategic role:** Define the orchestration backbone of WOM before full GUI / cost / tariff / AI integration  
**Primary scope:** WOM Top Routine, Pipeline Core, Plugin Hooks, FullPlanResult, and future adapter positions  
**Current north star:** Management-visible simulation before recommendation AI  
**Development principle:** Thin orchestration, typed handoff contracts, flat visualization datasets, human-safe extensibility

---

## 1. Purpose

This memo defines the position and responsibility of the WOM Top Routine and Pipeline Core.

Recent Japanese Rice vertical slices proved that WOM can move step by step from:

```text
master data
  ↓
ProductPlanNode
  ↓
DemandAnchoredLot
  ↓
capacity gate
  ↓
runner output contract
  ↓
GUI table
  ↓
chart dataset
  ↓
chart view
  ↓
scenario variation
  ↓
scrollable GUI layout
```

The next major step is to connect these vertical slices to the real WOM Run Full Plan flow.

Before doing that, the orchestration layer must be clarified.

This memo therefore defines:

```text
what the WOM Top Routine is
what the Pipeline Core owns
where Plugin Hooks are placed
what FullPlanResult should mean
where visualization adapters are called
where future cost / tariff / rule-based / AI-assisted planning connects
```

The purpose is not to implement all of these immediately.

The purpose is to draw the execution backbone.

---

## 2. Basic Definition

The WOM Top Routine is the orchestration layer that connects the major WOM functions.

It is not the PSI engine.

It is not the GUI.

It is not the costing model.

It is not the rule-based planning system.

It is the execution controller that decides:

```text
what to load
what to instantiate
what to run
which plugins to call
what to evaluate
what datasets to generate
what outputs to export
what result object to return
```

In simple terms:

```text
WOM Top Routine = execution control tower
```

The Pipeline Core is the reusable implementation of that control tower.

The Plugin System is the extension mechanism around that control tower.

---

## 3. Why This Design Is Needed Now

The Japanese Rice Case now has a working smoke GUI.

However, the smoke GUI is still an independent vertical slice.

It currently consumes a diagnostic runner output.

To connect it to WOM本体, we need a stable flow:

```text
Run Full Plan
  ↓
FullPlanResult
  ↓
Visualization Adapter
  ↓
Flat Dataset
  ↓
Graph Panel / GUI / BI / CSV / SQL
```

Without a clear Top Routine, GUI and reporting code may start reading planner internals directly.

That should be avoided.

The correct structure is:

```text
Planner internals
  ↓
typed result / adapter
  ↓
flat visualization dataset
  ↓
GUI / report / BI
```

This prevents the GUI from becoming tightly coupled to `Node`, `psi4demand`, `psi4supply`, or internal lot structures.

---

## 4. Design Principle

The Top Routine should be:

```text
thin
explicit
testable
plugin-friendly
result-contract-driven
```

It should not become a large monolithic function.

### 4.1 Top Routine should do

```text
read config
call loaders
call runtime model builder
call planner
call evaluators
call visualization adapters
call exporters
collect diagnostics
return FullPlanResult
```

### 4.2 Top Routine should not do

```text
parse every CSV column directly
implement PSI logic directly
implement capacity allocation directly
implement tariff calculation directly
draw GUI widgets directly
hard-code scenario-specific graph logic
modify master data without explicit action contract
```

A good Top Routine is a traffic controller.

A bad Top Routine is a kitchen sink.

---

## 5. Overall Execution Flow

Recommended high-level flow:

```text
run_wom_pipeline(config)
  ↓
load scenario config
  ↓
run before_load plugins
  ↓
load master data
  ↓
run after_load plugins
  ↓
instantiate runtime WOM model
  ↓
run before_plan plugins
  ↓
run PSI planning engine
  ↓
run after_plan plugins
  ↓
run cost / tariff / money evaluation
  ↓
run after_evaluation plugins
  ↓
generate visualization flat datasets
  ↓
run after_visualization plugins
  ↓
export outputs
  ↓
return FullPlanResult
```

This is the baseline orchestration model.

---

## 6. Proposed Top Routine Skeleton

Conceptual Python shape:

```python
def run_wom_pipeline(config: WomRunConfig) -> FullPlanResult:
    ctx = WomPipelineContext(config=config)

    run_plugins("before_load", ctx)

    master_load_result = load_master_data(config)
    ctx.master_load_result = master_load_result

    run_plugins("after_load", ctx)

    runtime_model = instantiate_runtime_model(master_load_result, config)
    ctx.runtime_model = runtime_model

    run_plugins("before_plan", ctx)

    psi_result = run_psi_planning_engine(runtime_model, config)
    ctx.psi_result = psi_result

    run_plugins("after_plan", ctx)

    evaluation_result = run_evaluation(runtime_model, psi_result, config)
    ctx.evaluation_result = evaluation_result

    run_plugins("after_evaluation", ctx)

    visualization_datasets = build_visualization_datasets(ctx)
    ctx.visualization_datasets = visualization_datasets

    run_plugins("after_visualization", ctx)

    output_paths = export_outputs(ctx)
    ctx.output_paths = output_paths

    return FullPlanResult.from_context(ctx)
```

This is not final implementation code.

It is the target shape.

---

## 7. Pipeline Context

The Pipeline Context is the shared runtime object passed between stages and plugins.

Recommended conceptual fields:

```text
WomPipelineContext
  config
  scenario_id
  scenario_root
  run_id
  master_load_result
  runtime_model
  psi_result
  capacity_result
  cost_result
  tariff_result
  money_result
  visualization_datasets
  output_paths
  diagnostics
  warnings
  action_todos
```

The context should be explicit.

It should not be a mysterious global variable.

Plugins should receive this context and either:

```text
read it
append diagnostics
append output datasets
append action TODOs
```

If a plugin mutates planning parameters, it should do so through explicit action contracts or well-defined hook semantics.

---

## 8. FullPlanResult Contract

The Top Routine should return a stable `FullPlanResult`.

This is the most important handoff contract for:

```text
GUI
reporting
BI export
scenario comparison
rule-based planning
AI-assisted diagnosis
completion memo generation
```

Recommended conceptual structure:

```text
FullPlanResult
  contract_version
  run_id
  scenario_id
  scenario_root
  run_mode
  full_psi_plan
  product_list
  node_list
  week_list
  master_load_result
  runtime_model_summary
  psi_result_summary
  capacity_result_summary
  cost_result_summary
  tariff_result_summary
  money_result_summary
  visualization_datasets
  output_paths
  diagnostics
  warnings
  messages
```

The returned object does not need to expose every internal object to the GUI.

It should expose stable summaries and dataset handles.

---

## 9. Master Loading Position

Master loading should be a stage called by the Top Routine.

It should not be spread across GUI code.

Recommended flow:

```text
scenario_root
  ↓
master file discovery
  ↓
load master CSVs
  ↓
normalize rows
  ↓
validate rows
  ↓
MasterLoadResult
```

The result should describe what was loaded.

Recommended conceptual fields:

```text
MasterLoadResult
  scenario_root
  loaded_files
  node_master_rows
  network_master_rows
  demand_master_rows
  capacity_master_rows
  cost_master_rows
  tariff_master_rows
  price_master_rows
  validation_messages
  diagnostics
```

This connects to the next planned memo:

```text
docs/design/wom_master_data_loading_and_runtime_model_map.md
```

---

## 10. Runtime Model Instantiation Position

After master loading, the Top Routine should call the runtime model builder.

For the Japanese Rice vertical slice, this already exists in a partial form:

```text
network master rows
  ↓
ProductPlanNode tree
  ↓
DemandAnchoredLot attachment
  ↓
MARKET_TOKYO.psi4demand[week][0]
```

Future generalized flow:

```text
MasterLoadResult
  ↓
RuntimeModelBuilder
  ↓
WomRuntimeModel
```

Recommended conceptual structure:

```text
WomRuntimeModel
  scenario_id
  products
  plan_node_trees
  node_index
  edge_index
  lot_index
  capacity_index
  cost_index
  tariff_index
  calendar_index
```

The runtime model should be a stable internal object.

GUI should not directly depend on all its internals.

---

## 11. PSI Planning Engine Position

The PSI planning engine should remain focused on quantity planning.

It should answer:

```text
what lot
where
when
how many
accepted or blocked
inventory movement
production / shipment / arrival / sale
```

It should not directly perform:

```text
tariff simulation
business reporting
GUI rendering
AI recommendation
```

The Top Routine calls the PSI engine and receives a planning result.

Recommended conceptual result:

```text
PsiPlanningResult
  plan_nodes
  psi_snapshots
  lot_flows
  capacity_usages
  blocked_lots
  backlog_lots
  event_trace
  diagnostics
```

---

## 12. Cost / Tariff / Money Evaluation Position

Cost, tariff, and money evaluation should be outside the PSI quantity engine.

Recommended flow:

```text
PsiPlanningResult
  ↓
Cost / Tariff / Money Evaluators
  ↓
EvaluationResult
```

This keeps the PSI engine clean.

Cost and tariff should be calculated as post-plan evaluation at first.

Future phases may use these values for optimization, but that should not be the first implementation.

Recommended evaluation result:

```text
EvaluationResult
  cost_result
  tariff_result
  money_result
  kpi_summary
  diagnostics
```

---

## 13. Visualization Adapter Position

Visualization adapters should run after planning and evaluation.

They convert internal result objects into flat datasets.

Recommended flow:

```text
FullPlanResult / PipelineContext
  ↓
Visualization Adapter
  ↓
Flat Dataset
  ↓
GUI / CSV / pandas / SQL / BI
```

The adapter is the key layer between WOM internals and visual presentation.

It prevents the GUI from reaching deep into planner internals.

### 13.1 Capacity gate dataset

```text
wom_visual_capacity_gate_weekly
  scenario_id
  product_name
  node_name
  week
  requested
  capacity
  accepted
  blocked
  unused_capacity
  capacity_usage_ratio
  blocked_ratio
  capacity_usage_pct
  blocked_pct
```

### 13.2 PSI weekly dataset

```text
wom_visual_psi_weekly
  scenario_id
  product_name
  node_name
  tree_side
  week
  S
  CO
  I
  P
```

### 13.3 Money weekly dataset

```text
wom_visual_money_weekly
  scenario_id
  product_name
  node_name
  week
  revenue
  cogs
  gross_profit
  logistics_cost
  tariff_cost
  inventory_value
  cash_in
  cash_out
```

### 13.4 KPI summary dataset

```text
wom_kpi_summary
  scenario_id
  product_name
  metric_name
  metric_value
  unit
  status
  comment
```

---

## 14. GUI Position

The GUI should consume visualization datasets.

It should not be responsible for planning logic.

Recommended GUI dependency:

```text
GUI
  depends on chart datasets
  depends on FullPlanResult summaries
  does not depend on deep planner internals
```

The Japanese Rice smoke graph panel is therefore a prototype of the future GUI graph panel.

Current smoke flow:

```text
Japanese Rice runner
  ↓
demo_summary
  ↓
GUI model
  ↓
chart dataset
  ↓
Canvas chart
```

Future main flow:

```text
Run Full Plan
  ↓
FullPlanResult
  ↓
Visualization Adapter
  ↓
chart dataset
  ↓
same Canvas chart pattern
```

---

## 15. Plugin Hook Positions

Plugin hooks should be stable extension points.

Recommended hook positions:

```text
before_load
after_load
before_runtime_model
after_runtime_model
before_plan
after_plan
before_evaluation
after_evaluation
before_visualization
after_visualization
before_export
after_export
before_next_run
```

Not all hooks must be implemented immediately.

The core set should be small.

Recommended initial hooks:

```text
before_load
after_load
before_plan
after_plan
after_evaluation
after_visualization
after_export
```

---

## 16. Plugin Responsibility

Plugins should be used for extension, not for hidden core logic.

Good plugin examples:

```text
capacity override
demand adjustment
master validation
diagnostic report generation
visual dataset export
tariff post-evaluation
rule-based action TODO generation
```

Bad plugin examples:

```text
secretly rewriting planner internals
silently changing lot identity
silently changing PSI bucket semantics
drawing GUI widgets directly from inside planner
```

Plugins must be transparent and testable.

---

## 17. Rule Based Planning System Position

The future Rule Based Planning System should run after facts are available.

Recommended position:

```text
after_plan
after_evaluation
after_visualization
before_next_run
```

Conceptual flow:

```text
FullPlanResult / Visualization Dataset / KPI Summary
  ↓
Rule Base Diagnosis
  ↓
Meta Plan Action TODO
  ↓
Validator
  ↓
Scenario Override
  ↓
Re-run WOM Pipeline
  ↓
Before / After Evaluation
```

The Rule Base should not directly mutate master CSV files.

It should generate typed action TODOs.

---

## 18. AI-assisted Planning Position

AI should be positioned as an assistant that reads facts and proposes typed actions.

Recommended flow:

```text
flat datasets / KPI summaries / graph images
  ↓
AI diagnosis
  ↓
typed Meta Plan Action TODO
  ↓
schema validation
  ↓
hard constraint check
  ↓
scenario simulation
  ↓
human approval
```

AI should not freely rewrite WOM internals.

AI should not directly edit master files without validation.

The safe design is:

```text
AI proposes
WOM validates
WOM simulates
human approves
```

---

## 19. Meta Plan Action TODO Position

Meta Plan Action TODO is a future handoff contract between:

```text
Rule Base
AI diagnosis
Scenario variation
Pipeline rerun
Human approval
```

Example action types:

```text
CapacityIncreaseAction
DemandShiftAction
DemandSmoothingAction
BufferStockIncreaseAction
LaneSwitchAction
ProductionPrebuildAction
InventoryTargetChangeAction
TariffScenarioAction
SourcingMixChangeAction
```

Common fields:

```text
action_type
target_node
target_product
target_weeks
parameter_name
current_value
proposed_value
reason
expected_effect
risk
priority
approval_required
```

This is not implemented in this memo.

It is positioned as a future extension point.

---

## 20. Development Automation Position

WOM development process automation should be outside the runtime Top Routine.

It is a development pipeline, not a planning pipeline.

However, the structure is similar:

```text
design MD
  ↓
Codex request
  ↓
diff apply
  ↓
test
  ↓
commit / push
  ↓
completion memo
```

This should be documented later in:

```text
docs/design/wom_development_process_automation_environment.md
```

It is related to WOM engineering, not WOM planning runtime.

---

## 21. Entrypoint Strategy

The existing `python -m main` should not be overloaded.

Recommended approach:

```text
python -m main
  = thin router, if retained

dedicated entrypoints:
  python -m pysi.runners.run_full_plan
  python -m pysi.gui.wom_main_cockpit
  python -m pysi.reporting.export_run_full_plan_dataset
  python -m pysi.gui.japanese_rice_first_runner_view
```

The Top Routine should be callable from CLI and GUI.

Recommended future command:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001
```

For GUI:

```bat
python -m pysi.gui.wom_main_cockpit --scenario-root examples/scenarios/japanese_rice_vslice_001
```

This keeps responsibilities clean.

---

## 22. Relationship to Current Japanese Rice Work

Current Japanese Rice vertical slices are not throwaway work.

They are the test aircraft for the future Top Routine.

The following components are reusable ideas:

```text
runner output contract
GUI model extraction
chart dataset helper
chart series helper
Canvas chart panel
scenario variation comparison
scrollable GUI layout
```

What must be generalized:

```text
hard-coded Japanese Rice scenario
hard-coded DC_KANTO
hard-coded three weeks
diagnostic smoke result
full_psi_plan = False
```

Future generalized version:

```text
scenario_id arbitrary
product arbitrary
node arbitrary
week range arbitrary
FullPlanResult based
full plan result based
```

---

## 23. Relationship to Future Tariff Simulation

Tariff simulation should be called after PSI planning.

Recommended future position:

```text
PsiPlanningResult
  ↓
Tariff Cost Evaluator
  ↓
TariffCostResult
  ↓
MoneyResult
  ↓
Visualization Dataset
```

Tariff should initially be a post-plan evaluation.

It should not be embedded inside the PSI engine.

Future phases may use tariff as a planning objective, but not initially.

---

## 24. Relationship to Cost / Profit Structure Simulation

Cost / profit simulation should be handled by evaluation modules.

Recommended position:

```text
PsiPlanningResult
  ↓
Cost Structure Evaluator
  ↓
MoneyResult
  ↓
KPI Summary
```

This supports the WOM TOBE image:

```text
Demand Anchored Lot Base Weekly PSI quantity model
  ↓
Cost / Profit Structure Ratio money model
  ↓
Management evaluation
```

---

## 25. Key Contracts to Define Next

This Top Routine design leads to the next design memos.

Recommended order:

```text
1. docs/design/wom_master_data_loading_and_runtime_model_map.md
2. docs/design/wom_entrypoint_and_run_full_plan_contract.md
3. docs/design/wom_full_plan_result_contract.md
4. docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
5. docs/design/wom_tariff_cost_simulation_model_vertical_slice.md
6. docs/design/wom_rule_based_planning_system_future_image.md
7. docs/design/wom_development_process_automation_environment.md
```

The immediate next memo should probably be:

```text
docs/design/wom_master_data_loading_and_runtime_model_map.md
```

Reason:

```text
Top Routine defines the flow.
Master Data Map defines what enters the flow.
```

---

## 26. Acceptance Criteria for This Design

This design is useful if it clarifies:

```text
Top Routine is orchestration, not calculation
Pipeline Core owns execution order
Plugin Hooks are extension points
FullPlanResult is the main handoff contract
Visualization Adapter converts internal results into flat datasets
GUI consumes datasets, not planner internals
Rule Base / AI will propose typed action TODOs, not freely mutate internals
Development Automation is related but separate from runtime pipeline
```

This memo does not require implementation yet.

It prepares the next implementation map.

---

## 27. Completion Summary

The WOM Top Routine should be defined as:

```text
the orchestration layer that connects master loading, runtime model instantiation,
PSI planning, evaluation, visualization dataset generation, export,
plugin hooks, and future AI / rule-based action loops.
```

The Pipeline Core should remain:

```text
thin
explicit
plugin-friendly
result-contract-driven
```

The Top Routine should not become:

```text
a monolithic calculation engine
a GUI renderer
a hidden master data mutator
```

The future direction is:

```text
Run Full Plan
  ↓
FullPlanResult
  ↓
Visualization Adapter
  ↓
Flat Dataset
  ↓
GUI / CSV / pandas / SQL / BI
```

This is the backbone for connecting the current Japanese Rice smoke visualization to the future WOM main cockpit.
