# Codex Request: Implement Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design memo has already been added:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_ctx_guard_diagnostics_view.md
```

Please read this design memo first.

The current branch already includes:

```text
Explicit KPI View UI MVP
Summary KPI Cards
Graphs tab with Tk Canvas charts
Explicit KPI demo flag preset helper
Explicit KPI ON checkbox / GUI wiring
Explicit KPI required ctx guard
```

The required ctx guard is already implemented and committed.

The guard prevents `Run Full Plan` from crashing when `Explicit KPI ON` is checked but required explicit pipeline context is missing.

The observed missing key is:

```text
explicit_pipeline_backward_weekly_capability
```

Current guarded behavior:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard detects missing ctx
    ↓
explicit pipeline safely skipped
    ↓
Run Full Plan completes
    ↓
Explicit KPI View opens but remains unavailable / empty
```

This is safe, but the UI currently does not clearly explain why the view is unavailable.

This request implements the next step:

```text
surface ctx guard diagnostics in the Explicit KPI View
```

---

## 2. Main Objective

When the Explicit KPI View is unavailable because the ctx guard skipped the explicit pipeline, show a clear diagnostic reason in the view.

Expected user-facing meaning:

```text
Explicit KPI ON was enabled, but the explicit pipeline was skipped because required context is missing:
explicit_pipeline_backward_weekly_capability
```

This request is **display-only**.

It must not generate missing context.

It must not run planning.

It must not run exports.

---

## 3. Existing Env Diagnostics

The ctx guard already records these fields on `env`:

```text
explicit_kpi_demo_flag_ctx_guard_skipped
explicit_kpi_demo_flag_missing_ctx_keys
explicit_kpi_demo_flag_guard_message
```

Example:

```python
env.explicit_kpi_demo_flag_ctx_guard_skipped = True
env.explicit_kpi_demo_flag_missing_ctx_keys = [
    "explicit_pipeline_backward_weekly_capability"
]
env.explicit_kpi_demo_flag_guard_message = (
    "Explicit KPI demo pipeline skipped because required ctx keys are missing: "
    "explicit_pipeline_backward_weekly_capability"
)
```

The Explicit KPI View should consume these diagnostics through its view model.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Do not generate explicit_pipeline_backward_weekly_capability.
2. Do not implement weekly capability master loading.
3. Do not implement MOM capacity master design.
4. Do not implement Price-Cost-Profit propagation.
5. Do not implement Cost / KPI context generation.
6. Do not add fallback capability values.
7. Do not run planning from the view.
8. Do not run exports from the view.
9. Do not execute ReplanCommand.
10. Do not implement automatic replanning.
11. Do not implement OR optimization.
12. Do not implement database persistence.
13. Do not implement Knowledge Continuity persistence.
14. Do not add waterfall / heatmap / drilldown.
15. Do not add new dependencies.
16. Do not make a large GUI layout redesign.
```

This request is only for:

```text
read-only diagnostics display in Explicit KPI View
```

---

## 5. Files Likely to Modify

Likely files:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Possibly:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

if Summary key-value rows are tested there.

Avoid modifying:

```text
pysi/gui/cockpit_tk.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/*
pysi/core/*
```

unless a tiny compatibility issue is unavoidable.

---

## 6. Recommended Integration Point

The current entry point is:

```python
WOMCockpit._open_explicit_pipeline_kpi_view()
```

which builds a view model using:

```python
build_explicit_pipeline_management_cockpit_view_model(self.env)
```

and renders using:

```python
render_explicit_pipeline_management_cockpit_tk(self, view_model)
```

Recommended integration point:

```text
build_explicit_pipeline_management_cockpit_view_model(env)
```

The renderer should remain view-model-driven.

Do not make the renderer inspect `env` directly.

---

## 7. View Model Additions

Add these flat keys to the view model:

```python
"ctx_guard_skipped": bool
"ctx_guard_missing_keys": list[str]
"ctx_guard_message": str
```

Default behavior when diagnostics are absent:

```python
"ctx_guard_skipped": False
"ctx_guard_missing_keys": []
"ctx_guard_message": ""
```

When diagnostics exist on `env`:

```python
view_model["ctx_guard_skipped"] = bool(
    getattr(env, "explicit_kpi_demo_flag_ctx_guard_skipped", False)
)

view_model["ctx_guard_missing_keys"] = list(
    getattr(env, "explicit_kpi_demo_flag_missing_ctx_keys", []) or []
)

view_model["ctx_guard_message"] = str(
    getattr(env, "explicit_kpi_demo_flag_guard_message", "") or ""
)
```

---

## 8. Message Priority

When the view is unavailable:

```python
view_model["available"] is False
```

and ctx guard diagnostics exist:

```python
view_model["ctx_guard_skipped"] is True
```

then the primary unavailable message should use the ctx guard diagnostic.

Recommended top message:

```text
Explicit KPI ON was enabled, but the explicit pipeline was skipped because required context is missing:
explicit_pipeline_backward_weekly_capability
```

If `ctx_guard_message` already contains a clear message, it may be used directly.

If no ctx guard diagnostic exists, preserve the current message:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

---

## 9. Display Locations

Please surface the diagnostic in at least these locations:

```text
1. top unavailable message area
2. Messages tab
```

Recommended optional addition:

```text
Summary tab key-value rows
```

For Summary tab, add rows only when `ctx_guard_skipped` is true:

```text
Context Guard: Skipped
Missing Context: explicit_pipeline_backward_weekly_capability
```

This helps the first visible tab explain why the cockpit is empty.

---

## 10. Graph View Model Behavior

If the graph view model has a `messages` list, add the ctx guard message there when:

```python
view_model.get("ctx_guard_skipped")
```

is true.

Recommended behavior:

```text
Graph Notes / Caveats includes ctx_guard_message
```

Do not require chart data to exist.

Charts can remain empty.

---

## 11. Messages Tab Behavior

The Messages tab should include a readable diagnostic.

Recommended content:

```text
Context guard skipped explicit pipeline execution.
Missing required context:
- explicit_pipeline_backward_weekly_capability
```

At minimum, include:

```text
ctx_guard_message
```

and the missing key value.

---

## 12. Renderer Requirements

The renderer must remain:

```text
read-only
side-effect-free
view-model-driven
```

It may inspect:

```python
view_model["ctx_guard_skipped"]
view_model["ctx_guard_missing_keys"]
view_model["ctx_guard_message"]
```

It must not inspect `env`.

It must not run planning.

It must not mutate the view model.

---

## 13. Summary Tab Requirements

If the Summary tab uses key-value rows derived from the view model, include ctx guard rows only when guard skipped is true.

Recommended rows:

```text
Context Guard               Skipped
Missing Context             explicit_pipeline_backward_weekly_capability
```

If multiple keys exist, join with:

```text
, 
```

or show a readable list.

Keep the format deterministic.

---

## 14. View-Model Tests

Update:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Add tests for:

### 14.1 Default diagnostics absent

Given env without ctx guard diagnostics:

```text
ctx_guard_skipped is False
ctx_guard_missing_keys == []
ctx_guard_message == ""
```

Existing behavior should remain unchanged.

### 14.2 Diagnostics present

Given env with:

```python
explicit_kpi_demo_flag_ctx_guard_skipped=True
explicit_kpi_demo_flag_missing_ctx_keys=[
    "explicit_pipeline_backward_weekly_capability"
]
explicit_kpi_demo_flag_guard_message=(
    "Explicit KPI demo pipeline skipped because required ctx keys are missing: "
    "explicit_pipeline_backward_weekly_capability"
)
```

Expected view model:

```text
ctx_guard_skipped is True
ctx_guard_missing_keys includes explicit_pipeline_backward_weekly_capability
ctx_guard_message contains explicit_pipeline_backward_weekly_capability
available remains False
```

---

## 15. Renderer Tests

Update:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

or create a focused test if more appropriate.

Recommended tests:

```text
ctx guard unavailable view renders without crashing
core tabs still exist
input view model is not mutated
```

If feasible, inspect widget text and assert it contains:

```text
explicit_pipeline_backward_weekly_capability
```

If widget text inspection is brittle, keep test focused on safe rendering and view model content.

Use existing Tk-safe skip behavior.

---

## 16. Graph View Model Tests

Update:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

If graph messages are extended, add test:

```text
ctx_guard_skipped=True
ctx_guard_message present
build_explicit_pipeline_kpi_graph_view_model(view_model)
returns messages containing ctx_guard_message
```

Do not require chart data.

Do not require graph bars.

---

## 17. Optional KPI Cards / Summary Tests

If Summary key-value rows are easy to test, add or update tests so that when ctx guard skipped is true, the Summary view model or rendered content includes:

```text
Context Guard
Missing Context
explicit_pipeline_backward_weekly_capability
```

Avoid brittle layout assertions.

---

## 18. Existing Tests to Run

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Then run related tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Optional smoke:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If optional tests are not run, state so clearly.

If Tk tests are skipped due to environment, state so clearly.

---

## 19. Manual GUI Validation

After implementation, manually validate:

```text
1. python -m main
2. check Explicit KPI ON
3. click Run Full Plan
4. confirm Run Full Plan completes
5. open Explicit KPI View
6. confirm the view explains the missing ctx reason
7. confirm the message includes:
   explicit_pipeline_backward_weekly_capability
```

Expected result:

```text
Cockpit data may still be unavailable,
but the reason should be visible.
```

---

## 20. Completion Criteria

This request is complete when:

```text
[OK] view model carries ctx guard diagnostics
[OK] default env without diagnostics preserves existing behavior
[OK] unavailable top message uses ctx guard reason when present
[OK] Messages tab includes ctx guard diagnostic
[OK] Summary tab optionally shows ctx guard rows
[OK] Graph notes optionally include ctx guard message
[OK] renderer remains read-only
[OK] no planning execution is added
[OK] no export execution is added
[OK] no capability context generation is added
[OK] focused tests pass
```

---

## 21. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. View model keys added
3. Top unavailable message behavior
4. Messages tab behavior
5. Summary tab behavior, if implemented
6. Graph messages behavior, if implemented
7. Safety boundaries preserved
8. Tests added / updated
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
capability ctx generation
weekly capability master loader
Price-Cost-Profit propagation
Cost / KPI context preset
export checkbox
waterfall
heatmap
drilldown
Knowledge Continuity handoff
```

This request is only for:

```text
Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View
```
