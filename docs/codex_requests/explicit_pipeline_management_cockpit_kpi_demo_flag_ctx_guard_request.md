# Codex Request: Implement Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following context-guard design memo has already been added:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_ctx_guard.md
```

Please read that design memo first.

The current branch already includes:

```text
Phase 1:
    apply_explicit_pipeline_kpi_demo_flags(...)
    pure helper + tests

Phase 2:
    Explicit KPI ON checkbox
    _maybe_apply_explicit_kpi_demo_flags()
    Run Full Plan preflight hook
```

The checkbox successfully applies the demo flag helper before `Run Full Plan`.

However, manual GUI validation found that when `Explicit KPI ON` is checked and `Run Full Plan` is executed, the application can stop with:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key: explicit_pipeline_backward_weekly_capability
```

This proves that the GUI wiring works, but required explicit pipeline context is missing in the normal GUI run path.

This request implements a guard so that:

```text
Explicit KPI ON + missing required ctx
```

does not crash `Run Full Plan`.

---

## 2. Main Objective

Add a safe context guard for the Explicit KPI demo flag path.

The desired behavior is:

```text
If Explicit KPI ON is checked
    apply demo flags
    check required explicit pipeline ctx
    if required ctx is missing:
        record missing ctx keys on env
        disable explicit pipeline/report flags for this run
        allow Run Full Plan to continue
    else:
        keep flags enabled
        allow explicit pipeline to run
```

The immediate success target is:

```text
Run Full Plan does not crash when Explicit KPI ON is checked but required ctx is missing.
```

The target is **not yet** fully populated KPI cards.

---

## 3. Confirmed Error

Manual GUI validation confirmed this error path:

```text
run_full_plan()
    ↓
_run_planning_sequence()
    ↓
maybe_run_explicit_bridge_capacity_pipeline_from_env(...)
    ↓
maybe_run_explicit_bridge_capacity_pipeline(ctx)
    ↓
ValueError: explicit bridge capacity pipeline enabled but missing ctx key: explicit_pipeline_backward_weekly_capability
```

Search results identified:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
    required ctx key:
    explicit_pipeline_backward_weekly_capability

pysi/gui/cockpit_tk.py
    passes:
    backward_weekly_capability=getattr(self.env, "explicit_pipeline_backward_weekly_capability", None)
```

The missing env attribute is:

```text
self.env.explicit_pipeline_backward_weekly_capability
```

or it exists but is `None`.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Do not generate explicit_pipeline_backward_weekly_capability in this request.
2. Do not implement weekly capacity master loading.
3. Do not implement MOM capacity master design.
4. Do not implement Price-Cost-Profit propagation.
5. Do not implement Cost / KPI context generation.
6. Do not add automatic fallback capacity values.
7. Do not run exports.
8. Do not execute ReplanCommand.
9. Do not implement automatic replanning.
10. Do not implement OR optimization.
11. Do not implement database persistence.
12. Do not implement Knowledge Continuity persistence.
13. Do not add waterfall / heatmap / drilldown.
14. Do not add new dependencies.
15. Do not make large GUI layout changes.
```

This request is only for:

```text
safe skipping when required explicit pipeline ctx is missing
```

The safety rule is:

```text
If the engine lacks required fuel, do not start the engine.
Do not crash the cockpit.
```

---

## 5. Files to Modify / Add

Likely files to modify:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/reporting/__init__.py
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Potential file to modify only if useful:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Avoid modifying:

```text
pysi/reporting/exporters/*
pysi/reporting/builders/*
pysi/plan/* other than explicit_bridge_capacity_pipeline.py if needed
pysi/core/*
```

---

## 6. Recommended Implementation Approach

Recommended MVP approach:

```text
Add a pure required-ctx detection helper near the demo flag helper.
Call it from WOMCockpit._maybe_apply_explicit_kpi_demo_flags().
```

Recommended new helper in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Recommended function:

```python
def get_missing_explicit_pipeline_demo_ctx_keys(env: Any) -> list[str]:
    ...
```

The helper returns env attribute names that are missing or `None`.

At minimum, it should check:

```text
explicit_pipeline_backward_weekly_capability
```

If practical, expose or reuse the same required-key list from:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

to avoid duplication.

If exposing that list would be too invasive, it is acceptable for this patch to define the required demo ctx keys in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

as:

```python
_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
)
```

---

## 7. Missing Context Semantics

A key should be considered missing when:

```python
not hasattr(env, key)
```

or:

```python
getattr(env, key) is None
```

Do not treat these as missing in this first guard:

```python
{}
[]
0
False
```

unless the existing pipeline explicitly requires non-empty values.

This request should avoid over-validating unknown future valid structures.

---

## 8. GUI Preflight Guard Behavior

Update:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

Current behavior:

```text
if checkbox missing/off:
    return None
if checkbox on:
    apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

New behavior:

```text
if checkbox missing/off:
    return None

if checkbox on:
    applied = apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)

    missing = get_missing_explicit_pipeline_demo_ctx_keys(self.env)

    if missing:
        record diagnostics on env
        disable explicit pipeline/report flags for this run
        return applied or guard result

    return applied
```

Recommended diagnostic env fields:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = True
explicit_kpi_demo_flag_missing_ctx_keys = ["explicit_pipeline_backward_weekly_capability"]
explicit_kpi_demo_flag_guard_message = "Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_backward_weekly_capability"
```

When no missing keys exist, either remove / reset the diagnostic fields or set:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = False
explicit_kpi_demo_flag_missing_ctx_keys = []
```

Choose a deterministic behavior and test it.

---

## 9. Flags to Disable When Context Is Missing

If required ctx is missing, disable:

```text
enable_explicit_bridge_capacity_pipeline
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
```

Also defensively set export flags to False:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

Reason:

```text
If pipeline artifacts cannot be produced, downstream report / issue / Cost-KPI steps should not expect them.
```

This prevents:

```text
maybe_run_explicit_bridge_capacity_pipeline_from_env(...)
```

from invoking the strict pipeline with missing ctx.

---

## 10. Helper Return Value

Do not break the existing return behavior of:

```python
apply_explicit_pipeline_kpi_demo_flags(...)
```

It should continue returning the applied flag map.

For `_maybe_apply_explicit_kpi_demo_flags()`, it is acceptable to return the original applied map even if guard disables flags afterward.

However, if a more informative return is simple, it may return a dict containing:

```text
applied flags
missing ctx keys
guard skipped status
```

But avoid changing tests or calling code unnecessarily.

Recommended simple approach:

```text
_keep existing return map_
and test env diagnostics / final env flag values.
```

---

## 11. Package Export

If a new helper is added:

```python
get_missing_explicit_pipeline_demo_ctx_keys
```

export it from:

```text
pysi/reporting/__init__.py
```

only if consistent with existing package style.

At minimum, tests may import it directly from:

```text
pysi.reporting.explicit_pipeline_kpi_demo_flags
```

---

## 12. Tests to Add / Update

Update focused tests.

### 12.1 Missing ctx detection helper

In:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Add:

```python
def test_missing_ctx_detection_reports_backward_weekly_capability():
    env = SimpleNamespace()
    missing = get_missing_explicit_pipeline_demo_ctx_keys(env)
    assert "explicit_pipeline_backward_weekly_capability" in missing
```

### 12.2 Present ctx passes guard

```python
def test_missing_ctx_detection_empty_when_backward_weekly_capability_present():
    env = SimpleNamespace(
        explicit_pipeline_backward_weekly_capability={"MOM": {"W01": 100}}
    )
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

### 12.3 GUI ON but missing ctx disables pipeline flags

In:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Add/update test:

```text
checkbox ON
env missing explicit_pipeline_backward_weekly_capability
_maybe_apply_explicit_kpi_demo_flags(fake)
env.explicit_kpi_demo_flag_ctx_guard_skipped is True
missing keys include explicit_pipeline_backward_weekly_capability
env.enable_explicit_bridge_capacity_pipeline is False
env.enable_explicit_bridge_capacity_report is False
env.enable_explicit_bridge_capacity_issue_candidates is False
env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi is False
export flags are False
```

### 12.4 GUI ON with ctx keeps flags enabled

Given:

```python
env = SimpleNamespace(
    explicit_pipeline_backward_weekly_capability={"MOM": {"W01": 100}}
)
```

Expect:

```text
env.enable_explicit_bridge_capacity_pipeline is True
env.enable_explicit_bridge_capacity_report is True
env.enable_explicit_bridge_capacity_issue_candidates is True
env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi is True
ctx guard skipped is absent or False
```

### 12.5 Checkbox OFF remains unchanged

Ensure existing OFF behavior remains:

```text
helper is not applied
env flags are not added
returns None
```

### 12.6 Run Full Plan ordering test remains valid

Existing test for preflight ordering should still pass.

---

## 13. Existing Tests to Run

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Then run related tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

Then run broader cockpit tests if time allows:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_canvas_rendering.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_button_integration.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

Optional smoke:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If optional tests are not run, state so clearly.

If Tk tests are skipped, state so clearly.

---

## 14. Manual GUI Validation

After implementation and commit, manually verify:

```text
1. python -m main
2. check Explicit KPI ON
3. click Run Full Plan
4. confirm no missing ctx key error appears
5. confirm Run Full Plan completes
6. open Explicit KPI View
7. confirm view opens
8. confirm it may remain unavailable because ctx is missing
```

Expected current behavior after this guard:

```text
Run Full Plan should not crash.
Explicit KPI View may still show unavailable.
```

This is acceptable.

This request does not aim to make KPI cards fully populated.

---

## 15. Important Success Criterion

Do not treat the following as failure for this request:

```text
Explicit KPI View still unavailable
```

That is expected until:

```text
explicit_pipeline_backward_weekly_capability
```

is generated or loaded.

Success for this request is:

```text
Explicit KPI ON no longer crashes Run Full Plan when ctx is missing.
```

---

## 16. Completion Criteria

This request is complete when:

```text
[OK] get_missing_explicit_pipeline_demo_ctx_keys or equivalent exists
[OK] missing explicit_pipeline_backward_weekly_capability is detected
[OK] present explicit_pipeline_backward_weekly_capability passes guard
[OK] Explicit KPI ON + missing ctx does not leave pipeline flag enabled
[OK] missing ctx keys are recorded on env
[OK] guard message is recorded on env
[OK] Run Full Plan can continue without ValueError
[OK] checkbox OFF behavior remains unchanged
[OK] checkbox ON with valid ctx keeps flags enabled
[OK] no automatic capability ctx generation is added
[OK] no export execution is added
[OK] no ReplanCommand execution is added
[OK] focused tests pass
```

---

## 17. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. New helper / guard functions
3. Required ctx keys checked
4. GUI preflight behavior when ctx missing
5. Final flag behavior when ctx missing
6. Env diagnostics added
7. Behavior when ctx is present
8. Safety boundaries preserved
9. Tests added / updated
10. Test commands executed
11. Test results
12. Skipped tests and why
13. Manual GUI validation notes if performed
14. Limitations / follow-up
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
Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard
```
