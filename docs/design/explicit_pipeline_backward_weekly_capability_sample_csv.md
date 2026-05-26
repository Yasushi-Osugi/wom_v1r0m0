# Explicit Pipeline Backward Weekly Capability Sample CSV Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_sample_csv.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`  
**Scenario:** Japanese Rice Case

---

## 1. Purpose

This memo defines Phase 2C for:

```text
explicit_pipeline_backward_weekly_capability
```

Phase 2C defines a scenario-specific sample capability CSV for the WOM GUI / Explicit KPI preflight path.

The target file is:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

The goal is to provide a valid capability context so that:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
GUI preflight loads capability CSV
    ↓
env.explicit_pipeline_backward_weekly_capability is attached
    ↓
ctx guard no longer reports:
        explicit_pipeline_backward_weekly_capability
```

This memo explicitly uses the **Japanese Rice Case** as the first sample scenario.

---

## 2. Scenario Decision

For Phase 2C, the target WOM scenario is:

```text
Japanese Rice Case
```

Reason:

```text
1. The current branch / local directory name includes Rice Case context.
2. Existing tests include Japanese Rice Case smoke coverage.
3. The current development sequence started from the capacity-aware Explicit KPI cockpit flow and has repeatedly used the Japanese Rice Case as a practical validation target.
4. Rice supply chain is a suitable MVP scenario for MOM capacity, weekly lot flow, and bottleneck demonstration.
```

Therefore, this memo assumes:

```text
sample capability CSV should match the node / product / week conventions used by the Japanese Rice Case.
```

If later another scenario is selected, the same CSV schema can be reused with scenario-specific rows.

---

## 3. Important Caveat

This memo defines the design and validation approach.

Before committing the actual CSV file, the following values must be confirmed from the repository:

```text
1. actual MOM node id
2. actual product name / product id
3. actual week bucket format
4. expected planning horizon
5. reasonable capability_lots values
```

Do not guess these values if they can be extracted from the repo.

A wrong node or product id may attach the context successfully but still produce no meaningful explicit pipeline output.

---

## 4. Current Runtime Path

The current runtime path is:

```text
Explicit KPI ON checked
    ↓
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
    ↓
apply_explicit_pipeline_kpi_demo_flags(...)
    ↓
WOMCockpit._maybe_attach_explicit_pipeline_backward_weekly_capability()
    ↓
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
    ↓
load data/explicit_pipeline_backward_weekly_capability.csv if present
    ↓
attach env.explicit_pipeline_backward_weekly_capability if non-empty
    ↓
ctx guard check
```

Therefore, if the sample CSV is correct and non-empty, the preflight should attach:

```python
env.explicit_pipeline_backward_weekly_capability
```

before the ctx guard runs.

---

## 5. CSV Target Path

Recommended runtime CSV path:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

This is the default path already used by:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

This file should be committed only when its rows are confirmed to match the Japanese Rice Case.

---

## 6. CSV Schema

The CSV schema is:

```text
scenario,node,product,week,capability_lots,capability_type,unit,source,note
```

Required fields for the adapter:

```text
node
product
week
capability_lots
```

Recommended values:

```text
scenario = japanese_rice_case or base
capability_type = output
unit = lot
source = sample
```

The current helper default scenario is:

```text
base
```

Therefore, for immediate GUI preflight compatibility, the safest MVP is:

```text
scenario = base
```

A later scenario selector can support:

```text
scenario = japanese_rice_case
```

---

## 7. Recommended Scenario Naming

There are two possible scenario naming choices.

### Option A: scenario=base

```text
scenario=base
```

Advantages:

```text
works with current helper default without GUI change
simple
safest for Phase 2C
```

Disadvantages:

```text
less explicit that this file is for Japanese Rice Case
```

### Option B: scenario=japanese_rice_case

```text
scenario=japanese_rice_case
```

Advantages:

```text
clear scenario identity
better long-term scenario management
```

Disadvantages:

```text
requires helper call to use scenario="japanese_rice_case"
or future GUI scenario selector
```

Recommended Phase 2C:

```text
Use scenario=base in the runtime CSV,
and document in source/note that this is Japanese Rice Case sample data.
```

This avoids changing the helper or GUI again.

---

## 8. Values to Confirm from Repo

Before creating the actual CSV, inspect the repo for the Japanese Rice Case values.

Recommended commands:

```bat
findstr /S /N /I /C:"japanese" tests\*.py pysi\*.py data\*.csv docs\*.md
findstr /S /N /I /C:"rice" tests\*.py pysi\*.py data\*.csv docs\*.md
findstr /S /N /I /C:"MOM" data\*.csv pysi\master_data\*.csv tests\*.py
findstr /S /N /I /C:"RICE" data\*.csv pysi\master_data\*.csv tests\*.py
```

Also inspect the smoke test:

```bat
type tests\test_japanese_rice_case_smoke.py
```

If the test uses helper fixtures or data paths, inspect those files too.

---

## 9. MOM Node ID Confirmation

The sample CSV must use the actual MOM node id used by the Japanese Rice Case.

Possible patterns may include names like:

```text
MOM
MOM_JP
MOM_JP_FG
JPN_MOM
RICE_MOM
```

But these are examples only.

The actual value must be confirmed from repo data or test fixtures.

Recommended confirmation source priority:

```text
1. Japanese Rice Case test fixture
2. data CSV used by python -m main
3. node master CSV
4. scenario runner code
5. GUI env initialization code
```

---

## 10. Product Name / Product ID Confirmation

The sample CSV must use the actual product name / product id used by the Japanese Rice Case.

Possible patterns may include:

```text
RICE
RICE_5KG
JAPANESE_RICE
KOME
```

But these are examples only.

The actual value must be confirmed.

Recommended confirmation commands:

```bat
findstr /S /N /I /C:"product" data\*.csv pysi\master_data\*.csv tests\test_japanese_rice_case_smoke.py
findstr /S /N /I /C:"rice" data\*.csv pysi\master_data\*.csv tests\test_japanese_rice_case_smoke.py
```

---

## 11. Week Bucket Format Confirmation

The adapter preserves the week key exactly as provided by CSV.

Therefore the sample CSV must match the week format expected by the explicit pipeline.

Possible week formats:

```text
202601
202602
W001
1
2
```

The actual format must be confirmed from the Japanese Rice Case planning data.

Recommended commands:

```bat
findstr /S /N /I /C:"2026" data\*.csv tests\*.py
findstr /S /N /I /C:"week" data\*.csv tests\*.py pysi\*.py
```

If the existing planning pipeline uses integer week indices, sample CSV should use integer week keys.

If existing reporting uses `YYYYWW`, sample CSV should use `YYYYWW`.

---

## 12. Capability Lots Policy

The sample `capability_lots` should be chosen to demonstrate capacity-aware behavior.

There are three useful profiles.

### 12.1 Capacity Enough

```text
capability_lots >= demand lots
```

Purpose:

```text
verify context attach and guard pass without bottleneck
```

### 12.2 Mild Bottleneck

```text
capability_lots slightly below demand lots
```

Purpose:

```text
verify capacity shortage / issue candidate path
```

### 12.3 Strong Bottleneck

```text
capability_lots significantly below demand lots
```

Purpose:

```text
make bottleneck visible in capacity report / KPI view
```

Recommended Phase 2C MVP:

```text
start with Capacity Enough or Mild Bottleneck
```

Reason:

```text
first objective is to verify that the missing ctx diagnostic disappears.
A strong bottleneck can be introduced later once the pipeline path is stable.
```

---

## 13. Initial Sample CSV Template

Do not commit this exact template until node/product/week are confirmed.

Template:

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,<ACTUAL_MOM_NODE_ID>,<ACTUAL_PRODUCT>,<ACTUAL_WEEK_1>,100,output,lot,japanese_rice_case_sample,MOM output capability sample
base,<ACTUAL_MOM_NODE_ID>,<ACTUAL_PRODUCT>,<ACTUAL_WEEK_2>,100,output,lot,japanese_rice_case_sample,MOM output capability sample
base,<ACTUAL_MOM_NODE_ID>,<ACTUAL_PRODUCT>,<ACTUAL_WEEK_3>,100,output,lot,japanese_rice_case_sample,MOM output capability sample
```

After confirmation, replace placeholders with actual values.

---

## 14. Recommended Sample CSV Shape

The first committed sample should be small.

Recommended row count:

```text
3 to 8 rows
```

Reason:

```text
small enough to inspect manually
large enough to cover several weeks
```

Recommended profile:

```text
same MOM node
same product
multiple weeks
```

Example after confirmation:

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,ACTUAL_MOM_NODE,ACTUAL_PRODUCT,ACTUAL_WEEK_1,100,output,lot,japanese_rice_case_sample,Japanese Rice Case MOM output capability
base,ACTUAL_MOM_NODE,ACTUAL_PRODUCT,ACTUAL_WEEK_2,100,output,lot,japanese_rice_case_sample,Japanese Rice Case MOM output capability
base,ACTUAL_MOM_NODE,ACTUAL_PRODUCT,ACTUAL_WEEK_3,80,output,lot,japanese_rice_case_sample,Japanese Rice Case mild bottleneck
```

The final values should not include placeholder text.

---

## 15. Local Validation Before Commit

After creating the sample CSV locally, validate the loader before running GUI.

Recommended command:

```bat
python -c "from pysi.plan.explicit_pipeline_capacity_context import load_explicit_pipeline_backward_weekly_capability_csv; import pprint; pprint.pp(load_explicit_pipeline_backward_weekly_capability_csv('data/explicit_pipeline_backward_weekly_capability.csv'))"
```

Expected result:

```python
{
    "ACTUAL_MOM_NODE": {
        "ACTUAL_PRODUCT": {
            "ACTUAL_WEEK_1": 100,
            "ACTUAL_WEEK_2": 100,
            "ACTUAL_WEEK_3": 80,
        }
    }
}
```

Then validate attach helper:

```bat
python -c "from types import SimpleNamespace; from pysi.plan.explicit_pipeline_capacity_context import maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv; env=SimpleNamespace(); print(maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)); print(hasattr(env, 'explicit_pipeline_backward_weekly_capability')); print(env.explicit_pipeline_backward_weekly_capability)"
```

Expected:

```text
attached=True
hasattr(...) = True
non-empty context printed
```

---

## 16. Manual GUI Validation

After the sample CSV is committed or created locally:

```bat
python -m main
```

Manual flow:

```text
1. Confirm Explicit KPI ON checkbox exists
2. Check Explicit KPI ON
3. Run Full Plan
4. Open Explicit KPI View
5. Confirm that missing diagnostic for explicit_pipeline_backward_weekly_capability disappears
```

Expected first success condition:

```text
The missing key explicit_pipeline_backward_weekly_capability is no longer shown.
```

This is the minimum Phase 2C success condition.

---

## 17. If KPI View Still Looks Empty

Even after the missing context diagnostic disappears, the Explicit KPI View may still be empty or incomplete.

Possible causes:

```text
node id mismatch
product mismatch
week key mismatch
capability context shape mismatch
other implicit pipeline expectations
other missing runtime data
capacity report not generated
issue candidates not generated
cost/KPI bundle not generated
```

Recommended investigation:

```bat
findstr /S /N /C:"explicit_pipeline_backward_weekly_capability" pysi\*.py tests\*.py
findstr /S /N /C:"maybe_run_explicit_bridge_capacity_pipeline" pysi\*.py tests\*.py
findstr /S /N /C:"backward_weekly_capability" pysi\*.py tests\*.py
```

Also inspect:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 18. Test Strategy

For Phase 2C implementation, add or update tests only if the sample CSV is committed.

Potential test:

```text
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

Test coverage:

```text
sample CSV exists
sample CSV loads non-empty context
sample CSV scenario=base loads with default helper
context has at least one node/product/week
attach helper returns attached=True
```

This test should not require GUI.

---

## 19. Commit Scope for Phase 2C

Recommended files if sample CSV is committed:

```text
data/explicit_pipeline_backward_weekly_capability.csv
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

Optional documentation:

```text
docs/design/explicit_pipeline_backward_weekly_capability_sample_csv_completion.md
```

Do not include generated output CSVs unless intentional.

Do not include `outputs/` generated files.

---

## 20. Safety Boundaries

Phase 2C should not implement:

```text
new GUI widgets
scenario selector
planning engine changes
export execution
replan execution
price-cost-profit propagation
tariff calculation
cold-chain shelf-life logic
process-level capacity
database persistence
```

This phase is only:

```text
scenario-specific sample capability CSV
loader validation
manual GUI validation
```

---

## 21. Completion Criteria

Phase 2C is complete when:

```text
[OK] Japanese Rice Case is explicitly selected as the sample scenario
[OK] actual MOM node id is confirmed
[OK] actual product name/id is confirmed
[OK] actual week bucket format is confirmed
[OK] sample CSV is created with real values
[OK] loader returns non-empty canonical context
[OK] attach helper returns attached=True
[OK] GUI preflight can consume the sample CSV
[OK] missing diagnostic for explicit_pipeline_backward_weekly_capability disappears in manual GUI validation
```

If the Explicit KPI View still does not populate full reports, that should be treated as the next diagnostic step, not failure of the sample CSV phase.

---

## 22. Summary

For Phase 2C, the selected scenario is:

```text
Japanese Rice Case
```

The objective is to create a real sample CSV:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

using actual Japanese Rice Case values:

```text
MOM node id
product name / id
week bucket format
capability_lots
```

The first success condition is not full KPI richness.

The first success condition is:

```text
Explicit KPI ON + Run Full Plan no longer reports missing:
explicit_pipeline_backward_weekly_capability
```

This phase turns the preflight bridge into a visible scenario validation path.
