# Codex Request: Add Explicit Pipeline Forward Weekly Capacity Sample CSV Phase F3

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
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
```

Please read especially:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
```

Phase F1 implemented the forward weekly capacity adapter:

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

Phase F2 wired the forward attach helper into the Explicit KPI ON GUI preflight path.

This request implements **Phase F3**:

```text
Add the runtime sample CSV for explicit_pipeline_forward_weekly_capacity
and focused validation tests.
```

---

## 2. Main Objective

Add the default runtime CSV:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

with a minimal Japanese Rice Case forward weekly capacity sample.

This file should allow the existing helper:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

to attach:

```python
env.explicit_pipeline_forward_weekly_capacity
```

when Explicit KPI ON preflight runs.

The first success condition is:

```text
Explicit KPI ON + Run Full Plan no longer reports
explicit_pipeline_forward_weekly_capacity as missing,
provided both backward and forward sample CSVs are loaded and accepted.
```

This request does **not** require full capacity report or KPI cockpit population.

---

## 3. Scenario

Use the same runtime scenario convention as the existing backward capability sample CSV:

```text
scenario = base
```

Semantic source:

```text
Japanese Rice Case / RICE_AS_IS
```

Reason:

```text
The GUI preflight currently calls the attach helper with default scenario="base".
Using scenario=base avoids adding a scenario selector or changing GUI/helper behavior in this phase.
```

The `source` and `note` fields should clarify that the semantic source is Japanese Rice Case / RICE_AS_IS.

---

## 4. Sample Values

Use the Japanese Rice Case capacity proxy values:

```text
product = PACKAGED_RICE_STANDARD
node = MILL_EAST
capacity_type = P
week = 2027-W40, 2027-W41
capacity_lots = 5, 6
unit = lot
source = japanese_rice_case_sample
```

Interpretation:

```text
MILL_EAST is used as a milling / processing capacity proxy.
capacity_type=P means production / processing capacity.
```

---

## 5. File to Add

Add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Content:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

Keep the sample intentionally small.

Do not add generated output files.

---

## 6. Expected Runtime Context

The sample CSV should load into this product-first runtime context:

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

## 7. Relationship to Backward Capability Sample

The existing backward sample file is:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

The new forward sample file is:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Together, they should satisfy the current required Explicit KPI context guard keys:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

After both attach helpers run:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

---

## 8. Test File to Add

Add a focused test file:

```text
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

This test should validate the sample CSV without requiring the GUI.

---

## 9. Recommended Tests

### 9.1 Sample CSV exists and loads

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

### 9.2 Maybe attach helper attaches context

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

### 9.3 Sample CSV uses base scenario

Use `csv.DictReader` and assert:

```python
assert {row["scenario"] for row in rows} == {"base"}
```

Reason:

```text
GUI preflight uses helper default scenario="base".
```

### 9.4 Backward and forward samples clear ctx guard

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

## 10. Existing Tests to Run

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

If any Tk tests are skipped because of environment, state that clearly.

---

## 11. Manual GUI Validation

Manual GUI validation is recommended after this patch.

Run:

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

If B happens, treat it as the next diagnostic phase, not as failure of this sample CSV patch.

---

## 12. Important Limitation: Scenario Alignment

The current GUI default product may still be:

```text
IPHONE_NM_2028_BASE
```

while this sample CSV is for:

```text
PACKAGED_RICE_STANDARD
```

Therefore, the sample CSV may clear ctx guard presence but may not produce meaningful downstream explicit pipeline results for the current GUI default scenario.

This distinction is important:

```text
ctx guard validation:
    confirms required runtime context objects exist

meaningful pipeline validation:
    requires product / node / week / scenario alignment
```

This request is primarily a ctx guard / attach validation step.

---

## 13. Important Limitation: Pipeline Shape Compatibility

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

If the explicit bridge capacity pipeline expects another shape or week-key convention, the next issue may appear after ctx guard passes.

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

## 14. Safety Boundaries

Preserve these boundaries:

```text
1. Do not modify GUI preflight logic.
2. Do not modify planning engine logic.
3. Do not modify explicit bridge capacity pipeline logic.
4. Do not implement pipeline shape refactor.
5. Do not generate dummy capacity.
6. Do not add scenario selector.
7. Do not implement price-cost-profit propagation.
8. Do not implement tariff simulation.
9. Do not implement cold-chain or shelf-life logic.
10. Do not execute exports.
11. Do not execute ReplanCommand.
12. Do not commit outputs/ generated files.
```

This request is only:

```text
forward weekly capacity sample CSV + focused tests
```

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

## 16. Completion Criteria

This patch is complete when:

```text
[OK] data/explicit_pipeline_forward_weekly_capacity.csv exists
[OK] CSV loads into product-first context
[OK] maybe attach helper attaches the context
[OK] scenario column is base
[OK] backward + forward sample CSVs together clear ctx guard
[OK] tests pass
[OK] no unrelated files changed
```

Manual GUI validation is recommended after patch application.

---

## 17. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Sample CSV rows added
3. Runtime context shape loaded
4. Scenario choice and reason
5. Tests added
6. Test commands executed
7. Test results
8. Manual GUI validation status
9. Safety boundaries preserved
10. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
pipeline shape refactor
scenario alignment refactor
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Forward Weekly Capacity Sample CSV Phase F3
```
