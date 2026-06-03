# WOM Entrypoint and Run Full Plan Contract

**Version:** v0r1 draft  
**Date:** 2026-06-03  
**Status:** Design memo  
**Target path:** `docs/design/wom_entrypoint_and_run_full_plan_contract.md`

**Preceding design docs:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
docs/design/wom_master_data_loading_and_runtime_model_map.md
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
```

**Strategic role:** Define how WOM is launched, how Run Full Plan is invoked, and what contract it returns  
**Primary scope:** Entry points, Run Full Plan orchestration, FullPlanResult, CLI/GUI/report handoff  
**Current north star:** Management-visible simulation before recommendation AI  
**Development principle:** Thin entrypoint, stable result contract, adapter-friendly outputs

---

## 1. Purpose

This memo defines the entrypoint and Run Full Plan contract for WOM.

The previous design memos clarified:

```text
Top Routine / Pipeline Core
  = the orchestration backbone

Master Data Loading Map
  = the conceptual input wiring diagram

Source Audit
  = the current source-code-grounded input wiring map
```

The next question is:

```text
How should WOM be started?
What exactly is Run Full Plan?
What result should it return?
How should GUI / report / BI / future Rule Base consume the result?
```

This memo answers those questions.

In simple terms:

```text
Top Routine = control tower
Master Data Map = input wiring
Run Full Plan Contract = launch button and output connector
```

---

## 2. Design Position

`Run Full Plan` should be the standard execution mode that runs a WOM scenario through the full planning and evaluation pipeline.

Conceptual flow:

```text
Entrypoint
  ↓
Run Config
  ↓
run_wom_pipeline(config)
  ↓
FullPlanResult
  ↓
Visualization Dataset Adapter / Export / GUI / BI / Rule Base
```

The entrypoint should not contain planning logic.

The entrypoint should parse arguments, build a config, call the pipeline, and hand off the result.

---

## 3. Why This Contract Is Needed

Current WOM development has several runner types:

```text
diagnostic smoke runner
Japanese Rice first runner
GUI wrapper launcher
capacity diagnostic runner
legacy main entrypoint
reporting / cockpit runners
```

This is normal during vertical-slice development.

However, to connect the main WOM cockpit and future graph panels safely, we need a stable contract:

```text
one scenario in
one FullPlanResult out
optional output files generated
GUI / report / BI consume stable result or flat datasets
```

Without this contract, GUI and reporting code may directly depend on internal planner structures.

That should be avoided.

---

## 4. Entrypoint Strategy

The existing `python -m main` should not become a large monolithic program.

Recommended strategy:

```text
python -m main
  = thin router, retained for convenience if needed
```

Dedicated entrypoints should carry actual execution roles:

```text
python -m pysi.runners.run_full_plan
python -m pysi.gui.wom_main_cockpit
python -m pysi.reporting.export_run_full_plan_dataset
python -m pysi.gui.japanese_rice_first_runner_view
```

This keeps the system easier to test and reason about.

---

## 5. Entrypoint Types

### 5.1 CLI full-plan runner

Primary future command:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Purpose:

```text
load scenario
run WOM pipeline
return / print summary
export result datasets
exit with status code
```

### 5.2 GUI launcher

Future command:

```bat
python -m pysi.gui.wom_main_cockpit --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Purpose:

```text
launch GUI
allow Run Full Plan
display FullPlanResult-derived datasets
```

### 5.3 Reporting / export runner

Future command:

```bat
python -m pysi.reporting.export_run_full_plan_dataset --scenario-root examples/scenarios/japanese_rice_vslice_001 --output-dir outputs/run_full_plan
```

Purpose:

```text
run or read FullPlanResult
export flat datasets for CSV / pandas / SQL / BI
```

### 5.4 Existing Japanese Rice smoke GUI

Current command:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Status:

```text
independent vertical slice
prototype of future graph panel
not yet the general WOM main cockpit
```

---

## 6. Role of `python -m main`

`python -m main` may be retained, but only as a thin router.

Recommended behavior:

```bat
python -m main --mode gui --scenario-root examples/scenarios/japanese_rice_vslice_001
python -m main --mode run-full-plan --scenario-root examples/scenarios/japanese_rice_vslice_001
python -m main --mode export --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Internally:

```text
main.py
  ↓
parse mode
  ↓
delegate to pysi.runners.run_full_plan or pysi.gui.wom_main_cockpit
```

`main.py` should not:

```text
load every master directly
run planning logic directly
draw GUI directly
contain cost / tariff / graph logic directly
```

It should be an entrance hall, not the whole factory.

---

## 7. WomRunConfig Contract

Before `Run Full Plan` starts, the entrypoint should create a run configuration.

Recommended conceptual structure:

```text
WomRunConfig
  scenario_root
  scenario_id
  run_id
  run_mode
  product_filter
  node_filter
  week_start
  week_end
  output_dir
  enable_capacity
  enable_cost
  enable_tariff
  enable_visualization_export
  enable_rule_base
  plugin_config
  debug
```

### 7.1 Minimal v0r1 config

For the first implementation, keep the config small:

```text
scenario_root
scenario_id
run_id
run_mode
output_dir
enable_capacity
enable_visualization_export
debug
```

### 7.2 Future config fields

Later:

```text
enable_cost
enable_tariff
enable_rule_base
scenario_overrides
action_todos
approval_policy
```

---

## 8. Run Modes

Recommended run modes:

```text
diagnostic_smoke
full_plan
export_only
gui_interactive
scenario_compare
rule_base_diagnosis
```

### 8.1 diagnostic_smoke

Used by existing Japanese Rice vertical slices.

```text
full_psi_plan = False
goal = deterministic diagnostics and visualization prototype
```

### 8.2 full_plan

Future normal mode.

```text
full_psi_plan = True
goal = complete scenario run through master loading, runtime model, planning, evaluation, visualization dataset export
```

### 8.3 gui_interactive

Used by the main cockpit.

```text
user opens GUI
presses Run Full Plan
GUI receives FullPlanResult or output dataset handles
```

### 8.4 scenario_compare

Future mode.

```text
run base scenario
run variant scenario
compare FullPlanResults
```

### 8.5 rule_base_diagnosis

Future mode.

```text
run scenario
diagnose result
generate Meta Plan Action TODO
```

---

## 9. Run Full Plan Definition

`Run Full Plan` should mean:

```text
execute one WOM scenario from master loading through planning,
evaluation, visualization dataset generation, and output export,
then return a FullPlanResult.
```

Recommended v0r1 flow:

```text
1. read WomRunConfig
2. load master data
3. instantiate runtime model
4. run PSI planning
5. run capacity diagnostics / capacity-aware planning where enabled
6. build evaluation summary
7. build visualization flat datasets
8. export outputs
9. return FullPlanResult
```

Future flow includes:

```text
tariff evaluation
cost / money evaluation
cash-flow evaluation
rule-based diagnosis
AI-assisted action TODO generation
```

---

## 10. FullPlanResult Concept

`FullPlanResult` is the main output connector from the WOM pipeline.

It should be stable enough for:

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
  status
  started_at
  completed_at
  product_list
  node_list
  week_list
  master_load_summary
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

---

## 11. Minimal FullPlanResult v0r1

The first implementation should not try to fill every future field.

Minimal v0r1:

```text
contract_version
run_id
scenario_id
scenario_root
run_mode
full_psi_plan
status
master_load_summary
runtime_model_summary
capacity_result_summary
visualization_datasets
output_paths
diagnostics
messages
```

This allows the graph panel adapter to start.

Cost, tariff, money can be `None`, `{}`, or `"not_connected"` with explicit status.

---

## 12. FullPlanResult Status

Recommended status values:

```text
success
warning
failed
unavailable
partial
```

Example:

```text
status = success
full_psi_plan = False
run_mode = diagnostic_smoke
```

for current Japanese Rice smoke.

Future full run:

```text
status = success
full_psi_plan = True
run_mode = full_plan
```

---

## 13. Contract Versioning

FullPlanResult must have a contract version.

Recommended first version:

```text
wom_full_plan_result_v0r1
```

Existing Japanese Rice runner has its own runner-specific output contract.

That is acceptable.

Relationship:

```text
Japanese Rice runner contract
  = diagnostic vertical-slice contract

FullPlanResult contract
  = future generalized WOM pipeline contract
```

Do not break the existing Japanese Rice runner contract while creating the general contract.

---

## 14. Output Paths

Run Full Plan should write outputs under a run directory.

Recommended structure:

```text
outputs/run_full_plan/<run_id>/
  full_plan_result.json
  visual_capacity_gate_weekly.csv
  visual_psi_weekly.csv
  visual_money_weekly.csv
  kpi_summary.csv
  diagnostics.json
  messages.txt
```

For development:

```text
outputs/run_full_plan/latest/
```

may be useful as a convenience pointer, but immutable `run_id` directories are safer.

---

## 15. Visualization Dataset Contract

The Run Full Plan result should include dataset handles.

Example:

```text
visualization_datasets:
  capacity_gate_weekly:
    format: csv
    path: outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
    row_count: 123
  psi_weekly:
    format: csv
    path: outputs/run_full_plan/<run_id>/visual_psi_weekly.csv
    row_count: 456
```

The GUI should be able to consume either:

```text
in-memory dataset
```

or:

```text
output CSV path
```

The adapter should support both eventually.

---

## 16. Capacity Gate Visualization Dataset

The first Run Full Plan graph adapter should probably start with capacity gate rows because the Japanese Rice smoke already proves the pattern.

Recommended dataset:

```text
visual_capacity_gate_weekly.csv
```

Columns:

```text
scenario_id
run_id
product_name
node_name
capacity_type
week
requested
capacity
accepted
blocked
shortage
unused_capacity
capacity_usage_ratio
blocked_ratio
capacity_usage_pct
blocked_pct
```

This is the direct generalization of the Japanese Rice chart dataset.

---

## 17. PSI Weekly Visualization Dataset

Next dataset:

```text
visual_psi_weekly.csv
```

Columns:

```text
scenario_id
run_id
product_name
node_name
tree_side
week
S
CO
I
P
```

For lot-based PSI, the dataset must specify whether values are:

```text
lot_count
quantity
value
```

Recommended field:

```text
measure_type
```

Example:

```text
measure_type = lot_count
```

---

## 18. Money Weekly Visualization Dataset

Future dataset:

```text
visual_money_weekly.csv
```

Columns:

```text
scenario_id
run_id
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
currency
```

This should wait until cost / money source consolidation is defined.

---

## 19. KPI Summary Dataset

Future dataset:

```text
kpi_summary.csv
```

Columns:

```text
scenario_id
run_id
product_name
metric_name
metric_value
unit
status
comment
```

This will become important for Rule Base and AI diagnosis.

---

## 20. GUI Handoff Contract

The main GUI should not read planner internals directly.

Recommended GUI flow:

```text
User clicks Run Full Plan
  ↓
GUI builds WomRunConfig
  ↓
GUI calls run_wom_pipeline(config)
  ↓
GUI receives FullPlanResult
  ↓
GUI loads visualization datasets or in-memory dataset objects
  ↓
GUI graph panels render datasets
```

The GUI can also run in file-reading mode:

```text
User opens previous run directory
  ↓
GUI reads full_plan_result.json and visualization CSVs
  ↓
GUI displays saved result
```

This supports reproducibility and BI integration.

---

## 21. Reporting / BI Handoff Contract

Reports and BI should consume flat datasets.

Recommended output types:

```text
CSV
JSON
Parquet in future
SQLite in future
```

The Run Full Plan should not require GUI.

A headless report/export run should be possible:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --no-gui --export
```

---

## 22. Rule Base / AI Handoff Contract

Rule Base and AI should consume:

```text
FullPlanResult summary
visualization datasets
KPI summary
diagnostics
graph images in future
```

They should generate:

```text
Meta Plan Action TODO
```

They should not directly mutate master CSV files.

Future flow:

```text
Run Full Plan
  ↓
FullPlanResult
  ↓
Rule Base / AI Diagnosis
  ↓
Meta Plan Action TODO
  ↓
Validator
  ↓
Scenario Override
  ↓
Re-run
```

This contract is future-facing, but Run Full Plan must be designed to support it.

---

## 23. Error Handling Contract

Run Full Plan should return structured errors where possible.

Recommended fields:

```text
status
error_code
error_message
diagnostics
warnings
```

If a fatal exception occurs in CLI mode:

```text
print concise error
return nonzero exit code
optionally write diagnostics
```

In GUI mode:

```text
show error panel
do not crash the entire app if avoidable
```

---

## 24. Exit Code Contract

Recommended CLI exit codes:

```text
0 = success
1 = failed
2 = invalid config / missing scenario root
3 = master validation failed
4 = planning failed
5 = export failed
```

This supports development automation.

---

## 25. Relationship to Existing Japanese Rice Runner

Current Japanese Rice runner:

```text
pysi.runners.run_japanese_rice_first_psi_vslice
```

Current Japanese Rice GUI:

```text
pysi.gui.japanese_rice_first_runner_view
```

These are still valuable.

They should remain as:

```text
diagnostic vertical-slice runner
prototype graph panel
prototype scenario variation
prototype scrollable layout
```

The future Run Full Plan should not delete or break them.

Instead, it should generalize their patterns:

```text
runner output contract
GUI model extraction
chart dataset
chart series
Canvas chart panel
scenario comparison text
```

---

## 26. Relationship to Source Audit Findings

The source audit found:

```text
clearly implemented:
  network / demand / capacity / Japanese Rice visualization

partial:
  cost / money / cash-flow
  price / offering price
  tariff
  product / SKU
  calendar / week
  lane / logistics

missing unified contracts:
  MasterLoadResult
  WomRuntimeModel
  FullPlanResult
```

Therefore, the first Run Full Plan contract should start with the clearly implemented categories.

Recommended first target:

```text
network + demand + capacity + visualization
```

Do not force cost / tariff into v0r1.

Mark them as:

```text
not_connected
partial
future
```

---

## 27. Recommended First Implementation Slice

The first Codex implementation after this design should probably be:

```text
docs/codex_requests/wom_entrypoint_and_run_full_plan_contract_request.md
```

Scope:

```text
add WomRunConfig dataclass
add FullPlanResult dataclass or dict contract
add pysi/runners/run_full_plan.py minimal CLI
reuse Japanese Rice first runner as a diagnostic backend where appropriate
write full_plan_result.json
write or expose capacity_gate visualization dataset
add focused tests
do not change planner behavior
do not change GUI behavior
```

This would establish the launch button and output connector.

---

## 28. Minimal First Implementation Idea

The minimal implementation can wrap existing Japanese Rice components.

Conceptual flow:

```text
run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001
  ↓
detect Japanese Rice vertical slice scenario
  ↓
call run_japanese_rice_first_psi_vslice(...)
  ↓
convert to FullPlanResult-like contract
  ↓
export full_plan_result.json
  ↓
export visual_capacity_gate_weekly.csv
```

This is not the final full planner.

It is a bridge from current vertical slice to future full pipeline.

That bridge is useful if it is clearly labeled:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
```

---

## 29. Future Full Implementation Path

After the minimal bridge, the path should be:

```text
1. WomRunConfig / FullPlanResult minimal contract
2. FullPlanResult JSON export
3. capacity gate visual dataset export
4. GUI reads FullPlanResult output
5. PSI weekly dataset adapter
6. cost / money dataset adapter
7. tariff cost simulation adapter
8. scenario comparison using two FullPlanResults
9. Rule Base diagnosis using KPI / visual datasets
```

This order is safer than jumping directly to all features.

---

## 30. Acceptance Criteria for This Design

This design is useful if it clarifies:

```text
python -m main should be a thin router if retained
dedicated entrypoints should own actual execution modes
Run Full Plan means scenario execution through pipeline and result export
WomRunConfig is the input contract
FullPlanResult is the output contract
GUI consumes FullPlanResult / visualization datasets
reporting and BI consume flat datasets
Rule Base / AI consume FullPlanResult facts and generate typed Action TODOs
Japanese Rice smoke runner remains a prototype and bridge
```

This memo does not implement code.

It defines the next implementation contract.

---

## 31. Completion Summary

The recommended execution architecture is:

```text
Entrypoint
  ↓
WomRunConfig
  ↓
run_wom_pipeline(config)
  ↓
FullPlanResult
  ↓
Visualization Datasets
  ↓
GUI / CSV / pandas / SQL / BI / Rule Base
```

The first implementation should be small and bridge from existing Japanese Rice vertical slices.

The key rule is:

```text
Do not connect the GUI directly to planner internals.
Connect the GUI to FullPlanResult and visualization datasets.
```

This contract is the foundation for the future Run Full Plan graph panel adapter.
