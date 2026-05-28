# Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment Observation Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-28  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion of the **Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment Observation** phase.

This phase was not a behavior-fix phase. It was an observation and characterization phase intended to capture the first **WOM Knowledge Increment** for:

```text
Explicit Pipeline Capacity Context
```

The purpose was to understand what the Explicit Pipeline Management Cockpit was saying after Phase F3 made it speak.

---

## 2. Background

Phase F3 successfully added:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

and the cockpit began to display diagnostic output.

Observed GUI state after Phase F3:

```text
Available = Yes
Explicit Pipeline Result = Yes
Capacity Report = Yes
Issue Candidates = Yes
Cost / KPI Bundle = Yes
```

However, the cockpit also showed:

```text
Management Issues: 92,422
Warnings: 184,844
Top Issues: blocked_lot / service_risk
Cost / KPI Impact Composition: not available
Weekly Issue Count: not available
```

The question moved from:

```text
Can the pipeline run?
```

to:

```text
What is the pipeline actually saying?
```

---

## 3. Implemented Commit

The observation memo and characterization tests were committed as:

```text
1209199 Add explicit pipeline capacity shape observation and characterization tests
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Added

The following files were added:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

No runtime business logic was changed.

No planning engine behavior was changed.

No GUI behavior was changed.

No CSV sample data was changed.

---

## 5. Role of This Phase

This phase should be understood as:

```text
inspection + characterization + WOM Knowledge Increment creation
```

rather than:

```text
bug fix
feature implementation
pipeline refactor
scenario alignment correction
```

The observation memo is the **カルテ**.

The characterization tests are the **録音装置**.

Together, they record how WOM currently interprets Explicit Pipeline Capacity Context.

---

## 6. Pipeline Entry Points Identified

The observation memo identified the explicit bridge capacity pipeline entry points:

```text
maybe_run_explicit_bridge_capacity_pipeline_from_env(...)
maybe_run_explicit_bridge_capacity_pipeline(...)
run_explicit_bridge_capacity_pipeline(...)
```

These functions form the main path from:

```text
env / ctx
    ↓
explicit bridge capacity pipeline
    ↓
capacity report / issue candidates / cost-kpi bundle
    ↓
cockpit view model
```

---

## 7. Required Context Keys

The current Explicit KPI demo guard requires:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The Phase F3 sample CSV work made both keys available.

The observation phase then focused on how those keys are actually interpreted once the guard passes.

---

## 8. Forward Capacity Shape Observation

The producer-side forward capacity context shape is:

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

Codex observed an important shape-consumption issue:

```text
producer path provides week-key map
consumer path expects list-indexed weeks
```

This creates a semantic mismatch / exception risk depending on the runtime path.

The new characterization test records that the current dict-week shape can raise `KeyError` in the observed consumer path.

---

## 9. Selected Product Handling

The observation memo found that the pipeline product comes from the explicit pipeline context argument:

```text
explicit_pipeline_product
```

rather than reading `env.product_selected` directly inside the pipeline function.

The selected product is used to top-level-filter the forward capacity map.

This is important because the observed GUI product was:

```text
IPHONE_NM_2028_BASE
```

while the forward sample CSV product is:

```text
PACKAGED_RICE_STANDARD
```

This mismatch is now formally recorded as a scenario / product alignment issue.

---

## 10. Missing Selected Product Behavior

Codex observed that when the selected product is absent from the forward capacity context, the current layer does not produce a clear explicit unavailable marker.

The behavior is better described as:

```text
capacity lookup falls through / fails to match
```

rather than:

```text
clear scenario alignment diagnostic
```

This becomes a candidate for future operational semantics improvement:

```text
If selected product is absent from forward capacity context,
produce an explicit scenario alignment diagnostic.
```

No behavior change was made in this phase.

---

## 11. Week-Key Handling

The observation phase confirmed that there is no general normalization between:

```text
ISO-like week keys:
    2027-W40
    2027-W41

internal integer week indexes:
    27
    28
    29
    ...
```

This means week-key alignment remains an important next diagnostic and design topic.

---

## 12. Node Matching Behavior

The current consumer path expects exact node-name matching.

There is no semantic mapping at this layer from:

```text
MILL_EAST
```

to iPhone scenario nodes such as:

```text
MOM_final_assy_ASIA
DAD_FAS_APAC
DAD_FAS_EURO
DAD_FAS_AMER
```

This confirms that the current sample CSV is valid for ctx presence validation, but not yet semantically aligned with the active iPhone GUI scenario.

---

## 13. Capacity Type Behavior

The forward capacity context builder normalizes capacity type aliases to:

```text
P
S
I
```

However, the observed `blocked_lot` issue rows do not carry `capacity_type`.

Therefore, blank `capacity_type` values in the issue table are expected for current blocked-lot issue rows.

---

## 14. blocked_lot Issue Generation

The observed top issue pattern was:

```text
issue_type = blocked_lot
impact_category = service_risk
product = IPHONE_NM_2028_BASE
estimated impact = 0.00
```

This indicates that the pipeline is generating service-risk issues for blocked lots, but the current cost / impact enrichment is not assigning non-zero monetary impact.

---

## 15. Issue Count Lineage

Observed GUI result:

```text
Lot Exceptions = 92,422
Planning Issues = 92,422
Management Issues = 92,422
Warnings = 184,844
```

Codex characterized the likely lineage as:

```text
one blocked lot exception
    ↓
one planning warning
    ↓
one management warning
```

The warning summary aggregates both planning and management warning layers.

Therefore:

```text
Warnings = Planning Issues + Management Issues
Warnings = 92,422 + 92,422
Warnings = 184,844
```

The new characterization test records this current 2x warning count behavior.

---

## 16. Cost / KPI Impact Composition No-Data Behavior

The graph view shows:

```text
No Cost / KPI impact composition is available.
```

Codex observed that the graph composition depends on executive impact totals.

If totals are zero or non-positive, the graph shows no-data behavior.

This explains the current combination:

```text
blocked_lot issues exist
estimated impact = 0.00
Cost / KPI Impact Composition = not available
```

---

## 17. Weekly Issue Count No-Data Behavior

The graph view shows:

```text
No week-level issue data is available.
```

Codex observed that the weekly graph counts top-impact rows only when the issue records have a non-empty week field.

If issue rows have empty or missing week values, there are no week-level bars.

The new characterization test records this current behavior.

---

## 18. Characterization Tests Added

A new test file was added:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

The tests cover:

```text
forward-capacity dict-week shape currently raising KeyError
warning count lineage: planning warnings + management warnings
weekly graph no-data behavior with empty week fields and zero impact totals
```

These tests are intentionally non-invasive.

They do not fix behavior.

They record current operational semantics.

---

## 19. Test Results

The focused and related tests were run successfully.

Observed test result:

```text
69 passed
```

Included test groups:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
tests/test_explicit_pipeline_forward_capacity_context.py
tests/test_explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

---

## 20. WOM Knowledge Increment Summary

This phase produced the first formal WOM Knowledge Increment for:

```text
Explicit Pipeline Capacity Context
```

### Case Observation

```text
Case:
    iPhone GUI default scenario with Japanese Rice capacity sample

Active product:
    IPHONE_NM_2028_BASE

Forward capacity sample product:
    PACKAGED_RICE_STANDARD

Observed output:
    blocked_lot / service_risk issue rows
    92,422 management issues
    184,844 warnings
    zero estimated impact
    missing Cost / KPI composition graph
    missing weekly issue graph
```

### Context Dictionary Update

Important ctx keys:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
explicit_pipeline_product
```

Key finding:

```text
forward capacity producer shape and consumer expectation are not fully aligned
```

### Operational Semantics Rule Candidate

Candidate future rule:

```text
If selected product is absent from forward capacity context,
do not silently fall through.
Emit an explicit scenario alignment diagnostic.
```

### Diagnostic Pattern

Pattern:

```text
active product missing from capacity context
    ↓
blocked_lot / service_risk issues
    ↓
zero estimated impact
    ↓
no capacity violations
    ↓
possible product / scenario / capacity context mismatch
```

### Characterization Test Candidate

Now implemented in part:

```text
dict-week shape KeyError
warning count lineage
weekly graph no-data behavior
```

### Grammar / Context Delta Proposal

Potential future ctx additions:

```text
scenario_alignment_diagnostic
selected_product_capacity_presence
capacity_context_product_set
week_key_format metadata
capacity_context_node_level metadata
```

No ctx grammar fields were added in this phase.

---

## 21. Safety Boundaries Preserved

This phase preserved all requested safety boundaries.

No changes were made to:

```text
explicit bridge capacity pipeline behavior
planning engine behavior
GUI behavior
CSV sample data
cost/kpi calculations
scenario selector
iPhone capacity sample
Japanese Rice GUI scenario wiring
export execution
ReplanCommand execution
```

Only documentation and characterization tests were added.

---

## 22. Interpretation of the Milestone

This phase marks a transition from:

```text
implementation debugging
```

to:

```text
WOM operational semantics learning
```

The cockpit has spoken.

This phase recorded:

```text
what it said
how it likely said it
which ctx structures were involved
which interpretation gaps remain
```

This is a meaningful step toward turning WOM’s runtime behavior into an explicit planning language dictionary.

---

## 23. Recommended Next Engineering Step

The next step should not be a broad refactor.

Recommended next direction:

```text
define scenario alignment diagnostic behavior
```

Candidate design topic:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
```

Purpose:

```text
When selected product is absent from forward capacity context,
show a clear scenario alignment diagnostic instead of allowing ambiguous blocked_lot explosion.
```

Before implementation, define:

```text
Should missing selected product capacity mean:
    A. scenario mismatch / unavailable diagnostic
    B. zero capacity / all lots blocked
    C. fallback to global capacity
```

The current recommendation is:

```text
A. scenario mismatch / unavailable diagnostic
```

because it is the safest and most explainable behavior.

---

## 24. Summary

The observation phase is complete.

The milestone commit is:

```text
1209199 Add explicit pipeline capacity shape observation and characterization tests
```

The key learning is:

```text
The Explicit Pipeline Management Cockpit is now operational,
but the current output reflects a scenario/product/context alignment ambiguity.
```

This ambiguity is now documented and partially locked down by characterization tests.

The next task is to decide how WOM should speak when the selected product and capacity context do not align.
