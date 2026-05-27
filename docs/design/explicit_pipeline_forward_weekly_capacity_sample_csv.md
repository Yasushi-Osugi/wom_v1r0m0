# Explicit Pipeline Forward Weekly Capacity Sample CSV Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-27  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines **Phase F3** for the Explicit Pipeline Forward Weekly Capacity work.

Phase F3 adds the first runtime sample CSV for:

```text
explicit_pipeline_forward_weekly_capacity
```

The expected file path is:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

The first objective is not full KPI population.

The first objective is:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
GUI preflight loads backward capability CSV
    ↓
GUI preflight loads forward weekly capacity CSV
    ↓
ctx guard no longer reports:
        explicit_pipeline_forward_weekly_capacity
```

In short:

```text
remove the current missing forward capacity diagnostic
```

This phase provides the first real “fuel” for the forward capacity attach helper.

---

## 2. Background

The following phases have already been completed:

```text
Forward weekly capacity ctx guard
Forward weekly capacity context design
Forward weekly capacity adapter Phase F1
Forward weekly capacity GUI preflight wiring Phase F2
```

Current preflight order:

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

Current missing runtime context:

```text
explicit_pipeline_forward_weekly_capacity
```

The forward attach helper now looks for:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

but that file does not yet exist.

---

## 3. Phase F3 Scope

Phase F3 should add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

and focused validation tests.

Expected implementation scope:

```text
1. Add forward weekly capacity sample CSV.
2. Add loader / attach sample CSV tests.
3. Confirm backward + forward sample CSVs together clear ctx guard.
```

Phase F3 should not change:

```text
GUI preflight logic
planning engine logic
explicit bridge capacity pipeline logic
reporting stack logic
price-cost-profit logic
```

---

## 4. Scenario

Use the same scenario convention as the existing backward capability sample CSV:

```text
scenario = base
```

Semantic source:

```text
Japanese Rice Case / RICE_AS_IS
```

Reason:

```text
The GUI preflight helper currently calls the attach helper with default scenario="base".
Using scenario=base allows the file to be loaded without introducing a scenario selector or new GUI logic.
```

This is intentionally a runtime demo/default scenario value, not a claim that the original business scenario name is `base`.

The source and note fields should preserve the semantic origin.

---

## 5. Sample Rows

Use the Japanese Rice Case capacity proxy values already used in the backward capability sample design:

```text
product = PACKAGED_RICE_STANDARD
node = MILL_EAST
capacity_type = P
week = 2027-W40, 2027-W41
capacity_lots = 5, 6
unit = lot
source = japanese_rice_case_sample
```

These values represent a small milling / processing capacity proxy for Japanese Rice Case.

---

## 6. Target CSV Path

Add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

---

## 7. Target CSV Schema

CSV columns:

```text
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
```

Recommended content:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

Keep the sample intentionally small.

---

## 8. Expected Runtime Context

The CSV should load into this product-first runtime context:

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

This is the canonical forward capacity shape:

```text
product -> node -> capacity_type -> week -> capacity_lots
```

---

## 9. Relationship to Backward Capability Sample

The existing backward capability sample CSV is:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

It provides:

```text
explicit_pipeline_backward_weekly_capability
```

The new forward sample CSV provides:

```text
explicit_pipeline_forward_weekly_capacity
```

Together, they should satisfy the current required ctx guard keys:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

Expected result after both attach helpers run:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

---

## 10. First Success Condition

The first success condition for Phase F3 is:

```text
Explicit KPI View no longer shows:
    explicit_pipeline_forward_weekly_capacity
as missing context
```

This means the ctx guard can pass when both backward and forward sample CSVs are available.

This does not guarantee:

```text
capacity report is populated
issue candidates are populated
KPI cards are populated
graph view is populated
```

Those depend on downstream explicit bridge capacity pipeline compatibility and scenario alignment.

---

## 11. Important Limitation: Scenario Alignment

The current GUI default product may still be:

```text
IPHONE_NM_2028_BASE
```

while this sample CSV is for:

```text
PACKAGED_RICE_STANDARD
```

Therefore, the sample CSV may clear ctx guard presence, but may not produce meaningful downstream explicit pipeline results for the current GUI default scenario.

This distinction is important:

```text
ctx guard validation:
    confirms the required runtime context objects exist

meaningful pipeline validation:
    requires product / node / week / scenario alignment
```

Phase F3 is primarily a ctx guard / attach validation step.

---

## 12. Important Limitation: Pipeline Shape Compatibility

The forward capacity runtime shape is:

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

If the explicit bridge capacity pipeline expects another shape or week key convention, the next issue may appear after ctx guard passes.

That is not a Phase F3 failure.

It would be the next diagnostic step.

At that point, inspect:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

and verify exact assumptions for:

```text
product key
node key
capacity_type key
week key
lot quantity key
```

---

## 13. Test File

Add a focused test file:

```text
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

This should validate the sample CSV without requiring the GUI.

---

## 14. Recommended Tests

### 14.1 Sample CSV exists and loads

Test:

```python
from pathlib import Path

from pysi.plan.explicit_pipeline_capacity_context import (
    load_explicit_pipeline_forward_weekly_capacity_csv,
)

def test_forward_capacity_sample_csv_exists_and_loads_non_empty_context():
    path = Path("data/explicit_pipeline_forward_weekly_capacity.csv")
    assert path.exists()

    context = load_explicit_pipeline_forward_weekly_capacity_csv(path)

    assert context == {
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

---

### 14.2 Maybe attach helper attaches context

Test:

```python
from types import SimpleNamespace

from pysi.plan.explicit_pipeline_capacity_context import (
    maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv,
)

def test_forward_capacity_sample_csv_attach_helper_attaches_context():
    env = SimpleNamespace()

    result = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env)

    assert result["file_exists"] is True
    assert result["attached"] is True
    assert result["reason"] == ""
    assert result["record_count"] == 2
    assert result["product_count"] == 1
    assert result["node_count"] == 1
    assert result["capacity_type_count"] == 1

    assert env.explicit_pipeline_forward_weekly_capacity == {
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

---

### 14.3 Scenario column is base

Test with `csv.DictReader`:

```python
def test_forward_capacity_sample_csv_uses_base_scenario_for_gui_default():
    ...
    assert {row["scenario"] for row in rows} == {"base"}
```

Reason:

```text
GUI preflight uses helper default scenario="base".
```

---

### 14.4 Backward + forward samples clear ctx guard

Test:

```python
from types import SimpleNamespace

from pysi.plan.explicit_pipeline_capacity_context import (
    maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
    maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv,
)
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    get_missing_explicit_pipeline_demo_ctx_keys,
)

def test_backward_and_forward_sample_csvs_clear_explicit_kpi_ctx_guard():
    env = SimpleNamespace()

    backward = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)
    forward = maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env)

    assert backward["attached"] is True
    assert forward["attached"] is True
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

This is the most important Phase F3 test.

---

## 15. Expected Files Changed

Expected files:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

No code files should need to change.

If a code file must be changed, explain why.

---

## 16. Existing Tests to Run

Run the new test:

```bat
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

Run related context tests:

```bat
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Run cockpit / reporting regression tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Run scenario smoke tests:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
python -m pytest tests/test_japanese_rice_case_smoke.py
```

---

## 17. Manual GUI Validation

Manual GUI validation is recommended after Phase F3.

Command:

```bat
python -m main
```

Manual steps:

```text
1. Check Explicit KPI ON.
2. Run Full Plan.
3. Open Explicit KPI View.
4. Confirm missing context diagnostic no longer shows:
       explicit_pipeline_forward_weekly_capacity
```

Possible result:

```text
A. ctx guard passes and explicit pipeline runs.
B. another downstream error or unavailable state appears.
```

If B happens, treat it as the next diagnostic phase, not as a sample CSV failure.

---

## 18. Safety Boundaries

Phase F3 must not implement:

```text
GUI preflight changes
planning engine changes
explicit bridge capacity pipeline changes
pipeline shape refactor
dummy capacity generation
scenario selector
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
export execution
ReplanCommand execution
```

This phase is only:

```text
forward weekly capacity sample CSV + tests
```

---

## 19. Completion Criteria

Phase F3 is complete when:

```text
[OK] data/explicit_pipeline_forward_weekly_capacity.csv exists
[OK] CSV loads into product-first context
[OK] maybe attach helper attaches the context
[OK] scenario column is base
[OK] backward + forward sample CSVs together clear ctx guard
[OK] tests pass
[OK] no unrelated files changed
```

Manual GUI validation is recommended but can be logged separately if it reveals downstream pipeline issues.

---

## 20. Recommended Next Phase

After Phase F3, create:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md
```

Then perform manual GUI validation.

If ctx guard passes but explicit pipeline still fails or the cockpit remains empty, the next design topic should be:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
```

Purpose:

```text
verify explicit_bridge_capacity_pipeline.py expectations
align Japanese Rice Case sample vs current iPhone GUI default
confirm product / node / week key compatibility
```

---

## 21. Summary

Phase F3 adds the real forward weekly capacity sample CSV.

Target file:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Target context:

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

First success condition:

```text
explicit_pipeline_forward_weekly_capacity
```

no longer appears as a missing context key after GUI preflight loads both backward and forward sample CSVs.
