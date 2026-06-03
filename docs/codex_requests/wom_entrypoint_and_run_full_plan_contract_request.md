# Codex Request: WOM Entrypoint and Run Full Plan Contract

**Version:** v0r1  
**Date:** 2026-06-03  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_entrypoint_and_run_full_plan_contract_request.md`

**Parent design doc:**

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
```

**Preceding design docs:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
docs/design/wom_master_data_loading_and_runtime_model_map.md
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
```

**Related Japanese Rice implementation files:**

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/gui/japanese_rice_first_runner_view.py
pysi/plan/capacity_constrained_first_flow.py
pysi/plan/plan_node_tree_instantiation.py
pysi/capacity/capacity_weekly_rows_source.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first minimal WOM `Run Full Plan` entrypoint contract.

This request should not implement the final full WOM planning engine.

Instead, it should create a safe bridge from the existing Japanese Rice vertical-slice runner to a generalized `Run Full Plan` style contract.

The goal is to establish:

```text
WomRunConfig
  ↓
run_full_plan(...)
  ↓
FullPlanResult-like contract
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
```

This is the first implementation of the launch button and output connector described in:

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
```

---

## 2. Strategic Context

The current WOM design sequence is:

```text
WOM Top Routine / Pipeline Core
  ↓
Master Data Loading / Runtime Model Map
  ↓
Source-code grounded Master Data Audit
  ↓
Entrypoint and Run Full Plan Contract
  ↓
Minimal Run Full Plan implementation
```

The Japanese Rice vertical slice already has:

```text
diagnostic runner
runner output contract
GUI model extraction
capacity gate chart dataset
chart series
Tkinter chart view
scenario variation comparison
scrollable layout
```

This request should reuse those proven components rather than invent a new planner.

---

## 3. Scope

### 3.1 In scope

Implement:

```text
WomRunConfig dataclass or simple typed config
FullPlanResult dataclass or stable dict contract
pysi/runners/run_full_plan.py
CLI entrypoint: python -m pysi.runners.run_full_plan
bridge from Japanese Rice first runner to FullPlanResult-like contract
full_plan_result.json export
visual_capacity_gate_weekly.csv export
focused tests
```

### 3.2 Out of scope

Do not implement:

```text
final full PSI engine
new planner logic
cost / money evaluation
tariff simulation
Rule Base / AI diagnosis
main GUI cockpit integration
scenario editor
database persistence
BI connector
```

Do not modify planner behavior.

Do not modify GUI behavior.

Do not modify scenario master CSV files.

Do not remove or modify NetworkX.

---

## 4. Expected Changed / Added Files

Expected new file:

```text
pysi/runners/run_full_plan.py
```

Expected new test file:

```text
tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Optional small support file only if strongly justified:

```text
pysi/runners/full_plan_contract.py
```

For v0r1, keeping `WomRunConfig` and `FullPlanResult` in `pysi/runners/run_full_plan.py` is acceptable if simpler.

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Avoid modifying the existing Japanese Rice runner unless a small import-safe reuse is necessary.

---

## 5. Required Public API

### 5.1 WomRunConfig

Add a typed configuration object.

Recommended dataclass:

```python
@dataclass(frozen=True)
class WomRunConfig:
    scenario_root: str
    scenario_id: str = "unknown"
    run_id: str = ""
    run_mode: str = "diagnostic_smoke_bridge"
    output_dir: str = "outputs/run_full_plan"
    enable_capacity: bool = True
    enable_visualization_export: bool = True
    debug: bool = False
```

Behavior:

```text
if run_id is empty, generate a deterministic-enough run id
for tests, allow explicit run_id
```

### 5.2 FullPlanResult

Add a stable result object.

Recommended dataclass:

```python
@dataclass
class FullPlanResult:
    contract_version: str
    run_id: str
    scenario_id: str
    scenario_root: str
    run_mode: str
    full_psi_plan: bool
    status: str
    master_load_summary: dict
    runtime_model_summary: dict
    capacity_result_summary: dict
    visualization_datasets: dict
    output_paths: dict
    diagnostics: list
    messages: list
```

The first version should use:

```text
contract_version = "wom_full_plan_result_v0r1"
```

For this bridge implementation:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

if the Japanese Rice runner succeeds.

### 5.3 Main function

Add:

```python
def run_full_plan(config: WomRunConfig) -> FullPlanResult:
    ...
```

### 5.4 Dict/JSON helpers

Add helpers:

```python
def full_plan_result_to_dict(result: FullPlanResult) -> dict:
    ...

def write_full_plan_outputs(result: FullPlanResult, *, output_dir: str) -> FullPlanResult:
    ...
```

or equivalent.

The JSON output should be stable and testable.

---

## 6. CLI Entrypoint

Implement:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Required arguments:

```text
--scenario-root
```

Optional arguments:

```text
--scenario-id
--run-id
--output-dir
--format summary
--format json
```

Recommended defaults:

```text
--scenario-id japanese_rice_vslice_001
--output-dir outputs/run_full_plan
--format summary
```

The CLI should:

```text
build WomRunConfig
call run_full_plan(config)
write outputs
print summary or JSON
return exit code 0 on success
return nonzero on failure
```

---

## 7. Bridge to Existing Japanese Rice Runner

For v0r1, `run_full_plan` should bridge to:

```python
pysi.runners.run_japanese_rice_first_psi_vslice.run_japanese_rice_first_psi_vslice
```

for the Japanese Rice scenario.

The bridge should:

```text
call the existing Japanese Rice first runner
read its stable result
extract master counts
extract actual plan node summary
extract capacity gate summary
extract demo_summary
extract cli_summary_lines
convert to FullPlanResult fields
export capacity gate weekly rows
```

Do not change the existing Japanese Rice runner contract.

---

## 8. Required FullPlanResult Mapping

Map existing Japanese Rice runner result to `FullPlanResult`.

### 8.1 Top-level fields

```text
contract_version = wom_full_plan_result_v0r1
run_id = config.run_id
scenario_id = config.scenario_id
scenario_root = config.scenario_root
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

### 8.2 master_load_summary

Should include at least:

```text
network
demand
capacity
master_counts
```

Use existing runner fields where available.

### 8.3 runtime_model_summary

Should include at least:

```text
actual_plan_node_tree
inbound_node_count
outbound_node_count
market_node
MARKET_TOKYO S-slot counts if available
```

### 8.4 capacity_result_summary

Should include at least:

```text
capacity_node = DC_KANTO
capacity_type = S
weekly
totals
```

Expected base totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 8.5 visualization_datasets

Should include:

```text
capacity_gate_weekly
```

with a path after output writing:

```text
outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
```

### 8.6 output_paths

Should include:

```text
run_dir
full_plan_result_json
visual_capacity_gate_weekly_csv
```

### 8.7 messages

Should include:

```text
existing cli_summary_lines if available
a bridge message stating this is diagnostic_smoke_bridge
```

---

## 9. Required Output Files

When `write_full_plan_outputs` is called, create:

```text
outputs/run_full_plan/<run_id>/full_plan_result.json
outputs/run_full_plan/<run_id>/visual_capacity_gate_weekly.csv
```

### 9.1 full_plan_result.json

Should contain a JSON-serializable dict version of FullPlanResult.

Must include:

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

### 9.2 visual_capacity_gate_weekly.csv

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

Expected rows for Japanese Rice base:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

Expected totals:

```text
requested=285
capacity=270
accepted=260
blocked=25
```

---

## 10. Summary Format

If CLI is called with:

```bat
--format summary
```

Print stable lines including:

```text
WOM Run Full Plan
contract_version: wom_full_plan_result_v0r1
run_mode: diagnostic_smoke_bridge
full_psi_plan: False
scenario_id: japanese_rice_vslice_001
capacity gate: DC_KANTO S
requested: 285
capacity: 270
accepted: 260
blocked: 25
outputs:
  full_plan_result.json
  visual_capacity_gate_weekly.csv
```

Exact wording may vary, but tests should check key terms and values.

---

## 11. JSON Format

If CLI is called with:

```bat
--format json
```

Print JSON to stdout.

The JSON should include:

```text
contract_version
run_id
scenario_id
run_mode
status
capacity_result_summary
output_paths
```

---

## 12. Error Handling

If `scenario_root` does not exist:

```text
status = failed
exit code nonzero
print concise error
```

If the Japanese Rice bridge is unavailable:

```text
status = failed
diagnostics includes reason
exit code nonzero
```

Do not crash with a long traceback for expected missing-path errors.

---

## 13. Test File

Add focused test:

```text
tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

---

## 14. Required Tests

### 14.1 Dataclass / contract test

Assert:

```text
WomRunConfig exists
FullPlanResult exists
contract_version == wom_full_plan_result_v0r1
run_mode == diagnostic_smoke_bridge
full_psi_plan is False
```

### 14.2 run_full_plan bridge test

Call:

```python
config = WomRunConfig(
    scenario_root="examples/scenarios/japanese_rice_vslice_001",
    scenario_id="japanese_rice_vslice_001",
    run_id="test_run_full_plan_v0r1",
    output_dir=tmp_path,
)
result = run_full_plan(config)
```

Assert:

```text
result.status == success
result.capacity_result_summary totals requested=285 capacity=270 accepted=260 blocked=25
result.runtime_model_summary contains actual_plan_node_tree or equivalent
```

### 14.3 output export test

Call output writer.

Assert files exist:

```text
full_plan_result.json
visual_capacity_gate_weekly.csv
```

Read JSON and assert:

```text
contract_version == wom_full_plan_result_v0r1
run_mode == diagnostic_smoke_bridge
full_psi_plan is False
```

Read CSV and assert rows:

```text
W40 80/90/80/0
W41 95/90/90/5
W42 110/90/90/20
```

### 14.4 CLI summary smoke

Use subprocess or direct `main(...)` if implemented.

Assert summary includes:

```text
WOM Run Full Plan
diagnostic_smoke_bridge
DC_KANTO
accepted
blocked
260
25
```

### 14.5 CLI JSON smoke

Assert JSON output parses and includes:

```text
contract_version
capacity_result_summary
output_paths
```

### 14.6 Missing scenario root test

Use invalid path.

Assert nonzero or failed result.

---

## 15. Required Test Commands

Focused test:

```bat
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Existing Japanese Rice GUI/runner tests:

```bat
python -m pytest tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing runner / plan-node tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile and format:

```bat
python -m compileall -q pysi/runners/run_full_plan.py tests/test_wom_entrypoint_and_run_full_plan_contract.py
python -m black --check pysi/runners/run_full_plan.py tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

CLI smoke:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id cli_smoke_run_full_plan_v0r1 --format summary
```

JSON smoke:

```bat
python -m pysi.runners.run_full_plan --scenario-root examples/scenarios/japanese_rice_vslice_001 --scenario-id japanese_rice_vslice_001 --run-id cli_smoke_run_full_plan_v0r1_json --format json
```

---

## 16. Safety Boundaries

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
scenario master CSV files
existing Japanese Rice runner contract
NetworkX usage
planner behavior
```

Do not implement:

```text
cost evaluation
tariff simulation
rule-based planning
AI action TODO
main cockpit integration
```

This request is only the first Run Full Plan contract bridge.

---

## 17. Acceptance Criteria

This request is complete when:

```text
pysi/runners/run_full_plan.py exists
WomRunConfig exists
FullPlanResult exists
run_full_plan(config) exists
CLI module execution works
FullPlanResult contract_version is wom_full_plan_result_v0r1
run_mode is diagnostic_smoke_bridge for Japanese Rice bridge
full_psi_plan is False for Japanese Rice bridge
full_plan_result.json is exported
visual_capacity_gate_weekly.csv is exported
CSV has W40/W41/W42 expected values
focused tests pass
existing Japanese Rice tests pass
capacity tests pass
compileall passes
black check passes
planner behavior unchanged
GUI behavior unchanged
scenario master CSV files unchanged
NetworkX untouched
```

---

## 18. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was WomRunConfig implemented?
Where was FullPlanResult implemented?
What runner module was added?
What test file was added?
Does python -m pysi.runners.run_full_plan work?
What contract_version is returned?
What run_mode is returned for Japanese Rice?
Does full_psi_plan remain False for the bridge?
Does full_plan_result.json get written?
Does visual_capacity_gate_weekly.csv get written?
Does CSV contain W40 80/90/80/0?
Does CSV contain W41 95/90/90/5?
Does CSV contain W42 110/90/90/20?
Did you modify existing Japanese Rice runner contract?
Did you modify GUI behavior?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 19. Development Meaning

Before this request:

```text
WOM has design docs for the Top Routine and Run Full Plan contract.
```

After this request:

```text
WOM has an executable minimal Run Full Plan bridge.
```

This is not the final WOM planner.

It is the first stable launch button and output connector.

In simple terms:

```text
The control tower now has a first launch command.
The result now has a first standard connector.
```
