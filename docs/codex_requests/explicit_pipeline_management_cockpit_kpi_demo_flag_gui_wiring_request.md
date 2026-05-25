# Codex Request: Implement Explicit Pipeline Management Cockpit KPI Demo Flag GUI Wiring Phase 2

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following Phase 2 design memo has already been added:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_gui_wiring.md
```

Please read this design memo first.

Phase 1 has already completed the pure helper:

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

The helper is already exported from:

```text
pysi/reporting/__init__.py
```

and can be imported as:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags
```

Phase 1 completion memo:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset_completion.md
```

This request implements **Phase 2 GUI wiring**.

---

## 2. Current State

The Explicit Pipeline Management Cockpit KPI UI MVP already exists.

The WOM GUI has:

```text
Explicit KPI View
```

and the Explicit KPI View window contains:

```text
Summary
Graphs
Top Issues
Replan Candidates
Health
Assumptions / Exports
Messages
```

The Summary tab has KPI Cards.

The Graphs tab has Tk Canvas charts.

However, under normal GUI usage:

```text
python -m main
    ↓
Run Full Plan
    ↓
Explicit KPI View
```

the Explicit KPI View can still show:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

because explicit pipeline reporting flags are default-off.

Phase 2 should add a visible GUI control that lets the user enable these flags before `Run Full Plan`.

---

## 3. Main Objective

Add a small, visible GUI checkbox or equivalent toggle:

```text
Explicit KPI ON
```

When checked, `Run Full Plan` should apply the Phase 1 helper before the existing planning sequence begins.

Expected behavior:

```text
[ ] Explicit KPI ON
    ↓
Run Full Plan
    ↓
if checked:
        apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
    ↓
existing Run Full Plan proceeds
    ↓
Explicit KPI View can display reporting artifacts
```

The checkbox itself must not run planning.

The checkbox only prepares the next `Run Full Plan`.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Keep checkbox default OFF.
2. Do not run planning when checkbox is toggled.
3. Do not run exports from the checkbox.
4. Do not enable export flags by default.
5. Use include_exports=False.
6. Do not execute ReplanCommand.
7. Do not implement automatic replanning.
8. Do not implement OR optimization.
9. Do not implement database persistence.
10. Do not implement Knowledge Continuity persistence.
11. Do not modify Cost / KPI enrichment logic.
12. Do not modify reporting builder logic.
13. Do not modify exporter logic.
14. Do not change Explicit KPI View rendering behavior except if a very small message improvement is necessary.
15. Do not add waterfall / heatmap / drilldown.
16. Do not add new dependencies.
```

This request is only for:

```text
GUI checkbox / toggle wiring to the existing helper
```

The safety rule remains:

```text
The checkbox prepares the ignition.
Run Full Plan starts the engine.
```

---

## 5. Files to Modify / Add

Likely files to modify:

```text
pysi/gui/cockpit_tk.py
```

Add test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Do not modify Phase 1 helper unless absolutely necessary:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Do not modify:

```text
pysi/reporting/exporters
pysi/reporting/builders
pysi/plan/*
pysi/core/*
```

unless a tiny compatibility issue is unavoidable.

---

## 6. GUI Control

Add a Tk variable to `WOMCockpit`:

```python
self.var_enable_explicit_kpi_reporting = tk.BooleanVar(value=False)
```

Add a visible checkbox:

```text
Explicit KPI ON
```

Recommended widget:

```python
ttk.Checkbutton
```

Recommended label:

```text
Explicit KPI ON
```

Recommended placement:

```text
near Run Full Plan / Mgmt Cockpit / Explicit KPI View
```

Conceptual layout:

```text
Run Full Plan | Mgmt Cockpit | Explicit KPI View | [ ] Explicit KPI ON | Business Animation
```

If the header/action row is crowded, place it near `Run Full Plan`, because it affects the next full plan run.

Do not create a new window.

Do not create a menu item.

---

## 7. Apply Timing

The helper must be applied before the existing full planning sequence reads explicit pipeline flags.

Add a small private method to `WOMCockpit`:

```python
def _maybe_apply_explicit_kpi_demo_flags(self) -> dict[str, bool] | None:
    ...
```

Suggested implementation:

```python
def _maybe_apply_explicit_kpi_demo_flags(self):
    var = getattr(self, "var_enable_explicit_kpi_reporting", None)
    if var is None:
        return None
    if not var.get():
        return None

    from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags

    return apply_explicit_pipeline_kpi_demo_flags(
        self.env,
        include_exports=False,
    )
```

Then call:

```python
self._maybe_apply_explicit_kpi_demo_flags()
```

near the beginning of the existing `Run Full Plan` path.

Do not call this helper from `_open_explicit_pipeline_kpi_view`.

Do not call this helper from checkbox toggle event.

---

## 8. Run Full Plan Hook

Find the actual method in:

```text
pysi/gui/cockpit_tk.py
```

that is bound to the `Run Full Plan` button.

Add the call at the start of that method, before planning execution begins.

Conceptually:

```python
def _run_full_plan(...):
    self._maybe_apply_explicit_kpi_demo_flags()
    ...
    existing full planning behavior
```

Use the actual existing method name.

Do not change the existing planning sequence structure except for this small pre-flight hook.

---

## 9. Export Safety

The GUI wiring must call:

```python
apply_explicit_pipeline_kpi_demo_flags(
    self.env,
    include_exports=False,
)
```

Do not add a GUI export checkbox in this request.

Do not enable:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

unless a future explicit export feature is designed separately.

---

## 10. Cost / KPI Context

Do not pass a new `cost_kpi_context` in this phase.

Call:

```python
apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

This preserves any existing:

```text
explicit_bridge_capacity_cost_kpi_context
```

according to Phase 1 helper behavior.

---

## 11. Optional Debug Logging

A small debug print is acceptable if consistent with the current style:

```text
[explicit-kpi] demo reporting flags enabled for Run Full Plan
```

However:

```text
tests should not depend on this print
```

No message box is required.

No modal dialog is required.

---

## 12. Optional Empty Message Improvement

The current empty message can remain unchanged:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

Optionally, it can be improved later to:

```text
No explicit pipeline reporting data is available.
Enable Explicit KPI ON, run Full Plan, then reopen this view.
```

For this request, prefer no view message change unless trivial.

---

## 13. Testing Strategy

Add focused tests in:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Tests should avoid brittle GUI layout assertions.

The most important behavior is the small method:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags(...)
```

This can be tested with a fake `self` object rather than constructing the full GUI.

Example fake:

```python
from types import SimpleNamespace

fake = SimpleNamespace(
    env=SimpleNamespace(),
    var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
)
result = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
```

---

## 14. Required Tests

Please add tests covering:

### 14.1 Missing variable safety

If `var_enable_explicit_kpi_reporting` is absent:

```text
_maybe_apply_explicit_kpi_demo_flags(fake) returns None
```

and should not raise.

### 14.2 Checkbox OFF

If:

```python
var_enable_explicit_kpi_reporting.get() -> False
```

then:

```text
helper is not applied
return is None
env flags are not added
```

### 14.3 Checkbox ON

If:

```python
var_enable_explicit_kpi_reporting.get() -> True
```

then:

```text
helper is applied
display flags become True
export flags become False
return map is the Phase 1 helper map
```

### 14.4 Export safety

Verify that the GUI wiring uses:

```python
include_exports=False
```

This can be verified by checking returned map export flags are False.

### 14.5 Run Full Plan pre-flight hook

If feasible without brittle full GUI setup, test that the Run Full Plan path calls:

```python
_maybe_apply_explicit_kpi_demo_flags()
```

before the main planning body.

If this is too brittle, keep the test focused on the private method and state the limitation.

---

## 15. Optional Checkbox Presence Test

If existing tests already instantiate `WOMCockpit` safely, add one test to verify:

```text
var_enable_explicit_kpi_reporting exists
```

and default is:

```python
False
```

If full Tk initialization is environment-sensitive, use safe skip behavior:

```python
try:
    root = WOMCockpit(...)
except tk.TclError as exc:
    pytest.skip(...)
```

Do not add fragile pixel/grid assertions.

---

## 16. Existing Tests to Run

Please run focused tests first:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Then run related cockpit / reporting tests:

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

If optional tests are not run, state so clearly.

---

## 17. Manual GUI Validation

After implementation and tests, manually verify:

```text
1. python -m main
2. Confirm checkbox appears:
   Explicit KPI ON
3. Leave checkbox OFF.
4. Click Run Full Plan.
5. Open Explicit KPI View.
6. Expected: view may still be unavailable.
7. Check Explicit KPI ON.
8. Click Run Full Plan.
9. Open Explicit KPI View.
10. Expected:
    Available = Yes
    Explicit Pipeline Result = Yes
    Capacity Report = Yes
    Issue Candidates = available, possibly zero
    Cost / KPI Bundle = available if produced
```

If still unavailable after enabling, inspect whether the hook is placed before the explicit pipeline planning sequence reads flags.

---

## 18. Important Distinction

The success target is not necessarily:

```text
many issues displayed
```

The success target is:

```text
reporting stack available
```

The UI should move from:

```text
Unavailable:
    Explicit Pipeline Result = No
    Capacity Report = No
```

to:

```text
Available:
    Explicit Pipeline Result = Yes
    Capacity Report = Yes
```

Even if:

```text
Issue Candidates = 0
```

---

## 19. Completion Criteria

This request is complete when:

```text
[OK] GUI has visible Explicit KPI ON checkbox or equivalent
[OK] checkbox default is OFF
[OK] checkbox does not run planning by itself
[OK] _maybe_apply_explicit_kpi_demo_flags exists
[OK] helper is not applied when checkbox is OFF
[OK] helper is applied when checkbox is ON
[OK] include_exports=False is used
[OK] Run Full Plan calls the helper before planning
[OK] Explicit KPI View remains read-only
[OK] no export execution is added
[OK] no ReplanCommand execution is added
[OK] no Knowledge Continuity persistence is added
[OK] focused GUI wiring tests pass
[OK] existing related cockpit/reporting tests pass
```

---

## 20. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. GUI control added
3. Checkbox variable and default value
4. Helper method added
5. Run Full Plan hook location
6. include_exports behavior
7. Safety boundaries preserved
8. Tests added
9. Test commands executed
10. Test results
11. Skipped tests and why
12. Manual GUI validation notes if performed
13. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
export checkbox
waterfall
heatmap
drilldown
Knowledge Continuity handoff
automatic refresh
large layout redesign
```

This request is only for:

```text
Explicit Pipeline Management Cockpit KPI Demo Flag GUI Wiring Phase 2
```

The completion memo will be written after local apply / test / commit / push.
