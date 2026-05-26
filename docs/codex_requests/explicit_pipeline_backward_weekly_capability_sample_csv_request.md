# Codex Request: Add Japanese Rice Case Sample CSV for Explicit Pipeline Backward Weekly Capability Phase 2C

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design / completion documents have already been added:

```text
docs/design/plan_with_capacity_context_and_planning_story.md
docs/design/explicit_pipeline_backward_weekly_capability_context.md
docs/design/explicit_pipeline_backward_weekly_capability_context_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_sample_csv.md
```

Please read especially:

```text
docs/design/explicit_pipeline_backward_weekly_capability_sample_csv.md
```

Phase 1 implemented the context adapter:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Phase 2A implemented optional CSV attach helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

Phase 2B wired the helper into the Explicit KPI ON GUI preflight.

This request implements **Phase 2C**:

```text
Add a small Japanese Rice Case sample CSV that the GUI preflight can load.
```

---

## 2. Main Objective

Create the default runtime CSV:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

with a minimal Japanese Rice Case sample.

This file should allow the existing helper:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

to attach:

```python
env.explicit_pipeline_backward_weekly_capability
```

when Explicit KPI ON preflight runs.

The first success condition is:

```text
Explicit KPI ON + Run Full Plan no longer reports
explicit_pipeline_backward_weekly_capability as missing,
provided the sample CSV is loaded and accepted.
```

This request does **not** require full KPI report population.

---

## 3. Scenario

Use the following WOM scenario for this sample:

```text
Japanese Rice Case
```

The sample CSV should be aligned to the Japanese Rice Case / Rice AS-IS context.

The scenario found in Rice case data / tests is:

```text
RICE_AS_IS
```

However, the existing attach helper default is:

```python
scenario="base"
```

Therefore, for this specific runtime CSV, use:

```text
scenario = base
```

and set `source` / `note` to clarify that the rows are for the Japanese Rice Case.

Reason:

```text
The GUI preflight currently calls the helper without specifying scenario.
The helper therefore filters scenario="base".
Using scenario=base avoids another GUI or helper change in this phase.
```

---

## 4. Confirmed Sample Values

Use these sample values:

```text
node = MILL_EAST
product = PACKAGED_RICE_STANDARD
week = 2027-W40, 2027-W41
capability_lots = 5, 6
capability_type = output
unit = lot
source = japanese_rice_case_sample
```

Important note:

```text
The underlying Rice Case capacity row identified in existing tests uses:
scenario_id=RICE_AS_IS
product_id=PACKAGED_RICE_STANDARD
capacity_owner_type=node
capacity_owner_id=MILL_EAST
week=2027-W40 / 2027-W41
capacity_type=P
capacity_qty=5.0 / 6.0
```

For the Explicit Pipeline runtime CSV, use `scenario=base` as explained above.

---

## 5. File to Add

Add:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Content:

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,5,output,lot,japanese_rice_case_sample,Japanese Rice Case milling/output capacity proxy from RICE_AS_IS weekly capacity
base,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W41,6,output,lot,japanese_rice_case_sample,Japanese Rice Case milling/output capacity proxy from RICE_AS_IS weekly capacity
```

Keep the sample intentionally small.

Do not add generated output files.

---

## 6. Test File to Add

Add a focused test file:

```text
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

This test should validate the sample CSV without running the GUI.

Recommended tests:

### 6.1 Sample CSV exists and loads

```python
from pathlib import Path

from pysi.plan.explicit_pipeline_capacity_context import (
    load_explicit_pipeline_backward_weekly_capability_csv,
)

def test_sample_csv_exists_and_loads_non_empty_context():
    path = Path("data/explicit_pipeline_backward_weekly_capability.csv")
    assert path.exists()

    context = load_explicit_pipeline_backward_weekly_capability_csv(path)

    assert context == {
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
```

### 6.2 Attach helper attaches sample CSV

```python
from types import SimpleNamespace

from pysi.plan.explicit_pipeline_capacity_context import (
    maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv,
)
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    get_missing_explicit_pipeline_demo_ctx_keys,
)

def test_sample_csv_attach_helper_attaches_context_and_clears_guard_key():
    env = SimpleNamespace()

    result = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)

    assert result["file_exists"] is True
    assert result["attached"] is True
    assert result["reason"] == ""
    assert result["record_count"] == 2
    assert result["node_count"] == 1
    assert result["product_count"] == 1

    assert env.explicit_pipeline_backward_weekly_capability == {
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
    assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

### 6.3 Sample CSV uses base scenario for GUI default

Read CSV using standard library and assert:

```text
all row["scenario"] == "base"
```

Reason:

```text
GUI preflight currently calls helper with scenario default "base".
```

---

## 7. Existing Tests to Run

Run the new test:

```bat
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

Run related adapter/preflight tests:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Run Japanese Rice Case smoke:

```bat
python -m pytest tests/test_japanese_rice_case_smoke.py
```

Run related cockpit tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

Run broader explicit pipeline regression tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If any optional test is skipped by environment, state it clearly.

---

## 8. Manual Validation

Manual GUI validation is recommended after this patch.

Steps:

```bat
python -m main
```

Then:

```text
1. Confirm Explicit KPI ON checkbox exists.
2. Check Explicit KPI ON.
3. Run Full Plan.
4. Open Explicit KPI View.
5. Confirm that the missing diagnostic for:
       explicit_pipeline_backward_weekly_capability
   disappears.
```

If the view still remains empty or partially unavailable, do not treat that as failure of this sample CSV patch.

This patch's first success condition is:

```text
the capability context missing diagnostic disappears
```

not:

```text
full capacity report / cost KPI cockpit population
```

---

## 9. Important Limitation: Shape Compatibility

This request intentionally adds a sample CSV for the current adapter shape:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

However, some existing explicit capacity planning tests use a different internal capability shape, such as:

```python
{
    product: {
        node: {
            week: capability_lots
        }
    }
}
```

This request does **not** resolve that possible downstream shape mismatch.

If the missing diagnostic disappears but the explicit bridge capacity pipeline still does not produce expected results, the next phase should inspect:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

and verify whether the pipeline expects:

```text
node-first
```

or:

```text
product-first
```

capability context.

Do not change pipeline shape in this request.

---

## 10. Important Limitation: MILL_EAST as Capacity Proxy

This sample uses:

```text
MILL_EAST
```

as the capacity node because it appears in Japanese Rice Case capacity-related data as a milling capacity node.

This is a practical Phase 2C proxy.

It may not be identical to the earlier conceptual "MOM node" label.

For Japanese Rice Case, the more natural bottleneck proxy is:

```text
milling / packaging capacity
```

rather than a generic node named `MOM`.

Do not rename the node to `MOM` in this sample.

Use the real Rice Case node:

```text
MILL_EAST
```

---

## 11. Safety Boundaries

Please preserve these boundaries:

```text
1. Do not modify cockpit_tk.py in this request.
2. Do not modify Run Full Plan.
3. Do not modify planning engine logic.
4. Do not modify explicit bridge capacity pipeline logic.
5. Do not add exports.
6. Do not execute ReplanCommand.
7. Do not implement price-cost-profit propagation.
8. Do not implement tariff simulation.
9. Do not implement cold-chain or shelf-life logic.
10. Do not add scenario selector.
11. Do not add GUI layout changes.
12. Do not commit outputs/ generated files.
```

This request is only:

```text
sample CSV + loader/attach validation tests
```

---

## 12. Expected Files Changed

Expected files:

```text
data/explicit_pipeline_backward_weekly_capability.csv
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

No other code files should need to change.

---

## 13. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Sample CSV rows added
3. Scenario / node / product / week / capability values used
4. Why scenario=base is used
5. Tests added
6. Test commands executed
7. Test results
8. Manual GUI validation status
9. Skipped tests and why
10. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
pipeline shape refactor
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Backward Weekly Capability Sample CSV Phase 2C
```
