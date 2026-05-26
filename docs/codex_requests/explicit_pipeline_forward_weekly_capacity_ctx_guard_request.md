# Codex Request: Extend Explicit Pipeline Context Guard for Forward Weekly Capacity

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design / completion documents have already been added:

```text
docs/design/explicit_pipeline_backward_weekly_capability_context.md
docs/design/explicit_pipeline_backward_weekly_capability_context_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_sample_csv.md
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md
```

Please read especially:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md
```

The current Explicit KPI ON path now loads:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

and can attach:

```python
env.explicit_pipeline_backward_weekly_capability
```

before the context guard runs.

During manual GUI validation, the previous missing key was effectively passed, but the explicit bridge capacity pipeline then crashed with:

```text
ValueError: explicit bridge capacity pipeline enabled but missing ctx key:
explicit_pipeline_forward_weekly_capacity
```

This request implements the safety patch described in the design memo.

---

## 2. Main Objective

Extend the existing Explicit KPI demo context guard so that it also checks:

```text
explicit_pipeline_forward_weekly_capacity
```

before the explicit bridge capacity pipeline is allowed to run.

The required context keys should become:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

Target behavior:

```text
If backward capability is present but forward weekly capacity is missing:
    do not call explicit bridge capacity pipeline
    force explicit pipeline/report/issue/cost-kpi flags OFF for this run
    record missing context diagnostic
    let Run Full Plan complete safely
    show explicit_pipeline_forward_weekly_capacity in Explicit KPI View
```

This request does **not** implement forward weekly capacity itself.

---

## 3. Scope of This Request

Implement only:

```text
1. required ctx key list extension
2. tests for missing forward key
3. tests for backward-only vs both-context behavior
4. preserve GUI safety behavior
```

Do not implement:

```text
forward weekly capacity CSV
forward weekly capacity adapter
forward weekly capacity generation
planning engine changes
explicit bridge capacity pipeline changes
sample forward capacity file
```

This is a guard patch only.

---

## 4. Files to Modify

Expected files:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Modify these only if necessary:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Avoid modifying:

```text
pysi/gui/cockpit_tk.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/explicit_pipeline_capacity_context.py
data/explicit_pipeline_backward_weekly_capability.csv
```

No new CSV file should be added in this request.

---

## 5. Required Key Extension

Find the required-key list used by:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

It may look like:

```python
_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
)
```

Update it to:

```python
_REQUIRED_EXPLICIT_PIPELINE_DEMO_CTX_KEYS = (
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
)
```

If the exact constant name differs, update the existing required-key mechanism used by:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

Do not create a duplicate independent required-key list.

---

## 6. Missing Detection Rule

Preserve the existing missing detection semantics.

Expected rule:

```text
missing if attribute is absent
missing if attribute is None
```

Do not expand this request to treat empty dictionaries as missing unless that is already the existing behavior.

Reason:

```text
The current crash is caused by absent/None forward context.
Changing empty-dict semantics is a separate behavior decision.
```

---

## 7. Expected Diagnostics

When backward context exists but forward context is missing, the GUI preflight should produce:

```python
env.explicit_kpi_demo_flag_ctx_guard_skipped = True
env.explicit_kpi_demo_flag_missing_ctx_keys = [
    "explicit_pipeline_forward_weekly_capacity"
]
env.explicit_kpi_demo_flag_guard_message = (
    "Explicit KPI demo pipeline skipped because required ctx keys are missing: "
    "explicit_pipeline_forward_weekly_capacity"
)
```

If both are missing:

```python
env.explicit_kpi_demo_flag_missing_ctx_keys = [
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
]
```

The order should be deterministic:

```text
backward first
forward second
```

---

## 8. GUI Preflight Expected Behavior

The existing GUI preflight in:

```text
pysi/gui/cockpit_tk.py
```

already does this:

```text
apply demo flags
try optional backward capability CSV attach
run get_missing_explicit_pipeline_demo_ctx_keys(env)
if missing:
    force explicit flags OFF
```

After this patch, no control-flow change should be needed in `cockpit_tk.py`.

When forward capacity is absent, the existing preflight should:

```text
force explicit flags OFF
prevent explicit bridge capacity pipeline from running
allow normal Run Full Plan to continue
```

Do not modify `cockpit_tk.py` unless tests reveal that the existing preflight cannot use the expanded guard list.

---

## 9. Test Updates: Required-Key Helper

Update / add tests in:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

### 9.1 Empty env reports both keys

```python
env = SimpleNamespace()
missing = get_missing_explicit_pipeline_demo_ctx_keys(env)

assert missing == [
    "explicit_pipeline_backward_weekly_capability",
    "explicit_pipeline_forward_weekly_capacity",
]
```

### 9.2 Backward-only env reports forward key

```python
env = SimpleNamespace(
    explicit_pipeline_backward_weekly_capability={
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5
            }
        }
    }
)
missing = get_missing_explicit_pipeline_demo_ctx_keys(env)

assert missing == ["explicit_pipeline_forward_weekly_capacity"]
```

### 9.3 Backward + forward env reports no missing keys

```python
env = SimpleNamespace(
    explicit_pipeline_backward_weekly_capability={
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5
            }
        }
    },
    explicit_pipeline_forward_weekly_capacity={
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {
                    "2027-W40": 5
                }
            }
        }
    },
)
missing = get_missing_explicit_pipeline_demo_ctx_keys(env)

assert missing == []
```

The exact forward context shape here is only for guard presence.

The guard should only check that the attribute exists and is not None.

---

## 10. Test Updates: GUI Wiring

Update / add tests in:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

### 10.1 Explicit KPI ON + backward-only attach should guard skip

Simulate the optional attach helper populating only:

```python
env.explicit_pipeline_backward_weekly_capability
```

Do not populate:

```python
env.explicit_pipeline_forward_weekly_capacity
```

Expected:

```text
ctx guard skipped is True
missing ctx keys == ["explicit_pipeline_forward_weekly_capacity"]
enable_explicit_bridge_capacity_pipeline is False
enable_explicit_bridge_capacity_report is False
enable_explicit_bridge_capacity_issue_candidates is False
enable_explicit_bridge_capacity_issue_candidate_cost_kpi is False
all export flags remain False
```

### 10.2 Explicit KPI ON + both contexts should guard pass

Simulate the optional attach helper populating both:

```python
env.explicit_pipeline_backward_weekly_capability
env.explicit_pipeline_forward_weekly_capacity
```

Expected:

```text
ctx guard skipped is False
missing ctx keys == []
enable_explicit_bridge_capacity_pipeline is True
enable_explicit_bridge_capacity_report is True
enable_explicit_bridge_capacity_issue_candidates is True
enable_explicit_bridge_capacity_issue_candidate_cost_kpi is True
all export flags remain False
```

### 10.3 Existing no-attach / missing behavior should update expected missing keys

If existing tests previously expected only:

```text
explicit_pipeline_backward_weekly_capability
```

when no context exists, update them to expect both:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

---

## 11. View / Renderer Tests

The existing view-model and renderer should already display whatever appears in:

```python
env.explicit_kpi_demo_flag_missing_ctx_keys
```

If existing tests assert exact text for missing keys, update expected text to include:

```text
explicit_pipeline_forward_weekly_capacity
```

Do not add new UI widgets.

Do not redesign the view.

---

## 12. Manual GUI Validation Target

After implementation, manual GUI behavior should be:

```text
1. python -m main
2. check Explicit KPI ON
3. Run Full Plan
4. Run Full Plan should not crash
5. Open Explicit KPI View
6. Missing Context should show:
       explicit_pipeline_forward_weekly_capacity
```

This is the desired safe intermediate state.

Full KPI population is not the goal of this patch.

---

## 13. Test Commands to Run

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

If any Tk tests are skipped because of environment, report that clearly.

---

## 14. Safety Boundaries

Please preserve these boundaries:

```text
1. Do not implement forward weekly capacity generation.
2. Do not add forward capacity CSV.
3. Do not modify explicit bridge capacity pipeline behavior.
4. Do not modify planning engine logic.
5. Do not bypass ctx guard.
6. Do not remove ctx guard.
7. Do not create dummy forward capacity.
8. Do not add GUI widgets.
9. Do not add scenario selector.
10. Do not run exports.
11. Do not execute ReplanCommand.
12. Do not implement price-cost-profit propagation.
13. Do not implement tariff simulation.
14. Do not implement cold-chain or shelf-life logic.
15. Do not commit outputs/ generated files.
```

This request is only:

```text
extend guard required keys + update tests
```

---

## 15. Expected Files Changed

Expected files:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Possibly, only if tests require it:

```text
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

No data file should be changed.

No planning code should be changed.

---

## 16. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Required ctx key list before / after
3. Missing detection behavior
4. Backward-only behavior
5. Both-context behavior
6. GUI preflight behavior
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
main PR
forward capacity adapter
forward capacity sample CSV
pipeline shape refactor
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Forward Weekly Capacity Context Guard
```
