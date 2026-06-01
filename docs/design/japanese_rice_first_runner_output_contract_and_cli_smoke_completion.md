# Japanese Rice First Runner Output Contract and CLI Smoke Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_first_runner_output_contract_and_cli_smoke_request.md
```

**Related north-star doc:**

```text
docs/design/wom_tobe_management_simulator_image.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_capacity_constrained_flow_runner_actual_plan_node_upgrade_completion.md
docs/design/japanese_rice_capacity_constrained_first_flow_vertical_slice_completion.md
docs/design/japanese_rice_plan_node_tree_instantiation_vertical_slice_completion.md
docs/design/japanese_rice_first_psi_run_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice first runner output contract and CLI smoke slice.

The purpose of this slice was to move the Japanese Rice first PSI runner from:

```text
rich internal diagnostic object
```

to:

```text
stable demo summary and CLI / GUI wrapper-readable output contract
```

The runner now returns:

```text
contract_version
demo_summary
cli_summary_lines
```

This is an important step toward management-visible simulation.

It does not implement GUI wiring yet.

It does not implement full PSI planning.

It provides the stable meter signal before cockpit wiring.

---

## 2. Key Commit

Implementation commit:

```text
6fba57d Add Japanese Rice runner output contract
```

Related preceding commits:

```text
faa64d1 Add Japanese Rice first runner output contract CLI smoke Codex request
c7e075f Add Japanese Rice first runner output contract and CLI smoke design
88ce357 Add WOM TOBE management simulator image
a15e66f Add Japanese Rice first PSI runner actual plan node upgrade completion memo
5b5b286 Upgrade Japanese rice first PSI runner diagnostics
5993533 Add Japanese Rice first PSI runner actual plan node upgrade Codex request
8034ee9 Add Japanese Rice first PSI runner actual plan node upgrade design
d039e60 Add Japanese Rice capacity constrained first flow completion memo
febc28e Add Japanese rice capacity constrained first flow
```

---

## 3. Files Changed / Added

This implementation changed:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

This implementation added:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

The commit created:

```text
2 files changed
343 insertions
9 deletions
```

No separate helper file was added.

The helper functions were added directly to the existing runner module.

No GUI files were changed.

No planner engine files were changed.

No NetworkX dependency was removed or modified.

No scenario master CSV files were changed.

---

## 4. Output Contract Implemented

The runner now exposes a runner-specific contract version:

```python
CONTRACT_VERSION = "japanese_rice_first_runner_output_v0r1"
```

The top-level runner result now includes:

```text
contract_version
demo_summary
cli_summary_lines
```

The existing runner function remains:

```python
run_japanese_rice_first_psi_vslice(...)
```

The existing diagnostic meaning is preserved:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

---

## 5. demo_summary Implemented

The runner now returns:

```text
demo_summary
```

The summary includes:

```text
scenario_id
product_name
runner_mode
full_psi_plan
weeks
master_counts
plan_node_summary
capacity_gate_summary
management_message
```

This section is intended for:

```text
future GUI wrapper
future cockpit text panel
public demo summary
stable test contract
```

---

## 6. Master Counts in demo_summary

The `demo_summary.master_counts` section exposes:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

These values prove that the Japanese Rice vertical slice masters are loaded and aligned.

---

## 7. PlanNode Summary in demo_summary

The `demo_summary.plan_node_summary` section exposes actual ProductPlanNode evidence.

Confirmed values:

```text
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

Weekly S-slot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

This preserves the key internal WOM design principle:

```text
Demand lot visibility should come from actual ProductPlanNode PSI buckets,
not only from raw demand master counts.
```

---

## 8. Capacity Gate Summary in demo_summary

The `demo_summary.capacity_gate_summary` section exposes the DC_KANTO S capacity gate.

Confirmed values:

```text
capacity_node = DC_KANTO
capacity_type = S
unit = lot
```

Weekly results:

```text
2027-W40:
  requested = 80
  capacity = 90
  accepted = 80
  blocked = 0

2027-W41:
  requested = 95
  capacity = 90
  accepted = 90
  blocked = 5

2027-W42:
  requested = 110
  capacity = 90
  accepted = 90
  blocked = 20
```

Totals:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

This is the first stable demo contract for the Japanese Rice capacity-constrained lot flow.

---

## 9. cli_summary_lines Implemented

The runner now returns:

```text
cli_summary_lines
```

This is a list of plain strings intended for compact CLI and GUI text display.

Expected contents include:

```text
WOM Japanese Rice first PSI smoke
Scenario: JAPANESE_RICE_VSLICE_001
Product: JAPANESE_RICE_STANDARD
Mode: diagnostic_first_psi_smoke
Full PSI plan: False
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

This makes the runner output human-readable without requiring users to inspect nested dictionaries.

---

## 10. CLI main Implemented

A CLI entrypoint was implemented for:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice
```

Supported formats:

```text
summary
json
```

Example summary command:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format summary
```

Example JSON command:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format json
```

The CLI is diagnostic-only.

It does not require GUI.

It does not import cockpit modules.

---

## 11. Tests Added

Focused test file:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

The focused tests verify:

```text
contract_version
demo_summary
demo_summary.master_counts
demo_summary.plan_node_summary
demo_summary.capacity_gate_summary
MARKET_TOKYO S-slot counts 80 / 95 / 110
DC_KANTO accepted / blocked 80/0, 90/5, 90/20
total accepted / blocked 260 / 25
cli_summary_lines
CLI summary format
CLI json format
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

---

## 12. Tests Executed

Focused output contract test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Observed result:

```text
9 passed
```

Existing Japanese Rice related tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
55 passed
```

Capacity integration / diagnostic tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
40 passed
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Observed result:

```text
compileall completed successfully
```

CLI smoke check was also reported as successful for both:

```text
--format summary
--format json
```

The JSON payload contained:

```text
contract_version = japanese_rice_first_runner_output_v0r1
demo_summary.capacity_gate_summary.totals.accepted = 260
```

---

## 13. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
GUI layout
NetworkX dependency
scenario master CSV files
full PSI planner behavior
capacity enforcement engine behavior
inventory calculation
CO / backlog calculation
cost / price / profit behavior
```

This phase only added:

```text
stable output contract
demo summary
CLI summary lines
CLI summary / json output
focused tests
```

This is consistent with the current strategy:

```text
Visualization before recommendation.
Stable output before GUI wiring.
```

---

## 14. Current Japanese Rice Case State

The Japanese Rice Case now has:

```text
Capacity master
Demand master
Network master
Actual ProductPlanNode tree
DemandAnchoredLot attachment to MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted_lot_ids / blocked_lot_ids
first PSI smoke runner exposing these diagnostics
stable output contract
CLI summary / JSON smoke output
```

The current runner-level output chain is:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
contract_version
    ↓
demo_summary
    ↓
cli_summary_lines
    ↓
CLI / GUI wrapper-readable meter signal
```

---

## 15. Development Meaning

This is a major demo-readiness milestone.

Before this phase:

```text
The runner contained rich diagnostic data.
```

After this phase:

```text
The runner exposes a stable summary contract.
The runner can be called from CLI.
The runner can print a compact summary.
The same contract can later feed a GUI wrapper.
```

This changes the Japanese Rice Case from:

```text
internally executable diagnostic
```

to:

```text
externally showable diagnostic
```

This is exactly aligned with the near-term goal:

```text
Management-visible simulation before recommendation AI.
```

---

## 16. Still Deferred

The following remain intentionally deferred.

### 16.1 GUI cockpit wiring

Not yet implemented:

```text
button / menu entry to run Japanese Rice first PSI smoke
text panel for cli_summary_lines
chart panel for requested / capacity / accepted / blocked
```

### 16.2 Full canonical event generation

Not yet implemented:

```text
P_TO_I
I_TO_S
S_TO_NEXT_P
capacity_gate_accepted
capacity_gate_blocked
event persistence
LotCAP export
```

### 16.3 psi_state persistence

Not yet implemented:

```text
tree_physical_outbound.json
tree_physical_inbound.json
plan_tree_outbound.json
plan_tree_inbound.json
psi_events.parquet
state_hash.txt
```

### 16.4 Cost / Profit Structure connection

Not yet implemented:

```text
accepted lots to revenue
blocked lots to lost sales
capacity usage to cost
profit impact summary
```

### 16.5 Multi-gate capacity flow

Not yet implemented:

```text
RICE_MILL_A capacity gate
FARM_REGION_A capacity gate
multi-stage accepted / blocked propagation
```

---

## 17. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_first_runner_cli_output_completion.md
```

only if a separate CLI behavior completion memo is desired.

However, because this completion memo already records CLI smoke, the more natural next design is:

```text
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice.md
```

Purpose:

```text
Define how the existing WOM GUI / cockpit can call run_japanese_rice_first_psi_vslice(...)
and display demo_summary / cli_summary_lines without touching full planner behavior.
```

Alternative next design:

```text
docs/design/japanese_rice_first_runner_output_chart_dataset.md
```

Purpose:

```text
Convert demo_summary.capacity_gate_summary.weekly into a chart-ready dataset:
week, requested, capacity, accepted, blocked.
```

Recommended order:

```text
1. First runner output contract completion memo
2. GUI wrapper vertical slice
3. Chart-ready weekly balance dataset
4. GUI chart panel
5. Cost / Profit Structure ratio connection
```

---

## 18. Future GUI Meaning

The GUI should not directly parse the deep diagnostic structure.

Instead, the GUI should consume:

```text
demo_summary
cli_summary_lines
```

Minimal GUI use:

```text
display cli_summary_lines in a text panel
```

Next GUI use:

```text
display requested / capacity / accepted / blocked as weekly chart
```

The stable output contract protects the GUI from internal runner changes.

This is why this slice is important.

---

## 19. Completion Summary

Completed:

```text
runner-specific CONTRACT_VERSION added
run_japanese_rice_first_psi_vslice(...) returns contract_version
run_japanese_rice_first_psi_vslice(...) returns demo_summary
run_japanese_rice_first_psi_vslice(...) returns cli_summary_lines
demo_summary includes master_counts
demo_summary includes plan_node_summary
demo_summary includes capacity_gate_summary
demo_summary shows MARKET_TOKYO S-slot counts 80 / 95 / 110
demo_summary shows DC_KANTO weekly accepted / blocked 80/0, 90/5, 90/20
demo_summary shows total accepted / blocked 260 / 25
cli_summary_lines are compact and human-readable
CLI main implemented
CLI formats summary and json supported
runner remains diagnostic_first_psi_smoke
full_psi_plan remains False
no GUI dependency introduced
existing Japanese Rice runner tests passed
focused output contract test passed
capacity integration tests passed
compileall passed
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
```

Current milestone:

```text
Japanese Rice runner now emits a stable CLI / GUI wrapper-readable output contract.
```

In simple terms:

```text
The rice bags are on the WOM vehicle.
DC_KANTO accepted 260 and blocked 25.
Now the dashboard has a stable signal that says exactly that.
```
