# Explicit Pipeline Forward Weekly Capacity GUI Preflight Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-27  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion of **Explicit Pipeline Forward Weekly Capacity GUI Preflight Phase F2**.

Phase F2 connected the existing forward weekly capacity optional attach helper into the Explicit KPI ON GUI preflight path.

The target order was:

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

This phase was intentionally limited to GUI preflight wiring.

It did not add a forward sample CSV.

---

## 2. Background

Before Phase F2, Phase F1 had already implemented the standalone forward weekly capacity adapter:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
load_explicit_pipeline_forward_weekly_capacity_csv(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

However, the GUI preflight did not yet call:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

Therefore, even though the adapter existed, the Explicit KPI ON path still reported:

```text
Missing Context: explicit_pipeline_forward_weekly_capacity
```

unless forward capacity context had been attached manually elsewhere.

Phase F2 addressed this by wiring the optional attach helper into the preflight path.

---

## 3. Implemented Commit

The implementation was committed as:

```text
44b691b Wire forward weekly capacity attach into KPI preflight
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

Changed files:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

No data file was added.

No planning engine file was changed.

No explicit bridge capacity pipeline file was changed.

No GUI layout or widget was changed.

---

## 5. GUI Helper Added

The following private GUI helper was added to `WOMCockpit`:

```python
_maybe_attach_explicit_pipeline_forward_weekly_capacity(...)
```

Its responsibility is to delegate to:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(self.env)
```

from:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

This mirrors the existing backward capability attach helper.

---

## 6. Preflight Order Implemented

The preflight order in:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

is now:

```text
1. Check Explicit KPI ON variable
2. Apply Explicit KPI demo flags
3. Attach backward weekly capability from CSV
4. Attach forward weekly capacity from CSV
5. Run ctx guard missing-key check
6. If missing keys exist:
       record diagnostics
       force explicit flags OFF
7. If no missing keys:
       clear guard diagnostics
       keep explicit runtime flags ON
```

The important F2 insertion is:

```text
backward attach
    ↓
forward attach
    ↓
ctx guard
```

---

## 7. Explicit KPI OFF Behavior

The Explicit KPI OFF path remains unchanged.

When the checkbox variable is missing or OFF:

```text
_maybe_apply_explicit_kpi_demo_flags() returns None
demo flags are not applied
backward attach is not attempted
forward attach is not attempted
ctx guard diagnostics are not mutated
```

This behavior is now covered by tests for both backward and forward attach helpers.

---

## 8. Explicit KPI ON + Missing Forward CSV Behavior

When Explicit KPI ON is checked but no forward CSV exists:

```text
demo flags are applied
backward attach is attempted
forward attach is attempted
forward attach helper returns file_missing
forward context remains absent
ctx guard reports explicit_pipeline_forward_weekly_capacity
explicit runtime flags are forced OFF
Run Full Plan remains safe
```

This is the expected safe intermediate state after F2.

Because Phase F2 does not add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

the manual GUI behavior can still show:

```text
Missing Context: explicit_pipeline_forward_weekly_capacity
```

until Phase F3 adds the forward sample CSV.

---

## 9. Explicit KPI ON + Both Contexts Behavior

When both contexts are available:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

the ctx guard passes:

```text
ctx guard skipped = False
missing keys = []
explicit runtime flags remain ON
export flags remain OFF
```

This behavior is covered by the updated GUI wiring tests.

---

## 10. Tests Updated

Updated test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Coverage now includes:

```text
Explicit KPI OFF does not call backward or forward attach helpers
Explicit KPI ON calls forward attach helper
Backward-only context still fails guard on missing forward capacity
Both-context path passes guard
Practical ordering: backward attach before forward attach before guard pass behavior
Export flags remain OFF
```

The focused GUI wiring test count increased to:

```text
8 tests
```

---

## 11. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
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
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                 8 passed
tests/test_explicit_pipeline_forward_capacity_context.py                12 passed
tests/test_explicit_pipeline_capacity_context.py                        16 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                           7 passed
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py     3 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py             10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py         9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py  4 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                 7 passed
tests/test_explicit_pipeline_reporting_flags.py                          10 passed
tests/test_covid_vaccine_with_capacity_push.py                            1 passed
tests/test_japanese_rice_case_smoke.py                                    1 passed
```

Total observed result:

```text
88 passed
```

No skipped tests were observed in this local run.

---

## 12. Safety Boundaries Preserved

This phase intentionally did not implement:

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
database persistence
outputs/ generated file commit
```

Only the GUI preflight wiring and its tests were changed.

---

## 13. Current State After Phase F2

Current preflight state:

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

Current expected runtime behavior without forward CSV:

```text
forward attach is attempted
file_missing is recorded by the forward attach helper
ctx guard still reports explicit_pipeline_forward_weekly_capacity
Run Full Plan remains safe
```

This is expected because Phase F2 does not provide the forward CSV.

---

## 14. Meaning of This Milestone

Before Phase F2:

```text
forward capacity adapter existed,
but GUI preflight did not use it.
```

After Phase F2:

```text
GUI preflight attempts to use the forward capacity adapter.
```

This means the software is ready for the next integration step:

```text
placing a real forward weekly capacity CSV at the expected path.
```

---

## 15. Recommended Next Step

The next phase should be:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
```

Purpose:

```text
define the first sample CSV for:
data/explicit_pipeline_forward_weekly_capacity.csv
```

Candidate Japanese Rice Case sample:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

The first validation target after Phase F3 should be:

```text
Missing Context: explicit_pipeline_forward_weekly_capacity
```

disappears from the Explicit KPI View.

---

## 16. Later Follow-Up

After the forward CSV is added, two outcomes are possible.

### Case A: ctx guard passes and explicit pipeline runs

This means:

```text
both required contexts are present
explicit pipeline is allowed to run
```

The next diagnostic target becomes:

```text
whether capacity reports / issue candidates / KPI view populate meaningfully
```

### Case B: another runtime error or unavailable state appears

Likely causes:

```text
product mismatch
node mismatch
week mismatch
scenario mismatch
runtime shape mismatch
additional implicit pipeline requirements
iPhone GUI default scenario vs Japanese Rice Case sample mismatch
```

At that point, inspect:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

and confirm the exact runtime shape and scenario alignment requirements.

---

## 17. Summary

Explicit Pipeline Forward Weekly Capacity GUI Preflight Phase F2 is complete.

Implemented:

```text
private GUI forward attach helper
forward attach call in Explicit KPI ON preflight
updated GUI wiring tests
preflight ordering validation
```

The current target flow is now in place:

```text
apply demo flags
attach backward capability
attach forward weekly capacity
ctx guard
```

The next step is to add the actual forward capacity sample CSV in Phase F3.
