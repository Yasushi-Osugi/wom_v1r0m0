# Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-28  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the next diagnostic design topic after Phase F3:

```text
Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment
```

Phase F3 succeeded in moving the Explicit Pipeline Management Cockpit KPI View from:

```text
missing context / unavailable
```

to:

```text
available diagnostic output
```

The current question is no longer:

```text
Can the pipeline speak?
```

The current question is:

```text
What is the pipeline saying, and is it aligned with the active WOM scenario?
```

This memo defines the diagnostic work needed to interpret the newly visible output.

---

## 2. Background

The following phases have been completed:

```text
Forward weekly capacity ctx guard
Forward weekly capacity context design
Forward weekly capacity adapter Phase F1
Forward weekly capacity GUI preflight wiring Phase F2
Forward weekly capacity sample CSV Phase F3
```

The key runtime files now include:

```text
data/explicit_pipeline_backward_weekly_capability.csv
data/explicit_pipeline_forward_weekly_capacity.csv
```

The key runtime ctx keys are now present:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The Explicit KPI View now shows:

```text
Available = Yes
Explicit Pipeline Result = Yes
Capacity Report = Yes
Issue Candidates = Yes
Cost / KPI Bundle = Yes
```

This means the first visible integration path is operational.

---

## 3. Observed Manual GUI Output

Manual GUI validation after Phase F3 showed the cockpit producing output.

Observed Summary tab values included:

```text
Total Business Impact: 0.00
Capacity Violations: 0 records
Management Issues: 92,422 issues
Health Warnings: 0 warnings
Replan Candidates: 0 candidates
```

The lower summary rows showed:

```text
Product: IPHONE_NM_2028_BASE
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

Graphs tab showed:

```text
Issue Severity Distribution
warning = 184,844
```

Top Issues tab showed rows like:

```text
severity = warning
issue_type = blocked_lot
impact_category = service_risk
product = IPHONE_NM_2028_BASE
estimated impact = 0.00
```

Messages tab showed:

```text
Cost / KPI values are directional scenario estimates, not formal accounting values.
Double counting may be possible depending on assumptions.
Export results are not available. Export flags may be off.
```

This is an important milestone, but it also exposes the next design question:

```text
Why is an iPhone product generating many blocked_lot issues while the sample capacity CSV is Japanese Rice Case based?
```

---

## 4. Immediate Interpretation

The current result should be interpreted as:

```text
ctx guard and pipeline availability are working
```

not yet as:

```text
scenario-aligned business diagnostic is complete
```

The pipeline is now running with enough context to produce output.

However, the sample context is deliberately small and semantically based on Japanese Rice Case:

```text
PACKAGED_RICE_STANDARD
MILL_EAST
P
2027-W40 / 2027-W41
```

while the GUI active product observed in manual validation is:

```text
IPHONE_NM_2028_BASE
```

This means the current output may be a **presence / availability success** rather than a **business scenario alignment success**.

---

## 5. Main Diagnostic Questions

The next diagnostic phase should answer these questions:

```text
1. What exact shape does explicit_bridge_capacity_pipeline.py consume?
2. Does the pipeline filter capacity context by selected product?
3. What happens when selected product is not present in capacity context?
4. Why are blocked_lot issues generated for IPHONE_NM_2028_BASE?
5. Why are warnings exactly twice management issues?
6. Why is Capacity Violations = 0 while Management Issues = 92,422?
7. Why is Cost / KPI Impact Composition unavailable?
8. Why is Weekly Issue Count unavailable?
9. What is the minimum scenario-aligned sample needed for meaningful KPI output?
```

---

## 6. Candidate Root Causes

### 6.1 Scenario mismatch

Current GUI selected product:

```text
IPHONE_NM_2028_BASE
```

Current forward sample CSV product:

```text
PACKAGED_RICE_STANDARD
```

If the pipeline does not strictly filter capacity context by product, it may produce generic issue candidates while still labeling the active product as iPhone.

If it does filter by product but treats missing product capacity as zero capacity, then all active iPhone lots may become blocked.

This would explain:

```text
blocked_lot
service_risk
large issue count
capacity violations = 0
```

because the issue may be generated as a service-risk planning issue rather than a formal capacity-violation record.

---

### 6.2 Product capacity absence treated as blocking

If active product capacity is absent from:

```text
explicit_pipeline_forward_weekly_capacity
```

the pipeline may interpret absence as:

```text
available capacity = 0
```

This may block every lot that needs capacity.

This would generate many:

```text
blocked_lot
```

issues.

---

### 6.3 Duplicate issue expansion

Observed relationship:

```text
Management Issues = 92,422
Warnings = 184,844
```

This suggests:

```text
Warnings = 2 × Management Issues
```

Potential causes:

```text
one issue candidate becomes two warnings
lot exception + planning issue both counted as warnings
issue candidate and management issue layers both emit warning records
graph severity count sums multiple issue lists
```

This requires inspection of the issue aggregation logic.

---

### 6.4 Week-level issue data missing

Graphs tab shows:

```text
Weekly Issue Count: No week-level issue data is available.
```

This may mean one of the following:

```text
issue records do not include week field
week field exists but is blank
graph view expects a different key name
issue candidates are summary-level, not week-level
```

This should be checked in the view model and issue candidate schema.

---

### 6.5 Cost / KPI impact composition missing

Graphs tab shows:

```text
No Cost / KPI impact composition is available.
```

Possible causes:

```text
cost_kpi_bundle exists but lacks composition breakdown
estimated impact values are all zero
issue candidates have estimated_impact = 0.00
cost master / price data is not linked to blocked_lot issues
composition graph expects category-level impact records
```

This is likely a downstream Cost/KPI enrichment issue, not a capacity context issue.

---

## 7. Files to Inspect

The next diagnostic work should inspect the following files:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_reporting_stack.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_forward_capacity_context.py
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Focus should be on:

```text
ctx shape consumed by the pipeline
issue candidate generation
blocked lot logic
product filtering
capacity default behavior
summary counts
graph view data expectations
cost/kpi composition requirements
```

---

## 8. Runtime Contexts to Compare

### 8.1 Backward capability context

Current backward context shape:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

Example:

```python
{
    "MILL_EAST": {
        "PACKAGED_RICE_STANDARD": {
            "2027-W40": 5,
            "2027-W41": 6,
        }
    }
}
```

### 8.2 Forward weekly capacity context

Current forward context shape:

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

### 8.3 Active GUI product

Observed active product:

```text
IPHONE_NM_2028_BASE
```

The diagnostic should verify whether the pipeline is using:

```text
selected GUI product
```

to select capacity context.

---

## 9. Expected Correct Behavior Options

There are several possible correct behaviors when selected product is missing from forward capacity context.

### Option A: Strict missing product behavior

If selected product is absent from capacity context:

```text
explicit pipeline should return unavailable or diagnostic warning
```

Example message:

```text
Forward weekly capacity context is present, but selected product IPHONE_NM_2028_BASE is not found.
```

This avoids interpreting absence as zero capacity.

### Option B: Zero-capacity behavior

If selected product is absent:

```text
capacity = 0
all required lots are blocked
```

This is mathematically valid but can be misleading unless clearly reported.

If this behavior is intended, the cockpit should explain:

```text
No forward capacity found for selected product; all lots are treated as blocked.
```

### Option C: Product-independent capacity behavior

If capacity is treated as global:

```text
capacity can be applied across products
```

This is not currently recommended for WOM because product-specific capacity is usually required.

---

## 10. Recommended Near-Term Policy

Recommended near-term policy:

```text
Do not silently treat missing selected product capacity as zero without diagnostic explanation.
```

Recommended diagnostic behavior:

```text
if selected_product not in explicit_pipeline_forward_weekly_capacity:
    produce a clear scenario alignment diagnostic
    avoid massive blocked_lot explosion unless user explicitly chooses zero-capacity semantics
```

Before implementing behavior changes, the current pipeline behavior should be documented with characterization tests.

---

## 11. Week Bucket Alignment

A key diagnostic issue is week-key alignment.

The sample CSV uses:

```text
2027-W40
2027-W41
```

The GUI plan debug logs often show integer weeks such as:

```text
27
28
29
30
31
32
33
34
```

If the explicit pipeline compares these directly, the capacity rows may never match the plan weeks.

Possible strategies:

```text
1. Use integer week keys in scenario-aligned sample CSV.
2. Add week-bucket normalization adapter.
3. Add explicit mapping between ISO week buckets and WOM internal week indexes.
4. Treat sample CSV as presence-only and create scenario-aligned integer-week test separately.
```

Recommended next step:

```text
inspect explicit_bridge_capacity_pipeline.py to see how week keys are looked up.
```

---

## 12. Product Alignment

The sample CSV product is:

```text
PACKAGED_RICE_STANDARD
```

The GUI selected product is:

```text
IPHONE_NM_2028_BASE
```

For meaningful cockpit output, one of the following is needed:

```text
1. Run a Japanese Rice Case scenario in GUI.
2. Add an iPhone-aligned forward capacity sample.
3. Make the cockpit explicitly report scenario mismatch.
```

Recommended short-term approach:

```text
add diagnostics before adding more sample data
```

Reason:

```text
If the pipeline is currently interpreting missing iPhone capacity as blocked all lots, adding iPhone sample data may hide the root behavior.
```

---

## 13. Node Alignment

The sample CSV node is:

```text
MILL_EAST
```

The iPhone plan observed nodes include:

```text
MOM_final_assy_ASIA
MOM_final_assy_EURO
DAD_FAS_APAC
DAD_FAS_EURO
DAD_FAS_AMER
CS_CN_PREMIUM
```

If the explicit pipeline expects capacity at MOM or DAD nodes, then `MILL_EAST` will not align.

The next diagnostic should determine which node level the pipeline consumes:

```text
MOM node?
DAD node?
leaf node?
capacity owner node?
process node?
```

---

## 14. Capacity Type Alignment

The sample CSV uses:

```text
capacity_type = P
```

The issue table showed a `capacity_type` column, but visible values appeared blank.

This may mean:

```text
capacity_type is not propagated into issue candidates
capacity_type is missing on blocked_lot issues
capacity_type is not shown due to table column width
capacity_type does not match expected key
```

This should be checked in the issue candidate schema.

---

## 15. Issue Count Interpretation

Observed:

```text
Lot Exceptions = 92,422
Planning Issues = 92,422
Management Issues = 92,422
Warnings = 184,844
```

Potential count structure:

```text
lot_exception_count = blocked lots
planning_issue_count = converted from lot exceptions
management_issue_count = converted from planning issues
warning_count = planning issues + management issues
```

If so, the count is internally consistent but visually alarming.

Recommended improvement:

```text
show issue count lineage in diagnostics
```

Example:

```text
92,422 blocked lots generated 92,422 planning issues and 92,422 management issues.
Warning count includes both layers.
```

This would prevent the cockpit from looking like it double-counted accidentally.

---

## 16. KPI Impact Interpretation

Observed:

```text
Total Business Impact: 0.00
estimated impact: 0.00
```

This likely means one of:

```text
impact estimation is not connected to product money data
service_risk penalty is zero
blocked_lot issue has no cost mapping
cost/kpi bundle exists but values are directional zero
```

This should be diagnosed separately from capacity shape.

Recommended next question:

```text
What input is required for blocked_lot service_risk to have non-zero estimated impact?
```

---

## 17. Diagnostic Tests to Add Later

Potential future tests:

### 17.1 Selected product absent from capacity context

Given:

```text
selected_product = IPHONE_NM_2028_BASE
capacity context only has PACKAGED_RICE_STANDARD
```

Expected behavior should be defined explicitly:

```text
either scenario_alignment_warning
or zero-capacity blocked_lot behavior
```

The test should lock down whichever policy is chosen.

### 17.2 Selected product present in capacity context

Given:

```text
selected_product = IPHONE_NM_2028_BASE
capacity context has IPHONE_NM_2028_BASE
```

Expected:

```text
capacity report uses matching product context
blocked_lot count reflects actual capacity shortage
```

### 17.3 Week key mismatch

Given capacity weeks:

```text
2027-W40
2027-W41
```

and plan weeks:

```text
integer week index 27, 28, ...
```

Expected:

```text
clear week alignment behavior
```

---

## 18. Proposed Next Codex Work

Recommended next document:

```text
docs/codex_requests/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_request.md
```

This request should ask Codex to inspect and document current behavior first, not immediately change logic.

Suggested deliverable:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
```

or a small diagnostic test suite.

Potential scope:

```text
1. Inspect explicit_bridge_capacity_pipeline.py.
2. Identify expected ctx shapes.
3. Identify selected product handling.
4. Identify missing product behavior.
5. Identify week-key handling.
6. Identify issue count lineage.
7. Add non-invasive characterization tests if possible.
```

---

## 19. Recommended No-Change Diagnostic First

Before any behavioral patch, prefer:

```text
read code
add characterization tests
document observed behavior
```

Avoid immediately changing:

```text
capacity matching semantics
zero capacity behavior
issue aggregation
cost/kpi enrichment
graph view schema
```

The current cockpit has just started speaking.

The next step is to listen carefully before teaching it new words.

---

## 20. Completion Criteria for This Diagnostic Phase

This design phase should be considered complete when the team can answer:

```text
1. What shape does the pipeline consume?
2. What product does the pipeline evaluate?
3. What happens when selected product capacity is absent?
4. What week key format is expected?
5. Which nodes are expected to have capacity?
6. Why does the current run generate 92,422 management issues?
7. Why are warnings 184,844?
8. Why are cost impact composition and weekly issue count unavailable?
9. What exact sample data is needed for a semantically aligned next demo?
```

---

## 21. Summary

Phase F3 succeeded.

The Explicit Pipeline Management Cockpit now speaks.

The next diagnostic topic is not about missing context.

It is about alignment:

```text
pipeline shape alignment
scenario alignment
product alignment
node alignment
week alignment
issue count lineage
KPI impact enrichment
```

The immediate recommended next step is to inspect and characterize:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

and related reporting/view-model code before changing behavior.

This will turn the current first voice of the cockpit into a trustworthy management diagnostic language.
