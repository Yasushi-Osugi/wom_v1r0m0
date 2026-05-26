# Explicit Pipeline Backward Weekly Capability GUI Preflight Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-26  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of **Explicit Pipeline Backward Weekly Capability GUI Preflight Phase 2B**.

The purpose of Phase 2B was to wire the already implemented optional CSV attach helper into the Explicit KPI GUI preflight path.

The helper is:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

The target behavior was:

```text
Explicit KPI ON checked
    ↓
Run Full Plan
    ↓
apply demo flags
    ↓
attempt optional capability CSV attach
    ↓
ctx guard checks required context
```

This phase connects the runtime capability CSV loading path to the existing Explicit KPI ON preflight.

---

## 2. Background

Before this phase, the following pieces already existed:

```text
Explicit KPI ON checkbox
demo flag helper
required ctx guard
ctx guard diagnostics view
capability context adapter
CSV loader
env attach helper
optional CSV attach helper
```

The remaining gap was:

```text
The GUI preflight did not yet call the optional capability CSV attach helper.
```

Therefore, even if:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

existed, the GUI path would not automatically use it before the ctx guard checked for:

```text
explicit_pipeline_backward_weekly_capability
```

Phase 2B closed this gap.

---

## 3. Implemented Commit

The implementation was committed as:

```text
291a28a Wire explicit capability CSV attach into KPI preflight
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

The implementation changed two files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

No sample CSV file was added.

No planning engine file was changed.

No reporting stack file was changed.

No monetary KPI file was changed.

---

## 5. Private GUI Helper Added

A new private helper was added to `WOMCockpit`:

```python
WOMCockpit._maybe_attach_explicit_pipeline_backward_weekly_capability()
```

Its role is to delegate to the existing plan-layer helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(self.env)
```

This avoids reimplementing the attach logic in the GUI.

The GUI now uses the plan-layer capability context helper as the single source of behavior.

---

## 6. Preflight Order Implemented

The preflight order is now:

```text
1. check Explicit KPI ON checkbox
2. apply explicit KPI demo flags
3. attempt optional capability CSV attach
4. run required ctx guard check
5. if ctx is missing, disable explicit flags and record guard diagnostics
6. if ctx is present, keep explicit flags enabled and clear guard diagnostics
```

The critical insertion point is:

```text
after apply_explicit_pipeline_kpi_demo_flags(...)
before get_missing_explicit_pipeline_demo_ctx_keys(...)
```

This order is important because the optional CSV attach must happen before the ctx guard decides whether the explicit pipeline can remain enabled.

---

## 7. Explicit KPI OFF Behavior

When `Explicit KPI ON` is unchecked:

```text
no demo flags are applied
no capability attach attempt is made
ctx guard behavior is not changed
_maybe_apply_explicit_kpi_demo_flags() returns None
```

This preserves existing default safety.

The checkbox remains OFF by default.

---

## 8. Explicit KPI ON + Missing CSV Behavior

When `Explicit KPI ON` is checked but the default CSV does not exist:

```text
demo flags are applied
optional attach helper is called
helper returns file_missing
env.explicit_pipeline_backward_weekly_capability is not attached
ctx guard still detects missing context
explicit pipeline/report/issue/cost-kpi flags are forced OFF
ctx guard diagnostics remain visible
```

This preserves the current safe diagnostic behavior.

The GUI still explains that:

```text
explicit_pipeline_backward_weekly_capability
```

is missing.

---

## 9. Explicit KPI ON + Empty / Invalid CSV Behavior

When the default CSV exists but produces no valid context:

```text
demo flags are applied
optional attach helper is called
helper returns empty_context
env.explicit_pipeline_backward_weekly_capability is not attached
ctx guard still detects missing context
explicit flags are forced OFF
ctx guard diagnostics remain visible
```

This prevents an empty capability context from being treated as valid planning fuel.

---

## 10. Explicit KPI ON + Valid CSV Behavior

When the default CSV exists and produces a non-empty valid context:

```text
demo flags are applied
optional attach helper is called
env.explicit_pipeline_backward_weekly_capability is attached
ctx guard no longer reports that key as missing
explicit pipeline/report/issue/cost-kpi flags remain enabled
export flags remain OFF
```

This is the intended runtime bridge from:

```text
capability CSV master
```

to:

```text
Explicit KPI ON preflight
```

---

## 11. Export Flag Behavior

Export flags remain disabled.

This phase does not enable exports.

Expected export flags remain:

```text
enable_explicit_bridge_capacity_report_export = False
enable_explicit_bridge_capacity_issue_candidate_export = False
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export = False
```

This preserves the existing safety boundary.

---

## 12. Tests Updated

The following test file was updated:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

The GUI wiring test count increased to:

```text
6 tests
```

New / updated coverage includes:

```text
Explicit KPI OFF does not attempt attach
Explicit KPI ON + simulated missing-file attach still triggers ctx guard skip
Explicit KPI ON + attach-populated context lets ctx guard pass
explicit runtime flags remain enabled when required ctx is attached
export flags remain false
existing run_full_plan preflight ordering behavior remains intact
```

The tests use a monkeypatched / fake attach path rather than relying on a real file in `data/`.

This keeps the test deterministic.

---

## 13. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

Observed results:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                  6 passed
tests/test_explicit_pipeline_capacity_context.py                         16 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                            6 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py              10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py         9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py  4 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                 7 passed
tests/test_explicit_pipeline_reporting_flags.py                          10 passed
tests/test_covid_vaccine_with_capacity_push.py                            1 passed
```

Total observed result:

```text
69 passed
```

No skipped tests were observed in this run.

---

## 14. Scope Boundaries Preserved

This phase intentionally did not implement:

```text
sample capability CSV
manual GUI validation with sample CSV
scenario selector
planning engine changes
planning execution changes
export execution
ReplanCommand execution
automatic replanning
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
process-level capacity
resource-level capacity
GUI layout redesign
new checkbox
new dependency
```

The implementation remained a small GUI preflight wiring patch.

---

## 15. Current State After Phase 2B

Current state:

```text
Explicit KPI ON checkbox exists
demo flag helper exists
required ctx guard exists
ctx guard diagnostics view exists
capability context adapter exists
optional CSV attach helper exists
GUI preflight now calls optional CSV attach helper
tests pass
```

Therefore:

```text
If a valid default capability CSV exists,
Run Full Plan preflight can attach capability context before ctx guard runs.
```

If no valid default CSV exists:

```text
the current missing-context diagnostic behavior remains unchanged.
```

---

## 16. Meaning of This Milestone

Before this phase:

```text
The fuel container and hose existed,
but the GUI preflight did not connect the hose before Run Full Plan.
```

After this phase:

```text
Explicit KPI ON preflight connects the hose and tries to load fuel from the default CSV.
```

In WOM terms:

```text
data/explicit_pipeline_backward_weekly_capability.csv
    ↓
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
    ↓
env.explicit_pipeline_backward_weekly_capability
    ↓
ctx guard
    ↓
explicit bridge capacity pipeline
```

This is the first runtime bridge from capability CSV to the Explicit KPI cockpit path.

---

## 17. Expected Runtime Behavior Without Sample CSV

Because no sample CSV was added in this phase, the current GUI may still show:

```text
explicit_pipeline_backward_weekly_capability
```

as missing.

This is expected.

The difference is that the GUI preflight now attempts to load the default CSV before showing the missing diagnostic.

If the file is absent, the system safely falls back to the existing diagnostic path.

---

## 18. Recommended Next Step

The next phase should define a scenario-specific sample CSV.

Recommended next design memo:

```text
docs/design/explicit_pipeline_backward_weekly_capability_sample_csv.md
```

This should define:

```text
actual node ids
actual product names
actual week bucket format
capability lot counts
where to place the sample CSV
how to validate the sample manually
expected Explicit KPI View behavior
```

Candidate file:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

However, before committing this file, confirm that its contents match the actual running scenario.

---

## 19. Manual GUI Validation Target for Next Phase

With a valid sample CSV:

```text
1. python -m main
2. check Explicit KPI ON
3. Run Full Plan
4. open Explicit KPI View
5. confirm missing diagnostic for explicit_pipeline_backward_weekly_capability disappears
```

If the explicit pipeline still does not produce full reporting data, inspect:

```text
node id mismatch
product mismatch
week bucket mismatch
additional ctx requirements
pipeline shape expectations
```

---

## 20. Summary

Explicit Pipeline Backward Weekly Capability GUI Preflight Phase 2B is complete.

Implemented:

```text
private GUI attach helper
preflight optional CSV attach call
tests for OFF / missing / attached behavior
```

The resulting preflight order is:

```text
Explicit KPI ON
    ↓
apply demo flags
    ↓
optional capability CSV attach
    ↓
ctx guard check
```

This preserves current safety while allowing future capability CSV files to supply:

```text
env.explicit_pipeline_backward_weekly_capability
```

before the explicit bridge capacity pipeline is enabled.
