# Explicit Pipeline Forward Weekly Capacity GUI Preflight Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-27  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines **Phase F2** for the Explicit Pipeline Forward Weekly Capacity work.

Phase F1 implemented the standalone adapter functions for:

```text
explicit_pipeline_forward_weekly_capacity
```

Phase F2 wires the new optional attach helper into the existing Explicit KPI ON GUI preflight path.

The target preflight order is:

```text
Explicit KPI ON
    ↓
apply demo flags
    ↓
attach backward capability from CSV
    ↓
attach forward weekly capacity from CSV
    ↓
ctx guard check
```

This phase is a GUI preflight wiring phase only.

It should not add a forward sample CSV yet.

---

## 2. Background

The Explicit KPI ON path currently has the following pieces:

```text
Explicit KPI ON checkbox
demo flag helper
ctx guard
ctx guard diagnostics view
backward capability CSV attach helper
backward capability GUI preflight wiring
forward weekly capacity adapter
forward weekly capacity optional attach helper
```

The forward adapter was added in Phase F1 with these functions:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
load_explicit_pipeline_forward_weekly_capacity_csv(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

The missing piece is:

```text
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
does not yet call the forward weekly capacity optional attach helper.
```

---

## 3. Current Behavior

Current GUI preflight order:

```text
Explicit KPI ON
    ↓
apply_explicit_pipeline_kpi_demo_flags(...)
    ↓
_maybe_attach_explicit_pipeline_backward_weekly_capability()
    ↓
get_missing_explicit_pipeline_demo_ctx_keys(...)
```

Because forward weekly capacity is not yet attached by GUI preflight, the ctx guard still reports:

```text
explicit_pipeline_forward_weekly_capacity
```

as missing unless it has been manually attached elsewhere.

This is expected after Phase F1.

---

## 4. Target Behavior

Target GUI preflight order after Phase F2:

```text
Explicit KPI ON
    ↓
apply_explicit_pipeline_kpi_demo_flags(...)
    ↓
_maybe_attach_explicit_pipeline_backward_weekly_capability()
    ↓
_maybe_attach_explicit_pipeline_forward_weekly_capacity()
    ↓
get_missing_explicit_pipeline_demo_ctx_keys(...)
```

If no forward capacity CSV exists, behavior should remain safe:

```text
forward attach helper returns file_missing
env.explicit_pipeline_forward_weekly_capacity is not attached
ctx guard detects explicit_pipeline_forward_weekly_capacity missing
explicit flags are forced OFF for the run
Run Full Plan completes safely
Explicit KPI View shows missing forward capacity diagnostic
```

If a valid forward capacity CSV exists later:

```text
forward capacity is attached before ctx guard
ctx guard can pass if backward capability is also present
explicit pipeline is allowed to run
```

---

## 5. Scope

Phase F2 should implement only:

```text
1. private GUI helper method for forward capacity attach
2. call that helper from Explicit KPI ON preflight
3. focused GUI wiring tests
```

Expected files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Do not add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

That belongs to Phase F3.

---

## 6. Non-Goals

This phase must not implement:

```text
forward sample CSV
manual GUI validation with sample CSV
explicit bridge capacity pipeline changes
planning engine changes
pipeline shape refactor
new GUI widgets
scenario selector
export execution
ReplanCommand execution
Price-Cost-Profit propagation
tariff simulation
cold-chain shelf-life modeling
database persistence
```

This phase is only:

```text
GUI preflight wiring for the existing forward attach helper
```

---

## 7. Recommended GUI Helper

Add a private helper to `WOMCockpit`:

```python
def _maybe_attach_explicit_pipeline_forward_weekly_capacity(self) -> dict[str, Any] | None:
    from pysi.plan.explicit_pipeline_capacity_context import (
        maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv,
    )

    return maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(self.env)
```

This mirrors the existing backward helper:

```python
_maybe_attach_explicit_pipeline_backward_weekly_capability()
```

The helper should be called only when Explicit KPI ON preflight is active.

It should not be called when the checkbox is OFF.

---

## 8. Required Preflight Order

The ordering is important.

Correct order:

```text
1. Explicit KPI ON check
2. apply_explicit_pipeline_kpi_demo_flags(...)
3. attach backward capability from CSV
4. attach forward weekly capacity from CSV
5. get_missing_explicit_pipeline_demo_ctx_keys(...)
6. if missing: force explicit flags OFF
7. if no missing: keep explicit flags ON
```

Do not attach forward capacity before demo flags are applied.

Do not run ctx guard before attempting forward capacity attach.

Do not call the explicit bridge capacity pipeline in this helper.

---

## 9. Existing Preflight Method

The existing method is:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

It currently handles:

```text
checkbox missing
checkbox OFF
demo flag application
backward capability attach
required ctx guard check
ctx guard diagnostics
explicit flag disabling when ctx is missing
ctx guard pass behavior
```

Phase F2 should keep all of this behavior and insert forward attach after backward attach.

---

## 10. Expected Behavior Matrix

### 10.1 Explicit KPI OFF

Expected:

```text
no demo flags
no backward attach attempt
no forward attach attempt
no ctx guard mutation
return None
```

### 10.2 Explicit KPI ON + no forward CSV

Expected:

```text
demo flags applied
backward attach attempted
forward attach attempted
forward attach result reason=file_missing
ctx guard still reports explicit_pipeline_forward_weekly_capacity
explicit pipeline flags forced OFF
Run Full Plan safe
```

### 10.3 Explicit KPI ON + forward attach returns empty_context

Expected:

```text
demo flags applied
backward attach attempted
forward attach attempted
forward attach result reason=empty_context
ctx guard reports explicit_pipeline_forward_weekly_capacity
explicit pipeline flags forced OFF
Run Full Plan safe
```

### 10.4 Explicit KPI ON + backward and forward contexts both attached

Expected:

```text
demo flags applied
backward context present
forward context present
ctx guard skipped=False
missing keys=[]
explicit runtime flags remain ON
export flags remain OFF
```

---

## 11. Diagnostics

The forward attach helper records diagnostics on env:

```text
explicit_pipeline_forward_weekly_capacity_attach_result
explicit_pipeline_forward_weekly_capacity_source_path
explicit_pipeline_forward_weekly_capacity_source_scenario
explicit_pipeline_forward_weekly_capacity_attached
```

The GUI preflight does not need to create new diagnostic fields.

It may ignore the returned result for now.

Future diagnostics view enhancement can surface the attach result if needed.

---

## 12. Test Strategy

Update:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Use monkeypatching / fake methods rather than relying on a real file:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

This keeps Phase F2 independent from Phase F3 sample CSV.

---

## 13. Tests to Add / Update

### 13.1 Explicit KPI OFF does not call forward attach

Set:

```text
var_enable_explicit_kpi_reporting = False
```

Monkeypatch forward attach helper to fail if called.

Expected:

```text
_maybe_apply_explicit_kpi_demo_flags() returns None
forward attach is not called
```

If there is already a test for backward attach not being called, extend it to cover forward attach too.

---

### 13.2 Explicit KPI ON calls backward then forward then guard

Use fake methods to record call order.

Expected order:

```text
apply demo flags
backward attach
forward attach
ctx guard
```

Because directly intercepting `apply_explicit_pipeline_kpi_demo_flags` and `get_missing_explicit_pipeline_demo_ctx_keys` may be awkward, a practical test can verify:

```text
forward attach is called
when forward attach populates env, ctx guard passes
```

This indirectly proves forward attach happens before ctx guard.

---

### 13.3 Explicit KPI ON + backward-only remains guard skipped

Monkeypatch:

```python
_maybe_attach_explicit_pipeline_backward_weekly_capability()
```

to attach:

```python
env.explicit_pipeline_backward_weekly_capability = {
    "MILL_EAST": {
        "PACKAGED_RICE_STANDARD": {
            "2027-W40": 5
        }
    }
}
```

Monkeypatch forward helper to do nothing and return:

```python
{"attached": False, "reason": "file_missing"}
```

Expected:

```text
forward attach called
ctx guard skipped=True
missing ctx keys == ["explicit_pipeline_forward_weekly_capacity"]
explicit flags forced OFF
export flags remain False
```

---

### 13.4 Explicit KPI ON + both contexts passes guard

Monkeypatch backward helper to attach backward context.

Monkeypatch forward helper to attach:

```python
env.explicit_pipeline_forward_weekly_capacity = {
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5
            }
        }
    }
}
```

Expected:

```text
forward attach called
ctx guard skipped=False
missing ctx keys == []
explicit pipeline/report/issue/cost-kpi flags remain True
export flags remain False
```

---

### 13.5 No context still reports both keys

If both helpers do nothing:

```text
ctx guard skipped=True
missing keys include:
    explicit_pipeline_backward_weekly_capability
    explicit_pipeline_forward_weekly_capacity
```

This preserves the existing guard behavior.

---

## 14. Existing Tests to Run

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Run related tests:

```bat
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

Run broader regression tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
python -m pytest tests/test_japanese_rice_case_smoke.py
```

If Tk tests are skipped, state it clearly.

---

## 15. Manual GUI Validation

Manual GUI validation is optional for Phase F2 because no forward sample CSV is added.

Without forward CSV, the expected manual behavior remains:

```text
Explicit KPI ON
Run Full Plan
Run Full Plan completes
Explicit KPI View shows:
    explicit_pipeline_forward_weekly_capacity
```

The difference is that the GUI preflight now attempts to load forward capacity CSV before the ctx guard reports it missing.

Manual validation with the missing file is useful but not mandatory.

---

## 16. Completion Criteria

Phase F2 is complete when:

```text
[OK] private forward attach GUI helper added
[OK] Explicit KPI OFF does not call forward attach
[OK] Explicit KPI ON calls forward attach before ctx guard
[OK] missing forward capacity remains a safe diagnostic
[OK] both-context path allows guard pass
[OK] export flags remain OFF
[OK] no forward sample CSV added
[OK] no planning / pipeline / export changes added
[OK] focused tests pass
```

---

## 17. Safety Boundaries

Preserve:

```text
no data/explicit_pipeline_forward_weekly_capacity.csv
no GUI layout redesign
no new checkbox
no scenario selector
no planning engine change
no explicit bridge capacity pipeline change
no export execution
no ReplanCommand execution
no dummy context generation
no monetary KPI implementation
```

This is a small preflight wiring patch.

---

## 18. Recommended Next Phase

After Phase F2, proceed to Phase F3:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
```

Phase F3 should add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Candidate Japanese Rice Case sample:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

First validation target after F3:

```text
explicit_pipeline_forward_weekly_capacity missing diagnostic disappears
```

Full KPI population is a later pipeline / scenario alignment topic.

---

## 19. Summary

Phase F2 connects the forward weekly capacity adapter to the Explicit KPI GUI preflight.

Target order:

```text
apply demo flags
attach backward capability
attach forward weekly capacity
ctx guard
```

This keeps the system safe when no forward CSV exists and prepares the path for Phase F3 sample CSV validation.
