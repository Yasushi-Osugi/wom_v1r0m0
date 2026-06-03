# Codex Request: WOM Main Cockpit Run Full Plan Viewer Button Vertical Slice

**Version:** v0r1  
**Date:** 2026-06-03  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_main_cockpit_run_full_plan_button_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/wom_main_cockpit_run_full_plan_button_vertical_slice.md
```

**Preceding design docs / completion memos:**

```text
docs/design/wom_entrypoint_and_run_full_plan_contract.md
docs/design/wom_entrypoint_and_run_full_plan_contract_completion.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md
docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice_completion.md
docs/design/wom_run_full_plan_result_viewer_vertical_slice.md
docs/design/wom_run_full_plan_result_viewer_vertical_slice_completion.md
```

**Related implementation files:**

```text
pysi/runners/run_full_plan.py
pysi/gui/wom_run_full_plan_graph_panel_adapter.py
pysi/gui/wom_run_full_plan_result_viewer.py
```

**Likely cockpit files to inspect:**

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first safe main cockpit entry point to the new Run Full Plan standard-output path.

The existing WOM main cockpit already has an original `Run Full Plan` button, likely in the upper-right area.

Do not replace that existing button.

Do not rename it.

Do not change its handler.

Instead, add a separate new button or menu command:

```text
Run Full Plan → Viewer
```

This new button should run the output-contract based path:

```text
main cockpit
  ↓
Run Full Plan → Viewer button
  ↓
WomRunConfig
  ↓
run_full_plan(config)
  ↓
outputs/run_full_plan/<run_id>/
  ├─ full_plan_result.json
  └─ visual_capacity_gate_weekly.csv
  ↓
launch_run_full_plan_result_viewer(run_dir)
```

This request should be additive and minimal.

---

## 2. Strategic Context

The following chain is already implemented and manually smoke-verified on Windows:

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

The next step is to expose this proven path from the existing main cockpit without disturbing the legacy/internal `Run Full Plan` behavior.

This request is the first bridge from the main cockpit to the new standard-output architecture.

---

## 3. Key Design Decision

The cockpit must show two different paths clearly.

### Existing button

```text
Run Full Plan
```

Meaning:

```text
legacy / existing internal WOM GUI execution path
current cockpit data model handling
preserve existing behavior
```

### New button

```text
Run Full Plan → Viewer
```

Meaning:

```text
new standard-output execution path
calls pysi.runners.run_full_plan
writes JSON / CSV output files
opens read-only result viewer
does not update existing cockpit internals directly
```

The new path is currently:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
```

The UI should not imply that the final production full PSI planning engine is complete.

---

## 4. Scope

### 4.1 In scope

Implement:

```text
source audit of existing Run Full Plan button location
new button or menu item labelled Run Full Plan → Viewer
button handler for the new standard-output path
safe run_id generation
conservative scenario_root resolution
call run_full_plan(config)
write FullPlanResult JSON / visual CSV outputs
launch existing read-only result viewer
safe messagebox/status error handling
focused tests
manual Windows GUI smoke instructions
```

### 4.2 Out of scope

Do not implement:

```text
replacement of existing Run Full Plan button
deep cockpit refactoring
embedded result viewer panel inside main cockpit
scenario editor
capacity override editor
new planner behavior
cost / money graph
tariff graph
Rule Base / AI diagnosis
BI connector
database persistence
```

Do not modify:

```text
existing Run Full Plan behavior
planner behavior
scenario master CSV files
NetworkX usage
Japanese Rice runner contract
Run Full Plan bridge contract
Graph Panel Adapter contract
Result Viewer contract
```

---

## 5. Required Source Audit First

Before implementation, inspect the source tree and identify:

```text
where the existing Run Full Plan button is defined
where its handler is defined
which cockpit module is the current main GUI launch path
how the cockpit is normally launched
```

Likely files:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
main.py
```

Please report in the final summary:

```text
Where is the existing Run Full Plan button implemented?
Where is the existing Run Full Plan handler implemented?
What file was modified to add the new button?
```

Do not guess blindly.

---

## 6. Expected Changed / Added Files

Expected modification depends on source audit.

Likely modified file:

```text
pysi/gui/cockpit_tk.py
```

or:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Recommended optional new helper module:

```text
pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py
```

Recommended focused test file:

```text
tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

The helper module is recommended if cockpit code would otherwise become cluttered.

---

## 7. Recommended Helper Module

If practical, add:

```text
pysi/gui/wom_main_cockpit_run_full_plan_viewer_action.py
```

Purpose:

```text
keep run_full_plan/viewer orchestration out of the main cockpit file
make non-GUI helper tests easier
keep cockpit button handler thin
```

Recommended public functions:

```python
def make_cockpit_viewer_run_id(now=None) -> str:
    ...

def build_cockpit_viewer_run_config(
    *,
    scenario_root: str,
    scenario_id: str,
    run_id: str | None = None,
    output_dir: str = "outputs/run_full_plan",
) -> WomRunConfig:
    ...

def run_full_plan_and_open_viewer(config: WomRunConfig) -> int:
    ...
```

If a helper module is too much for this slice, implement equivalent small private functions in the modified cockpit file, but keep them testable if possible.

---

## 8. Button Label

Visible button label should be exactly or nearly:

```text
Run Full Plan → Viewer
```

Acceptable fallback if arrow causes font/encoding problems:

```text
Run Full Plan Viewer
```

or:

```text
Run Full Plan Export/View
```

Preferred:

```text
Run Full Plan → Viewer
```

Do not use:

```text
Run Final Full Plan
Run Production Full Plan
```

because the current path is still `diagnostic_smoke_bridge`.

---

## 9. Button Placement

Place the new button near the existing `Run Full Plan` button.

Preferred arrangement:

```text
[Run Full Plan]  [Run Full Plan → Viewer]
```

or stacked:

```text
[Run Full Plan]
[Run Full Plan → Viewer]
```

Do not remove or hide the existing button.

---

## 10. Scenario Root Resolution

The new button needs a scenario root.

Recommended resolution order:

```text
1. Use cockpit-selected scenario root if such state already exists.
2. Otherwise use the default Japanese Rice scenario:
   examples/scenarios/japanese_rice_vslice_001
3. If neither exists, show a concise error message.
```

Do not implement a full scenario selector in this request.

Default v0r1 scenario:

```text
examples/scenarios/japanese_rice_vslice_001
```

Default v0r1 scenario id:

```text
japanese_rice_vslice_001
```

---

## 11. Run ID Generation

Generate a unique run id for cockpit viewer runs.

Recommended format:

```text
cockpit_viewer_YYYYMMDD_HHMMSS
```

Example:

```text
cockpit_viewer_20260603_173500
```

Output directory:

```text
outputs/run_full_plan/<run_id>/
```

---

## 12. New Button Handler Flow

The new button handler should conceptually do this:

```python
def on_run_full_plan_viewer_clicked(...):
    scenario_root = resolve_scenario_root()
    scenario_id = resolve_scenario_id()
    run_id = make_cockpit_viewer_run_id()

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

Use actual signatures from existing modules.

---

## 13. Imports

Recommended imports for action/helper logic:

```python
from pysi.runners.run_full_plan import (
    WomRunConfig,
    run_full_plan,
    write_full_plan_outputs,
)
from pysi.gui.wom_run_full_plan_result_viewer import (
    launch_run_full_plan_result_viewer,
)
```

If importing at module load risks slowing or destabilizing cockpit startup, import inside the button handler or helper function.

Preferred for v0r1:

```python
def on_run_full_plan_viewer_clicked(...):
    from pysi.runners.run_full_plan import ...
    from pysi.gui.wom_run_full_plan_result_viewer import ...
    ...
```

or keep imports in a small helper module.

---

## 14. Error Handling

Expected errors should not crash the cockpit.

Handle at least:

```text
missing scenario root
run_full_plan failed
output writing failed
viewer launch failed
```

Use existing cockpit error mechanism if available.

If not, use Tkinter:

```python
from tkinter import messagebox
messagebox.showerror("Run Full Plan → Viewer failed", message)
```

On success, show a status message if the cockpit has a status area.

If not, success can be implicit through viewer opening.

---

## 15. Status Message

If a status label/log area exists, show:

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

Do not add a large new logging system in this slice.

---

## 16. Truthfulness Requirements

The new path should preserve the existing truthfulness indicators:

```text
run_mode = diagnostic_smoke_bridge
full_psi_plan = False
```

The read-only viewer already displays this.

The cockpit button label should not overstate the maturity of this path.

Do not label it as final production full planning.

---

## 17. Tests

Add focused test file:

```text
tests/test_wom_main_cockpit_run_full_plan_button_vertical_slice.py
```

The exact tests depend on the implementation location.

Recommended tests:

### 17.1 Helper import safety

If helper module is added:

```python
import pysi.gui.wom_main_cockpit_run_full_plan_viewer_action
```

Assert no GUI opens.

### 17.2 Run ID generation

Assert:

```text
run_id starts with cockpit_viewer_
run_id contains timestamp-like digits
```

### 17.3 Config builder

If `build_cockpit_viewer_run_config(...)` exists, assert:

```text
scenario_root preserved
scenario_id preserved
run_id preserved or generated
output_dir == outputs/run_full_plan
run_mode == diagnostic_smoke_bridge
```

### 17.4 Source inspection

Assert modified cockpit source includes:

```text
Run Full Plan → Viewer
```

or approved fallback label.

Assert existing label still appears:

```text
Run Full Plan
```

### 17.5 No contract changes

Import existing modules and assert expected public functions still exist:

```text
run_full_plan
launch_run_full_plan_result_viewer
```

Do not open actual GUI in automated tests.

---

## 18. Required Test Commands

Focused cockpit button test:

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

Manual cockpit smoke:

```bat
python -m main
```

or the currently documented cockpit launch command discovered by source audit.

---

## 19. Manual Windows GUI Smoke

After implementation, manually verify on Windows:

```text
main cockpit opens
existing Run Full Plan button still exists
new Run Full Plan → Viewer button is visible
click Run Full Plan → Viewer
output directory is created under outputs/run_full_plan/<run_id>
read-only viewer opens
capacity gate chart is visible
weekly table is visible
totals are visible
diagnostic_smoke_bridge note is visible
no crash
```

Optional:

```text
click existing Run Full Plan to confirm its behavior is unchanged
```

Do not fail implementation solely because Codex/headless environment cannot open GUI.

Document if manual GUI smoke is not possible in Codex environment.

---

## 20. Safety Boundaries

Do not:

```text
remove existing Run Full Plan button
rename existing Run Full Plan button
replace existing button handler
change planner behavior
change scenario master CSV files
change NetworkX usage
change Japanese Rice runner contract
change Run Full Plan bridge contract
change Graph Panel Adapter contract
change Result Viewer contract
embed the full viewer code into cockpit
```

The change should be additive and reversible.

---

## 21. Acceptance Criteria

This request is complete when:

```text
existing Run Full Plan button is preserved
new Run Full Plan → Viewer button or menu item is added
new button is visually distinguishable from existing Run Full Plan
new button uses run_full_plan standard-output path
new button writes outputs/run_full_plan/<run_id>
new button launches the read-only result viewer
existing Run Full Plan handler is not replaced
planner behavior is unchanged
scenario master CSV files are unchanged
NetworkX is untouched
focused tests pass
viewer / adapter / bridge tests pass
compileall passes
black check passes
manual Windows GUI smoke is attempted or documented
```

---

## 22. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is the existing Run Full Plan button implemented?
Where is the existing Run Full Plan handler implemented?
What file was modified to add the new button?
Was a helper module added?
What test file was added?
What is the new button label?
Does the existing Run Full Plan button still exist?
Was the existing Run Full Plan handler replaced?
Does the new button call run_full_plan?
Does the new button write outputs/run_full_plan/<run_id>?
Does the new button launch the read-only viewer?
What default scenario_root is used?
What run_id format is used?
Does the implementation preserve diagnostic_smoke_bridge / full_psi_plan False?
Did you modify pysi/runners/run_full_plan.py?
Did you modify wom_run_full_plan_graph_panel_adapter.py?
Did you modify wom_run_full_plan_result_viewer.py?
Did you modify existing Japanese Rice runner/viewer behavior?
Did you change planner behavior?
Did you change scenario master CSV files?
Did you remove or modify NetworkX?
Which tests passed?
Was manual GUI smoke run?
If not, why not?
```

---

## 23. Development Meaning

Before this request:

```text
Run Full Plan standard-output path can be launched from CLI and shown in a read-only viewer.
```

After this request:

```text
The existing main cockpit can open the new standard-output path through a clearly separate button.
```

This is not final cockpit integration.

It is the first safe bridge from the main cockpit to the new contract-first execution/display line.

In simple terms:

```text
Do not replace the old runway.
Add a new runway beside it.
Let the new standard-output flight path mature safely.
```
