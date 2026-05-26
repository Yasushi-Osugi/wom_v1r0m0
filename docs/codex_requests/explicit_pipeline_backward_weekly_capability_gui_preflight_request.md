# Codex Request: Wire Explicit Pipeline Backward Weekly Capability CSV Attach into GUI Preflight Phase 2B

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design and completion memos have already been added:

```text
docs/design/plan_with_capacity_context_and_planning_story.md
docs/design/explicit_pipeline_backward_weekly_capability_context.md
docs/design/explicit_pipeline_backward_weekly_capability_context_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md
```

Please read especially:

```text
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md
```

Phase 1 implemented the pure capability context adapter:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

with:

```python
build_explicit_pipeline_backward_weekly_capability(...)
load_explicit_pipeline_backward_weekly_capability_csv(...)
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

Phase 2A implemented the optional CSV attach helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

This request implements **Phase 2B**:

```text
call the optional CSV attach helper from Explicit KPI ON GUI preflight
before the ctx guard checks required context keys.
```

---

## 2. Main Objective

Wire the existing helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

into the existing Explicit KPI ON preflight path.

Target flow:

```text
Explicit KPI ON checked
    ↓
Run Full Plan
    ↓
_maybe_apply_explicit_kpi_demo_flags()
    ↓
apply demo flags
    ↓
optionally attach capability context from default CSV
    ↓
ctx guard checks missing required keys
```

The purpose is to allow this behavior:

```text
If data/explicit_pipeline_backward_weekly_capability.csv exists and yields non-empty valid context:
    env.explicit_pipeline_backward_weekly_capability is attached
    ctx guard can pass for this key

If CSV is missing or invalid/empty:
    existing ctx guard diagnostic behavior remains unchanged
```

---

## 3. Scope of This Request

Implement Phase 2B only:

```text
1. add a small private GUI helper method
2. call that helper from _maybe_apply_explicit_kpi_demo_flags()
3. add / update focused GUI wiring tests
```

This request should not create a sample CSV.

This request should not perform manual GUI validation.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Do not change the Explicit KPI ON checkbox default. It must remain OFF by default.
2. Do not bypass or remove ctx guard.
3. Do not generate dummy capability values.
4. Do not create data/explicit_pipeline_backward_weekly_capability.csv in this request.
5. Do not change planning algorithms.
6. Do not run planning from the attach helper.
7. Do not run exports.
8. Do not execute ReplanCommand.
9. Do not implement automatic replanning.
10. Do not implement OR optimization.
11. Do not implement Price-Cost-Profit propagation.
12. Do not implement PSI monetary KPI evaluation.
13. Do not implement tariff simulation.
14. Do not implement cold-chain shelf-life logic.
15. Do not implement process-level capacity.
16. Do not add new dependencies.
17. Do not make a large GUI redesign.
```

This request is only for:

```text
Explicit KPI ON preflight → optional capability CSV attach helper → ctx guard
```

---

## 5. Files to Modify

Expected files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Avoid modifying unless unavoidable:

```text
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

The helper already exists in:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Do not reimplement it elsewhere.

---

## 6. Existing Preflight Method

The existing method is:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

It currently handles:

```text
checkbox missing
checkbox OFF
demo flag application
required ctx guard check
ctx guard skip diagnostics
explicit flag disabling when ctx is missing
ctx guard pass behavior
```

This behavior should be preserved.

---

## 7. Recommended Implementation Pattern

Add a small private helper method to `WOMCockpit`:

```python
def _maybe_attach_explicit_pipeline_backward_weekly_capability(self) -> dict[str, Any] | None:
    from pysi.plan.explicit_pipeline_capacity_context import (
        maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
    )

    return maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(self.env)
```

Then update `_maybe_apply_explicit_kpi_demo_flags()` so that after demo flags are applied and before ctx guard missing-key detection, it calls:

```python
self._maybe_attach_explicit_pipeline_backward_weekly_capability()
```

Recommended order:

```python
applied = apply_explicit_pipeline_kpi_demo_flags(
    self.env,
    include_exports=False,
)

self._maybe_attach_explicit_pipeline_backward_weekly_capability()

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(self.env)
```

This keeps the new behavior small and testable.

---

## 8. Required Ordering

The ordering matters.

Correct order:

```text
1. Explicit KPI ON check
2. apply_explicit_pipeline_kpi_demo_flags(...)
3. maybe attach capability context from CSV
4. get_missing_explicit_pipeline_demo_ctx_keys(...)
5. if missing: guard skip and force flags off
6. if present: guard not skipped and flags remain enabled
```

Do not attach before the checkbox check.

Do not attach when Explicit KPI ON is OFF.

Do not attach after the ctx guard check.

---

## 9. Behavior Matrix

### 9.1 Explicit KPI OFF

Expected:

```text
no demo flags
no attach attempt
no ctx guard change
return None
```

### 9.2 Explicit KPI ON + default CSV missing

Expected:

```text
demo flags are applied
attach helper is called
attach result reason=file_missing
ctx guard still sees missing explicit_pipeline_backward_weekly_capability
explicit pipeline/report/issue/cost-kpi flags are forced off
ctx guard diagnostic remains visible in Explicit KPI View
```

### 9.3 Explicit KPI ON + default CSV invalid / empty

Expected:

```text
demo flags are applied
attach helper is called
attach result reason=empty_context
ctx guard still sees missing explicit_pipeline_backward_weekly_capability
explicit flags are forced off
ctx guard diagnostic remains visible
```

### 9.4 Explicit KPI ON + valid CSV / attached context

Expected:

```text
demo flags are applied
attach helper attaches env.explicit_pipeline_backward_weekly_capability
ctx guard no longer reports explicit_pipeline_backward_weekly_capability
explicit flags remain enabled
ctx guard skipped = False
```

---

## 10. Diagnostics

The attach helper already records diagnostics on `env`:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_source_path
explicit_pipeline_backward_weekly_capability_source_scenario
explicit_pipeline_backward_weekly_capability_attached
```

The GUI preflight does not need to add new diagnostic fields.

It may ignore the returned attach result for now.

Future view improvements can surface these diagnostics.

---

## 11. Test Strategy

Update:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

The tests should avoid depending on a real file at:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Recommended approach:

```text
subclass / monkeypatch WOMCockpit._maybe_attach_explicit_pipeline_backward_weekly_capability
```

or monkeypatch the imported helper if easier.

A private method makes testing simpler.

---

## 12. Tests to Add / Update

### 12.1 Explicit KPI OFF does not attempt attach

Given an instance with:

```text
var_enable_explicit_kpi_reporting = False
```

and a monkeypatched attach method that would fail if called.

Expected:

```text
_maybe_apply_explicit_kpi_demo_flags() returns None
attach method is not called
```

### 12.2 Explicit KPI ON + attach missing file keeps guard skip

Monkeypatch `_maybe_attach_explicit_pipeline_backward_weekly_capability()` to record it was called but not attach context.

Example return:

```python
{
    "attached": False,
    "reason": "file_missing",
}
```

Expected:

```text
attach method called
ctx guard skipped is True
missing ctx keys include explicit_pipeline_backward_weekly_capability
enable_explicit_bridge_capacity_pipeline is False
export flags are False
```

### 12.3 Explicit KPI ON + attach context lets guard pass

Monkeypatch `_maybe_attach_explicit_pipeline_backward_weekly_capability()` to set:

```python
self.env.explicit_pipeline_backward_weekly_capability = {
    "MOM_A": {
        "P1": {
            "202601": 100
        }
    }
}
```

Expected:

```text
attach method called
ctx guard skipped is False
missing ctx keys == []
enable_explicit_bridge_capacity_pipeline is True
enable_explicit_bridge_capacity_report is True
enable_explicit_bridge_capacity_issue_candidates is True
enable_explicit_bridge_capacity_issue_candidate_cost_kpi is True
export flags remain False
```

### 12.4 Preflight ordering

Ensure order is:

```text
apply demo flags
attach capability context
ctx guard check
```

A simple test can monkeypatch the attach method and verify that when it attaches context, the guard passes.

If there is already a run_full_plan preflight ordering test, update it carefully.

Avoid brittle GUI assertions.

---

## 13. Existing Tests to Run

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Then related cockpit tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

Then broader regression tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If Tk tests are skipped, state so clearly.

---

## 14. Manual GUI Validation

Manual GUI validation is optional for this request because no sample CSV is committed.

Without default CSV, the expected manual behavior remains:

```text
1. python -m main
2. Explicit KPI ON
3. Run Full Plan
4. Explicit KPI View still shows missing context diagnostic
```

This confirms no regression.

Manual validation with a real CSV should be done in a later sample CSV phase.

---

## 15. Completion Criteria

This phase is complete when:

```text
[OK] Explicit KPI ON preflight calls optional capability attach helper
[OK] Explicit KPI OFF does not call attach helper
[OK] missing/empty CSV behavior preserves current ctx guard diagnostic path
[OK] valid attach can allow ctx guard to pass in tests
[OK] explicit flags remain enabled when required ctx is attached
[OK] export flags remain False
[OK] no sample CSV is added
[OK] no planning/export/replan execution is added
[OK] focused tests pass
```

---

## 16. Safety Boundaries

Please preserve:

```text
no sample CSV commit
no GUI layout redesign
no new checkbox
no scenario selector
no planning engine change
no export execution
no ReplanCommand execution
no automatic dummy context
no monetary KPI calculation
```

This patch should be small.

---

## 17. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Private helper method added
3. Preflight order implemented
4. Explicit KPI OFF behavior
5. Explicit KPI ON + missing/empty context behavior
6. Explicit KPI ON + attached context behavior
7. Safety boundaries preserved
8. Tests added / updated
9. Test commands executed
10. Test results
11. Skipped tests and why
12. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
sample CSV master
manual GUI validation with sample data
Price-Cost-Profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Backward Weekly Capability GUI Preflight Phase 2B
```
