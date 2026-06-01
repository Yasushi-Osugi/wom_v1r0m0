# Japanese Rice First Runner GUI Wrapper Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-06-01  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_runner_gui_wrapper_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_first_runner_gui_wrapper_vertical_slice_request.md
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

---

## 1. Purpose

This completion memo records the successful completion of the Japanese Rice first runner GUI wrapper vertical slice.

This phase moved the Japanese Rice Case from:

```text
CLI-visible result
```

to:

```text
GUI-visible result
```

The runner already emitted a stable output contract:

```text
contract_version
demo_summary
cli_summary_lines
```

This slice added a small independent GUI wrapper that consumes that stable contract and displays the Japanese Rice first PSI smoke result.

This is not a full WOM cockpit.

This is not full PSI planning.

This is the first visible GUI wrapper for the Japanese Rice Case.

---

## 2. Key Commit

Implementation commit:

```text
63d7e5b Add Japanese Rice first runner GUI wrapper
```

Related preceding commits:

```text
39943b8 Add Japanese Rice first runner GUI wrapper Codex request
8a56a5f Add Japanese Rice first runner GUI wrapper vertical slice design
ebca2a3 Add Japanese Rice first runner output contract completion memo
6fba57d Add Japanese Rice runner output contract
faa64d1 Add Japanese Rice first runner output contract CLI smoke Codex request
c7e075f Add Japanese Rice first runner output contract and CLI smoke design
88ce357 Add WOM TOBE management simulator image
a15e66f Add Japanese Rice first PSI runner actual plan node upgrade completion memo
5b5b286 Upgrade Japanese rice first PSI runner diagnostics
```

---

## 3. Files Added

This implementation added:

```text
pysi/gui/japanese_rice_first_runner_view.py
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

The commit created:

```text
2 files changed
345 insertions
```

No existing cockpit file was modified.

Specifically, this phase did not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

No planner engine file was modified.

No scenario master CSV file was modified.

No NetworkX dependency was removed or modified.

---

## 4. GUI Wrapper Added

The new GUI wrapper file is:

```text
pysi/gui/japanese_rice_first_runner_view.py
```

The wrapper consumes:

```python
run_japanese_rice_first_psi_vslice(...)
```

and reads the stable runner output contract:

```text
demo_summary
cli_summary_lines
contract_version
```

The wrapper does not directly depend on deep internal diagnostic fields when stable contract fields are available.

This keeps the GUI layer protected from future internal runner changes.

---

## 5. Import-Safe Design

The module can be imported without opening a GUI window.

This is important for tests and future integration.

The import-smoke test confirms that:

```text
pysi.gui.japanese_rice_first_runner_view
```

can be imported without launching Tkinter automatically.

This avoids fragile GUI behavior during pytest execution.

---

## 6. Helper Functions Implemented

The following helper functions were implemented.

### 6.1 GUI model extraction

```python
extract_japanese_rice_first_runner_gui_model(...)
```

This function converts the runner result into a GUI-friendly model.

The model includes:

```text
available
title
scenario_id
product_name
contract_version
runner_mode
full_psi_plan
summary_text
weekly_rows
totals
management_message
```

### 6.2 Weekly capacity gate rows

```python
build_japanese_rice_weekly_capacity_gate_rows(...)
```

This function reads:

```text
demo_summary.capacity_gate_summary.weekly
```

and returns chart/table-ready weekly rows.

It preserves:

```text
demo_summary["weeks"]
```

order when available.

It falls back to sorted weekly keys when weeks are missing.

### 6.3 GUI summary text

```python
format_japanese_rice_gui_summary_text(...)
```

This function formats GUI summary text directly from:

```text
result["cli_summary_lines"]
```

This means the GUI text output remains aligned with the CLI summary output.

---

## 7. Safe Unavailable Model

The wrapper returns a safe unavailable model for malformed or unavailable runner results.

Expected behavior:

```text
available = False
weekly_rows = []
totals = {}
summary_text explains that Japanese Rice first PSI smoke could not be run
error is available
```

This prevents the GUI display layer from crashing on bad input.

---

## 8. Tkinter Launcher Implemented

A minimal Tkinter launcher was implemented.

Command:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Expected behavior:

```text
a small Tkinter window opens
the title is WOM Japanese Rice First PSI Smoke
summary text is displayed
weekly table is displayed
totals are displayed
management message is displayed
```

This launcher is intentionally simple.

It is not a full cockpit.

It is the first small GUI wrapper for the Rice Case.

---

## 9. GUI Display Confirmed on Windows

Manual GUI smoke was run locally on Windows.

Command used:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Observed result:

```text
Tkinter window opened successfully.
Window title: WOM Japanese Rice First PSI Smoke.
Header displayed.
Scenario / product / contract / mode / full PSI flag displayed.
CLI summary text displayed.
Weekly table displayed.
Totals displayed.
Management message displayed.
```

This confirms the Japanese Rice Case is now GUI-visible.

---

## 10. Displayed Scenario Information

The GUI window displays:

```text
Scenario: JAPANESE_RICE_VSLICE_001
Product: JAPANESE_RICE_STANDARD
Contract: japanese_rice_first_runner_output_v0r1
Mode: diagnostic_first_psi_smoke
Full PSI plan: False
```

This confirms that the GUI wrapper is showing the stable runner output contract, not a hidden internal state.

---

## 11. Displayed Summary Text

The GUI displays the CLI summary lines, including:

```text
WOM Japanese Rice first PSI smoke
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

This is the first reusable text display of the Japanese Rice runner result in GUI form.

---

## 12. Displayed Weekly Table

The GUI displays the weekly capacity gate table:

```text
Week      Requested  Capacity  Accepted  Blocked
2027-W40  80         90        80        0
2027-W41  95         90        90        5
2027-W42  110        90        90        20
```

This table is the first visible weekly requested / capacity / accepted / blocked table for the Japanese Rice Case.

---

## 13. Displayed Totals

The GUI displays:

```text
requested = 285
capacity = 270
accepted = 260
blocked = 25
```

This is the first simple management-visible capacity-gate summary for the Rice Case.

---

## 14. Displayed Management Message

The GUI displays:

```text
DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon.
```

This message translates the lot-level diagnostic into a human-readable management statement.

---

## 15. Tests Added

Focused test file:

```text
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

The tests verify:

```text
module imports without opening a GUI window
extract_japanese_rice_first_runner_gui_model(...) exists and works
build_japanese_rice_weekly_capacity_gate_rows(...) exists and works
format_japanese_rice_gui_summary_text(...) exists and works
wrapper consumes demo_summary and cli_summary_lines
GUI model shows scenario / product / contract
GUI model shows weekly rows W40 / W41 / W42
GUI model shows totals requested=285, capacity=270, accepted=260, blocked=25
unavailable model behavior is safe
sorted-key fallback works
```

---

## 16. Tests Executed

Focused GUI wrapper test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Observed result:

```text
7 passed
```

Output contract test:

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
python -m compileall -q pysi/gui/japanese_rice_first_runner_view.py tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py
```

Observed result:

```text
compileall completed successfully
```

Manual Windows GUI smoke:

```bat
python -m pysi.gui.japanese_rice_first_runner_view --scenario-root examples/scenarios/japanese_rice_vslice_001
```

Observed result:

```text
GUI window opened successfully
```

---

## 17. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
existing cockpit layout
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
independent GUI wrapper
GUI model helper
weekly table helper
summary text helper
focused tests
optional Tkinter launcher
```

This is consistent with the current strategy:

```text
small visible wrapper first
full cockpit integration later
```

---

## 18. Current Japanese Rice Case State

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
independent GUI wrapper
```

The current visibility chain is:

```text
run_japanese_rice_first_psi_vslice(...)
    ↓
contract_version
demo_summary
cli_summary_lines
    ↓
pysi/gui/japanese_rice_first_runner_view.py
    ↓
Tkinter GUI window
    ↓
weekly requested / capacity / accepted / blocked table
```

---

## 19. Development Meaning

This is a major milestone for the Rice Case.

Before this phase:

```text
The runner emitted a stable CLI / GUI wrapper-readable signal.
```

After this phase:

```text
A GUI wrapper displays that signal.
```

This is the first step from:

```text
internal diagnostic
```

to:

```text
visible user-facing demonstration
```

It is not yet the full WOM cockpit, but it proves that the output contract can drive a GUI display.

---

## 20. Relationship to Note Publication

This phase supports the earlier decision:

```text
Do not publish too early.
First build visible GUI evidence.
```

The Rice Case is now closer to public demonstration because a GUI window can show the first result.

However, note publication should still wait until at least one of the following is added:

```text
scenario variation
before / after comparison
weekly chart
cost / profit impact
integration into existing cockpit
```

The current GUI wrapper is a good first screen.

The next publishable leap is comparison or chart visualization.

---

## 21. Still Deferred

The following remain intentionally deferred.

### 21.1 Existing cockpit integration

Not yet implemented:

```text
menu item or button in existing WOM cockpit
embedding this wrapper into cockpit_tk.py
management cockpit tab
```

### 21.2 Scenario variation

Not yet implemented:

```text
DC_KANTO capacity changed from 90 to 100
demand W42 changed from 110 to 130
before / after comparison
```

### 21.3 Chart visualization

Not yet implemented:

```text
requested / capacity / accepted / blocked weekly chart
blocked lots line chart
capacity usage chart
```

### 21.4 Cost / Profit Structure connection

Not yet implemented:

```text
accepted lots to revenue
blocked lots to lost sales
profit impact
cost structure ratio impact
```

### 21.5 Full PSI and event flow

Not yet implemented:

```text
canonical event generation
leadtime-aware propagation
multi-gate capacity flow
inventory carry-over
CO / backlog
```

---

## 22. Recommended Next Step

The next design should likely be:

```text
docs/design/japanese_rice_first_runner_gui_wrapper_completion.md
```

only if a separate shorter public-facing completion note is desired.

However, because this memo already records the GUI wrapper completion, the more natural next design is:

```text
docs/design/japanese_rice_first_runner_chart_dataset_vertical_slice.md
```

Purpose:

```text
Convert the GUI model weekly_rows into chart-ready dataset and define a simple requested / capacity / accepted / blocked visualization path.
```

Alternative next design:

```text
docs/design/japanese_rice_first_runner_scenario_variation_vertical_slice.md
```

Purpose:

```text
Define a simple scenario variation such as DC_KANTO capacity 90 -> 100 and show before / after accepted / blocked.
```

Recommended order:

```text
1. GUI wrapper completion memo
2. Chart-ready dataset / simple chart
3. Scenario variation
4. Before / after comparison
5. Cost / profit impact
6. Existing cockpit integration
```

The reason is simple:

```text
The GUI now shows a table.
The next useful visual is a chart.
Then a scenario comparison.
```

---

## 23. Future GUI Meaning

The GUI should continue to consume stable contracts rather than deep internal fields.

The ideal chain remains:

```text
runner
    ↓
demo_summary
    ↓
GUI model
    ↓
table / chart / cockpit
```

This keeps the GUI robust.

It also keeps future iPhone Case and Tesla Case easier to add.

---

## 24. Completion Summary

Completed:

```text
pysi/gui/japanese_rice_first_runner_view.py added
tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py added
module imports without opening a GUI window
extract_japanese_rice_first_runner_gui_model(...) implemented
build_japanese_rice_weekly_capacity_gate_rows(...) implemented
format_japanese_rice_gui_summary_text(...) implemented
wrapper consumes demo_summary and cli_summary_lines
GUI model shows scenario/product/contract
GUI model shows weekly rows W40/W41/W42
GUI model shows totals requested=285, capacity=270, accepted=260, blocked=25
Tkinter launcher implemented
manual Windows GUI smoke succeeded
existing cockpit_tk.py was not modified
planner behavior unchanged
scenario master CSV files unchanged
NetworkX untouched
focused GUI wrapper tests passed
output contract tests passed
existing Japanese Rice tests passed
capacity integration tests passed
compileall passed
```

Current milestone:

```text
Japanese Rice Case is now GUI-visible through an independent Tkinter wrapper.
```

In simple terms:

```text
The runner sends a stable signal.
The GUI wrapper now displays that signal.
The Rice Case has reached the first visible dashboard stage.
