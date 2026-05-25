# Explicit Pipeline Management Cockpit KPI Demo Flag GUI Wiring Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-25  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_gui_wiring.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the Phase 2 design for wiring the **Explicit Pipeline KPI Demo Flag Preset Helper** into the WOM GUI.

Phase 1 completed the pure helper:

```python
apply_explicit_pipeline_kpi_demo_flags(
    env,
    *,
    include_exports=False,
    cost_kpi_context=None,
)
```

implemented in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Phase 2 will expose this helper through the GUI so that the user can enable explicit KPI reporting before running the plan.

The goal is:

```text
Enable Explicit KPI Reporting
    ↓
Run Full Plan
    ↓
Explicit KPI View
    ↓
Summary KPI Cards / Graphs / Issues become available
```

This design keeps the cockpit read-only and keeps the reporting stack default-off unless the user explicitly enables it.

---

## 2. Background

The Explicit Pipeline Management Cockpit KPI UI MVP is already implemented.

The current UI contains:

```text
Explicit KPI View
    ├─ Summary
    │   └─ KPI Cards
    ├─ Graphs
    │   └─ Canvas Charts
    ├─ Top Issues
    ├─ Replan Candidates
    ├─ Health
    ├─ Assumptions / Exports
    └─ Messages
```

The UI opens correctly from the WOM GUI.

However, when the user runs:

```bat
python -m main
```

then clicks:

```text
Run Full Plan
    ↓
Explicit KPI View
```

the view can still show:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

because explicit pipeline reporting flags remain default-off.

Phase 2 adds the GUI control needed to turn on the reporting signal path before `Run Full Plan`.

---

## 3. Current Completed Phase 1

Phase 1 completed:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset.md
docs/codex_requests/explicit_pipeline_management_cockpit_kpi_demo_flag_preset_request.md
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset_completion.md
```

Latest Phase 1 implementation commit:

```text
030872c Add explicit pipeline KPI demo flag preset helper
```

Latest Phase 1 completion memo commit:

```text
c0ac8fc Add explicit pipeline KPI demo flag preset helper completion memo
```

Phase 1 created the ignition switch body.

Phase 2 mounts it onto the WOM GUI.

---

## 4. Problem Statement

The helper exists, but there is currently no user-facing GUI path to call it.

Current state:

```text
Explicit KPI View UI exists.
Demo flag helper exists.
But Run Full Plan does not apply the helper from the GUI.
```

Therefore:

```text
Explicit KPI View can remain unavailable even after Run Full Plan.
```

The GUI needs a small, explicit, safe control to enable KPI reporting before planning.

---

## 5. Design Goal

Add a visible GUI control that allows the user to enable Explicit KPI reporting for the next plan run.

Recommended behavior:

```text
User checks Explicit KPI ON
    ↓
User clicks Run Full Plan
    ↓
WOM applies apply_explicit_pipeline_kpi_demo_flags(self.env)
    ↓
Run Full Plan proceeds normally
    ↓
Explicit KPI View can display reporting artifacts
```

The checkbox must not run planning by itself.

It only controls whether the helper is applied before the existing planning sequence.

---

## 6. Non-Goals

This phase must not implement:

```text
new planning logic
new reporting logic
new Cost / KPI enrichment logic
new exporter logic
automatic planning execution when checkbox is clicked
automatic export execution
ReplanCommand execution
automatic replanning
OR optimization
database persistence
Knowledge Continuity persistence
waterfall chart
heatmap
drilldown
large GUI redesign
```

This phase is only:

```text
GUI wiring for the existing demo flag preset helper
```

---

## 7. Core Safety Rule

The existing safety rule remains:

```text
Show the instruments.
Do not start the engine.
```

Phase 2 may:

```text
add a checkbox
store checkbox state
apply demo flags before Run Full Plan
show that the preset is enabled
```

Phase 2 must not:

```text
run planning when checkbox is toggled
run exports by default
execute ReplanCommand
mutate planning results from the view
change feature flags from Explicit KPI View rendering
```

The checkbox prepares the ignition.

`Run Full Plan` starts the engine.

---

## 8. Recommended GUI Control

Recommended control:

```text
ttk.Checkbutton
```

Recommended label:

```text
Explicit KPI ON
```

Alternative labels:

```text
Enable KPI
KPI Demo ON
Explicit KPI Reporting
```

Recommended MVP label:

```text
Explicit KPI ON
```

Reason:

```text
short enough for crowded header row
clear enough for development / demo use
```

---

## 9. Recommended Placement

Place the checkbox near:

```text
Run Full Plan
Explicit KPI View
Mgmt Cockpit
```

Recommended location:

```text
same action/header row as Explicit KPI View
```

Conceptual layout:

```text
Run Full Plan | Mgmt Cockpit | Explicit KPI View | [ ] Explicit KPI ON | Business Animation
```

If the header row is crowded, place it near `Run Full Plan`, because it affects the next full plan run.

---

## 10. Checkbox Variable

Add a Tk boolean variable to `WOMCockpit`.

Recommended attribute:

```python
self.var_enable_explicit_kpi_reporting = tk.BooleanVar(value=False)
```

Default:

```python
False
```

Reason:

```text
preserve default-off safety behavior
```

The user must explicitly enable the preset.

---

## 11. Apply Timing

The helper should be applied immediately before the existing `Run Full Plan` planning logic begins.

Recommended logic:

```python
if self.var_enable_explicit_kpi_reporting.get():
    apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

This should be placed inside the existing Run Full Plan command path, before the explicit pipeline / planning sequence can read the flags.

Do not apply the helper when the Explicit KPI View is opened.

Do not apply the helper when the checkbox is toggled.

---

## 12. Import Strategy

To avoid heavy import side effects during GUI import, use local import inside the relevant method.

Recommended:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags
```

inside the Run Full Plan handler or a small helper method.

Alternative:

```python
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    apply_explicit_pipeline_kpi_demo_flags,
)
```

Both are acceptable.

Recommended for consistency with Phase 1 package export:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags
```

---

## 13. Recommended Helper Method in WOMCockpit

Add a small private method:

```python
def _maybe_apply_explicit_kpi_demo_flags(self) -> dict[str, bool] | None:
    ...
```

Suggested behavior:

```python
def _maybe_apply_explicit_kpi_demo_flags(self):
    if not getattr(self, "var_enable_explicit_kpi_reporting", None):
        return None
    if not self.var_enable_explicit_kpi_reporting.get():
        return None

    from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags

    return apply_explicit_pipeline_kpi_demo_flags(
        self.env,
        include_exports=False,
    )
```

The return value can be used for tests or optional logging.

No message box is required for MVP.

---

## 14. Run Full Plan Integration

Find the existing `Run Full Plan` handler in:

```text
pysi/gui/cockpit_tk.py
```

The current class already has:

```text
WOMCockpit
```

and already includes:

```text
Explicit KPI View button
_open_explicit_pipeline_kpi_view(...)
```

Add a call to:

```python
self._maybe_apply_explicit_kpi_demo_flags()
```

near the beginning of the Run Full Plan execution path.

Conceptual placement:

```python
def _run_full_plan(...):
    self._maybe_apply_explicit_kpi_demo_flags()
    ...
    existing planning flow
```

or in the actual method used by the button.

The exact method name should be discovered from the current file.

---

## 15. Export Flags

For Phase 2 MVP, call the helper with:

```python
include_exports=False
```

Reason:

```text
GUI display does not require exports.
Export behavior writes files and should remain separately controlled.
```

Do not add a GUI export checkbox in this phase.

Do not enable export flags by default.

---

## 16. Cost / KPI Context

For Phase 2 MVP, do not pass a new `cost_kpi_context`.

Call:

```python
apply_explicit_pipeline_kpi_demo_flags(
    self.env,
    include_exports=False,
)
```

This preserves any existing context.

A later phase may define a scenario-specific context, but this phase should stay minimal.

---

## 17. GUI Feedback

MVP can rely on the checkbox label only.

Optional future improvement:

```text
status label: Explicit KPI reporting enabled for next Run Full Plan
```

For Phase 2, avoid adding extra status UI unless very simple.

A debug log print is acceptable if consistent with existing GUI style:

```text
[explicit-kpi] demo reporting flags enabled for Run Full Plan
```

But tests should not depend on a print message.

---

## 18. Explicit KPI View Empty Message

This phase may leave the current empty message unchanged:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

Optional small improvement:

```text
No explicit pipeline reporting data is available.
Enable Explicit KPI ON, run Full Plan, then reopen this view.
```

Recommended for Phase 2:

```text
Do not change view messages unless trivial.
```

Keep scope focused on wiring.

---

## 19. Test Strategy

Add focused GUI integration tests.

Recommended test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

The tests should avoid starting a full Tk window if possible.

They can call methods on a fake `self` object if the wiring method is small.

Recommended tests:

```text
1. checkbox disabled -> helper is not called
2. checkbox enabled -> helper is called with self.env and include_exports=False
3. method returns applied flag map when enabled
4. method is safe if variable is missing
```

If testing the actual checkbox widget is feasible with existing patterns, use safe Tk skip behavior.

---

## 20. Recommended Unit-Testable Method

The most testable design is to add:

```python
def _maybe_apply_explicit_kpi_demo_flags(self):
    ...
```

Then tests can create a fake object:

```python
from types import SimpleNamespace

fake = SimpleNamespace(
    env=SimpleNamespace(),
    var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
)
result = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
```

This avoids needing to instantiate the full GUI.

For monkeypatch testing, patch:

```python
pysi.reporting.apply_explicit_pipeline_kpi_demo_flags
```

or patch the imported path used by the method.

---

## 21. Button / Checkbox Presence Test

If feasible, add one test to verify that the GUI class can be inspected or initialized and that the checkbox variable exists.

However, avoid brittle layout tests.

Preferred:

```text
test method behavior
test no planning execution
test no export flags
```

Not required:

```text
pixel / layout / exact grid position
```

---

## 22. Suggested Test Cases

### 22.1 Missing variable safety

```text
fake self has env only
_maybe_apply_explicit_kpi_demo_flags(fake) returns None
```

### 22.2 Checkbox off

```text
fake self has var_enable_explicit_kpi_reporting.get() -> False
helper is not called
returns None
```

### 22.3 Checkbox on

```text
fake self has var_enable_explicit_kpi_reporting.get() -> True
helper is called
return map has display flags True
export flags False
```

### 22.4 Export safety

```text
when GUI wiring calls helper, include_exports is False
```

### 22.5 Run Full Plan hook position

If testable through monkeypatch:

```text
Run Full Plan path calls _maybe_apply_explicit_kpi_demo_flags before planning body
```

This may be more brittle and can be deferred if necessary.

---

## 23. Existing Tests to Run

After implementation, run:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Then run related cockpit tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_canvas_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_button_integration.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Optional smoke:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If Tk tests are skipped because Tk is unavailable, state so clearly.

---

## 24. Manual GUI Validation

After implementation, manually verify:

```text
1. python -m main
2. confirm checkbox appears:
   Explicit KPI ON
3. leave unchecked
4. click Run Full Plan
5. open Explicit KPI View
6. expected: may still be unavailable
7. restart or reset if needed
8. check Explicit KPI ON
9. click Run Full Plan
10. open Explicit KPI View
11. expected:
    Available = Yes
    Explicit Pipeline Result = Yes
    Capacity Report = Yes
    Issue Candidates = Yes or 0 but available
    Cost / KPI Bundle = Yes if data produced
```

If values are still unavailable after enabling checkbox, inspect whether the flags are being applied before the correct planning sequence.

---

## 25. Important Distinction: Unavailable vs Empty

The UI should distinguish:

```text
Unavailable:
  reporting stack did not run
  Explicit Pipeline Result = No
  Capacity Report = No

Empty:
  reporting stack ran
  Explicit Pipeline Result = Yes
  Capacity Report = Yes
  Issue Candidates = 0
  no issues found
```

Phase 2 success means moving from:

```text
Unavailable
```

to:

```text
Available
```

Even if the issue count is zero.

---

## 26. Recommended Codex Request Scope

The next Codex request should implement:

```text
Phase 2 GUI wiring
```

Files likely changed:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Possibly no other files.

Do not modify:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

unless a tiny compatibility issue is found.

---

## 27. Completion Criteria

Phase 2 is complete when:

```text
[OK] GUI has a visible Explicit KPI ON checkbox or equivalent
[OK] checkbox default is OFF
[OK] checkbox does not run planning by itself
[OK] helper is applied before Run Full Plan when checked
[OK] helper is not applied when unchecked
[OK] include_exports=False is used
[OK] Explicit KPI View remains read-only
[OK] no ReplanCommand execution is added
[OK] no export execution is added from the checkbox
[OK] tests cover checkbox / helper wiring
[OK] existing cockpit tests pass
```

---

## 28. Future Enhancements

After Phase 2, possible follow-up items include:

```text
improved unavailable-view message
status label showing KPI reporting ON/OFF
startup config option
CLI demo preset
export enable checkbox
scenario-specific cost_kpi_context preset
automatic refresh of Explicit KPI View after Run Full Plan
```

These should remain separate from Phase 2 MVP.

---

## 29. Summary

Phase 1 built the helper:

```text
apply_explicit_pipeline_kpi_demo_flags(env, include_exports=False)
```

Phase 2 should mount that helper into the WOM GUI.

The recommended MVP behavior is:

```text
[ ] Explicit KPI ON
    ↓
Run Full Plan
    ↓
apply demo flags before planning
    ↓
Explicit KPI View becomes available
```

The cockpit remains read-only.

The checkbox prepares the ignition.

Run Full Plan starts the engine.
