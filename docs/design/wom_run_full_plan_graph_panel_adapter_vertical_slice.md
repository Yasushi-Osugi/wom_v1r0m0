# WOM Run Full Plan Graph Panel Adapter Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-03  
**Status:** Design memo  
**Target path:** `docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md`

**Preceding design docs:**

```text
docs/design/wom_top_routine_and_pipeline_core_design.md
docs/design/wom_master_data_loading_and_runtime_model_map.md
docs/design/wom_master_data_loading_and_runtime_model_map_source_audit.md
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
```

**Implemented bridge commit:**

```text
be4c4a9 Add WOM run full plan bridge
```

**Completion memo commit:**

```text
f370666 Add WOM run full plan bridge completion memo
```

**Strategic role:** Connect the new Run Full Plan output connector to a reusable graph-panel adapter  
**Primary scope:** `full_plan_result.json`, `visual_capacity_gate_weekly.csv`, adapter model, chart dataset, graph panel reuse  
**Current north star:** Management-visible simulation before recommendation AI  
**Development principle:** GUI consumes FullPlanResult / visualization datasets, not planner internals

---

## 1. Purpose

This memo defines the next vertical slice after the successful `Run Full Plan` bridge.

The current implemented bridge provides:

```text
python -m pysi.runners.run_full_plan
  ↓
FullPlanResult
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
```

The current Japanese Rice smoke GUI already proved this display pattern:

```text
Japanese Rice runner
  ↓
GUI model
  ↓
capacity gate chart dataset
  ↓
chart series
  ↓
Tkinter Canvas chart panel
  ↓
weekly table / totals / scenario variation
```

The purpose of this vertical slice is to connect these two lines.

Target flow:

```text
python -m pysi.runners.run_full_plan
  ↓
full_plan_result.json
  ↓
visual_capacity_gate_weekly.csv
  ↓
Run Full Plan Graph Panel Adapter
  ↓
capacity gate chart dataset
  ↓
existing chart panel pattern
```

This is the first step toward a real WOM main cockpit where graph panels are driven by standard Run Full Plan outputs rather than by runner-specific internals.

---

## 2. Strategic Meaning

The previous work created the launch button and output connector.

This work connects that output connector to the instrument panel.

In WOM terms:

```text
Run Full Plan bridge
  = first standard launch command

FullPlanResult / visual CSV
  = first standard result connector

Graph Panel Adapter
  = first standard visualization connector
```

The critical design rule is:

```text
The GUI should not reach into planner internals.
The GUI should read FullPlanResult and visualization datasets.
```

This keeps future GUI, BI, reporting, scenario comparison, and Rule Base diagnosis aligned around the same evidence.

---

## 3. Current Proven Assets

### 3.1 Run Full Plan bridge

Implemented in:

```text
pysi/runners/run_full_plan.py
```

Provides:

```text
WomRunConfig
FullPlanResult
run_full_plan(config)
full_plan_result.json export
visual_capacity_gate_weekly.csv export
CLI summary / JSON output
```

Current bridge status:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
contract_version = wom_full_plan_result_v0r1
```

### 3.2 Existing Japanese Rice graph panel pattern

Implemented mainly in:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Existing helper concepts:

```text
extract_japanese_rice_first_runner_gui_model(...)
build_japanese_rice_capacity_gate_chart_dataset(...)
build_japanese_rice_capacity_gate_chart_series(...)
add_capacity_gate_chart_to_window(...)
build_capacity_override_chart_dataset(...)
build_capacity_gate_scenario_comparison(...)
format_capacity_gate_scenario_comparison_text(...)
```

These are runner-specific today, but the pattern is reusable.

---

## 4. What This Slice Should Achieve

This vertical slice should prove that the graph panel can be driven by Run Full Plan outputs.

The minimum successful chain is:

```text
run_full_plan output directory
  ↓
load full_plan_result.json
  ↓
load visual_capacity_gate_weekly.csv
  ↓
build adapter model
  ↓
build chart dataset
  ↓
build chart series
  ↓
display or test graph-ready data
```

The first implementation can focus on data/model adapters and tests.

A later implementation can connect the adapter to a GUI launcher.

---

## 5. In Scope

This design covers:

```text
Run Full Plan output loading
FullPlanResult JSON reader
visual_capacity_gate_weekly.csv reader
adapter model for capacity gate graph panel
chart dataset generation from Run Full Plan outputs
chart series generation from Run Full Plan outputs
basic summary text
future GUI connection point
focused tests
```

---

## 6. Out of Scope

Do not implement in this slice:

```text
final WOM main cockpit
new PSI planner
cost / money graph
tariff graph
Rule Base diagnosis
AI action TODO
scenario editor
database-backed visualization store
BI connector
```

Do not change:

```text
planner behavior
Japanese Rice runner contract
scenario master CSV files
NetworkX
existing cockpit_tk.py layout
```

---

## 7. Input Contract

The adapter should consume a Run Full Plan output directory.

Example:

```text
outputs/run_full_plan/<run_id>/
  full_plan_result.json
  visual_capacity_gate_weekly.csv
```

The minimum required files are:

```text
full_plan_result.json
visual_capacity_gate_weekly.csv
```

Optional future files:

```text
visual_psi_weekly.csv
visual_money_weekly.csv
kpi_summary.csv
diagnostics.json
```

---

## 8. full_plan_result.json Requirements

The adapter should read at least:

```text
contract_version
run_id
scenario_id
scenario_root
run_mode
full_psi_plan
status
capacity_result_summary
visualization_datasets
output_paths
messages
diagnostics
```

Expected current values for Japanese Rice bridge:

```text
contract_version = wom_full_plan_result_v0r1
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
status = success
```

The adapter must preserve the fact that this is still a diagnostic bridge.

It should not label it as final full planning.

---

## 9. visual_capacity_gate_weekly.csv Requirements

The adapter should read rows with columns:

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

Expected current Japanese Rice rows:

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

---

## 10. Proposed Adapter Module

Recommended new module:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

Reason:

```text
keep generic Run Full Plan graph adapter separate from Japanese Rice-specific GUI wrapper
avoid adding generic adapter code to pysi/gui/japanese_rice_first_runner_view.py
allow future main cockpit to import this adapter
```

This module should not open a GUI window on import.

It should be safe for headless tests.

---

## 11. Proposed Public Functions

### 11.1 Load FullPlanResult JSON

```python
def load_full_plan_result_json(path: str | Path) -> dict:
    ...
```

Behavior:

```text
read JSON
return dict
raise or return unavailable model for missing file depending on helper level
```

For low-level loader, raising `FileNotFoundError` is acceptable.

For GUI model extractor, return safe unavailable model.

### 11.2 Load capacity gate CSV

```python
def load_visual_capacity_gate_weekly_csv(path: str | Path) -> list[dict]:
    ...
```

Behavior:

```text
read CSV
convert numeric fields
preserve week order
return list of rows
```

Numeric fields:

```text
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

### 11.3 Extract adapter model

```python
def extract_run_full_plan_capacity_gate_graph_model(
    *,
    full_plan_result: dict,
    capacity_gate_rows: list[dict],
) -> dict:
    ...
```

Return a GUI/graph model:

```text
available
contract_version
run_id
scenario_id
scenario_root
run_mode
full_psi_plan
status
product_name
node_name
capacity_type
summary_text
rows
totals
messages
diagnostics
management_message
```

### 11.4 Build chart dataset

```python
def build_run_full_plan_capacity_gate_chart_dataset(model: dict) -> dict:
    ...
```

Return chart dataset compatible with current Japanese Rice chart series pattern.

Suggested dataset contract:

```text
title
unit
x_key
series
rows
totals
chart_hint
```

### 11.5 Build chart series

```python
def build_run_full_plan_capacity_gate_chart_series(dataset: dict) -> dict:
    ...
```

Return:

```text
weeks
series:
  requested
  capacity
  accepted
  blocked
```

### 11.6 Build summary text

```python
def format_run_full_plan_graph_panel_summary_text(model: dict) -> str:
    ...
```

Include:

```text
WOM Run Full Plan
contract_version
run_mode
full_psi_plan
scenario_id
status
capacity gate
requested / capacity / accepted / blocked totals
output source
```

---

## 12. Safe Unavailable Model

If files are missing or malformed, the adapter should return a safe unavailable model at the high-level extraction layer.

Example:

```text
available = False
status = unavailable
reason = missing full_plan_result.json
rows = []
totals = {}
summary_text = concise explanation
```

This prevents GUI crashes.

Low-level file loaders may still raise exceptions.

The high-level convenience helper should catch them.

Recommended helper:

```python
def extract_run_full_plan_graph_panel_model_from_output_dir(output_dir: str | Path) -> dict:
    ...
```

Behavior:

```text
try to load full_plan_result.json
try to load visual_capacity_gate_weekly.csv
return available model if both are valid
return unavailable model if not
```

---

## 13. Relationship to Existing Japanese Rice Helpers

Existing Japanese Rice functions should not be broken.

This slice should not remove or rename:

```text
extract_japanese_rice_first_runner_gui_model(...)
build_japanese_rice_capacity_gate_chart_dataset(...)
build_japanese_rice_capacity_gate_chart_series(...)
add_capacity_gate_chart_to_window(...)
```

However, the new adapter may intentionally mirror their structure.

Future refactoring may extract shared chart rendering helpers, but this slice should avoid broad refactoring.

Recommended approach:

```text
copy the proven pattern conceptually
keep new generic adapter separate
test the generic adapter independently
```

---

## 14. GUI Connection Strategy

This design memo does not require immediate GUI integration.

However, the next implementation after adapter tests can add a GUI launcher such as:

```text
python -m pysi.gui.wom_run_full_plan_result_view --run-dir outputs/run_full_plan/<run_id>
```

or extend an existing GUI later.

Recommended phased approach:

```text
Phase 1:
  adapter model / dataset / series only

Phase 2:
  simple read-only Run Full Plan result viewer

Phase 3:
  main cockpit Run Full Plan button integration
```

This avoids destabilizing the existing GUI.

---

## 15. Phase 1 Recommended Implementation

The first Codex request following this design should implement Phase 1 only.

Expected new file:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

Expected new test file:

```text
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Expected tests:

```text
load full_plan_result.json
load visual_capacity_gate_weekly.csv
extract available model
calculate totals
build chart dataset
build chart series
handle missing output dir
handle missing CSV
preserve W40/W41/W42 values
```

No GUI window should open in tests.

---

## 16. Phase 1 Test Data Strategy

Tests should create temporary output files using the existing `run_full_plan` bridge.

Recommended test flow:

```python
config = WomRunConfig(
    scenario_root="examples/scenarios/japanese_rice_vslice_001",
    scenario_id="japanese_rice_vslice_001",
    run_id="test_graph_adapter_v0r1",
    output_dir=tmp_path,
)
result = run_full_plan(config)
write_full_plan_outputs(result, output_dir=tmp_path)
model = extract_run_full_plan_graph_panel_model_from_output_dir(tmp_path / "test_graph_adapter_v0r1")
```

Then assert:

```text
model.available is True
model.contract_version == wom_full_plan_result_v0r1
model.run_mode == diagnostic_smoke_bridge
model.full_psi_plan is False
model.totals.requested == 285
model.totals.capacity == 270
model.totals.accepted == 260
model.totals.blocked == 25
```

Also assert rows:

```text
2027-W40 requested=80  capacity=90 accepted=80 blocked=0
2027-W41 requested=95  capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

---

## 17. Chart Dataset Contract

The chart dataset generated from Run Full Plan output should follow this structure:

```text
title
unit
x_key
series
rows
totals
chart_hint
```

Example:

```text
title = "WOM Run Full Plan Capacity Gate"
unit = "lot"
x_key = "week"
chart_hint = "line_or_grouped_bar"
```

Series:

```text
requested
capacity
accepted
blocked
```

Rows:

```text
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

---

## 18. Chart Series Contract

The chart series helper should return:

```text
weeks:
  ["2027-W40", "2027-W41", "2027-W42"]

series:
  requested: [80, 95, 110]
  capacity: [90, 90, 90]
  accepted: [80, 90, 90]
  blocked: [0, 5, 20]
```

This mirrors the current Japanese Rice chart view pattern.

---

## 19. Summary Text Contract

The summary text should be concise and management-readable.

Example content:

```text
WOM Run Full Plan
Scenario: japanese_rice_vslice_001
Run mode: diagnostic_smoke_bridge
Full PSI plan: False
Status: success

Capacity gate: DC_KANTO S
Requested: 285
Capacity: 270
Accepted: 260
Blocked: 25
```

It should also state:

```text
This result is generated through diagnostic_smoke_bridge; final full PSI planning is not yet executed.
```

Truthfulness matters.

---

## 20. Future GUI Viewer

A later slice can add:

```text
pysi/gui/wom_run_full_plan_result_view.py
```

Command:

```bat
python -m pysi.gui.wom_run_full_plan_result_view --run-dir outputs/run_full_plan/cli_smoke_run_full_plan_v0r1
```

This viewer can reuse:

```text
load output dir
extract adapter model
build chart dataset
build chart series
display chart panel
display table
display totals
display messages
```

This would be the first generic WOM result viewer.

---

## 21. Main Cockpit Future Integration

After the read-only result viewer works, the main cockpit can integrate:

```text
Run Full Plan button
  ↓
call pysi.runners.run_full_plan.run_full_plan(config)
  ↓
write outputs
  ↓
adapter extracts model
  ↓
graph panel updates
```

This should not be implemented before the adapter is stable.

---

## 22. Scenario Comparison Future Integration

Once two FullPlanResult output directories exist:

```text
base run dir
variant run dir
```

the same adapter can support comparison:

```text
load base visual_capacity_gate_weekly.csv
load variant visual_capacity_gate_weekly.csv
compare totals
compare blocked reduction
compare accepted increase
```

This will generalize the current Japanese Rice capacity-up scenario comparison.

---

## 23. Relationship to PSI Weekly Dataset

This slice focuses only on capacity gate rows.

Next likely dataset after this is:

```text
visual_psi_weekly.csv
```

That future dataset will enable:

```text
S / CO / I / P graph panels
inventory graph panels
node-level PSI views
```

But that should follow after the capacity gate graph adapter proves the FullPlanResult-based pattern.

---

## 24. Relationship to Cost / Money / Tariff

Cost, money, and tariff are not in this slice.

Future datasets:

```text
visual_money_weekly.csv
kpi_summary.csv
tariff_cost_weekly.csv
```

should follow the same adapter pattern:

```text
FullPlanResult / visual CSV
  ↓
adapter model
  ↓
chart dataset
  ↓
graph panel
```

This keeps visualization consistent across quantity and money views.

---

## 25. Safety Boundaries

This slice must preserve:

```text
planner behavior
Japanese Rice runner contract
Run Full Plan bridge contract
GUI behavior
scenario master CSV files
NetworkX
```

No change should be made to:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

unless explicitly requested in a later slice.

---

## 26. Acceptance Criteria for This Design

This design is complete if it defines:

```text
why Run Full Plan output should drive graph panels
which files are input to the adapter
which adapter module should be added
which public functions should exist
what model / dataset / series contracts should look like
how missing output files should be handled safely
how this relates to Japanese Rice smoke GUI helpers
what should be implemented in Phase 1
what should remain future work
```

---

## 27. Recommended Next Codex Request

Create:

```text
docs/codex_requests/wom_run_full_plan_graph_panel_adapter_vertical_slice_request.md
```

Implementation target:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
```

Scope:

```text
load full_plan_result.json
load visual_capacity_gate_weekly.csv
extract graph panel model
build chart dataset
build chart series
format summary text
handle unavailable cases
focused tests only
no GUI window
no planner change
```

---

## 28. Completion Summary

This design connects the newly implemented `Run Full Plan` bridge to the next visualization step.

The current system can already generate:

```text
full_plan_result.json
visual_capacity_gate_weekly.csv
```

The next system should be able to read those outputs and build:

```text
graph panel model
chart dataset
chart series
summary text
```

This is the first step toward a generic WOM graph panel driven by standard Run Full Plan outputs.

In simple terms:

```text
The launch command now produces a standard result.
The next step is to plug that result into the instrument panel.
```
