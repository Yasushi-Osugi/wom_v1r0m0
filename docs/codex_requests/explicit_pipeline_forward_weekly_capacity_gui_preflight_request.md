# Codex Request: Wire Explicit Pipeline Forward Weekly Capacity into GUI Preflight Phase F2

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design / completion documents already exist:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_forward_weekly_capacity_context_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md
```

Please read especially:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md
```

Phase F1 implemented the standalone forward weekly capacity adapter in:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

with these functions:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
load_explicit_pipeline_forward_weekly_capacity_csv(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

Phase F2 should wire the optional forward attach helper into the existing Explicit KPI ON GUI preflight path.

---

## 2. Main Objective

Update the Explicit KPI ON GUI preflight so that it attempts to attach forward weekly capacity from CSV before the ctx guard checks required keys.

Target order:

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

The forward helper to call is:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(self.env)
```

This request must not add the forward sample CSV yet.

---

## 3. Scope of This Request

Implement only:

```text
1. Add a private GUI helper method for forward weekly capacity attach.
2. Call that helper from _maybe_apply_explicit_kpi_demo_flags().
3. Update focused GUI wiring tests.
```

Do not implement:

```text
forward sample CSV
manual GUI validation with sample CSV
planning engine changes
explicit bridge capacity pipeline changes
pipeline shape refactor
new GUI widgets
scenario selector
export execution
ReplanCommand execution
Price-Cost-Profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This is a small preflight wiring patch.

---

## 4. Expected Files to Modify

Expected files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Avoid modifying unless absolutely necessary:

```text
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/explicit_bridge_capacity_pipeline.py
data/explicit_pipeline_backward_weekly_capability.csv
```

Do not add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

That belongs to Phase F3.

---

## 5. Existing Context

The existing GUI preflight method is:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

It already handles:

```text
Explicit KPI checkbox missing
Explicit KPI OFF
demo flag application
backward capability optional attach
ctx guard missing-key detection
ctx guard diagnostics
explicit flag disabling when ctx is missing
ctx guard pass behavior
```

Phase F2 should preserve all of that and insert the forward attach call between:

```text
backward capability attach
```

and:

```text
ctx guard missing-key detection
```

---

## 6. Recommended Implementation

Add a private method to `WOMCockpit`:

```python
def _maybe_attach_explicit_pipeline_forward_weekly_capacity(self) -> dict[str, Any] | None:
    from pysi.plan.explicit_pipeline_capacity_context import (
        maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv,
    )

    return maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(self.env)
```

This should mirror the existing helper:

```python
_maybe_attach_explicit_pipeline_backward_weekly_capability()
```

Then update `_maybe_apply_explicit_kpi_demo_flags()` so the order becomes conceptually:

```python
applied = apply_explicit_pipeline_kpi_demo_flags(
    self.env,
    include_exports=False,
)

self._maybe_attach_explicit_pipeline_backward_weekly_capability()
self._maybe_attach_explicit_pipeline_forward_weekly_capacity()

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(self.env)
```

Do not call the forward helper when Explicit KPI ON is OFF.

---

## 7. Required Ordering

The exact ordering is important:

```text
1. Explicit KPI ON check
2. apply_explicit_pipeline_kpi_demo_flags(...)
3. _maybe_attach_explicit_pipeline_backward_weekly_capability()
4. _maybe_attach_explicit_pipeline_forward_weekly_capacity()
5. get_missing_explicit_pipeline_demo_ctx_keys(...)
6. if missing: record diagnostics and force explicit flags OFF
7. if no missing: keep explicit flags ON and clear diagnostics
```

Do not run ctx guard before forward attach.

Do not call explicit bridge capacity pipeline from the helper.

Do not generate dummy context.

---

## 8. Expected Behavior Matrix

### 8.1 Explicit KPI OFF

Expected:

```text
no demo flags are applied
no backward attach attempt
no forward attach attempt
no ctx guard mutation
_maybe_apply_explicit_kpi_demo_flags() returns None
```

### 8.2 Explicit KPI ON + no forward CSV

Expected:

```text
demo flags applied
backward attach attempted
forward attach attempted
forward attach helper returns file_missing
forward context is not attached
ctx guard still reports explicit_pipeline_forward_weekly_capacity
explicit flags are forced OFF
Run Full Plan remains safe
```

### 8.3 Explicit KPI ON + forward CSV empty / invalid

Expected:

```text
demo flags applied
backward attach attempted
forward attach attempted
forward attach helper returns empty_context
forward context is not attached
ctx guard still reports explicit_pipeline_forward_weekly_capacity
explicit flags are forced OFF
Run Full Plan remains safe
```

### 8.4 Explicit KPI ON + backward and forward contexts both attached

Expected:

```text
demo flags applied
backward context exists
forward context exists
ctx guard skipped = False
missing keys = []
explicit runtime flags remain True
export flags remain False
```

---

## 9. Diagnostics

The forward attach helper already records these diagnostics on env:

```text
explicit_pipeline_forward_weekly_capacity_attach_result
explicit_pipeline_forward_weekly_capacity_source_path
explicit_pipeline_forward_weekly_capacity_source_scenario
explicit_pipeline_forward_weekly_capacity_attached
```

The GUI preflight does not need to add new diagnostic fields.

It can ignore the returned result for now.

---

## 10. Test Strategy

Update:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Use monkeypatching / fake helper methods.

Do not depend on a real file:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

That file does not exist in Phase F2.

---

## 11. Tests to Add / Update

### 11.1 Explicit KPI OFF does not call forward attach

Set:

```text
var_enable_explicit_kpi_reporting = False
```

Monkeypatch `_maybe_attach_explicit_pipeline_forward_weekly_capacity()` to fail if called.

Expected:

```text
_maybe_apply_explicit_kpi_demo_flags() returns None
forward attach helper is not called
```

If there is already a test that checks backward attach is not called when OFF, extend it to also check forward attach.

---

### 11.2 Explicit KPI ON calls forward attach

Monkeypatch forward helper to record that it was called.

Expected:

```text
Explicit KPI ON calls forward attach helper
```

This can be combined with the backward-only guard test below.

---

### 11.3 Explicit KPI ON + backward-only remains guard skipped

Monkeypatch backward helper to attach:

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
ctx guard skipped is True
missing ctx keys == ["explicit_pipeline_forward_weekly_capacity"]
enable_explicit_bridge_capacity_pipeline is False
enable_explicit_bridge_capacity_report is False
enable_explicit_bridge_capacity_issue_candidates is False
enable_explicit_bridge_capacity_issue_candidate_cost_kpi is False
all export flags remain False
```

---

### 11.4 Explicit KPI ON + both contexts passes guard

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
ctx guard skipped is False
missing ctx keys == []
enable_explicit_bridge_capacity_pipeline is True
enable_explicit_bridge_capacity_report is True
enable_explicit_bridge_capacity_issue_candidates is True
enable_explicit_bridge_capacity_issue_candidate_cost_kpi is True
all export flags remain False
```

---

### 11.5 Both helpers do nothing still reports both keys

Monkeypatch both helper methods to do nothing.

Expected:

```text
ctx guard skipped is True
missing ctx keys include:
    explicit_pipeline_backward_weekly_capability
    explicit_pipeline_forward_weekly_capacity
explicit flags forced OFF
```

This preserves existing guard behavior.

---

### 11.6 Preflight ordering

A focused test may verify practical ordering:

```text
backward attach happens before forward attach
forward attach happens before ctx guard
```

A simple implementation approach:

```text
- backward helper records "backward"
- forward helper records "forward" and attaches forward context
- guard pass proves forward attach happened before missing-key check
```

If intercepting `get_missing_explicit_pipeline_demo_ctx_keys` is too brittle, avoid over-testing internals and rely on behavior:

```text
forward context attached by helper
ctx guard sees it
guard passes
```

---

## 12. Existing Tests to Run

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

If Tk tests are skipped because of environment, report that clearly.

---

## 13. Manual GUI Validation

Manual GUI validation is optional for Phase F2 because no forward sample CSV is added.

Without forward CSV, expected manual behavior remains:

```text
Explicit KPI ON
Run Full Plan
Run Full Plan completes
Explicit KPI View shows:
    explicit_pipeline_forward_weekly_capacity
```

The only difference is that GUI preflight now attempts to load:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

before the ctx guard reports it missing.

Manual validation with missing file is useful but not required.

---

## 14. Safety Boundaries

Preserve these boundaries:

```text
1. Do not add data/explicit_pipeline_forward_weekly_capacity.csv.
2. Do not modify explicit bridge capacity pipeline behavior.
3. Do not modify planning engine behavior.
4. Do not generate dummy forward capacity.
5. Do not add new GUI widgets.
6. Do not add scenario selector.
7. Do not execute exports.
8. Do not execute ReplanCommand.
9. Do not implement price-cost-profit propagation.
10. Do not implement tariff simulation.
11. Do not implement cold-chain or shelf-life logic.
12. Do not commit outputs/ generated files.
```

This request is only:

```text
connect existing forward attach helper into Explicit KPI ON preflight
```

---

## 15. Expected Files Changed

Expected files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

No data CSV should be changed.

No planning code should be changed.

No explicit bridge capacity pipeline code should be changed.

---

## 16. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Private GUI helper added
3. Preflight order implemented
4. Explicit KPI OFF behavior
5. Explicit KPI ON + missing forward CSV behavior
6. Explicit KPI ON + both-context behavior
7. Safety boundaries preserved
8. Tests added / updated
9. Test commands executed
10. Test results
11. Skipped tests and why
12. Manual GUI validation status
13. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
forward sample CSV
main PR
pipeline shape refactor
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Forward Weekly Capacity GUI Preflight Phase F2
```
