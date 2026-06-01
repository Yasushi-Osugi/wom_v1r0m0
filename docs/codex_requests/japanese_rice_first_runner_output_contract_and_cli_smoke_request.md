# Codex Request: Japanese Rice First Runner Output Contract and CLI Smoke

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_runner_output_contract_and_cli_smoke_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke.md
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

**Related implementation files already present:**

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
pysi/plan/capacity_constrained_first_flow.py
pysi/plan/plan_node_tree_instantiation.py
pysi/network/network_master_loader.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/capacity/capacity_weekly_rows_source.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice first runner output contract and CLI smoke slice.

The current runner:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

already exposes rich diagnostic information, including:

```text
masters loaded
actual ProductPlanNode tree
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted / blocked lots
```

This request should make that output stable and demo-friendly by adding:

```text
contract_version
demo_summary
cli_summary_lines
```

Optional but recommended:

```text
CLI main(...) with --format summary/json
```

This request is not GUI wiring.

This request is not full PSI planning.

This request is the stable output contract before GUI/cockpit integration.

---

## 2. Strategic Context

The current WOM north star is:

```text
Management-visible simulation before recommendation AI.
```

The Japanese Rice Case now proves that:

```text
Demand lots can be generated.
Demand lots can be attached to actual ProductPlanNode.
DC_KANTO capacity gate can split lots into accepted / blocked.
The first PSI smoke runner can expose this diagnostic result.
```

The next requirement is:

```text
Make the runner output easy to show.
```

The purpose of this slice is to move from:

```text
rich diagnostic object
```

to:

```text
stable demo summary and CLI smoke output
```

---

## 3. Scope Control

### 3.1 In scope

Modify or add code so that `run_japanese_rice_first_psi_vslice(...)` returns:

```text
contract_version
demo_summary
cli_summary_lines
```

Optionally add CLI support:

```text
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format summary
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format json
```

Add focused tests.

### 3.2 Out of scope

Do not implement:

```text
GUI cockpit wiring
full canonical event generation
full psi_state persistence
full cost / profit simulation
multi-gate flow
leadtime-aware propagation
inventory carry-over
recommendation AI
```

Do not modify planner behavior.

Do not modify GUI layout.

Do not remove or modify NetworkX.

Do not change scenario master CSV files.

---

## 4. Expected Changed / Added Files

Expected modified file:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Optional new helper file:

```text
pysi/runners/japanese_rice_first_psi_output_contract.py
```

Recommended new test file:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Optional only if needed:

```text
pysi/runners/__init__.py
```

Do not modify GUI files.

---

## 5. Current Runner Contract to Preserve

The runner must preserve the existing smoke contract.

Required fields must remain available:

```text
scenario_id
product_name
available
run_mode
full_psi_plan
masters
weeks
demand
network
capacity
balance
actual_plan_node_tree
capacity_constrained_first_flow
messages
```

Required values:

```text
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

Existing master counts must remain available:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

Do not break the existing tests.

---

## 6. Required New Field: contract_version

Add:

```python
"contract_version": "japanese_rice_first_runner_output_v0r1"
```

This should be top-level.

The version is intentionally specific to this runner and this first visible contract.

---

## 7. Required New Field: demo_summary

Add a stable `demo_summary` section.

Recommended shape:

```python
"demo_summary": {
    "title": "Japanese Rice first PSI smoke",
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "runner_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],

    "master_counts": {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    },

    "plan_node_summary": {
        "inbound_node_count": 5,
        "outbound_node_count": 5,
        "demand_node": "MARKET_TOKYO",
        "demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]",
        "weekly_s_slot_counts": {
            "2027-W40": 80,
            "2027-W41": 95,
            "2027-W42": 110,
        },
    },

    "capacity_gate_summary": {
        "capacity_node": "DC_KANTO",
        "capacity_type": "S",
        "unit": "lot",
        "weekly": {
            "2027-W40": {
                "requested": 80,
                "capacity": 90,
                "accepted": 80,
                "blocked": 0,
            },
            "2027-W41": {
                "requested": 95,
                "capacity": 90,
                "accepted": 90,
                "blocked": 5,
            },
            "2027-W42": {
                "requested": 110,
                "capacity": 90,
                "accepted": 90,
                "blocked": 20,
            },
        },
        "totals": {
            "requested": 285,
            "capacity": 270,
            "accepted": 260,
            "blocked": 25,
        },
    },

    "management_message": "DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon."
}
```

Exact nesting may vary slightly, but tests must verify the same facts.

---

## 8. Required New Field: cli_summary_lines

Add top-level:

```python
"cli_summary_lines": [...]
```

It should be a list of plain strings.

Recommended content:

```text
WOM Japanese Rice first PSI smoke
Scenario: JAPANESE_RICE_VSLICE_001
Product: JAPANESE_RICE_STANDARD
Mode: diagnostic_first_psi_smoke
Full PSI plan: False

Masters:
  capacity_rows=9, demand_rows=3, demand_lots=285, network_nodes=9, network_edges=8

Actual ProductPlanNode:
  inbound_nodes=5, outbound_nodes=5
  demand_node=MARKET_TOKYO
  demand_lot_source=MARKET_TOKYO.psi4demand[week][0]

Weekly demand S-slot:
  2027-W40: 80
  2027-W41: 95
  2027-W42: 110

DC_KANTO S capacity gate:
  2027-W40: requested=80, capacity=90, accepted=80, blocked=0
  2027-W41: requested=95, capacity=90, accepted=90, blocked=5
  2027-W42: requested=110, capacity=90, accepted=90, blocked=20

Totals:
  requested=285, capacity=270, accepted=260, blocked=25
```

This list should be stable enough for CLI output and GUI text panel use.

---

## 9. Optional CLI main

If feasible without increasing risk, add a `main(...)` entrypoint to:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Recommended command:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format summary
```

Supported formats:

```text
summary
json
```

### 9.1 summary format

Print only `cli_summary_lines`.

### 9.2 json format

Print full JSON diagnostic.

### 9.3 exit status

Recommended:

```text
0 = runner available and completed
1 = runner unavailable or validation failed
```

### 9.4 no GUI dependency

The CLI smoke must not require GUI.

Do not import Tkinter or cockpit modules.

---

## 10. Recommended Helper Functions

Recommended helper:

```python
build_japanese_rice_first_runner_demo_summary(result: dict) -> dict
```

Recommended helper:

```python
format_japanese_rice_first_runner_cli_summary(result: dict) -> list[str]
```

Optional:

```python
main(argv: list[str] | None = None) -> int
```

These may be placed in:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

or, if cleaner:

```text
pysi/runners/japanese_rice_first_psi_output_contract.py
```

Keep the existing public runner name unchanged:

```python
run_japanese_rice_first_psi_vslice(...)
```

---

## 11. Required Values

The output contract must expose these values.

### 11.1 Master counts

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

### 11.2 Actual plan_node summary

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

### 11.3 Capacity gate summary

```text
capacity_node = DC_KANTO
capacity_type = S
unit = lot
```

Weekly capacity gate:

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

---

## 12. Test File

Add focused test:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

---

## 13. Required Tests

### 13.1 Contract version

Assert:

```text
result["contract_version"] == "japanese_rice_first_runner_output_v0r1"
```

### 13.2 demo_summary exists

Assert:

```text
"demo_summary" in result
demo_summary["scenario_id"] == "JAPANESE_RICE_VSLICE_001"
demo_summary["product_name"] == "JAPANESE_RICE_STANDARD"
demo_summary["full_psi_plan"] is False
```

### 13.3 master_counts

Assert:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

from:

```text
demo_summary.master_counts
```

### 13.4 plan_node_summary

Assert:

```text
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

Assert weekly S-slot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

### 13.5 capacity_gate_summary weekly counts

Assert:

```text
2027-W40 accepted / blocked = 80 / 0
2027-W41 accepted / blocked = 90 / 5
2027-W42 accepted / blocked = 90 / 20
```

### 13.6 capacity_gate_summary totals

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 13.7 cli_summary_lines

Assert:

```text
"cli_summary_lines" in result
isinstance(result["cli_summary_lines"], list)
```

Assert the joined text contains:

```text
WOM Japanese Rice first PSI smoke
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

### 13.8 CLI command

If `main(...)` is implemented, test:

```text
--format summary
```

and optionally:

```text
--format json
```

The test must not require GUI.

---

## 14. Test Commands

Focused test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing related tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

If helper file is added:

```bat
python -m compileall -q pysi/runners/japanese_rice_first_psi_output_contract.py
```

---

## 15. Safety Boundaries

Expected modified / added files:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Optional helper file:

```text
pysi/runners/japanese_rice_first_psi_output_contract.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Do not remove NetworkX.

Do not modify scenario master CSV files.

Do not rename or remove `run_japanese_rice_first_psi_vslice(...)`.

Do not claim full PSI planning.

---

## 16. Acceptance Criteria

This request is complete when:

```text
run_japanese_rice_first_psi_vslice(...) returns contract_version
contract_version = japanese_rice_first_runner_output_v0r1
run_japanese_rice_first_psi_vslice(...) returns demo_summary
run_japanese_rice_first_psi_vslice(...) returns cli_summary_lines
demo_summary includes master_counts
demo_summary includes plan_node_summary
demo_summary includes capacity_gate_summary
demo_summary shows MARKET_TOKYO weekly S-slot counts 80 / 95 / 110
demo_summary shows DC_KANTO weekly accepted / blocked 80/0, 90/5, 90/20
demo_summary shows total accepted / blocked 260 / 25
cli_summary_lines are compact and human-readable
runner remains diagnostic_first_psi_smoke
full_psi_plan remains False
no GUI dependency is introduced
existing Japanese Rice runner tests still pass
focused output contract test passes
capacity integration tests still pass
compileall passes
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
```

---

## 17. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the output contract implemented?
Was a helper file added?
What test file was added?
Does the runner return contract_version?
Does the runner return demo_summary?
Does demo_summary include master_counts?
Does demo_summary include plan_node_summary?
Does demo_summary include capacity_gate_summary?
Does demo_summary show MARKET_TOKYO S-slot counts 80/95/110?
Does demo_summary show DC_KANTO accepted/blocked 80/0, 90/5, 90/20?
Does demo_summary show total accepted/blocked 260/25?
Does the runner return cli_summary_lines?
Was CLI main implemented?
If yes, what formats are supported?
Did you preserve run_mode = diagnostic_first_psi_smoke?
Did you preserve full_psi_plan = False?
Did you change planner behavior?
Did you change GUI layout?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 18. Non-Goals

This request does not implement:

```text
GUI cockpit
canonical event generation
psi_state persistence
cost / profit simulation
multi-gate flow
leadtime-aware propagation
inventory carry-over
recommendation AI
```

This request only stabilizes and exposes the runner output contract.

---

## 19. Development Meaning

Before this request:

```text
The runner has rich diagnostic data.
```

After this request:

```text
The runner has a stable demo summary and CLI smoke output.
```

This is important because GUI and public demo should not directly consume unstable nested diagnostic details.

They should consume:

```text
demo_summary
cli_summary_lines
```

In simple terms:

```text
The rice bags are on the WOM vehicle.
DC_KANTO accepted 260 and blocked 25.
Now the dashboard gets a stable signal that says exactly that.
```
