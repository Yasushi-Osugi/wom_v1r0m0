# WOM Entrypoint and Run Full Plan Contract Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-06-03  
**Status:** Completed implementation memo  
**Target path:** `docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md`

**Parent design doc:**

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
```

**Codex request:**

```text
docs/codex_requests/wom_entrypoint_and_run_full_plan_contract_request.md
```

**Implemented commit:**

```text
be4c4a9 Add WOM run full plan bridge
```

**Branch:**

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 1. Completion Summary

The first minimal WOM `Run Full Plan` bridge has been implemented and committed.

This implementation establishes the first executable standard entrypoint and output connector for WOM.

The completed bridge provides:

```text
WomRunConfig
  ↓
run_full_plan(config)
  ↓
Japanese Rice first runner bridge
  ↓
FullPlanResult
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
```

This is not the final full WOM planning engine.

It is the first safe bridge from the current Japanese Rice diagnostic vertical slice to the future generalized WOM `Run Full Plan` pipeline.

---

## 2. What Was Added

### 2.1 New runner module

```text
pysi/runners/run_full_plan.py
```

This module defines the minimal Run Full Plan bridge.

It includes:

```text
WomRunConfig
FullPlanResult
run_full_plan(config)
full_plan_result_to_dict(...)
write_full_plan_outputs(...)
CLI main(...)
```

### 2.2 New focused test file

```text
tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

This test file verifies:

```text
dataclass / contract stability
Japanese Rice bridge mapping
capacity totals
JSON export
CSV export
CLI summary smoke
CLI JSON smoke
missing scenario-root behavior
```

---

## 3. Contract Implemented

The implemented contract version is:

```text
wom_full_plan_result_v0r1
```

The Japanese Rice bridge uses:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

This is intentional.

The bridge is a diagnostic and integration step, not a declaration that the final full PSI planning engine is complete.

---

## 4. WomRunConfig

`WomRunConfig` was implemented in:

```text
pysi/runners/run_full_plan.py
```

It provides the input contract for running WOM through the new entrypoint.

Conceptual fields include:

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

The key role of `WomRunConfig` is to separate:

```text
how WOM is invoked
```

from:

```text
how WOM internally loads, plans, evaluates, and exports
```

This keeps the entrypoint thin and testable.

---

## 5. FullPlanResult

`FullPlanResult` was implemented in:

```text
pysi/runners/run_full_plan.py
```

It provides the first stable output connector for WOM.

The implemented result includes:

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

This object is the first step toward a generalized pipeline result that GUI, reporting, BI export, scenario comparison, Rule Base, and future AI diagnosis can consume.

---

## 6. Japanese Rice Bridge

The initial `run_full_plan(...)` implementation bridges to the existing Japanese Rice first runner.

The bridge does not replace or modify the existing runner contract.

It reads the existing Japanese Rice runner result and maps it into the new `FullPlanResult` structure.

Current bridge source:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Current bridge target:

```text
pysi/runners/run_full_plan.py
```

The bridge preserves the existing diagnostic status:

```text
bridge_source_run_mode = diagnostic_first_psi_smoke
bridge_source_full_psi_plan = False
bridge_source_contract_version = japanese_rice_first_runner_output_v0r1
```

---

## 7. Capacity Gate Output

The bridge exports the Japanese Rice DC_KANTO capacity gate result.

Expected capacity gate identity:

```text
capacity_node = DC_KANTO
capacity_type = S
unit = lot
```

Expected weekly values:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

Expected totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

These values were confirmed by the focused tests and CLI smoke.

---

## 8. Output Files

The bridge writes two output files under:

```text
outputs/run_full_plan/<run_id>/
```

### 8.1 FullPlanResult JSON

```text
full_plan_result.json
```

This contains the JSON-serializable `FullPlanResult` dict.

It includes:

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

### 8.2 Capacity gate visualization CSV

```text
visual_capacity_gate_weekly.csv
```

This is the first standardized visualization dataset generated by the Run Full Plan bridge.

It contains rows with:

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

This dataset is the immediate bridge to the future graph panel adapter.

---

## 9. CLI Entrypoint

The new runner can be launched with:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id cli_smoke_run_full_plan_v0r1 --format summary
```

It also supports JSON output:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id cli_smoke_run_full_plan_v0r1_json --format json
```

The summary output confirms:

```text
WOM Run Full Plan
contract_version: wom_full_plan_result_v0r1
run_mode: diagnostic_smoke_bridge
full_psi_plan: False
scenario_id: japanese_rice_vslice_001
status: success
capacity gate: DC_KANTO S
requested: 285
capacity: 270
accepted: 260
blocked: 25
```

---

## 10. Tests Confirmed

The following test groups were executed and passed during implementation validation.

### 10.1 Focused Run Full Plan contract test

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Result:

```text
6 passed
```

### 10.2 Japanese Rice GUI / runner tests

```bat
python -m pytest tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Result:

```text
30 passed
```

### 10.3 Japanese Rice plan / node / capacity tests

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Result:

```text
55 passed
```

### 10.4 Capacity integration tests

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Result:

```text
40 passed
```

### 10.5 Compile and format checks

```bat
python -m compileall -q pysi/runners/run_full_plan.py tests/test_wom_entrypoint_and_run_full_plan_contract.py
python -m black --check pysi/runners/run_full_plan.py tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Result:

```text
compileall OK
black --check OK
```

---

## 11. Safety Confirmation

The implementation preserved the requested safety boundaries.

No changes were made to:

```text
existing Japanese Rice runner contract
GUI behavior
planner behavior
scenario master CSV files
NetworkX usage
cost evaluation
tariff simulation
Rule Base / AI logic
main cockpit integration
```

The new implementation is additive.

It adds a new bridge runner and focused tests.

---

## 12. Important Interpretation

This implementation should be understood as:

```text
a diagnostic_smoke_bridge
```

not as:

```text
the final full PSI planning engine
```

The bridge intentionally returns:

```text
full_psi_plan = False
```

This preserves truthfulness.

It allows WOM to gain a standard entrypoint and result contract before the final pipeline is fully implemented.

---

## 13. Development Meaning

Before this implementation:

```text
WOM had a design for the Top Routine and Run Full Plan contract.
```

After this implementation:

```text
WOM has an executable minimal Run Full Plan bridge.
```

This means the following now exists:

```text
python -m pysi.runners.run_full_plan
  ↓
FullPlanResult
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
```

This is a major connection point.

The current Japanese Rice vertical slice can now serve as a bridge to the future WOM main pipeline.

---

## 14. Relationship to North Star

The WOM north star is:

```text
management-visible simulation before recommendation AI
```

This bridge supports that north star by providing:

```text
standard scenario execution
standard result object
standard visualization dataset
headless CLI execution
repeatable JSON / CSV outputs
```

This makes it easier to connect:

```text
graph panels
business reporting
BI tools
scenario comparison
future KPI evaluation
future Rule Base / AI diagnosis
```

---

## 15. Recommended Next Step

The next design step should be:

```text
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
```

Purpose:

```text
connect Run Full Plan output datasets to the graph panel pattern proven by the Japanese Rice smoke GUI
```

Current proven flow:

```text
Japanese Rice runner
  ↓
GUI model
  ↓
chart dataset
  ↓
chart panel
```

Next target flow:

```text
python -m pysi.runners.run_full_plan
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
  ↓
Graph Panel Adapter
  ↓
same chart panel pattern
```

This is the most direct next step toward management-visible simulation.

---

## 16. Completion Statement

The WOM Run Full Plan bridge is complete for v0r1.

It provides the first standard launch command and output connector.

It does not yet complete the final WOM planner.

It does establish the foundation for the future graph panel adapter and main cockpit integration.

In simple terms:

```text
The control tower now has its first launch command.
The result now has its first standard connector.
```
