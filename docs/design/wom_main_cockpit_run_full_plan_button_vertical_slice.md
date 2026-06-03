# WOM Main Cockpit Run Full Plan Button Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-06-03  
**Status:** Design memo  
**Target path:** `docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md`

**Preceding design docs / completion memos:**

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice_completion.md
docs/design/wom_run_full_plan_result_viewer_vertical_slice.md
docs/design/wom_run_full_plan_result_viewer_vertical_slice_completion.md
```

**Implemented chain:**

```text
be4c4a9 Add WOM run full plan bridge
4570ade Add WOM run full plan graph panel adapter
4a0c2c9 Add WOM run full plan result viewer
d38ae6e Add WOM run full plan result viewer completion memo
```

**Strategic role:** Add a safe main cockpit entry point to the new Run Full Plan standard-output path  
**Primary scope:** main cockpit button/menu addition, no replacement of legacy Run Full Plan, launch standard viewer  
**Current north star:** Global Weekly Economic & Management Simulation Tool  
**Development principle:** Parallel path first, replacement later; contract-first expansion

---

## 1. Purpose

This memo defines how to connect the newly proven `Run Full Plan → standard output → adapter → viewer` path to the existing WOM main cockpit.

The current proven vertical line is:

```text
python -m pysi.runners.run_full_plan
  ↓
full_plan_result.json
visual_capacity_gate_weekly.csv
  ↓
wom_run_full_plan_graph_panel_adapter
  ↓
wom_run_full_plan_result_viewer
  ↓
screen display
```

The next step is to add a safe entry point from the existing WOM GUI main cockpit.

However, the existing cockpit already has an original `Run Full Plan` button in the upper-right area.

Therefore, this slice must not replace the existing button.

The new function should be added as a separate button or menu item:

```text
Run Full Plan → Viewer
```

or:

```text
Run Full Plan v2 Export/View
```

This makes the difference explicit.

---

## 2. Key Design Decision

The existing `Run Full Plan` and the new standard-output path must remain separate in this slice.

### Existing button

```text
Run Full Plan
```

Meaning:

```text
legacy / existing WOM GUI internal execution path
updates or uses existing internal GUI data model
preserves current cockpit behavior
```

### New button

```text
Run Full Plan → Viewer
```

Meaning:

```text
new output-contract based execution path
calls pysi.runners.run_full_plan
writes FullPlanResult JSON and visual CSV
opens the read-only result viewer
does not replace existing internal GUI flow
```

This separation is important because both paths currently have different responsibilities and different maturity levels.

---

## 3. Why Not Replace the Existing Run Full Plan Button Yet

Replacing the existing cockpit button now would be risky.

Reasons:

```text
the current Run Full Plan bridge is still diagnostic_smoke_bridge
full_psi_plan remains False
the new viewer currently displays only capacity gate output
the existing GUI may depend on internal runtime model updates
the existing button may support behaviors not yet covered by the new contract path
```

Therefore, this slice should be additive.

Recommended rule:

```text
Do not replace the existing Run Full Plan button.
Add a separate Run Full Plan → Viewer button or menu command.
```

This preserves the legacy runway while opening the new runway.

---

## 4. Current Architecture Before This Slice

Current new path:

```text
CLI:
  python -m pysi.runners.run_full_plan
    ↓
  outputs/run_full_plan/<run_id>/
    ├─ full_plan_result.json
    └─ visual_capacity_gate_weekly.csv
    ↓
  python -m pysi.gui.wom_run_full_plan_result_viewer --run-dir outputs/run_full_plan/<run_id>
```

Current viewer:

```text
pysi/gui/wom_run_full_plan_result_viewer.py
```

Current adapter:

```text
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
```

Current bridge runner:

```text
pysi/runners/run_full_plan.py
```

---

## 5. Target Architecture After This Slice

Target main cockpit connection:

```text
main cockpit
  ↓
Run Full Plan → Viewer button
  ↓
build WomRunConfig
  ↓
run_full_plan(config)
  ↓
write_full_plan_outputs(...)
  ↓
outputs/run_full_plan/<run_id>/
  ↓
launch_run_full_plan_result_viewer(run_dir)
```

This should reuse the existing viewer.

It should not embed all viewer logic inside the cockpit.

---

## 6. Scope

### 6.1 In scope

This vertical slice should define:

```text
new button or menu item in main cockpit
clear label distinguishing from legacy Run Full Plan
button handler for new standard-output path
run_id generation
scenario_root resolution
call run_full_plan(config)
write outputs
open read-only viewer
safe error handling
focused tests
manual Windows GUI smoke
```

### 6.2 Out of scope

Do not implement:

```text
replacement of existing Run Full Plan button
deep cockpit refactoring
embedding the result viewer chart directly into the main cockpit
scenario editing
capacity override editing
new planner behavior
cost / money graph
tariff graph
Rule Base / AI diagnosis
BI connector
database persistence
```

Do not modify:

```text
planner behavior
existing Run Full Plan behavior
scenario master CSV files
NetworkX usage
Japanese Rice runner contract
Run Full Plan bridge contract
graph panel adapter contract
result viewer contract
```

---

## 7. Recommended Button Label

Recommended visible label:

```text
Run Full Plan → Viewer
```

Alternative labels:

```text
Run Full Plan v2 Export/View
Run Full Plan Export/View
Run Full Plan JSON/CSV Viewer
```

Recommended for v0r1:

```text
Run Full Plan → Viewer
```

Reason:

```text
short enough for a button
clearly different from existing Run Full Plan
emphasizes output-to-viewer path
does not overstate final full-plan readiness
```

---

## 8. Tooltip / Help Text

If the current GUI framework supports tooltip or nearby help text, use:

```text
Run the new output-contract based Run Full Plan path.
It writes FullPlanResult JSON and visualization CSV files,
then opens the read-only result viewer.
This does not replace the existing Run Full Plan button.
```

If tooltip is not available, add a concise comment in code and possibly a status message.

---

## 9. Recommended Initial Position

If the existing `Run Full Plan` button is in the upper-right area, place the new button near it.

Suggested arrangement:

```text
[Run Full Plan]  [Run Full Plan → Viewer]
```

or stacked:

```text
[Run Full Plan]
[Run Full Plan → Viewer]
```

The visual difference should be clear.

Avoid renaming the existing button in this slice.

---

## 10. Scenario Root Resolution

The button handler needs a `scenario_root`.

For the first implementation, the safest option is to use the Japanese Rice scenario root as the default:

```text
examples/scenarios/japanese_rice_vslice_001
```

However, if the cockpit already has a selected scenario root, use that existing cockpit state.

Recommended resolution order:

```text
1. scenario root selected / configured in cockpit, if available
2. default Japanese Rice vertical slice scenario
3. error message if neither exists
```

The first slice can harden this gradually.

Do not build a full scenario selector in this request unless it already exists.

---

## 11. Scenario ID

For v0r1:

```text
scenario_id = japanese_rice_vslice_001
```

if the default Japanese Rice scenario is used.

If the cockpit has a selected scenario id, use it.

The result viewer should display the scenario id through the existing output files.

---

## 12. Run ID Generation

The new button should generate a run id.

Recommended pattern:

```text
cockpit_viewer_YYYYMMDD_HHMMSS
```

Example:

```text
cockpit_viewer_20260603_173500
```

This avoids overwriting previous runs.

The run output directory should be:

```text
outputs/run_full_plan/<run_id>/
```

---

## 13. Button Handler Flow

Recommended conceptual handler:

```python
def on_run_full_plan_viewer_clicked(...):
    scenario_root = resolve_scenario_root()
    scenario_id = resolve_scenario_id()
    run_id = make_cockpit_run_id()

    config = WomRunConfig(
        scenario_root=scenario_root,
        scenario_id=scenario_id,
        run_id=run_id,
        output_dir="outputs/run_full_plan",
        run_mode="diagnostic_smoke_bridge",
    )

    result = run_full_plan(config)
    result = write_full_plan_outputs(result, output_dir=config.output_dir)

    run_dir = Path(config.output_dir) / run_id
    launch_run_full_plan_result_viewer(run_dir)
```

Actual signatures should follow the implemented modules.

---

## 14. Imports

The cockpit code should import:

```python
from pysi.runners.run_full_plan import WomRunConfig, run_full_plan, write_full_plan_outputs
from pysi.gui.wom_run_full_plan_result_viewer import launch_run_full_plan_result_viewer
```

If direct imports risk slowing cockpit import, import inside the button handler.

Recommended:

```python
def on_run_full_plan_viewer_clicked(...):
    from pysi.runners.run_full_plan import WomRunConfig, run_full_plan, write_full_plan_outputs
    from pysi.gui.wom_run_full_plan_result_viewer import launch_run_full_plan_result_viewer
    ...
```

This limits side effects and keeps cockpit startup safer.

---

## 15. Error Handling

The button handler should catch expected errors and show a concise message.

Examples:

```text
missing scenario root
Run Full Plan failed
output writing failed
viewer launch failed
```

In Tkinter, use:

```python
messagebox.showerror(...)
```

or the existing cockpit status/error display mechanism.

The cockpit should not crash.

---

## 16. Status Message

If a status label or log area exists, display:

```text
Running Run Full Plan → Viewer...
Run output written to outputs/run_full_plan/<run_id>
Opening result viewer...
```

On success:

```text
Run Full Plan → Viewer completed: <run_id>
```

On failure:

```text
Run Full Plan → Viewer failed: <reason>
```

---

## 17. Truthfulness Note

The new button should not imply final full planning is complete.

Somewhere in tooltip, status, or viewer it should remain clear:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
```

The existing viewer already displays this.

The button label should not be:

```text
Run Final Full Plan
```

or:

```text
Run Production Full Plan
```

Use a restrained label.

---

## 18. Relationship to Existing Run Full Plan Button

This slice must preserve the existing button.

Existing:

```text
Run Full Plan
```

New:

```text
Run Full Plan → Viewer
```

The new button should not call the existing button handler.

The existing button should not call the new standard-output handler.

They are intentionally parallel for now.

Future unification can happen after the standard output path matures.

---

## 19. Relationship to Main Cockpit Integration

This is the first cockpit integration step, but it is intentionally shallow.

It adds an entry point to a proven external viewer.

It does not yet embed the viewer into the main cockpit layout.

This minimizes risk.

Future integration can move from:

```text
launch separate read-only viewer
```

to:

```text
embed graph panel inside cockpit
```

only after stable dataset expansion.

---

## 20. Expected Implementation File

The most likely file to modify is the main cockpit GUI module.

Current likely candidates include:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Codex should inspect the source tree and identify the actual file containing the existing upper-right `Run Full Plan` button.

Do not guess blindly.

The implementation request should ask Codex to report:

```text
Where is the existing Run Full Plan button implemented?
Where was the new button added?
What handler was added?
```

---

## 21. Testing Strategy

GUI tests are hard to automate fully.

Focus automated tests on:

```text
helper function for run_id generation
helper function for scenario_root resolution if added
handler can be imported
source contains new button label
source contains no replacement of existing button label
```

If the implementation adds a pure helper such as:

```python
build_run_full_plan_viewer_config(...)
```

test that directly.

Manual Windows smoke is important.

---

## 22. Recommended Helper Functions

If modifying cockpit code directly is too risky, create a small helper module:

```text
pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py
```

Possible functions:

```python
def make_cockpit_viewer_run_id(now=None) -> str:
    ...

def build_cockpit_viewer_run_config(
    *,
    scenario_root: str,
    scenario_id: str,
    run_id: str | None = None,
) -> WomRunConfig:
    ...

def run_full_plan_and_open_viewer(config: WomRunConfig) -> int:
    ...
```

Then the cockpit button only calls this helper.

This is safer than putting all logic inside the GUI file.

Recommended v0r1 approach:

```text
add helper module
add small button handler that calls helper
```

---

## 23. Manual Smoke Test

After implementation, run the main cockpit in the normal way.

If current launch command is known, use it.

If current launch command is:

```bat
python -m main
```

then test:

```bat
python -m main
```

Manual verification:

```text
existing Run Full Plan button still exists
new Run Full Plan → Viewer button is visible
click existing Run Full Plan, existing behavior still works or at least is unchanged
click Run Full Plan → Viewer
viewer output directory is created
read-only viewer opens
capacity gate chart is visible
weekly table is visible
totals are visible
diagnostic_smoke_bridge note is visible
no crash
```

If manual GUI smoke cannot be fully automated, record observations in the completion memo.

---

## 24. Required Test Commands

Likely focused tests:

```bat
python -m pytest tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

Existing viewer/adapter/bridge tests:

```bat
python -m pytest tests/test_wom_run_full_plan_result_viewer_vertical_slice.py
python -m pytest tests/test_wom_run_full_plan_graph_panel_adapter_vertical_slice.py
python -m pytest tests/test_wom_entrypoint_and_run_full_plan_contract.py
```

Compile / format:

```bat
python -m compileall -q <modified_files> tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
python -m black --check <modified_files> tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

Manual smoke:

```bat
python -m main
```

or the currently documented cockpit launch command.

---

## 25. Safety Boundaries

Do not:

```text
remove existing Run Full Plan button
rename existing Run Full Plan button unless explicitly required
replace existing button handler
change planner behavior
change scenario master CSV files
change NetworkX usage
change Japanese Rice runner contract
change Run Full Plan bridge contract
change Graph Panel Adapter contract
change Result Viewer contract
```

The change should be additive.

---

## 26. Acceptance Criteria for This Design

This design is complete if it clarifies:

```text
existing Run Full Plan remains
new Run Full Plan → Viewer button is added separately
new button uses run_full_plan standard-output path
new button writes outputs/run_full_plan/<run_id>
new button launches the read-only viewer
new button does not embed viewer logic directly into cockpit
scenario root resolution is conservative
run_id generation is stable
manual Windows GUI smoke is required
future replacement is deferred
```

---

## 27. Recommended Next Codex Request

Create:

```text
docs/codex_requests/wom_main_cockpit_run_full_plan_button_vertical_slice_request.md
```

Implementation target should be determined by source inspection.

Likely targets:

```text
pysi/gui/cockpit_tk.py
```

or:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Recommended optional helper:

```text
pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py
```

Expected test:

```text
tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

---

## 28. Long-Term Direction

The long-term direction is not to keep two buttons forever.

Eventually, the new standard-output path may become the main Run Full Plan path.

Future target:

```text
Run Full Plan
  ↓
standard run_full_plan pipeline
  ↓
FullPlanResult
  ↓
visual datasets
  ↓
cockpit panels / viewer / BI / reports / Rule Base
```

But that should happen only after:

```text
visual_psi_weekly.csv
cost / money datasets
scenario comparison
cockpit embedded graph panels
```

are sufficiently mature.

For now:

```text
parallel button
clear label
safe output-contract path
```

is the correct move.

---

## 29. Completion Summary

This design defines a safe first connection from the main cockpit to the new Run Full Plan standard-output path.

The existing cockpit `Run Full Plan` button remains untouched.

A new button or menu item is added:

```text
Run Full Plan → Viewer
```

This button follows the already proven chain:

```text
run_full_plan
  ↓
FullPlanResult JSON / visual CSV
  ↓
graph panel adapter
  ↓
read-only viewer
```

In simple terms:

```text
Do not replace the old runway yet.
Open a new clearly labeled runway beside it.
Let the new standard-output path mature safely.
```
