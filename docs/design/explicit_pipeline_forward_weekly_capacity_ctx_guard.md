# Explicit Pipeline Forward Weekly Capacity Context Guard Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the next safety patch for the Explicit KPI ON / explicit bridge capacity pipeline path.

The immediate purpose is to prevent `Run Full Plan` from crashing when the explicit bridge capacity pipeline is enabled but this required context is missing:

```text
explicit_pipeline_forward_weekly_capacity
```

The desired behavior is:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
preflight applies demo flags
    ↓
preflight loads backward capability CSV if available
    ↓
ctx guard checks all required explicit pipeline context keys
    ↓
if explicit_pipeline_forward_weekly_capacity is missing:
        do not run explicit bridge capacity pipeline
        force explicit flags OFF for this run
        show missing context diagnostic in Explicit KPI View
        continue normal full plan safely
```

This memo is about restoring and extending the safety guard.

It does not define forward weekly capacity generation.

---

## 2. Triggering Runtime Observation

After Phase 2C, the Japanese Rice Case sample CSV was added:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

The CSV allowed the previous missing key to be supplied:

```text
explicit_pipeline_backward_weekly_capability
```

However, during manual GUI validation with `Explicit KPI ON` and `Run Full Plan`, the application stopped with:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key:
explicit_pipeline_forward_weekly_capacity
```

This indicates that the prior ctx guard was incomplete.

It detected:

```text
explicit_pipeline_backward_weekly_capability
```

but did not yet detect:

```text
explicit_pipeline_forward_weekly_capacity
```

before the pipeline itself was called.

---

## 3. Interpretation

This is not a failure of the Japanese Rice Case backward capability CSV.

It is a useful discovery that the explicit bridge capacity pipeline requires at least two capability-related context objects:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The previous safety guard only covered the backward capability key.

Therefore, after the backward key was successfully attached, the guard let the explicit pipeline proceed, but the pipeline itself stopped at the next missing key.

The safety boundary should be moved earlier.

The ctx guard should detect all known required keys before calling the pipeline.

---

## 4. Current Problem

Current behavior:

```text
Explicit KPI ON checked
    ↓
backward capability CSV is attached
    ↓
ctx guard sees no missing backward key
    ↓
explicit pipeline remains enabled
    ↓
explicit bridge capacity pipeline is called
    ↓
pipeline checks ctx
    ↓
explicit_pipeline_forward_weekly_capacity is missing
    ↓
ValueError is raised
    ↓
Run Full Plan stops
```

This is not acceptable for GUI behavior.

The Explicit KPI demo path should remain safe even when optional pipeline contexts are incomplete.

---

## 5. Target Behavior

Target behavior after this patch:

```text
Explicit KPI ON checked
    ↓
backward capability CSV is attached if available
    ↓
ctx guard checks both backward and forward context keys
    ↓
forward key is missing
    ↓
guard records missing context
    ↓
guard forces explicit pipeline/report/issue/cost-kpi flags OFF for this run
    ↓
explicit bridge capacity pipeline is not called
    ↓
Run Full Plan completes
    ↓
Explicit KPI View shows:
        explicit_pipeline_forward_weekly_capacity
```

This restores the intended “do not crash” behavior.

---

## 6. Required Context Keys

The required ctx key list should be expanded from:

```text
explicit_pipeline_backward_weekly_capability
```

to:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

This list should live in the same helper mechanism already used by:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

The function should report a key as missing when:

```text
the env attribute is absent
or the env attribute is None
```

Recommended behavior regarding empty dictionaries:

```text
For this guard patch, keep the existing missing rule if it only treats absent/None as missing.
Do not expand semantics to treat empty dict as missing unless current tests already expect that.
```

Reason:

```text
The immediate crash is caused by absent/None forward context.
Changing empty-context semantics is a separate behavior change.
```

---

## 7. Expected Missing-Key Diagnostics

When only backward capability is attached and forward capacity is absent, diagnostics should become:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = True
explicit_kpi_demo_flag_missing_ctx_keys = ["explicit_pipeline_forward_weekly_capacity"]
explicit_kpi_demo_flag_guard_message =
    "Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_forward_weekly_capacity"
```

If both are missing, diagnostics should include both:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The ordering should be deterministic.

Recommended order:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

---

## 8. Scope

This patch should modify only the guard / tests.

Expected files:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Possibly also:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

only if existing diagnostics tests need updates.

---

## 9. Non-Goals

This patch must not implement:

```text
forward weekly capacity CSV
forward weekly capacity adapter
forward weekly capacity generation
planning engine changes
explicit bridge capacity pipeline changes
sample forward capacity CSV
GUI layout changes
scenario selector
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
ReplanCommand execution
automatic replanning
```

This patch is only:

```text
extend ctx guard required keys
prevent GUI crash
show missing forward capacity key as diagnostic
```

---

## 10. Important Scenario Note

The current manual GUI screen showed product:

```text
IPHONE_NM_2028_BASE
```

while the new backward capability sample CSV is for:

```text
Japanese Rice Case
PACKAGED_RICE_STANDARD
MILL_EAST
```

Therefore, even after the forward key is guarded or supplied, the GUI scenario and the sample CSV scenario may still be inconsistent.

This patch does not solve scenario alignment.

It only prevents the explicit pipeline from crashing when required context is incomplete.

---

## 11. Implementation Detail

Update the required-key constant in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Current conceptual form:

```python
_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
)
```

Recommended new form:

```python
_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
)
```

If the constant has a different exact name, update the existing required-key list used by:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

Do not create a second independent required-key list.

---

## 12. GUI Preflight Interaction

The existing preflight in:

```text
pysi/gui/cockpit_tk.py
```

already does the right high-level behavior:

```text
apply demo flags
try optional backward capability CSV attach
run get_missing_explicit_pipeline_demo_ctx_keys(env)
if missing:
    force explicit flags OFF
```

Once the required-key helper includes `explicit_pipeline_forward_weekly_capacity`, the existing GUI preflight should automatically skip the explicit pipeline when forward capacity is absent.

No GUI preflight control-flow change should be necessary.

---

## 13. Test Updates

### 13.1 Required-key helper test

Update / add tests in:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Cases:

```text
empty env:
    missing keys include both backward and forward

env with only backward:
    missing keys include forward only

env with backward and forward:
    missing keys == []
```

Example:

```python
env = SimpleNamespace(
    explicit_pipeline_backward_weekly_capability={"MILL_EAST": {"PACKAGED_RICE_STANDARD": {"2027-W40": 5}}},
)
assert get_missing_explicit_pipeline_demo_ctx_keys(env) == [
    "explicit_pipeline_forward_weekly_capacity"
]
```

### 13.2 GUI preflight with backward-only context

Update / add test in:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Simulate:

```text
Explicit KPI ON
attach helper supplies only backward capability
forward capacity absent
```

Expected:

```text
ctx guard skipped is True
missing ctx keys include explicit_pipeline_forward_weekly_capacity
explicit flags are forced OFF
Run Full Plan preflight remains safe
```

### 13.3 GUI preflight with both contexts

Update existing attach-pass test to attach both:

```python
self.env.explicit_pipeline_backward_weekly_capability = {
    "MILL_EAST": {"PACKAGED_RICE_STANDARD": {"2027-W40": 5}}
}
self.env.explicit_pipeline_forward_weekly_capacity = {
    "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}}
}
```

Expected:

```text
ctx guard skipped is False
missing ctx keys == []
explicit flags remain enabled
export flags remain False
```

The exact forward shape is only for guard presence and does not need to be pipeline-compatible in this test.

The guard only checks attribute presence / non-None.

---

## 14. Optional View Tests

Existing view-model diagnostics should already display any missing key in:

```text
explicit_kpi_demo_flag_missing_ctx_keys
```

If the tests already assert the previous missing key text, update them to allow or expect the new forward key.

No new renderer behavior should be required.

---

## 15. Test Commands

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Run related tests:

```bat
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
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

---

## 16. Manual GUI Validation

After implementation, run:

```bat
python -m main
```

Manual flow:

```text
1. Check Explicit KPI ON
2. Run Full Plan
3. Confirm Run Full Plan does not crash
4. Open Explicit KPI View
5. Confirm missing context diagnostic shows:
       explicit_pipeline_forward_weekly_capacity
```

Expected result:

```text
Run Full Plan completes.
Explicit KPI View reports missing explicit_pipeline_forward_weekly_capacity.
```

This is the desired safe intermediate state.

The goal is not yet full KPI population.

---

## 17. Completion Criteria

This patch is complete when:

```text
[OK] get_missing_explicit_pipeline_demo_ctx_keys checks both backward and forward keys
[OK] backward-only context no longer lets explicit pipeline run
[OK] missing forward key is shown as diagnostic
[OK] Run Full Plan no longer crashes from missing explicit_pipeline_forward_weekly_capacity
[OK] explicit flags are forced OFF when forward capacity is missing
[OK] both-context test allows guard pass
[OK] tests pass
```

---

## 18. Follow-Up Phase

After this guard patch, the next phase should define the forward capacity context itself.

Candidate design documents:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
```

Key questions for the next phase:

```text
1. What is the canonical forward capacity shape?
2. Does the explicit bridge capacity pipeline expect product-first or node-first structure?
3. Should forward capacity come from existing capacity master rows?
4. How should capacity_type P/S/I be represented?
5. How should Japanese Rice Case and iPhone GUI demo be separated?
```

---

## 19. Summary

Phase 2C successfully exposed the next required context key:

```text
explicit_pipeline_forward_weekly_capacity
```

The immediate fix is not to implement forward capacity yet.

The immediate fix is to extend the ctx guard so that this key is detected before the explicit bridge capacity pipeline is called.

This restores the GUI safety principle:

```text
missing optional explicit-pipeline context should produce diagnostics,
not crash Run Full Plan.
```
