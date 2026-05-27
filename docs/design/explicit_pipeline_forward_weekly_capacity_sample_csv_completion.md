# Explicit Pipeline Forward Weekly Capacity Sample CSV Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-28  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion of **Explicit Pipeline Forward Weekly Capacity Sample CSV Phase F3**.

Phase F3 added the first runtime sample CSV for:

```text
explicit_pipeline_forward_weekly_capacity
```

The target file was:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

The first success condition was:

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

This completion memo records that Phase F3 achieved that target and that the Explicit Pipeline Management Cockpit KPI View began to show actual diagnostic output.

---

## 2. Background

Before Phase F3, the project had completed:

```text
Forward weekly capacity ctx guard
Forward weekly capacity context design
Forward weekly capacity adapter Phase F1
Forward weekly capacity GUI preflight wiring Phase F2
```

The GUI preflight order was already:

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

However, before Phase F3, the forward CSV file did not yet exist.

Therefore, the forward attach helper could run, but it still returned:

```text
file_missing
```

and the Explicit KPI View still showed:

```text
Missing Context: explicit_pipeline_forward_weekly_capacity
```

Phase F3 supplied the missing runtime CSV.

---

## 3. Implemented Commit

The implementation was committed as:

```text
c0d9a42 Add explicit pipeline forward weekly capacity sample CSV
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Added

Phase F3 added two files:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

No GUI code was changed.

No planning engine code was changed.

No explicit bridge capacity pipeline code was changed.

No reporting stack code was changed.

---

## 5. Sample CSV Added

The sample CSV was added at:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Content:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

The sample uses:

```text
scenario = base
product = PACKAGED_RICE_STANDARD
node = MILL_EAST
capacity_type = P
week = 2027-W40, 2027-W41
capacity_lots = 5, 6
unit = lot
source = japanese_rice_case_sample
```

The semantic business source is:

```text
Japanese Rice Case / RICE_AS_IS
```

---

## 6. Scenario Choice

The sample uses:

```text
scenario = base
```

Reason:

```text
The GUI preflight helper calls maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
with default scenario="base".
```

This allows the sample CSV to be loaded without adding:

```text
scenario selector
GUI setting
helper argument wiring
new runtime configuration
```

The `source` and `note` fields preserve the Japanese Rice Case meaning.

---

## 7. Runtime Context Loaded

The CSV loads into the canonical product-first runtime shape:

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

Shape:

```text
product -> node -> capacity_type -> week -> capacity_lots
```

This is the expected context shape for:

```text
env.explicit_pipeline_forward_weekly_capacity
```

---

## 8. Relationship to Backward Capability CSV

The existing backward CSV is:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

The new forward CSV is:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Together, they supply the two required Explicit KPI context guard keys:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The focused test confirms:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

after both sample attach helpers run.

---

## 9. Tests Added

A new focused test file was added:

```text
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

It validates:

```text
sample CSV exists
sample CSV loads into exact expected product-first context
maybe attach helper attaches the context
record_count / product_count / node_count / capacity_type_count are correct
all sample rows use scenario=base
backward + forward sample CSVs together clear Explicit KPI ctx guard
```

---

## 10. Test Results

The following tests were executed successfully:

```bat
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
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
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py         4 passed
tests/test_explicit_pipeline_forward_capacity_context.py                  12 passed
tests/test_explicit_pipeline_capacity_context.py                          16 passed
tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py       3 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                             7 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                   8 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py               10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py           9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py    4 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                  7 passed
tests/test_explicit_pipeline_reporting_flags.py                           10 passed
tests/test_covid_vaccine_with_capacity_push.py                             1 passed
tests/test_japanese_rice_case_smoke.py                                     1 passed
```

Total observed result:

```text
92 passed
```

---

## 11. Manual GUI Validation

Manual GUI validation was performed with:

```bat
python -m main
```

Manual steps:

```text
1. Explicit KPI ON.
2. Run Full Plan.
3. Open Explicit KPI View.
4. Inspect Summary / Graphs / Top Issues / Messages.
```

Observed result:

```text
Run Full Plan completed.
Explicit KPI View displayed Available = Yes.
Explicit Pipeline Result = Yes.
Capacity Report = Yes.
Issue Candidates = Yes.
Cost / KPI Bundle = Yes.
```

The previous missing context diagnostic:

```text
explicit_pipeline_forward_weekly_capacity
```

was no longer shown as a missing context key.

The cockpit began to display actual diagnostic values.

---

## 12. GUI Output Observed

The Summary tab displayed diagnostic output including:

```text
Total Business Impact: 0.00
Capacity Violations: 0 records
Management Issues: 92,422 issues
Health Warnings: 0 warnings
Replan Candidates: 0 candidates
```

The lower summary rows showed:

```text
Available: Yes
Explicit Pipeline Result: Yes
Capacity Report: Yes
Issue Candidates: Yes
Cost / KPI Bundle: Yes
Lot Exceptions: 92,422
Planning Issues: 92,422
Management Issues: 92,422
Warnings: 184,844
Errors: 0
```

The Graphs tab displayed:

```text
Issue Severity Distribution
warning = 184,844
```

The Top Issues tab displayed rows with:

```text
severity = warning
issue_type = blocked_lot
impact_category = service_risk
product = IPHONE_NM_2028_BASE
estimated impact = 0.00
```

The Messages tab displayed:

```text
Cost / KPI values are directional scenario estimates, not formal accounting values.
Double counting may be possible depending on assumptions.
Export results are not available. Export flags may be off.
```

Next review actions included:

```text
Review high impact management issues.
Check capacity violations with high capacity risk.
```

---

## 13. Meaning of This Milestone

Before Phase F3:

```text
The forward attach helper existed,
but no default CSV existed.
The ctx guard still reported explicit_pipeline_forward_weekly_capacity as missing.
```

After Phase F3:

```text
The default forward capacity CSV exists.
The forward attach helper can attach context.
Backward + forward contexts clear ctx guard.
The Explicit KPI pipeline is allowed to run.
The cockpit begins to show diagnostic output.
```

This is a significant milestone.

It means the path from:

```text
Explicit KPI ON
    ↓
preflight
    ↓
ctx guard
    ↓
explicit pipeline
    ↓
view model
    ↓
GUI cockpit view
```

is now operational.

---

## 14. Safety Boundaries Preserved

Phase F3 intentionally did not implement:

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

Only the sample CSV and focused tests were added.

---

## 15. Current Limitations

The cockpit is now producing output, but several interpretation issues remain.

Observed:

```text
Management Issues: 92,422
Warnings: 184,844
Top Issues: blocked_lot / service_risk
Cost / KPI Impact Composition: not available
Weekly Issue Count: not available
```

These are not Phase F3 failures.

They are the next diagnostic targets.

Likely areas to inspect:

```text
scenario alignment between iPhone GUI default and Japanese Rice sample
explicit bridge capacity pipeline issue generation rules
blocked_lot aggregation logic
duplicate warning generation
cost / KPI impact composition data requirements
week-level issue aggregation data requirements
```

---

## 16. Scenario Alignment Caveat

The GUI default product observed in manual validation was:

```text
IPHONE_NM_2028_BASE
```

The forward sample CSV product is:

```text
PACKAGED_RICE_STANDARD
```

Therefore, the sample CSV has succeeded as a **ctx guard / runtime presence validation sample**.

It may not yet be semantically aligned with the active iPhone GUI scenario.

This is expected at this stage.

---

## 17. Recommended Next Design Topic

The next diagnostic design topic should be:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
```

Purpose:

```text
1. Verify explicit_bridge_capacity_pipeline.py runtime shape expectations.
2. Confirm how the pipeline maps selected GUI product to capacity context.
3. Explain why iPhone product produces blocked_lot issues with Rice sample CSV present.
4. Check whether warning counts are duplicated by product/node/week/lot expansion.
5. Identify the minimum scenario-aligned sample needed for meaningful KPI output.
```

This topic should be treated as the next diagnosis phase, not as a Phase F3 bug.

---

## 18. Recommended Next Engineering Work

Before changing behavior, inspect and document:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_reporting_stack.py
tests around explicit pipeline issue generation
```

Questions:

```text
1. What exact forward capacity context shape is consumed?
2. Does capacity context filter by selected product?
3. What happens when selected product is absent from capacity context?
4. Why are blocked_lot issues generated for IPHONE_NM_2028_BASE?
5. Why are warnings exactly twice management issues?
6. Why are weekly issue counts unavailable?
7. Why is Cost / KPI Impact Composition unavailable?
```

---

## 19. Completion Criteria

Phase F3 is complete because:

```text
[OK] data/explicit_pipeline_forward_weekly_capacity.csv exists
[OK] CSV loads into product-first context
[OK] maybe attach helper attaches the context
[OK] scenario column is base
[OK] backward + forward sample CSVs together clear ctx guard
[OK] tests pass
[OK] commit / push completed
[OK] manual GUI validation shows Explicit KPI pipeline result available
[OK] cockpit begins to display diagnostic output
```

---

## 20. Summary

Explicit Pipeline Forward Weekly Capacity Sample CSV Phase F3 is complete.

The milestone commit is:

```text
c0d9a42 Add explicit pipeline forward weekly capacity sample CSV
```

The system now reaches the next level:

```text
No longer missing forward capacity context.
Explicit KPI result is available.
Capacity report is available.
Issue candidates are available.
Cost / KPI bundle is available.
Graphs and issue tables begin to render.
```

This is the first visible moment where the Explicit Pipeline Management Cockpit begins to behave like a management diagnostic cockpit.

The next work is not to prove that the pipeline can speak.

It can now speak.

The next work is to understand what it is saying.
