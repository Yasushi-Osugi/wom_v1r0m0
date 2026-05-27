# Explicit Pipeline Forward Weekly Capacity Context Guard Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-27  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of the **Explicit Pipeline Forward Weekly Capacity Context Guard** patch.

The purpose of this patch was to prevent `Run Full Plan` from crashing when the Explicit KPI ON path enables the explicit bridge capacity pipeline but the following required context is missing:

```text
explicit_pipeline_forward_weekly_capacity
```

The intended behavior was:

```text
missing forward weekly capacity
    ↓
ctx guard detects missing key before pipeline execution
    ↓
explicit pipeline flags are forced OFF for the run
    ↓
Run Full Plan completes safely
    ↓
Explicit KPI View shows missing context diagnostic
```

This patch restored the safety principle:

```text
missing optional explicit-pipeline context should produce diagnostics,
not crash Run Full Plan.
```

---

## 2. Background

Before this patch, Phase 2C added the Japanese Rice Case sample CSV:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

This CSV allowed the runtime preflight to attach:

```text
env.explicit_pipeline_backward_weekly_capability
```

As a result, the previous missing context key:

```text
explicit_pipeline_backward_weekly_capability
```

was no longer the first blocker.

However, manual GUI validation then exposed the next required key:

```text
explicit_pipeline_forward_weekly_capacity
```

The explicit bridge capacity pipeline raised:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key:
explicit_pipeline_forward_weekly_capacity
```

This showed that the ctx guard was incomplete.

---

## 3. Implemented Commit

The implementation was committed as:

```text
aa74d2a Extend explicit KPI ctx guard with forward weekly capacity key
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

The implementation changed five files:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
tests/test_explicit_pipeline_capacity_context.py
```

No GUI control-flow file was changed.

No planning engine file was changed.

No explicit bridge capacity pipeline file was changed.

No new CSV file was added.

---

## 5. Required Context Key List

Before this patch, the required Explicit KPI demo context key list was effectively:

```python
(
    "explicit_pipeline_backward_weekly_capability",
)
```

After this patch, it is:

```python
(
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
)
```

The required-key list is used by:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

---

## 6. Missing Detection Semantics

The missing detection semantics were preserved.

A key is missing when:

```text
the env attribute is absent
or
the env attribute is None
```

This patch did not expand the meaning of missing to include empty dictionaries.

Reason:

```text
The immediate runtime failure was caused by absent forward context.
Changing empty-dict semantics is a separate design decision.
```

---

## 7. Backward-Only Behavior

When `env` contains:

```text
explicit_pipeline_backward_weekly_capability
```

but does not contain:

```text
explicit_pipeline_forward_weekly_capacity
```

the guard now returns:

```python
[
    "explicit_pipeline_forward_weekly_capacity"
]
```

In GUI preflight, this means:

```text
ctx guard skipped = True
explicit bridge capacity pipeline flag = False
explicit bridge capacity report flag = False
explicit bridge capacity issue candidate flag = False
explicit bridge capacity issue candidate cost KPI flag = False
export flags remain False
```

This prevents the explicit bridge capacity pipeline from being called with incomplete context.

---

## 8. Both-Context Behavior

When `env` contains both:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

the guard returns:

```python
[]
```

In GUI preflight, this means:

```text
ctx guard skipped = False
explicit bridge capacity pipeline flag remains True
explicit bridge capacity report flag remains True
explicit bridge capacity issue candidate flag remains True
explicit bridge capacity issue candidate cost KPI flag remains True
export flags remain False
```

The exact internal shape of `explicit_pipeline_forward_weekly_capacity` was not validated in this patch.

This patch only checks context presence.

---

## 9. Empty / No-Context Behavior

When neither key is present, the guard now returns both keys in deterministic order:

```python
[
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
]
```

This is important because the Explicit KPI View can now show all known missing required context keys rather than only the first known key.

---

## 10. Tests Updated

### 10.1 Guard Helper Tests

Updated:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Coverage now includes:

```text
empty env => backward and forward keys missing
backward-only env => forward key missing
backward + forward env => no missing keys
```

### 10.2 GUI Wiring Tests

Updated:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Coverage now includes:

```text
no context => both keys missing and explicit flags forced OFF
backward-only context => forward key missing and explicit flags forced OFF
both contexts => guard passes and explicit flags remain ON
export flags remain OFF
```

### 10.3 Backward Capability Sample CSV Tests

Updated:

```text
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

The sample CSV attach helper now correctly expects:

```text
explicit_pipeline_forward_weekly_capacity
```

to remain missing after only backward capability is attached.

### 10.4 Capacity Context Tests

Updated:

```text
tests/test_explicit_pipeline_capacity_context.py
```

Backward capability attach tests now correctly expect the forward capacity key to remain missing unless it is also supplied.

---

## 11. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
python -m pytest tests/test_japanese_rice_case_smoke.py
```

Observed results:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py                           7 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                 7 passed
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py    3 passed
tests/test_explicit_pipeline_capacity_context.py                        16 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py             10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py        9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py 3 passed, 1 skipped
tests/test_explicit_pipeline_reporting_stack_insertion.py                7 passed
tests/test_explicit_pipeline_reporting_flags.py                         10 passed
tests/test_covid_vaccine_with_capacity_push.py                           1 passed
tests/test_japanese_rice_case_smoke.py                                   1 passed
```

Total observed result:

```text
74 passed, 1 skipped
```

The skipped test is Tk rendering related and is not a failure.

---

## 12. Manual GUI Validation

Manual GUI validation was performed after the patch.

Flow:

```text
python -m main
Explicit KPI ON
Run Full Plan
Open Explicit KPI View
```

Observed behavior:

```text
Run Full Plan completed.
No ValueError stop occurred.
Explicit KPI View displayed missing context diagnostic.
```

Displayed diagnostic:

```text
Context Guard: Skipped
Missing Context: explicit_pipeline_forward_weekly_capacity
```

This matches the expected safe intermediate behavior.

---

## 13. Scope Boundaries Preserved

This patch intentionally did not implement:

```text
forward weekly capacity generation
forward weekly capacity CSV
forward weekly capacity adapter
planning engine changes
explicit bridge capacity pipeline changes
pipeline shape refactor
GUI layout changes
new checkbox
scenario selector
export execution
ReplanCommand execution
automatic replanning
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
process-level capacity
```

This patch only extended the guard.

---

## 14. Meaning of This Milestone

Before this patch:

```text
backward capability context could be attached,
but the pipeline could still crash due to missing forward capacity context.
```

After this patch:

```text
backward-only context is recognized as incomplete before pipeline execution.
```

The system now behaves as:

```text
backward capability exists
forward weekly capacity missing
    ↓
guard skip
    ↓
explicit flags OFF
    ↓
Run Full Plan completes
    ↓
Explicit KPI View explains missing forward capacity
```

This is the desired safe cockpit behavior.

---

## 15. Current State

Current Explicit KPI ON path:

```text
Explicit KPI ON
    ↓
apply demo flags
    ↓
load / attach backward capability CSV if present
    ↓
ctx guard checks:
        explicit_pipeline_backward_weekly_capability
        explicit_pipeline_forward_weekly_capacity
    ↓
if forward capacity missing:
        skip explicit pipeline safely
        show diagnostic
```

Current missing runtime context:

```text
explicit_pipeline_forward_weekly_capacity
```

Current UI state:

```text
Run Full Plan does not crash.
Explicit KPI View shows missing forward weekly capacity.
```

---

## 16. Recommended Next Step

The next design phase should define:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
```

The main questions are:

```text
1. What is the canonical shape of explicit_pipeline_forward_weekly_capacity?
2. Does explicit_bridge_capacity_pipeline.py expect product-first or node-first structure?
3. How should capacity type P / S / I be represented?
4. Should the source be existing capacity master rows?
5. How should Japanese Rice Case and the current iPhone GUI demo be separated?
6. Should forward capacity use the same scenario=base default strategy as backward capability?
```

Only after this shape is clarified should a sample forward capacity CSV or adapter be implemented.

---

## 17. Summary

The Explicit Pipeline Forward Weekly Capacity Context Guard patch is complete.

Implemented:

```text
required-key list extension
guard-helper tests
GUI preflight behavior tests
backward-only expected-missing updates
manual GUI confirmation
```

The key result is:

```text
Run Full Plan no longer crashes when forward weekly capacity is missing.
```

Instead, the cockpit now shows:

```text
Missing Context:
explicit_pipeline_forward_weekly_capacity
```

This completes the safety step and prepares the next phase: defining and supplying the forward weekly capacity context itself.
