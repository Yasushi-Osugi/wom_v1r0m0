# Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-26  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_ctx_guard_diagnostics_view_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of the **Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View** implementation.

The purpose of this milestone was to improve the user-facing behavior of the Explicit KPI View after the context guard safely skips the explicit pipeline.

Before this milestone, the cockpit was safe but quiet:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard skips explicit pipeline because required ctx is missing
    ↓
Run Full Plan completes
    ↓
Explicit KPI View opens but appears mostly empty
```

After this milestone, the cockpit explains why it is empty:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard skips explicit pipeline because required ctx is missing
    ↓
Run Full Plan completes
    ↓
Explicit KPI View shows missing ctx diagnostic:
       explicit_pipeline_backward_weekly_capability
```

This milestone is display-only.

It does not generate missing capability context.

It does not run planning.

It does not run exports.

It does not execute ReplanCommand.

---

## 2. Background

The previous milestone completed the context guard:

```text
Explicit KPI ON + missing required ctx
    ↓
required ctx guard
    ↓
explicit pipeline safely skipped
    ↓
Run Full Plan completed
    ↓
Explicit KPI View remains unavailable
```

The confirmed missing key is:

```text
explicit_pipeline_backward_weekly_capability
```

The guard records diagnostics on `env`:

```text
explicit_kpi_demo_flag_ctx_guard_skipped
explicit_kpi_demo_flag_missing_ctx_keys
explicit_kpi_demo_flag_guard_message
```

This diagnostics-view milestone connects those diagnostics to the Explicit KPI View.

---

## 3. Implemented Commit

The diagnostics view implementation was committed as:

```text
991fc0a Add explicit KPI ctx guard diagnostics to cockpit view
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

The implementation changed four files:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

No changes were made to:

```text
pysi/gui/cockpit_tk.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/*
pysi/core/*
```

This confirms that the milestone remained a diagnostics-view change.

---

## 5. View Model Additions

The following keys were added to the Explicit KPI View model:

```text
ctx_guard_skipped
ctx_guard_missing_keys
ctx_guard_message
```

Default values when no diagnostics exist:

```python
{
    "ctx_guard_skipped": False,
    "ctx_guard_missing_keys": [],
    "ctx_guard_message": "",
}
```

When diagnostics exist on `env`, the view model carries them forward:

```python
{
    "ctx_guard_skipped": True,
    "ctx_guard_missing_keys": ["explicit_pipeline_backward_weekly_capability"],
    "ctx_guard_message": "Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_backward_weekly_capability",
}
```

This keeps the renderer view-model-driven.

---

## 6. Top Unavailable Message Behavior

The top unavailable message now has priority logic.

If the view is unavailable and no context guard diagnostic exists, the previous message remains:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

If the view is unavailable because the context guard skipped the explicit pipeline, the view shows the guard diagnostic instead.

Observed message pattern:

```text
Explicit KPI demo pipeline skipped because required ctx keys are missing:
explicit_pipeline_backward_weekly_capability
```

This changes the user experience from:

```text
unavailable, but unclear why
```

to:

```text
unavailable, because required context is missing
```

---

## 7. Summary Tab Behavior

The Summary tab now includes conditional diagnostic rows when the context guard skipped the explicit pipeline.

Observed rows:

```text
Context Guard    Skipped
Missing Context  explicit_pipeline_backward_weekly_capability
```

These rows appear only when:

```text
ctx_guard_skipped = True
```

This makes the first visible tab useful even when the KPI data is unavailable.

---

## 8. Messages Tab Behavior

The messages content pipeline now includes context guard diagnostics.

When the guard has skipped execution, messages include the guard reason and missing key information.

Expected content includes:

```text
Context guard skipped explicit pipeline execution.
Missing required context:
explicit_pipeline_backward_weekly_capability
```

This turns the Messages tab into a diagnostic explanation area.

---

## 9. Graph View Model Behavior

The graph view model was updated so that unavailable graph messages include context guard diagnostics when present.

When graph data is unavailable and `ctx_guard_skipped=True`, graph notes can include:

```text
Explicit KPI demo pipeline skipped because required ctx keys are missing:
explicit_pipeline_backward_weekly_capability
```

Charts can remain empty.

The important behavior is that the graph view explains why no graph data exists.

---

## 10. Renderer Behavior

The renderer remains:

```text
read-only
side-effect-free
view-model-driven
```

The renderer does not inspect `env`.

It only reads:

```text
view_model["ctx_guard_skipped"]
view_model["ctx_guard_missing_keys"]
view_model["ctx_guard_message"]
```

This preserves clean separation:

```text
env
  ↓
view model builder
  ↓
renderer
```

---

## 11. Tests Updated

The following tests were updated:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

The tests cover:

```text
default diagnostics absent behavior
diagnostics present behavior
ctx guard message propagation to graph view model
Tk rendering with missing key visible
input view model no-mutation behavior
```

---

## 12. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Observed results:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py                  10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py      3 passed, 1 skipped
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py             9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_cards.py                  3 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                                6 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                      5 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                     7 passed
tests/test_explicit_pipeline_reporting_flags.py                              10 passed
```

Total observed result:

```text
53 passed, 1 skipped
```

The single skipped test is a Tk rendering environment skip and is not a failure.

---

## 13. Manual GUI Validation

Manual GUI validation was performed after the implementation.

Validation path:

```text
1. python -m main
2. Explicit KPI ON checkbox displayed
3. Explicit KPI ON checked
4. Run Full Plan clicked
5. Run Full Plan completed
6. Explicit KPI View opened
7. missing context diagnostic displayed
```

Confirmed on screen:

```text
Explicit KPI demo pipeline skipped because required ctx keys are missing:
explicit_pipeline_backward_weekly_capability
```

Confirmed Summary tab rows:

```text
Context Guard    Skipped
Missing Context  explicit_pipeline_backward_weekly_capability
```

This validates the intended behavior.

---

## 14. Completion Criteria

This diagnostics-view milestone satisfies the intended completion criteria.

```text
[OK] view model carries ctx guard diagnostics
[OK] default env without diagnostics preserves existing behavior
[OK] unavailable top message uses ctx guard reason when present
[OK] Messages tab includes ctx guard diagnostic
[OK] Summary tab shows ctx guard rows when skipped
[OK] Graph notes include ctx guard message when unavailable
[OK] renderer remains read-only
[OK] renderer remains view-model-driven
[OK] no planning execution is added
[OK] no export execution is added
[OK] no capability context generation is added
[OK] focused tests pass
[OK] manual GUI validation confirms the missing key is visible
```

---

## 15. Meaning of This Milestone

Before this milestone:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard safely skips explicit pipeline
    ↓
Explicit KPI View opens
    ↓
view is empty / unavailable
```

After this milestone:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard safely skips explicit pipeline
    ↓
Explicit KPI View opens
    ↓
view explains missing required context:
       explicit_pipeline_backward_weekly_capability
```

The cockpit moved from:

```text
silent unavailable state
```

to:

```text
diagnostic unavailable state
```

This is a meaningful usability improvement.

---

## 16. Known Minor Display Issue

The top message can show the missing key twice.

Reason:

```text
ctx_guard_message already contains the missing key
renderer can also append missing keys
```

Example:

```text
Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_backward_weekly_capability
explicit_pipeline_backward_weekly_capability
```

This is not functionally harmful.

It can be cleaned up later as a small display polish item.

Recommended later cleanup:

```text
avoid appending missing keys if ctx_guard_message already contains them
```

This should not block the current milestone.

---

## 17. Current State

The current state is:

```text
Explicit KPI ON checkbox exists
demo flag helper exists
required ctx guard exists
diagnostics view exists
Run Full Plan does not crash on missing ctx
Explicit KPI View explains why it is unavailable
```

The remaining missing piece is the actual required capability context:

```text
explicit_pipeline_backward_weekly_capability
```

Until this is supplied, the Explicit KPI View can explain the unavailable state but will not show full pipeline / capacity results.

---

## 18. Recommended Next Step

The next major design should define how to generate or load:

```text
explicit_pipeline_backward_weekly_capability
```

Recommended design memo:

```text
docs/design/explicit_pipeline_backward_weekly_capability_context.md
```

This should cover:

```text
Weekly Capability on MOM nodes
node-product-week capacity master
capacity calendar
resource / process capability table
scenario-specific capacity assumptions
how capability ctx is attached to env before Run Full Plan
```

This is the step that can move the Explicit KPI View from diagnostic unavailable to populated.

---

## 19. Later Work: Price-Cost-Profit Propagation

The user's target Price-Cost-Profit model remains important and should be handled separately.

Conceptual directions:

```text
A. market-accepted price propagated upstream through the E2E tree
B. material-accepted cost propagated downstream through the E2E tree
C. comparison of A and B to allocate price, profit, and cost portions
```

Recommended later inventory memo:

```text
docs/design/price_cost_profit_e2e_propagation_inventory.md
```

This should not be mixed into the diagnostics view.

---

## 20. Summary

The Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View is complete.

The milestone achieved:

```text
The cockpit now explains why it is unavailable when the explicit pipeline is skipped by the context guard.
```

Confirmed visible key:

```text
explicit_pipeline_backward_weekly_capability
```

The cockpit no longer merely stays empty.

It now tells the user what is missing.

The next step is to supply the missing capability context.
