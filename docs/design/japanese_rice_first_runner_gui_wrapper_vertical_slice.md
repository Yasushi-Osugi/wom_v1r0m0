# Japanese Rice First Runner GUI Wrapper Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice.md`

**Strategic role:** Connect the stable Japanese Rice first runner output contract to a minimal WOM GUI display  
**Primary case:** Japanese Rice Case  
**Current north star:** Management-visible simulation before recommendation AI  
**Immediate goal:** Launch a WOM GUI path that can show the Japanese Rice first runner summary without changing the full planner engine

---

## 1. Purpose

This memo defines the next vertical slice for Japanese Rice Case.

The current runner can already return a stable output contract:

```text
run_japanese_rice_first_psi_vslice(...)
  ↓
contract_version
demo_summary
cli_summary_lines
```

The next step is to connect that output to a minimal GUI wrapper.

The objective is not yet a complete cockpit.

The objective is:

```text
WOM GUI can launch.
User can run Japanese Rice first PSI smoke.
GUI can display the runner's stable demo summary.
GUI can show requested / capacity / accepted / blocked by week.
```

This is the next practical step toward public demonstration.

---

## 2. Why This Comes Before note Publication

The WOM public message should eventually be strong:

```text
Large hypothesis proven through public cases:
  Rice Case
  iPhone Case
  Tesla Case
```

However, publishing too early is not recommended.

The current priority is:

```text
not article first
not slogan first
not recommendation AI first
```

The current priority is:

```text
visible working GUI first
```

The logic is:

```text
1. Runner output is stable.
2. GUI displays the stable output.
3. Scenario changes can be compared.
4. Then note article can show actual screenshots and operation.
```

A note article before visible GUI would have limited impact.

A note article after the GUI shows the Rice Case will have much stronger impact.

This design therefore focuses on implementation.

No sidetrack.

---

## 3. Current Completed Foundations

### 3.1 North Star

The WOM north star is recorded in:

```text
docs/design/wom_tobe_management_simulator_image.md
```

Key principle:

```text
Visualization before recommendation.
```

### 3.2 Japanese Rice output contract

Completed in:

```text
docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke_completion.md
```

Implementation commit:

```text
6fba57d Add Japanese Rice runner output contract
```

The runner now returns:

```text
contract_version
demo_summary
cli_summary_lines
```

### 3.3 Current runner

Runner:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Public function:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

CLI support:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format summary
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format json
```

Current result contract:

```text
contract_version = japanese_rice_first_runner_output_v0r1
demo_summary
cli_summary_lines
```

---

## 4. Current Runner Output to Use

The GUI wrapper should not parse deep internal diagnostic details.

It should consume:

```text
demo_summary
cli_summary_lines
```

This is the stable meter signal.

### 4.1 Required demo_summary fields

```text
demo_summary.title
demo_summary.scenario_id
demo_summary.product_name
demo_summary.runner_mode
demo_summary.full_psi_plan
demo_summary.weeks
demo_summary.master_counts
demo_summary.plan_node_summary
demo_summary.capacity_gate_summary
demo_summary.management_message
```

### 4.2 Required cli_summary_lines

```text
cli_summary_lines = list[str]
```

The simplest GUI output can display these lines directly in a text panel.

This makes the first GUI wrapper low risk.

---

## 5. GUI Wrapper Goal

The first GUI wrapper should show:

```text
Scenario:
  JAPANESE_RICE_VSLICE_001

Product:
  JAPANESE_RICE_STANDARD

Runner mode:
  diagnostic_first_psi_smoke

Contract:
  japanese_rice_first_runner_output_v0r1

Master counts:
  capacity_rows = 9
  demand_rows = 3
  demand_lots = 285
  network_nodes = 9
  network_edges = 8

Actual ProductPlanNode:
  MARKET_TOKYO.psi4demand[week][0]
  W40 = 80
  W41 = 95
  W42 = 110

DC_KANTO S capacity gate:
  W40 requested 80 / capacity 90 / accepted 80 / blocked 0
  W41 requested 95 / capacity 90 / accepted 90 / blocked 5
  W42 requested 110 / capacity 90 / accepted 90 / blocked 20

Totals:
  requested 285
  capacity 270
  accepted 260
  blocked 25
```

This is the first management-visible screen.

---

## 6. Scope of This Vertical Slice

### 6.1 In scope

The first GUI wrapper should:

```text
launch without full planner engine changes
call run_japanese_rice_first_psi_vslice(...)
read demo_summary
read cli_summary_lines
display cli_summary_lines in a text panel
display compact weekly table
optionally prepare chart-ready rows
preserve current GUI behavior
add focused tests for GUI-adjacent helpers
```

### 6.2 Out of scope

Do not implement yet:

```text
full GUI redesign
full cockpit redesign
interactive scenario editing
full PSI graph integration
full network graph integration
cost / profit chart
multi-gate capacity flow
leadtime-aware propagation
recommendation AI
note article generation
```

This is a GUI wrapper vertical slice.

Not a GUI rebuild.

---

## 7. Implementation Strategy

There are two possible approaches.

### 7.1 Preferred: small independent GUI wrapper module

Add a small GUI wrapper module:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

This module can provide:

```python
launch_japanese_rice_first_runner_view(...)
```

or:

```python
JapaneseRiceFirstRunnerView
```

Purpose:

```text
Show runner output without touching the existing full cockpit too much.
```

Advantages:

```text
low risk
easy to test helper logic
easy to delete or replace later
does not destabilize existing cockpit
```

### 7.2 Alternative: add button to existing cockpit

Modify an existing GUI file such as:

```text
pysi/gui/cockpit_tk.py
```

to add a button:

```text
Run Japanese Rice Smoke
```

Button action:

```text
call run_japanese_rice_first_psi_vslice(...)
display cli_summary_lines
display compact table
```

This is useful but higher risk.

Recommended order:

```text
1. Add independent view/helper first.
2. Then add a minimal cockpit hook or menu button later.
```

---

## 8. Recommended Design Decision

For this vertical slice, prefer:

```text
independent GUI wrapper first
```

Recommended new files:

```text
pysi/gui/japanese_rice_first_runner_view.py
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Optional later integration:

```text
pysi/gui/cockpit_tk.py
```

This keeps the slice safe.

It also aligns with the current state:

```text
runner output contract is stable
GUI wrapper should consume stable contract
existing GUI should not be disturbed yet
```

---

## 9. GUI Display Components

### 9.1 Header

Show:

```text
WOM Japanese Rice First PSI Smoke
```

### 9.2 Scenario information

Show:

```text
Scenario ID
Product Name
Runner Mode
Full PSI Plan
Contract Version
```

### 9.3 CLI summary text panel

Display:

```text
"
".join(result["cli_summary_lines"])
```

This is the minimum reliable display.

### 9.4 Weekly table

Build rows from:

```text
demo_summary.capacity_gate_summary.weekly
```

Columns:

```text
week
requested
capacity
accepted
blocked
```

Expected rows:

```text
2027-W40 | 80  | 90 | 80 | 0
2027-W41 | 95  | 90 | 90 | 5
2027-W42 | 110 | 90 | 90 | 20
```

### 9.5 Totals

Show:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 9.6 Management message

Show:

```text
DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon.
```

---

## 10. Chart-Ready Data

This slice may prepare chart-ready data but does not need to render charts yet.

Recommended helper:

```python
build_japanese_rice_weekly_capacity_gate_rows(result: dict) -> list[dict]
```

Expected rows:

```python
[
    {
        "week": "2027-W40",
        "requested": 80,
        "capacity": 90,
        "accepted": 80,
        "blocked": 0,
    },
    {
        "week": "2027-W41",
        "requested": 95,
        "capacity": 90,
        "accepted": 90,
        "blocked": 5,
    },
    {
        "week": "2027-W42",
        "requested": 110,
        "capacity": 90,
        "accepted": 90,
        "blocked": 20,
    },
]
```

This helper prepares the next chart panel without forcing it now.

---

## 11. GUI Wrapper Entry Point

Recommended CLI-style GUI launch command:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

This command should:

```text
open a small Tkinter window
run the Japanese Rice first runner
display cli_summary_lines
display weekly table
```

If a headless environment is detected, tests should not require opening a real window.

Testing should focus on pure helper functions.

---

## 12. Headless Test Strategy

GUI tests are often fragile.

Therefore, separate:

```text
pure summary extraction helpers
actual Tkinter rendering
```

Focus tests on pure functions:

```python
extract_japanese_rice_gui_summary(result)
build_japanese_rice_weekly_capacity_gate_rows(result)
format_gui_text_lines(result)
```

Only smoke-test import of GUI module if safe.

Do not require a real Tkinter window in CI unless the existing test environment supports it.

---

## 13. Recommended Helper Functions

Add helper functions:

```python
extract_japanese_rice_first_runner_gui_model(result: dict) -> dict
```

Output:

```python
{
    "title": "...",
    "scenario_id": "...",
    "product_name": "...",
    "contract_version": "...",
    "summary_text": "...",
    "weekly_rows": [...],
    "totals": {...},
    "management_message": "...",
}
```

Add:

```python
build_japanese_rice_weekly_capacity_gate_rows(result: dict) -> list[dict]
```

Add:

```python
format_japanese_rice_gui_summary_text(result: dict) -> str
```

These helpers can be tested without opening GUI.

---

## 14. GUI Model Contract

Recommended GUI model:

```python
{
    "title": "WOM Japanese Rice First PSI Smoke",
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "contract_version": "japanese_rice_first_runner_output_v0r1",
    "runner_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    "summary_text": "...",
    "weekly_rows": [
        {
            "week": "2027-W40",
            "requested": 80,
            "capacity": 90,
            "accepted": 80,
            "blocked": 0,
        },
        {
            "week": "2027-W41",
            "requested": 95,
            "capacity": 90,
            "accepted": 90,
            "blocked": 5,
        },
        {
            "week": "2027-W42",
            "requested": 110,
            "capacity": 90,
            "accepted": 90,
            "blocked": 20,
        },
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

This GUI model should be stable enough to support both:

```text
text display
table display
future chart display
```

---

## 15. Error Handling

If runner fails, GUI should show a clear message.

Recommended model:

```python
{
    "available": False,
    "error": "...",
    "summary_text": "Japanese Rice first PSI smoke could not be run: ...",
}
```

Do not crash the GUI.

Do not hide the exception silently.

---

## 16. Relationship to Existing WOM GUI

The existing WOM GUI likely has broader responsibilities:

```text
scenario loading
node selection
PSI display
network display
cockpit KPI
trace/event views
```

This vertical slice should not try to merge everything.

The first wrapper should be allowed to be small.

Future integration options:

```text
add menu item
add button in cockpit
add tab in management cockpit
embed weekly table
embed chart panel
```

The first deliverable is a safe visible wrapper.

---

## 17. Relationship to Note Publication

Note publication should wait until the GUI can show:

```text
one working scenario
one visible output
one meaningful before/after or scenario result
```

This GUI wrapper is the next step toward that.

The publication path is:

```text
1. Runner output contract
2. GUI wrapper visible screen
3. Scenario variation
4. Comparison output
5. Screenshot / demo video
6. note article
```

This avoids premature publication.

---

## 18. Scenario Variation Roadmap

After the first GUI wrapper, the next important addition is scenario variation.

Possible variation knobs:

```text
DC_KANTO capacity 90 → 100
demand W42 110 → 130
capacity W41 90 → 70
```

The GUI should eventually show comparison:

```text
Base scenario
Changed scenario
Delta accepted
Delta blocked
Delta shortage
```

This is the point where note publication becomes much stronger.

---

## 19. Tests Required for Future Codex Request

Add test:

```text
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Test pure helpers:

### 19.1 GUI model extraction

Assert:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
contract_version = japanese_rice_first_runner_output_v0r1
```

### 19.2 Summary text

Assert text includes:

```text
WOM Japanese Rice first PSI smoke
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

### 19.3 Weekly rows

Assert rows:

```text
2027-W40 requested=80 capacity=90 accepted=80 blocked=0
2027-W41 requested=95 capacity=90 accepted=90 blocked=5
2027-W42 requested=110 capacity=90 accepted=90 blocked=20
```

### 19.4 Totals

Assert:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

### 19.5 No GUI dependency for pure tests

The focused test should not require opening a real GUI window.

---

## 20. Recommended Test Commands

Focused GUI wrapper helper test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Existing runner output contract test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing related Japanese Rice tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Compile check:

```bat
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

---

## 21. Acceptance Criteria

This vertical slice will be complete when:

```text
a Japanese Rice GUI wrapper module exists
the wrapper consumes run_japanese_rice_first_psi_vslice(...)
the wrapper consumes demo_summary and cli_summary_lines
a pure GUI model helper exists
weekly rows are extracted from demo_summary.capacity_gate_summary
summary text is generated from cli_summary_lines
focused tests pass without requiring real GUI window
optional Tkinter launch command is available
no full planner behavior is changed
no existing GUI layout is broken
no NetworkX dependency is changed
no scenario master CSV files are changed
```

---

## 22. Future Codex Request Name

Recommended next Codex request:

```text
docs/codex_requests/japanese_rice_first_runner_gui_wrapper_vertical_slice_request.md
```

Scope:

```text
add pysi/gui/japanese_rice_first_runner_view.py
add pure helper functions
add optional Tkinter launcher
add focused tests
do not modify existing cockpit unless necessary
do not change planner behavior
do not change scenario masters
```

---

## 23. Development Meaning

This slice is important because it moves WOM from:

```text
CLI-readable output
```

toward:

```text
human-visible GUI output
```

This is the correct direction before any note publication.

The near-term goal is not to write about WOM.

The near-term goal is to show WOM.

In simple terms:

```text
The runner now sends a stable signal.
The next task is to put that signal on the dashboard.
```

When that dashboard is visible, the Rice Case becomes a real demonstration candidate.

That is the moment when public note publication becomes worthwhile.
