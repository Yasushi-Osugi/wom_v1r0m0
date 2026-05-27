# Explicit Pipeline Forward Weekly Capacity Context Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-27  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_context_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion of **Explicit Pipeline Forward Weekly Capacity Context Adapter Phase F1**.

Phase F1 added the standalone adapter layer for:

```text
explicit_pipeline_forward_weekly_capacity
```

The adapter can now build, load, attach, and optionally attach forward weekly capacity context, while keeping GUI preflight wiring and sample CSV work out of scope.

---

## 2. Background

Before Phase F1, the Explicit KPI ON path could safely detect the missing forward capacity context:

```text
Missing Context: explicit_pipeline_forward_weekly_capacity
```

The backward side already had:

```text
backward capability adapter
backward capability CSV sample
GUI preflight backward attach
ctx guard diagnostics
```

The missing piece was a pure adapter for the forward side.

Phase F1 implements that adapter without changing GUI behavior.

---

## 3. Implemented Commit

The implementation was committed as:

```text
6f327ee Add forward weekly capacity context adapter
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

Changed files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_forward_capacity_context.py
```

No GUI file was changed.

No forward sample CSV was added.

No planning engine file was changed.

No explicit bridge capacity pipeline file was changed.

---

## 5. Functions Added

The following functions were added:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
load_explicit_pipeline_forward_weekly_capacity_csv(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

These functions mirror the backward capability helper family, but implement the forward capacity runtime shape.

---

## 6. Runtime Shape

The implemented runtime shape is product-first:

```python
{
    product: {
        node: {
            capacity_type: {
                week: capacity_lots
            }
        }
    }
}
```

Example:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

This is the intended shape for selected-product forward execution capacity.

---

## 7. Capacity Type Normalization

The adapter normalizes capacity type to:

```text
P
S
I
```

Supported aliases include:

```text
P / production / process / processing
S / shipping / shipment / sales
I / inventory / storage
```

Unsupported capacity types are:

```text
skipped when strict=False
raised as ValueError when strict=True
```

No arbitrary value is silently mapped to `P`.

---

## 8. Unit Handling

Supported unit:

```text
lot
```

Behavior:

```text
blank or missing unit => lot
unit=lot => accepted
other unit => skipped when strict=False
other unit => ValueError when strict=True
```

No unit conversion was added.

---

## 9. Capacity Lots Validation

Accepted examples:

```text
5
5.0
"5"
"5.0"
```

Rejected examples:

```text
5.5
-1
"abc"
```

Behavior:

```text
strict=False => invalid rows skipped
strict=True  => ValueError
```

This prevents fractional or negative lot capacity from entering the canonical context.

---

## 10. Scenario Filtering

Scenario behavior:

```text
blank/missing row scenario => base
default scenario="base" includes base rows and blank-scenario rows
scenario=None disables filtering
specific scenario includes only matching rows
```

This mirrors the backward capability adapter.

---

## 11. Duplicate Row Behavior

Duplicate rows use:

```text
last valid row wins
```

Duplicate key path:

```text
product / node / capacity_type / week
```

This gives deterministic overwrite behavior.

---

## 12. CSV Loader

The loader function:

```python
load_explicit_pipeline_forward_weekly_capacity_csv(...)
```

uses:

```text
csv.DictReader
pathlib.Path
standard library only
```

No pandas dependency was introduced.

---

## 13. Env Attach Helper

The attach helper sets:

```python
env.explicit_pipeline_forward_weekly_capacity = context
```

and returns `env`.

---

## 14. Optional Attach Helper

The optional attach helper:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

uses default path:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Behavior:

```text
file missing:
    attached=False
    reason=file_missing
    existing context preserved

file exists but context empty:
    attached=False
    reason=empty_context
    existing context preserved

file exists and context non-empty:
    attached=True
    reason=""
    context attached to env
```

No dummy context is generated.

No GUI call is made.

No planning execution is performed.

---

## 15. Return Map and Diagnostics

The optional attach helper returns:

```python
{
    "path": str,
    "scenario": scenario,
    "file_exists": bool,
    "attached": bool,
    "record_count": int,
    "product_count": int,
    "node_count": int,
    "capacity_type_count": int,
    "reason": str,
}
```

It also records diagnostics on `env`:

```text
explicit_pipeline_forward_weekly_capacity_attach_result
explicit_pipeline_forward_weekly_capacity_source_path
explicit_pipeline_forward_weekly_capacity_source_scenario
explicit_pipeline_forward_weekly_capacity_attached
```

---

## 16. Counting Rules

For this context:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

Counts are:

```text
product_count = 1
node_count = 1
capacity_type_count = 1
record_count = 2
```

Counting interpretation:

```text
node_count = number of product/node paths
capacity_type_count = number of product/node/capacity_type paths
record_count = number of product/node/capacity_type/week entries
```

---

## 17. Tests Added

New test file:

```text
tests/test_explicit_pipeline_forward_capacity_context.py
```

Coverage includes:

```text
product-first context build
scenario filtering
capacity type normalization
invalid row skip / raise behavior
duplicate overwrite behavior
CSV loading
env attach
maybe-attach missing file
maybe-attach valid file
failed attach preserving existing context
ctx guard clearing when backward + forward contexts are both present
```

---

## 18. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
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
tests/test_explicit_pipeline_forward_capacity_context.py                 12 passed
tests/test_explicit_pipeline_capacity_context.py                         16 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                            7 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                  7 passed
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py      3 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py              10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py          9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py   4 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                  7 passed
tests/test_explicit_pipeline_reporting_flags.py                           10 passed
tests/test_covid_vaccine_with_capacity_push.py                             1 passed
tests/test_japanese_rice_case_smoke.py                                     1 passed
```

Total observed result:

```text
87 passed
```

No skipped tests were observed in this run.

---

## 19. Safety Boundaries Preserved

This phase intentionally did not implement:

```text
GUI preflight wiring
forward capacity sample CSV
manual GUI validation
explicit bridge capacity pipeline changes
planning engine changes
dummy forward capacity
export execution
ReplanCommand execution
Price-Cost-Profit propagation
tariff simulation
cold-chain shelf-life modeling
scenario selector
outputs/ generated file commit
```

This was adapter-only work.

---

## 20. Current State After Phase F1

Current state:

```text
forward weekly capacity adapter exists
forward weekly capacity CSV loader exists
forward weekly capacity env attach helper exists
forward weekly capacity optional attach helper exists
forward diagnostics exist
tests pass
```

The GUI preflight does not yet call the new forward attach helper.

Therefore, current GUI behavior remains:

```text
Explicit KPI ON
Run Full Plan
    ↓
backward capability may attach
forward weekly capacity is still missing unless manually attached
    ↓
ctx guard may still show explicit_pipeline_forward_weekly_capacity
```

This is expected after F1.

---

## 21. Recommended Next Step

The next phase should be:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md
```

Purpose:

```text
wire maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
into WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
after backward attach and before ctx guard
```

Target preflight order:

```text
apply demo flags
attach backward capability from CSV
attach forward weekly capacity from CSV
ctx guard check
```

No sample CSV is required for that wiring phase.

---

## 22. Later Phase

After GUI preflight wiring, add a sample forward CSV:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Candidate Japanese Rice Case sample:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

First validation target after that phase:

```text
explicit_pipeline_forward_weekly_capacity missing diagnostic disappears
```

Full KPI population is a later pipeline / scenario alignment question.

---

## 23. Summary

Explicit Pipeline Forward Weekly Capacity Context Adapter Phase F1 is complete.

Implemented:

```text
build helper
CSV loader
env attach helper
optional runtime attach helper
diagnostics
tests
```

The context shape is:

```text
product -> node -> capacity_type -> week -> capacity_lots
```

This completes the standalone forward capacity adapter and prepares the next step: connecting it to GUI preflight.
