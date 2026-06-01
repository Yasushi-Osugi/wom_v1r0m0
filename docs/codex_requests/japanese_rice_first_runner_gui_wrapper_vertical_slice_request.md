# Codex Request: Japanese Rice First Runner GUI Wrapper Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_runner_gui_wrapper_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice.md
```

**Related north-star doc:**

```text
docs/design/wom_tobe_management_simulator_image.md
```

**Related completion docs:**

```text
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke_completion.md
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

Please implement the Japanese Rice first runner GUI wrapper vertical slice.

The current runner already returns a stable output contract:

```python
run_japanese_rice_first_psi_vslice(...)
```

with:

```text
contract_version
demo_summary
cli_summary_lines
```

This request should add a minimal, independent GUI wrapper that consumes those stable fields and displays the Japanese Rice first PSI smoke summary.

This is not a full GUI cockpit rewrite.

This is not full PSI planning.

This is not scenario comparison yet.

This is the first safe GUI wrapper that puts the existing runner meter signal onto a visible dashboard.

---

## 2. Strategic Context

The current WOM near-term strategy is:

```text
Visualization before recommendation.
Stable output before GUI wiring.
Visible GUI before note publication.
```

The Japanese Rice Case now has:

```text
master data
ProductPlanNode tree
DemandAnchoredLots
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted / blocked lots
runner output contract
CLI summary/json output
```

The next step is:

```text
GUI can display the runner output.
```

This request should make that step small and safe.

---

## 3. Scope Control

### 3.1 In scope

Implement:

```text
a small independent GUI wrapper module
pure helper functions for extracting a GUI model
summary text generation from cli_summary_lines
weekly table rows from demo_summary.capacity_gate_summary.weekly
optional Tkinter launcher
focused tests that do not require opening a real GUI window
```

### 3.2 Out of scope

Do not implement:

```text
full GUI cockpit redesign
full cockpit integration
interactive scenario editing
scenario comparison
chart rendering
full PSI graph integration
network graph integration
cost / profit chart
multi-gate capacity flow
leadtime-aware propagation
recommendation AI
note article generation
```

Do not change existing planner behavior.

Do not change existing scenario master CSV files.

Do not remove or modify NetworkX.

---

## 4. Expected Changed / Added Files

Recommended new GUI wrapper file:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

Recommended new focused test file:

```text
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Optional only if needed:

```text
pysi/gui/__init__.py
```

Avoid modifying existing cockpit files in this first slice unless absolutely necessary.

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 5. Existing Runner to Consume

Use:

```python
from pysi.runners.run_japanese_rice_first_psi_vslice import run_japanese_rice_first_psi_vslice
```

The wrapper should consume:

```text
result["demo_summary"]
result["cli_summary_lines"]
result["contract_version"]
```

The wrapper should not parse deep internal diagnostic fields when the same values are already available through `demo_summary`.

---

## 6. Required GUI Model Helper

Implement:

```python
extract_japanese_rice_first_runner_gui_model(result: dict) -> dict
```

Expected output:

```python
{
    "available": True,
    "title": "WOM Japanese Rice First PSI Smoke",
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "contract_version": "japanese_rice_first_runner_output_v0r1",
    "runner_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    "summary_text": "...",
    "weekly_rows": [
        {"week": "2027-W40", "requested": 80, "capacity": 90, "accepted": 80, "blocked": 0},
        {"week": "2027-W41", "requested": 95, "capacity": 90, "accepted": 90, "blocked": 5},
        {"week": "2027-W42", "requested": 110, "capacity": 90, "accepted": 90, "blocked": 20},
    ],
    "totals": {
        "requested": 285,
        "capacity": 270,
        "accepted": 260,
        "blocked": 25,
    },
    "management_message": "DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon.",
}
```

If the runner result is unavailable or malformed, return a safe unavailable model rather than raising unexpectedly in GUI display code.

Recommended unavailable model:

```python
{
    "available": False,
    "title": "WOM Japanese Rice First PSI Smoke",
    "summary_text": "Japanese Rice first PSI smoke could not be run: ...",
    "weekly_rows": [],
    "totals": {},
    "management_message": "",
    "error": "...",
}
```

---

## 7. Required Helper: Weekly Rows

Implement:

```python
build_japanese_rice_weekly_capacity_gate_rows(result: dict) -> list[dict]
```

It should read:

```text
result["demo_summary"]["capacity_gate_summary"]["weekly"]
```

Expected rows:

```python
[
    {"week": "2027-W40", "requested": 80, "capacity": 90, "accepted": 80, "blocked": 0},
    {"week": "2027-W41", "requested": 95, "capacity": 90, "accepted": 90, "blocked": 5},
    {"week": "2027-W42", "requested": 110, "capacity": 90, "accepted": 90, "blocked": 20},
]
```

Keep week order as provided by:

```text
demo_summary["weeks"]
```

If weeks are missing, fall back to sorted weekly keys.

---

## 8. Required Helper: Summary Text

Implement:

```python
format_japanese_rice_gui_summary_text(result: dict) -> str
```

It should use:

```text
result["cli_summary_lines"]
```

Expected:

```python
"\n".join(result["cli_summary_lines"])
```

The summary text should include, at minimum:

```text
WOM Japanese Rice first PSI smoke
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

---

## 9. Optional Tkinter Launcher

If feasible with low risk, implement:

```python
launch_japanese_rice_first_runner_view(
    scenario_root: str | Path = "examples/scenarios/japanese_rice_vslice_001",
) -> None
```

The launcher should:

```text
call run_japanese_rice_first_psi_vslice(...)
extract GUI model
open a small Tkinter window
show summary_text in a scrollable text area
show weekly_rows in a simple table area
show totals and management_message
```

Keep the UI simple.

Do not try to match the full cockpit design yet.

Suggested window title:

```text
WOM Japanese Rice First PSI Smoke
```

---

## 10. Optional Module CLI

If a Tkinter launcher is implemented, add:

```python
main(argv: list[str] | None = None) -> int
```

So this works:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Return:

```text
0 on successful launch
1 on runner failure
```

Do not require this command in headless tests.

---

## 11. Display Requirements

The minimal window should show:

### 11.1 Header

```text
WOM Japanese Rice First PSI Smoke
```

### 11.2 Scenario info

```text
Scenario: JAPANESE_RICE_VSLICE_001
Product: JAPANESE_RICE_STANDARD
Contract: japanese_rice_first_runner_output_v0r1
Mode: diagnostic_first_psi_smoke
Full PSI plan: False
```

### 11.3 Summary text

Display `summary_text`.

### 11.4 Weekly table

Columns:

```text
Week
Requested
Capacity
Accepted
Blocked
```

Rows:

```text
2027-W40 | 80  | 90 | 80 | 0
2027-W41 | 95  | 90 | 90 | 5
2027-W42 | 110 | 90 | 90 | 20
```

### 11.5 Totals

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 11.6 Management message

```text
DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon.
```

---

## 12. Test Strategy

GUI tests should not require opening a real window.

The focused test should verify pure helper functions.

Add:

```text
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

### 12.1 GUI model extraction

Call:

```python
result = run_japanese_rice_first_psi_vslice(SCENARIO_ROOT)
model = extract_japanese_rice_first_runner_gui_model(result)
```

Assert:

```text
model["available"] is True
model["scenario_id"] == "JAPANESE_RICE_VSLICE_001"
model["product_name"] == "JAPANESE_RICE_STANDARD"
model["contract_version"] == "japanese_rice_first_runner_output_v0r1"
model["runner_mode"] == "diagnostic_first_psi_smoke"
model["full_psi_plan"] is False
```

### 12.2 Summary text

Assert:

```text
"WOM Japanese Rice first PSI smoke" in model["summary_text"]
"MARKET_TOKYO.psi4demand[week][0]" in model["summary_text"]
"DC_KANTO S capacity gate" in model["summary_text"]
"accepted=260" in model["summary_text"]
"blocked=25" in model["summary_text"]
```

### 12.3 Weekly rows

Assert:

```text
len(model["weekly_rows"]) == 3
```

Expected rows:

```text
2027-W40 requested=80 capacity=90 accepted=80 blocked=0
2027-W41 requested=95 capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

### 12.4 Totals

Assert:

```text
model["totals"]["requested"] == 285
model["totals"]["capacity"] == 270
model["totals"]["accepted"] == 260
model["totals"]["blocked"] == 25
```

### 12.5 Unavailable model behavior

Test malformed or unavailable input:

```python
model = extract_japanese_rice_first_runner_gui_model({"available": False, "messages": ["x"]})
```

Assert:

```text
model["available"] is False
model["weekly_rows"] == []
"could not be run" in model["summary_text"] or model["error"]
```

### 12.6 Import smoke

Assert the module can be imported without opening a GUI window.

Do not create a real Tkinter root in tests unless unavoidable.

---

## 13. Test Commands

Focused test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Existing output contract test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing related Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Capacity integration tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py tests/test_wom_capacity_weekly_rows_source_diagnostic.py tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

---

## 14. Manual Smoke Command

If the Tkinter launcher is implemented, manually verify:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Expected:

```text
A small window opens.
The window title is WOM Japanese Rice First PSI Smoke.
The summary text is visible.
The weekly table shows W40 / W41 / W42 rows.
Totals show accepted=260 and blocked=25.
```

If the local environment is headless, report that manual GUI smoke was not run and explain why.

---

## 15. Safety Boundaries

Expected added files:

```text
pysi/gui/japanese_rice_first_runner_view.py
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Optional modified file:

```text
pysi/gui/__init__.py
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

Do not add cost / profit logic in this slice.

---

## 16. Acceptance Criteria

This request is complete when:

```text
pysi/gui/japanese_rice_first_runner_view.py exists
the module imports without opening a GUI window
extract_japanese_rice_first_runner_gui_model(...) exists
build_japanese_rice_weekly_capacity_gate_rows(...) exists
format_japanese_rice_gui_summary_text(...) exists
the helper consumes demo_summary and cli_summary_lines
weekly rows are extracted from demo_summary.capacity_gate_summary.weekly
summary text is generated from cli_summary_lines
focused tests pass without opening a real GUI window
weekly rows show 80/90/80/0, 95/90/90/5, 110/90/90/20
totals show requested=285, capacity=270, accepted=260, blocked=25
optional Tkinter launcher can be manually run
no full planner behavior is changed
no existing GUI layout is broken
no NetworkX dependency is changed
no scenario master CSV files are changed
existing runner output contract tests still pass
existing Japanese Rice tests still pass
capacity integration tests still pass
compileall passes
```

---

## 17. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
What GUI wrapper file was added?
What test file was added?
Does the module import without opening a GUI window?
Does extract_japanese_rice_first_runner_gui_model(...) exist?
Does build_japanese_rice_weekly_capacity_gate_rows(...) exist?
Does format_japanese_rice_gui_summary_text(...) exist?
Does the wrapper consume demo_summary and cli_summary_lines?
Does the GUI model show scenario/product/contract?
Does the GUI model show weekly rows W40/W41/W42?
Does the GUI model show totals requested=285, capacity=270, accepted=260, blocked=25?
Was a Tkinter launcher implemented?
If yes, what command runs it?
Was manual GUI smoke run?
Did you modify existing cockpit_tk.py?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 18. Development Meaning

Before this request:

```text
The Japanese Rice runner emits a stable CLI / GUI wrapper-readable signal.
```

After this request:

```text
A GUI wrapper can display that signal.
```

This is the first move from:

```text
CLI-visible result
```

to:

```text
GUI-visible result
```

This is the correct next step before note publication.

In simple terms:

```text
The runner now sends a stable signal.
This request puts that signal on a small dashboard.
```
