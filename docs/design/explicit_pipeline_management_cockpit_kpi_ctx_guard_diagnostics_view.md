# Explicit Pipeline Management Cockpit KPI Context Guard Diagnostics View Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_ctx_guard_diagnostics_view.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the design for surfacing **Explicit KPI context guard diagnostics** in the Explicit Pipeline Management Cockpit KPI View.

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

That behavior is correct and safe.

However, the current Explicit KPI View still shows the generic unavailable message:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

This is no longer sufficiently informative when the user already enabled `Explicit KPI ON`.

The goal of this design is to show a clearer diagnostic message when the explicit pipeline is skipped by the context guard.

---

## 2. Background

The current cockpit path is:

```text
python -m main
    ↓
Explicit KPI ON checked
    ↓
Run Full Plan
    ↓
ctx guard detects missing required ctx
    ↓
Run Full Plan completes
    ↓
Explicit KPI View opens
    ↓
view remains unavailable
```

The missing context key confirmed during validation is:

```text
explicit_pipeline_backward_weekly_capability
```

The context guard records diagnostics on `env`:

```text
explicit_kpi_demo_flag_ctx_guard_skipped
explicit_kpi_demo_flag_missing_ctx_keys
explicit_kpi_demo_flag_guard_message
```

The next improvement is to show these diagnostics in the Explicit KPI View.

---

## 3. Current User Experience

Current view message:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

This message is correct for the simple case where the user has not enabled the explicit pipeline.

But after `Explicit KPI ON` is checked, this message becomes confusing because the user did enable it.

The real situation is:

```text
Explicit KPI ON was enabled,
but the explicit pipeline was skipped because required context was missing.
```

The UI should make this distinction visible.

---

## 4. Design Goal

When the Explicit KPI View is unavailable because the ctx guard skipped the explicit pipeline, show a diagnostic reason.

Recommended message:

```text
Explicit KPI ON was enabled, but the explicit pipeline was skipped because required context is missing:
explicit_pipeline_backward_weekly_capability
```

The design should preserve the existing safe behavior:

```text
no planning execution from the view
no export execution from the view
no ReplanCommand execution
no capability context generation
```

This phase is display-only.

---

## 5. Non-Goals

This phase must not implement:

```text
explicit_pipeline_backward_weekly_capability generation
weekly capability master loading
MOM capacity master design
Price-Cost-Profit propagation
Cost / KPI context generation
automatic fallback capability values
automatic Run Full Plan
automatic export
ReplanCommand execution
automatic replanning
OR optimization
database persistence
Knowledge Continuity persistence
waterfall / heatmap / drilldown
large GUI redesign
```

This phase is only:

```text
surface existing ctx guard diagnostics in the read-only Explicit KPI View
```

---

## 6. Data Source

The diagnostics are already recorded on `env`.

Expected fields:

```text
env.explicit_kpi_demo_flag_ctx_guard_skipped
env.explicit_kpi_demo_flag_missing_ctx_keys
env.explicit_kpi_demo_flag_guard_message
```

Example values:

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

The view model builder should read these values from `env`.

---

## 7. Current View-Model Flow

The existing GUI entry point is:

```python
WOMCockpit._open_explicit_pipeline_kpi_view()
```

It currently builds a view model from:

```python
build_explicit_pipeline_management_cockpit_view_model(self.env)
```

and renders it using:

```python
render_explicit_pipeline_management_cockpit_tk(self, view_model)
```

Recommended integration point:

```text
build_explicit_pipeline_management_cockpit_view_model(env)
```

Reason:

```text
diagnostics should become part of the view model,
not be fetched directly by the renderer from env.
```

The renderer should remain read-only and view-model-only.

---

## 8. Recommended View-Model Additions

Add diagnostic keys to the view model.

Recommended keys:

```python
{
    "ctx_guard_skipped": bool,
    "ctx_guard_missing_keys": list[str],
    "ctx_guard_message": str,
}
```

Alternative nested form:

```python
{
    "ctx_guard": {
        "skipped": bool,
        "missing_keys": list[str],
        "message": str,
    }
}
```

Recommended MVP:

```python
"ctx_guard_skipped"
"ctx_guard_missing_keys"
"ctx_guard_message"
```

Reason:

```text
flat keys are consistent with the existing simple view model style
```

---

## 9. View-Model Behavior

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

When diagnostics do not exist:

```python
ctx_guard_skipped = False
ctx_guard_missing_keys = []
ctx_guard_message = ""
```

This keeps old behavior stable.

---

## 10. Message Priority

When the view is unavailable, choose message priority as:

```text
1. ctx guard diagnostic message
2. existing unavailable message
```

If:

```python
view_model["available"] is False
```

and:

```python
view_model["ctx_guard_skipped"] is True
```

then the primary message should be:

```text
Explicit KPI ON was enabled, but the explicit pipeline was skipped because required context is missing:
explicit_pipeline_backward_weekly_capability
```

If no guard diagnostic exists, keep the current message:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

---

## 11. Recommended Display Locations

The diagnostic should appear in at least one prominent place.

Recommended MVP:

```text
top message area above the Notebook tabs
```

This is where the existing unavailable message is currently shown.

Additionally, it can be included in:

```text
Messages tab
```

Recommended MVP:

```text
top message area + Messages tab
```

Reason:

```text
top area gives immediate explanation
Messages tab keeps the diagnostic available after tab changes
```

---

## 12. Summary Tab Behavior

The Summary tab currently shows:

```text
Available: No
Explicit Pipeline Result: No
Capacity Report: No
Issue Candidates: No
Cost / KPI Bundle: No
```

This can remain unchanged.

Optional addition:

```text
Context Guard: Skipped
Missing Context: explicit_pipeline_backward_weekly_capability
```

Recommended MVP:

```text
Add these two rows to Summary key-value table if ctx_guard_skipped is True.
```

This is useful because the Summary tab is often the first tab the user sees.

---

## 13. Graphs Tab Behavior

The Graphs tab can remain unchanged.

It currently shows empty chart messages such as:

```text
No top impact issues are available.
No Cost / KPI impact composition is available.
No issue severity counts are available.
No week-level issue data is available.
```

This is acceptable.

Optional improvement:

```text
Graph Notes / Caveats includes ctx guard message.
```

Recommended MVP:

```text
Add ctx_guard_message to graph model messages if ctx_guard_skipped is True.
```

This can be done either in:

```text
build_explicit_pipeline_kpi_graph_view_model(...)
```

or in the renderer.

Preferred:

```text
graph view model builder
```

because chart rendering should remain dumb/read-only.

---

## 14. Messages Tab Behavior

The Messages tab should include the diagnostic message.

Recommended behavior:

```text
if ctx_guard_skipped:
    Messages tab includes ctx_guard_message
    Messages tab includes missing ctx keys
```

Example:

```text
Context guard skipped explicit pipeline execution.
Missing required context:
- explicit_pipeline_backward_weekly_capability
```

This turns an empty cockpit into a useful diagnostic cockpit.

---

## 15. Renderer Behavior

The renderer should not inspect `env`.

It should only inspect `view_model`.

Recommended renderer logic:

```python
if not view_model.get("available"):
    if view_model.get("ctx_guard_skipped"):
        show ctx_guard_message
    else:
        show current unavailable message
```

The renderer remains:

```text
read-only
side-effect-free
view-model-driven
```

---

## 16. Tests to Add / Update

Recommended test files:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Possibly:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

if Summary key-value rows are tested there.

---

## 17. View-Model Tests

Add tests that create an `env` with:

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

Also test default behavior:

```text
env without diagnostics
ctx_guard_skipped is False
ctx_guard_missing_keys == []
ctx_guard_message == ""
```

---

## 18. Renderer Tests

For Tk rendering tests, if possible:

```text
render view model with ctx_guard_skipped=True
window opens safely
diagnostic text is included somewhere in labels or message widgets
```

If exact Tk widget text inspection is brittle, keep the test focused on:

```text
render does not crash
Messages tab exists
view model contains diagnostics
```

Avoid pixel/layout assertions.

Use existing Tk-safe skip behavior.

---

## 19. Graph View Model Tests

If graph messages are updated, add a test:

```text
ctx_guard_skipped=True
ctx_guard_message present
build_explicit_pipeline_kpi_graph_view_model(view_model)
returns messages containing ctx_guard_message
```

Do not require chart data to exist.

The chart panels can remain empty.

---

## 20. Completion Criteria

This diagnostic-view phase is complete when:

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

## 21. Manual GUI Validation

Manual validation after implementation:

```text
1. python -m main
2. check Explicit KPI ON
3. click Run Full Plan
4. confirm Run Full Plan completes
5. open Explicit KPI View
6. confirm it shows diagnostic reason:
   explicit_pipeline_backward_weekly_capability
```

Expected result:

```text
Cockpit data may still be unavailable,
but the reason is visible.
```

This is the intended outcome.

---

## 22. Later Work: Capability Context Generation

After diagnostics are visible, the next major design should define how to generate or load:

```text
explicit_pipeline_backward_weekly_capability
```

Likely input concepts:

```text
Weekly Capability on MOM nodes
node-product-week capacity master
capacity calendar
resource / process capability table
scenario-specific capacity assumptions
```

This later work is the step that can make the Explicit KPI View actually populate pipeline / capacity results.

---

## 23. Later Work: Price-Cost-Profit Propagation

The user's target Price-Cost-Profit model includes:

```text
A. market-accepted price propagated upstream through the E2E tree
B. material-accepted cost propagated downstream through the E2E tree
C. comparison of A and B to allocate price, profit, and cost portions
```

This should remain a separate topic.

Recommended later memo:

```text
docs/design/price_cost_profit_e2e_propagation_inventory.md
```

Do not mix this into the diagnostics-view patch.

---

## 24. Summary

The ctx guard made the cockpit stable.

The diagnostics-view improvement should make the cockpit understandable.

Current state:

```text
Explicit KPI ON + missing ctx
    ↓
Run Full Plan completes
    ↓
Explicit KPI View opens but is empty
```

Target after this phase:

```text
Explicit KPI ON + missing ctx
    ↓
Run Full Plan completes
    ↓
Explicit KPI View opens
    ↓
View explains:
       explicit pipeline skipped because required context is missing:
       explicit_pipeline_backward_weekly_capability
```

This phase turns silent safety behavior into visible diagnostic behavior.
