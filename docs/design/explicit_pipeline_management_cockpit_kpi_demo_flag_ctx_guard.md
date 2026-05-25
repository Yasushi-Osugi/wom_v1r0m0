# Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-25  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_ctx_guard.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the design for **Explicit Pipeline Management Cockpit KPI Demo Flag Context Guard**.

Phase 2 GUI wiring added the `Explicit KPI ON` checkbox and connected it to the full plan preflight path.

The checkbox successfully applies:

```python
apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

before `Run Full Plan`.

However, manual GUI validation found that when `Explicit KPI ON` is checked and `Run Full Plan` is executed, the application can stop with:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key: explicit_pipeline_backward_weekly_capability
```

This means:

```text
The GUI switch works.
The explicit pipeline is reached.
But the pipeline-required context is incomplete.
```

The immediate goal of this design is:

```text
Explicit KPI ON should not crash Run Full Plan when required explicit pipeline ctx is missing.
```

This design does **not** generate `explicit_pipeline_backward_weekly_capability`.

It only adds a guard so the application remains stable.

---

## 2. Background

The current staged implementation is:

```text
Explicit KPI View UI MVP                         completed
    ↓
Summary KPI Cards                                completed
    ↓
Graphs tab with Tk Canvas charts                 completed
    ↓
Demo flag preset helper Phase 1                  completed
    ↓
Explicit KPI ON GUI wiring Phase 2               implemented
    ↓
Manual GUI validation                            missing ctx key found
```

The new checkbox appears in the WOM GUI and the preflight hook is called before the planning sequence.

Current intended user path:

```text
python -m main
    ↓
check Explicit KPI ON
    ↓
Run Full Plan
    ↓
Explicit KPI View
```

Current observed issue:

```text
Run Full Plan stops with missing ctx key:
explicit_pipeline_backward_weekly_capability
```

---

## 3. Confirmed Error

Manual GUI validation produced the following error path:

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

The relevant observed message is:

```text
explicit bridge capacity pipeline enabled but missing ctx key: explicit_pipeline_backward_weekly_capability
```

This proves that:

```text
[OK] Explicit KPI ON checkbox is visible
[OK] preflight flag helper is applied
[OK] explicit pipeline flag becomes True
[OK] explicit bridge capacity pipeline is invoked
[NG] required ctx key is missing
```

The failure is not a GUI rendering failure.

The failure is a precondition failure inside the explicit bridge capacity pipeline.

---

## 4. Current Relevant Code Locations

The search results identified these important locations:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
    required ctx key:
    explicit_pipeline_backward_weekly_capability

pysi/gui/cockpit_tk.py
    passes:
    backward_weekly_capability=getattr(self.env, "explicit_pipeline_backward_weekly_capability", None)
```

This means the GUI currently attempts to provide the capability context from:

```python
self.env.explicit_pipeline_backward_weekly_capability
```

but the attribute is not present or is `None` in the normal GUI path.

---

## 5. Problem Statement

The Phase 2 GUI wiring can enable explicit pipeline reporting flags, but the explicit bridge capacity pipeline has required context keys.

If those keys are missing, the pipeline raises a `ValueError`, which currently stops `Run Full Plan`.

This is undesirable for GUI demo operation.

The correct behavior should be:

```text
If Explicit KPI ON is checked but required ctx is missing:
    do not crash
    skip explicit pipeline execution safely
    record missing ctx information
    allow Run Full Plan to continue
    keep Explicit KPI View unavailable with a diagnostic reason
```

The first priority is application stability.

---

## 6. Design Goal

Add a **required context guard** so that enabling `Explicit KPI ON` cannot crash `Run Full Plan`.

The guard should detect missing context before the explicit bridge capacity pipeline is invoked.

If required context is missing, the guard should:

```text
1. record the missing keys on env
2. disable the dependent explicit pipeline flags for this run
3. allow the normal planning sequence to continue
4. leave Explicit KPI View in unavailable state
5. make the reason inspectable
```

The guard does not create capability data.

It only prevents unsafe pipeline execution.

---

## 7. Non-Goals

This design does not implement:

```text
generation of explicit_pipeline_backward_weekly_capability
weekly capacity master loading
MOM capacity master design
Price-Cost-Profit propagation
Cost / KPI context generation
automatic fallback capability values
automatic report export
ReplanCommand execution
Knowledge Continuity persistence
waterfall chart
heatmap
drilldown
large GUI redesign
```

This design only handles:

```text
safe skipping when required explicit pipeline ctx is missing
```

---

## 8. Core Safety Rule

The safety rule for this phase is:

```text
If the engine lacks required fuel, do not start the engine.
Do not crash the cockpit.
```

More concretely:

```text
Explicit KPI ON can prepare the flags.
But required ctx guard must prevent unsafe pipeline execution.
```

The application should remain usable even if the explicit pipeline cannot run.

---

## 9. Important Distinction: Unavailable vs Empty

The cockpit must distinguish:

```text
Unavailable:
    explicit pipeline did not run because required ctx was missing

Empty:
    explicit pipeline ran successfully, but no issues were found
```

The current error is an **Unavailable** case.

The expected guarded behavior is:

```text
Run Full Plan completes.
Explicit KPI View remains unavailable.
Message explains missing ctx key.
```

This is better than raising an exception and stopping the run.

---

## 10. Required Context Keys

The currently observed missing key is:

```text
explicit_pipeline_backward_weekly_capability
```

The explicit bridge capacity pipeline may require additional keys.

The guard should avoid hardcoding only one key if the existing pipeline has a required-key list.

Recommended approach:

```text
Reuse the same required ctx key list semantics used by explicit_bridge_capacity_pipeline.py.
```

If the required list is not currently exposed, introduce a small helper or constant in that module.

Example:

```python
EXPLICIT_BRIDGE_CAPACITY_REQUIRED_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
)
```

Then both the pipeline and guard can use the same list.

If exposing the list is too much for the first patch, define a conservative private check in GUI/helper code, but avoid duplication if practical.

---

## 11. Recommended Location of Guard

There are three candidate locations.

### 11.1 Option A: Guard in GUI preflight helper

Enhance:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

so that after applying flags, it checks required env attributes.

If missing keys exist:

```python
self.env.explicit_kpi_demo_flag_missing_ctx_keys = [...]
self.env.enable_explicit_bridge_capacity_pipeline = False
self.env.enable_explicit_bridge_capacity_report = False
self.env.enable_explicit_bridge_capacity_issue_candidates = False
self.env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi = False
```

Then `Run Full Plan` continues.

Advantages:

```text
small patch
close to GUI checkbox behavior
easy to test
prevents pipeline invocation
```

Disadvantages:

```text
guard logic is GUI-specific
may duplicate required ctx list
```

---

### 11.2 Option B: Guard in reporting/helper module

Add a new pure helper, for example:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) -> list[str]
```

or:

```python
guard_explicit_pipeline_kpi_demo_flags_for_missing_ctx(env) -> list[str]
```

Advantages:

```text
centralized with demo flag helper
easy to reuse outside GUI
better separation from Tk
```

Disadvantages:

```text
slightly broader Phase 1 helper change
requires updating tests
```

---

### 11.3 Option C: Guard inside pipeline from-env adapter

Modify:

```python
maybe_run_explicit_bridge_capacity_pipeline_from_env(...)
```

so that missing required ctx returns `None` instead of raising.

Advantages:

```text
protects all callers
guard lives closest to pipeline adapter
```

Disadvantages:

```text
changes existing strict behavior
may weaken tests that expect ValueError
could hide configuration mistakes in non-GUI contexts
```

---

## 12. Recommended Approach

Recommended MVP approach:

```text
Option B + minimal GUI integration
```

Add a pure validation helper near the demo flag helper, then call it from GUI preflight.

Recommended helper module remains:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Recommended new function:

```python
def get_missing_explicit_pipeline_demo_ctx_keys(env: Any) -> list[str]:
    ...
```

Recommended behavior:

```text
return list of required env attribute names that are missing or None
```

Then in:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

after applying flags:

```python
missing = get_missing_explicit_pipeline_demo_ctx_keys(self.env)
if missing:
    self.env.explicit_kpi_demo_flag_missing_ctx_keys = missing
    self.env.explicit_kpi_demo_flag_ctx_guard_skipped = True
    self.env.explicit_kpi_demo_flag_guard_message = (
        "Explicit KPI demo pipeline skipped because required ctx keys are missing: "
        + ", ".join(missing)
    )

    self.env.enable_explicit_bridge_capacity_pipeline = False
    self.env.enable_explicit_bridge_capacity_report = False
    self.env.enable_explicit_bridge_capacity_issue_candidates = False
    self.env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi = False
    self.env.enable_explicit_bridge_capacity_report_export = False
    self.env.enable_explicit_bridge_capacity_issue_candidate_export = False
    self.env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export = False

    return applied
```

This keeps the pipeline from being called with missing ctx.

---

## 13. Required Context Check Semantics

A key should be considered missing if:

```python
not hasattr(env, key)
```

or:

```python
getattr(env, key) is None
```

A value such as:

```python
{}
[]
0
False
```

should not automatically be treated as missing unless the pipeline explicitly requires a non-empty structure.

For the first guard, use only:

```text
missing attribute or None
```

This avoids over-validating unknown future valid values.

---

## 14. Flags to Disable When Missing Context

If required ctx is missing, disable at least:

```text
enable_explicit_bridge_capacity_pipeline
```

To avoid downstream reporting flags expecting pipeline artifacts, recommended to also disable:

```text
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
```

Export flags should already be False in GUI usage, but can be set False defensively:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

Recommended result:

```text
all explicit KPI demo pipeline/report flags are turned off for the current run
when required ctx is missing.
```

This makes the run stable.

---

## 15. Env Diagnostics

When guard skips explicit pipeline execution, store diagnostic fields on `env`.

Recommended fields:

```text
explicit_kpi_demo_flag_ctx_guard_skipped = True
explicit_kpi_demo_flag_missing_ctx_keys = ["explicit_pipeline_backward_weekly_capability"]
explicit_kpi_demo_flag_guard_message = "Explicit KPI demo pipeline skipped because required ctx keys are missing: explicit_pipeline_backward_weekly_capability"
```

These fields can later be surfaced in the Explicit KPI View message tab.

For this phase, it is acceptable simply to store them.

---

## 16. Optional User-Facing Message

Current Explicit KPI View unavailable message is:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

A later improvement can change this to:

```text
No explicit pipeline reporting data is available.
Explicit KPI ON was enabled, but required context was missing:
explicit_pipeline_backward_weekly_capability
```

For this patch, message improvement is optional.

Do not over-expand scope.

---

## 17. Tests to Add / Update

Add or update focused tests.

Recommended test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

and/or:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Suggested tests:

### 17.1 Missing ctx detection helper

Given:

```python
env = SimpleNamespace()
```

Expect:

```text
get_missing_explicit_pipeline_demo_ctx_keys(env)
contains explicit_pipeline_backward_weekly_capability
```

### 17.2 Present ctx passes guard

Given:

```python
env = SimpleNamespace(
    explicit_pipeline_backward_weekly_capability={"MOM": {"W01": 100}}
)
```

Expect:

```text
missing keys == []
```

### 17.3 GUI checkbox ON but missing ctx does not leave pipeline enabled

Given fake self:

```python
fake = SimpleNamespace(
    env=SimpleNamespace(),
    var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
)
```

Call:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
```

Expect:

```text
env.explicit_kpi_demo_flag_ctx_guard_skipped is True
env.explicit_kpi_demo_flag_missing_ctx_keys includes explicit_pipeline_backward_weekly_capability
env.enable_explicit_bridge_capacity_pipeline is False
```

### 17.4 GUI checkbox ON with ctx keeps pipeline enabled

Given fake self with env containing:

```text
explicit_pipeline_backward_weekly_capability
```

Expect:

```text
env.enable_explicit_bridge_capacity_pipeline is True
env.explicit_kpi_demo_flag_ctx_guard_skipped is absent or False
```

### 17.5 Run Full Plan does not raise from missing ctx

If feasible with existing fake run_full_plan test:

```text
checkbox ON + missing ctx
run_full_plan(fake)
does not call explicit pipeline with missing ctx
does not raise ValueError
```

This may be approximated by verifying preflight behavior.

---

## 18. Test Commands

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Then related tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

Optional GUI / scenario smoke:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

Manual GUI validation remains important:

```text
Explicit KPI ON checked
Run Full Plan
application should not crash
Explicit KPI View should remain unavailable or show diagnostic reason
```

---

## 19. Completion Criteria

This guard phase is complete when:

```text
[OK] Explicit KPI ON with missing required ctx does not crash Run Full Plan
[OK] missing ctx keys are recorded on env
[OK] explicit pipeline flag is disabled/skipped for current run
[OK] normal planning continues
[OK] checkbox OFF behavior remains unchanged
[OK] checkbox ON with valid ctx still enables explicit pipeline flags
[OK] no automatic ctx generation is added
[OK] no export execution is added
[OK] no ReplanCommand execution is added
[OK] focused tests pass
```

---

## 20. Manual Validation Target

After implementation, the immediate manual validation should be:

```text
1. python -m main
2. check Explicit KPI ON
3. click Run Full Plan
4. confirm application does not show missing ctx key error
5. open Explicit KPI View
6. confirm view does not crash
7. confirm unavailable state is expected until capability ctx is supplied
```

The target is not yet:

```text
fully populated KPI cards
```

The target is:

```text
safe behavior when required ctx is missing
```

---

## 21. Later Work: Capability Context Generation

After the guard, a separate design should define how to generate or load:

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

This is separate from the guard.

---

## 22. Later Work: Price-Cost-Profit Integration

The user's conceptual Price-Cost-Profit model includes:

```text
A. market-accepted price propagated upstream through the E2E tree
B. material-accepted cost propagated downstream through the E2E tree
C. comparison of A and B to allocate price, profit, and cost portions
```

This is an important future topic, but not part of the current guard.

Recommended later memo:

```text
docs/design/price_cost_profit_e2e_propagation_inventory.md
```

---

## 23. Summary

The `Explicit KPI ON` checkbox has confirmed that GUI wiring works.

The next problem is not the checkbox itself.

The problem is:

```text
explicit bridge capacity pipeline required ctx is missing.
```

The immediate fix is to add a context guard so that:

```text
Explicit KPI ON + missing ctx
```

does not crash `Run Full Plan`.

The cockpit should remain stable.

The explicit pipeline should be skipped safely until required context is supplied.

This is the next guardrail before deeper capability and Price-Cost-Profit integration work.
