# Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-25  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_ctx_guard_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of the **Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard** implementation.

The purpose of this milestone was not to make the Explicit KPI View fully populated.

The purpose was narrower and safety-focused:

```text
Explicit KPI ON + missing required ctx
    ↓
Run Full Plan should not crash
```

The guard was introduced after manual GUI validation found that enabling `Explicit KPI ON` caused `Run Full Plan` to stop with:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key: explicit_pipeline_backward_weekly_capability
```

The context guard now prevents this crash by detecting missing required context before the strict explicit bridge capacity pipeline is invoked.

---

## 2. Background

The staged cockpit implementation before this guard was:

```text
Explicit KPI View UI MVP                         completed
    ↓
Summary KPI Cards                                completed
    ↓
Graphs tab with Tk Canvas charts                 completed
    ↓
Demo flag preset helper Phase 1                  completed
    ↓
Explicit KPI ON GUI wiring Phase 2               completed
    ↓
Manual GUI validation                            missing ctx key error found
```

The `Explicit KPI ON` checkbox was confirmed to work.

However, when checked, it enabled the explicit bridge capacity pipeline without the required context:

```text
explicit_pipeline_backward_weekly_capability
```

As a result, the strict pipeline path raised a `ValueError`.

This milestone adds a guard so that missing required context does not crash the cockpit.

---

## 3. Implemented Commit

The context guard implementation was committed as:

```text
c8fc017 Guard Explicit KPI demo flags when required pipeline ctx is missing
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
pysi/reporting/__init__.py
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

No capability generation logic was added.

No export execution logic was added.

No replanning logic was added.

---

## 5. New Required Context Detection Helper

A new pure helper was added:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

Implemented in:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

It checks for required explicit pipeline demo context keys.

The current required key is:

```text
explicit_pipeline_backward_weekly_capability
```

A key is considered missing when:

```text
the env attribute does not exist
```

or:

```text
the env attribute value is None
```

The helper intentionally does not treat these as missing:

```python
{}
[]
0
False
```

This avoids over-validating future valid structures.

---

## 6. Package Export

The new helper was exported from:

```text
pysi/reporting/__init__.py
```

The package now supports:

```python
from pysi.reporting import get_missing_explicit_pipeline_demo_ctx_keys
```

alongside the existing:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags
```

---

## 7. GUI Preflight Guard Behavior

The existing method:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

was enhanced.

The new behavior is:

```text
if checkbox variable is missing:
    return None

if Explicit KPI ON is unchecked:
    return None

if Explicit KPI ON is checked:
    apply demo flags
    check required ctx keys
```

When required ctx is missing, the method:

```text
records diagnostics on env
disables explicit pipeline/report/issue/cost-kpi flags
disables explicit export flags defensively
returns the original applied flag map
```

When required ctx is present, the method:

```text
sets guard skipped = False
sets missing keys = []
clears guard message
keeps explicit flags enabled
returns the applied flag map
```

---

## 8. Env Diagnostics Added

When the guard skips explicit pipeline execution due to missing ctx, the following diagnostics are recorded on `env`:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = True
explicit_kpi_demo_flag_missing_ctx_keys = ["explicit_pipeline_backward_weekly_capability"]
explicit_kpi_demo_flag_guard_message = "Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_backward_weekly_capability"
```

These diagnostics are not yet surfaced in the Explicit KPI View UI.

They are available for the next improvement phase.

---

## 9. Flags Disabled When Context Is Missing

When required ctx is missing, the guard forces these flags to `False`:

```text
enable_explicit_bridge_capacity_pipeline
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

This prevents the strict explicit bridge capacity pipeline from running with incomplete ctx.

It also prevents downstream report / issue / Cost-KPI steps from expecting missing pipeline artifacts.

---

## 10. Behavior When Required Context Is Present

When `env` contains:

```text
explicit_pipeline_backward_weekly_capability
```

and it is not `None`, the guard does not disable the explicit flags.

Expected behavior:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = False
explicit_kpi_demo_flag_missing_ctx_keys = []
explicit_kpi_demo_flag_guard_message = ""
enable_explicit_bridge_capacity_pipeline = True
enable_explicit_bridge_capacity_report = True
enable_explicit_bridge_capacity_issue_candidates = True
enable_explicit_bridge_capacity_issue_candidate_cost_kpi = True
```

This preserves the future path toward a fully populated Explicit KPI View once the required capability context is supplied.

---

## 11. Tests Updated

The following test files were updated:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

The tests now cover:

```text
missing ctx detection
present ctx pass behavior
checkbox OFF behavior
checkbox ON + missing ctx guard behavior
checkbox ON + ctx present behavior
Run Full Plan preflight ordering
```

---

## 12. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

Observed results:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py                  6 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py        5 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py        7 passed
tests/test_explicit_pipeline_reporting_flags.py                 10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py      8 passed
tests/test_explicit_pipeline_management_cockpit_kpi_cards.py     3 passed
```

Total observed result:

```text
39 passed
```

---

## 13. Manual GUI Validation

Manual GUI validation was performed after the guard implementation.

Validation path:

```text
1. python -m main
2. Explicit KPI ON checkbox displayed
3. Explicit KPI ON checked
4. Run Full Plan clicked
5. Run Full Plan completed
6. no missing ctx key error appeared
7. Explicit KPI View opened
8. cockpit content remained unavailable / empty
```

The important result is:

```text
Run Full Plan no longer crashes when Explicit KPI ON is checked and required ctx is missing.
```

The Explicit KPI View still shows unavailable / empty content because the guard correctly disables the explicit pipeline when required ctx is missing.

This is expected for this milestone.

---

## 14. Completion Criteria

This guard milestone satisfies the intended completion criteria.

```text
[OK] missing explicit_pipeline_backward_weekly_capability is detected
[OK] missing ctx keys are recorded on env
[OK] guard message is recorded on env
[OK] explicit pipeline flag is disabled when ctx is missing
[OK] report / issue / cost-kpi flags are disabled when ctx is missing
[OK] export flags are disabled defensively
[OK] checkbox OFF behavior remains unchanged
[OK] checkbox ON with valid ctx keeps flags enabled
[OK] no automatic capability ctx generation is added
[OK] no export execution is added
[OK] no ReplanCommand execution is added
[OK] focused tests pass
[OK] manual GUI validation confirms Run Full Plan does not crash
```

---

## 15. Meaning of This Milestone

Before this guard:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
missing ctx key error
    ↓
Run Full Plan stops
```

After this guard:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
required ctx guard
    ↓
explicit pipeline safely skipped
    ↓
Run Full Plan completed
    ↓
Explicit KPI View remains unavailable
```

This is a meaningful improvement.

The cockpit is now stable under missing required ctx conditions.

---

## 16. Current State

The current state is:

```text
GUI control exists
preflight flag helper exists
context guard exists
Run Full Plan does not crash on missing ctx
Explicit KPI View still lacks reporting data because required capability ctx is not supplied
```

This is the expected state after the guard.

The guardrail is now installed.

The fuel supply is still missing.

---

## 17. Known Limitation

The guard does not create:

```text
explicit_pipeline_backward_weekly_capability
```

Therefore, the Explicit KPI View can remain unavailable even when `Explicit KPI ON` is checked.

This is intentional.

The capability context generation / loading path belongs to a later design phase.

---

## 18. Recommended Next Step

The next small improvement should be:

```text
surface ctx guard diagnostics in Explicit KPI View
```

Recommended design memo:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_ctx_guard_diagnostics_view.md
```

Goal:

```text
when Explicit KPI View is unavailable because ctx guard skipped the pipeline,
show the missing ctx key and guard message to the user
```

Expected user-facing message:

```text
Explicit KPI ON was enabled, but the explicit pipeline was skipped because required context is missing:
explicit_pipeline_backward_weekly_capability
```

This will make the current unavailable state understandable.

---

## 19. Later Work: Capability Context Generation

After diagnostics are visible, a separate design should define how to generate or load:

```text
explicit_pipeline_backward_weekly_capability
```

Potential source concepts:

```text
Weekly Capability on MOM nodes
node-product-week capacity master
capacity calendar
resource / process capability table
scenario-specific capacity assumptions
```

This is not part of the guard.

---

## 20. Later Work: Price-Cost-Profit Propagation

The user's conceptual Price-Cost-Profit model remains an important later topic:

```text
A. market-accepted price propagated upstream through the E2E tree
B. material-accepted cost propagated downstream through the E2E tree
C. comparison of A and B to allocate price, profit, and cost portions
```

Recommended later inventory memo:

```text
docs/design/price_cost_profit_e2e_propagation_inventory.md
```

This should be handled after the cockpit safety path is stable.

---

## 21. Summary

The Explicit KPI demo flag context guard is complete.

The milestone achieved:

```text
Explicit KPI ON no longer crashes Run Full Plan when required explicit pipeline ctx is missing.
```

The expected current behavior is:

```text
Run Full Plan completes.
Explicit KPI View opens.
KPI data remains unavailable until explicit_pipeline_backward_weekly_capability is supplied.
```

This is the correct safety-first result.

The next step is to expose the guard diagnostics in the Explicit KPI View so the user can see why the cockpit remains unavailable.
