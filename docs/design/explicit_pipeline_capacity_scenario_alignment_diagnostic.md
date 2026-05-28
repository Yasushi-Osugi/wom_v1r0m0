# Explicit Pipeline Capacity Scenario Alignment Diagnostic

**Version:** v0r1 draft  
**Date:** 2026-05-28  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the design direction for an explicit diagnostic layer that checks whether the capacity context attached to the Explicit Pipeline is semantically aligned with the currently selected WOM planning scenario.

The immediate purpose is to move from:

```text
ctx key exists
```

to:

```text
ctx key exists
and
ctx meaning matches selected product / node / week / capacity shape
```

The current explicit pipeline has already reached the stage where required context keys can be attached and the Management Cockpit can display Explicit KPI results.

However, the next issue is not merely missing context.

The next issue is whether the supplied capacity context is aligned with the actual runtime scenario.

This memo therefore defines:

```text
selected product diagnostic
capacity product set diagnostic
node match diagnostic
week key domain diagnostic
forward capacity shape version diagnostic
scenario/sample alignment diagnostic
```

---

## 2. Background

The Explicit Bridge Capacity Pipeline requires the following runtime context keys:

```text
explicit_pipeline_outbound_root
explicit_pipeline_inbound_root
explicit_pipeline_product
explicit_pipeline_mom_policy
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The current ctx guard checks whether these keys exist.

That guard is necessary but no longer sufficient.

A context key can exist while still being semantically misaligned.

Examples:

```text
selected product = IPHONE_NM_2028_BASE
forward capacity product set = {PACKAGED_RICE_STANDARD}
```

```text
capacity week keys = 2027-W40 / 2027-W41
forward execution expects integer week index = 0 / 1 / 2
```

```text
capacity node = MILL_EAST
runtime supply node names = MOM_final_assy_ASIA / DAD_FAS_APAC / ...
```

In these cases, the pipeline may appear available while the capacity context is not actually constraining the intended runtime flow.

This is more dangerous than a missing context error because it can produce a silent semantic no-op.

---

## 3. Problem Statement

The current state can be summarized as follows.

```text
Explicit KPI ON
    ↓
GUI preflight attaches backward capability
    ↓
GUI preflight attaches forward weekly capacity
    ↓
ctx guard passes
    ↓
explicit pipeline runs
    ↓
Management Cockpit displays diagnostics
```

But the following questions are not yet explicitly answered:

```text
Does selected product exist in forward capacity context?
Does selected product exist in backward capability context?
Do capacity node names match runtime node names?
Do capacity week keys match the week domain expected by execution?
Is forward capacity provided as dict week map or list-indexed week vector?
Is sample data intended for Japanese Rice Case or iPhone GUI demo?
Is missing capacity intentionally unlimited or accidentally misaligned?
```

This memo proposes a diagnostic layer to answer those questions before or during explicit pipeline reporting.

---

## 4. Current Observed Mismatch Patterns

### 4.1 Product mismatch

Observed or likely pattern:

```text
selected product:
    IPHONE_NM_2028_BASE

forward capacity context product:
    PACKAGED_RICE_STANDARD
```

Interpretation:

```text
The forward capacity context exists,
but it may not apply to the currently selected GUI planning product.
```

Required diagnostic:

```text
selected_product_capacity_presence = missing
```

---

### 4.2 Node mismatch

Observed or likely pattern:

```text
capacity node:
    MILL_EAST

runtime node:
    MOM_final_assy_ASIA
    DAD_FAS_APAC
    DAD_FAS_EURO
    DAD_FAS_AMER
    ...
```

Interpretation:

```text
Capacity context may be valid for a sample case,
but not aligned to the runtime supply tree being evaluated.
```

Required diagnostic:

```text
node_match_status = no_runtime_node_match
```

---

### 4.3 Week domain mismatch

Observed or likely pattern:

```text
capacity week key:
    2027-W40
    2027-W41

forward execution week reference:
    0
    1
    2
```

Interpretation:

```text
The capacity context carries calendar week labels,
while the forward execution engine currently consumes integer week indexes.
```

Required diagnostic:

```text
week_key_domain = label_week
consumer_week_domain = integer_index
week_domain_alignment = mismatch
```

---

### 4.4 Shape mismatch

Observed or likely pattern:

```text
forward capacity producer shape:
    product -> node -> capacity_type -> week_label -> capacity_lots

forward execution consumer shape:
    product -> node -> capacity_type -> list[indexed_week]
```

Interpretation:

```text
The context producer and consumer both use product/node/capacity_type,
but they disagree at the week dimension.
```

Required diagnostic:

```text
forward_capacity_shape_version = product_node_type_week_map_v1
consumer_expected_shape_version = product_node_type_week_list_v0
shape_alignment = mismatch
```

---

### 4.5 False positive ctx availability

Observed or likely pattern:

```text
ctx guard = pass
capacity report = available
actual capacity constraint = not meaningfully applied
```

Interpretation:

```text
Context existence is not equivalent to context applicability.
```

Required diagnostic:

```text
ctx_presence_status = present
ctx_alignment_status = misaligned
effective_capacity_application = uncertain_or_not_applied
```

---

## 5. Design Goal

The goal is not to change planning behavior immediately.

The goal is to add an explicit diagnostic layer that can say:

```text
The capacity context exists,
but it does not appear aligned with the selected product / nodes / week domain.
```

The first implementation should be non-invasive.

It should inspect context and runtime metadata, then produce a structured diagnostic object.

It should not:

```text
change capacity enforcement
change planning engine behavior
change sample CSV rows
change GUI layout heavily
perform automatic replanning
normalize week keys silently
```

The diagnostic should make hidden semantic assumptions visible.

---

## 6. Proposed Diagnostic Object

Recommended object name:

```text
explicit_pipeline_capacity_scenario_alignment_diagnostic
```

Recommended Python shape:

```python
{
    "available": True,
    "severity": "warning",
    "selected_product": "IPHONE_NM_2028_BASE",

    "forward_capacity": {
        "available": True,
        "product_set": ["PACKAGED_RICE_STANDARD"],
        "selected_product_present": False,
        "node_set": ["MILL_EAST"],
        "capacity_type_set": ["P"],
        "week_key_sample": ["2027-W40", "2027-W41"],
        "week_key_domain": "label_week",
        "shape_version": "product_node_type_week_map_v1",
    },

    "backward_capability": {
        "available": True,
        "product_set": ["PACKAGED_RICE_STANDARD"],
        "selected_product_present": False,
        "node_set": ["MILL_EAST"],
        "week_key_sample": ["2027-W40", "2027-W41"],
        "week_key_domain": "label_week",
        "shape_version": "node_product_week_map_v1",
    },

    "runtime_tree": {
        "outbound_node_count": 0,
        "inbound_node_count": 0,
        "runtime_node_sample": [],
        "capacity_node_match_count": 0,
        "capacity_node_unmatched": ["MILL_EAST"],
    },

    "consumer_expectation": {
        "forward_capacity_week_domain": "integer_index",
        "forward_capacity_shape_version": "product_node_type_week_list_v0",
    },

    "alignment": {
        "product_alignment": "mismatch",
        "node_alignment": "mismatch_or_unknown",
        "week_domain_alignment": "mismatch",
        "shape_alignment": "mismatch",
        "scenario_alignment": "mismatch_or_sample_only",
        "effective_capacity_application": "uncertain_or_not_applied",
    },

    "messages": [
        "Forward capacity context is present, but selected product is not present in forward capacity product set.",
        "Forward capacity week keys appear to be label weeks, while current forward execution expects integer week indexes.",
        "Capacity context may be a Japanese Rice Case sample while GUI selected product appears to be an iPhone demo product.",
    ],
}
```

---

## 7. Diagnostic Status Vocabulary

Recommended status values:

```text
ok
warning
error
unknown
not_available
sample_only
mismatch
partial_match
```

Recommended alignment values:

```text
aligned
mismatch
partial_match
unknown
not_applicable
```

Recommended effective application values:

```text
applied
not_applied
uncertain_or_not_applied
unlimited_fallback
blocked_by_error
not_evaluated
```

---

## 8. Product Diagnostic

### 8.1 Inputs

```text
selected product:
    ctx["explicit_pipeline_product"]
    or env.product_selected
    or pipeline_result.product_name

forward capacity product set:
    keys of explicit_pipeline_forward_weekly_capacity

backward capability product set:
    nested product keys in explicit_pipeline_backward_weekly_capability
```

### 8.2 Checks

```text
selected_product in forward_capacity_product_set
selected_product in backward_capability_product_set
```

### 8.3 Output

```python
{
    "selected_product": selected_product,
    "forward_capacity_product_set": sorted([...]),
    "forward_selected_product_present": bool,
    "backward_capability_product_set": sorted([...]),
    "backward_selected_product_present": bool,
    "product_alignment": "aligned" | "mismatch" | "unknown",
}
```

### 8.4 Message examples

```text
Selected product IPHONE_NM_2028_BASE is not present in forward capacity context.
```

```text
Forward capacity context product set contains PACKAGED_RICE_STANDARD only.
```

---

## 9. Node Diagnostic

### 9.1 Inputs

```text
runtime outbound root
runtime inbound root
forward capacity node set
backward capability node set
```

### 9.2 Checks

```text
capacity_node_set intersects runtime_node_set
capacity_node_set subset of runtime_node_set
runtime_node_set contains selected MOM / DAD / supply nodes
```

### 9.3 Output

```python
{
    "runtime_node_count": 25,
    "runtime_node_sample": ["supply_point", "DAD_FAS_APAC", "..."],
    "capacity_node_set": ["MILL_EAST"],
    "matched_capacity_nodes": [],
    "unmatched_capacity_nodes": ["MILL_EAST"],
    "node_alignment": "mismatch",
}
```

### 9.4 Message examples

```text
Capacity node MILL_EAST was not found in the current runtime supply tree.
```

```text
Capacity context may belong to a different sample scenario.
```

---

## 10. Week Key Domain Diagnostic

### 10.1 Inputs

```text
forward capacity week keys
backward capability week keys
forward execution expected week domain
```

### 10.2 Week domain classification

Recommended helper classification:

```text
integer_index:
    0, 1, 2, ...

integer_string_index:
    "0", "1", "2", ...

label_week:
    "2027-W40", "2027-W41"

date:
    "2027-10-04"

mixed:
    more than one type

empty:
    no keys found

unknown:
    cannot classify
```

### 10.3 Output

```python
{
    "forward_capacity_week_key_sample": ["2027-W40", "2027-W41"],
    "forward_capacity_week_key_domain": "label_week",
    "consumer_expected_week_key_domain": "integer_index",
    "week_domain_alignment": "mismatch",
}
```

### 10.4 Message examples

```text
Forward capacity uses label week keys such as 2027-W40, while the current forward execution engine expects integer week indexes.
```

---

## 11. Shape Version Diagnostic

### 11.1 Proposed shape versions

```text
node_product_week_map_v1
    node -> product -> week -> value

product_node_type_week_map_v1
    product -> node -> capacity_type -> week -> value

product_node_type_week_list_v0
    product -> node -> capacity_type -> list[index] -> value

unknown
```

### 11.2 Current likely shapes

Backward capability:

```text
node_product_week_map_v1
```

Forward capacity producer:

```text
product_node_type_week_map_v1
```

Forward capacity consumer expectation:

```text
product_node_type_week_list_v0
```

### 11.3 Output

```python
{
    "producer_shape_version": "product_node_type_week_map_v1",
    "consumer_shape_version": "product_node_type_week_list_v0",
    "shape_alignment": "mismatch",
}
```

---

## 12. Scenario / Sample Diagnostic

### 12.1 Problem

The current sample capacity context may be loaded as:

```text
scenario = base
product = PACKAGED_RICE_STANDARD
node = MILL_EAST
source = japanese_rice_case_sample
```

while the GUI demo may evaluate:

```text
product = IPHONE_NM_2028_BASE
node family = DAD / MOM / supply_point
```

This means the sample data may correctly clear ctx guard but may not be semantically meaningful for the active GUI planning scenario.

### 12.2 Output

```python
{
    "sample_source_set": ["japanese_rice_case_sample"],
    "selected_product": "IPHONE_NM_2028_BASE",
    "sample_scenario_alignment": "sample_only_or_mismatch",
}
```

### 12.3 Message examples

```text
Forward capacity context appears to be a Japanese Rice Case sample, while the selected GUI product appears to be an iPhone demo product.
```

```text
This may be acceptable for ctx guard validation, but not for meaningful capacity bottleneck diagnosis.
```

---

## 13. Recommended Function Names

Recommended module:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

or, if treated as planning-context inspection:

```text
pysi/plan/explicit_pipeline_capacity_scenario_alignment.py
```

Recommended MVP location:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Reason:

```text
The first version is diagnostic/reporting only.
It should not change planning behavior.
```

Recommended functions:

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
classify_week_key_domain(...)
infer_forward_capacity_shape_version(...)
infer_backward_capability_shape_version(...)
extract_runtime_node_names(...)
```

---

## 14. Proposed Main Function Signature

```python
def build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
    *,
    selected_product: str | None,
    backward_weekly_capability: dict | None,
    forward_weekly_capacity: dict | None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    consumer_forward_capacity_shape_version: str = "product_node_type_week_list_v0",
    consumer_forward_week_domain: str = "integer_index",
) -> dict:
    ...
```

The function should be pure and side-effect free.

It should not mutate roots, env, ctx, or capacity contexts.

---

## 15. GUI / KPI View Integration Direction

The first implementation should not require a large GUI redesign.

Recommended integration approach:

```text
1. Build diagnostic after capacity contexts are attached.
2. Attach diagnostic to env or ctx.
3. Include diagnostic messages in Explicit KPI View messages.
4. Optionally add a compact Scenario Alignment section in Summary tab later.
```

Recommended env attribute:

```text
env.explicit_pipeline_capacity_scenario_alignment_diagnostic
```

Recommended ctx key:

```text
explicit_pipeline_capacity_scenario_alignment_diagnostic
```

Recommended message integration:

```text
Explicit KPI View / Messages tab:
    show warning messages from diagnostic["messages"]
```

---

## 16. Recommended MVP Tests

Recommended test file:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

### 16.1 Product mismatch test

```text
selected product = IPHONE_NM_2028_BASE
forward capacity product set = PACKAGED_RICE_STANDARD
expect product_alignment = mismatch
```

### 16.2 Product match test

```text
selected product = PACKAGED_RICE_STANDARD
forward capacity product set includes PACKAGED_RICE_STANDARD
expect product_alignment = aligned
```

### 16.3 Week domain mismatch test

```text
forward capacity week keys = 2027-W40
consumer expected week domain = integer_index
expect week_domain_alignment = mismatch
```

### 16.4 Shape mismatch test

```text
producer shape = product_node_type_week_map_v1
consumer expected shape = product_node_type_week_list_v0
expect shape_alignment = mismatch
```

### 16.5 Node mismatch test

```text
runtime tree nodes = supply_point / MOM_final_assy_ASIA
capacity node = MILL_EAST
expect node_alignment = mismatch
```

### 16.6 Sample-only scenario test

```text
source/note suggests Japanese Rice Case sample
selected product suggests iPhone demo
expect scenario_alignment = sample_only_or_mismatch
```

---

## 17. Expected Management Cockpit Message Examples

The diagnostic should produce messages like:

```text
Capacity scenario alignment warning:
selected product IPHONE_NM_2028_BASE is not present in forward capacity context product set [PACKAGED_RICE_STANDARD].
```

```text
Capacity week-domain warning:
forward capacity uses label week keys such as 2027-W40, while the current forward capacity consumer expects integer week indexes.
```

```text
Capacity sample alignment note:
forward capacity context appears to be a Japanese Rice Case sample. This can validate ctx attachment, but it may not validate the iPhone GUI scenario.
```

```text
Capacity shape warning:
forward capacity producer shape appears to be product_node_type_week_map_v1, while consumer expectation is product_node_type_week_list_v0.
```

---

## 18. Safety Boundaries

The diagnostic implementation must not:

```text
change weekly_forward_push_with_capacity behavior
change explicit_bridge_capacity_pipeline behavior
change capacity CSV rows
change GUI scenario selection
normalize week keys silently
convert dict week maps into list-indexed capacity
change warning counts
change cost/KPI enrichment
```

This is a diagnostic-only phase.

Behavior changes should be done later, after the diagnostic has made the semantic mismatch visible.

---

## 19. Development Sequence

Recommended sequence:

```text
D1. Create this design memo.
D2. Create Codex request for non-invasive diagnostic implementation.
D3. Implement pure diagnostic builder and tests.
D4. Attach diagnostic to env/ctx.
D5. Surface diagnostic messages in Explicit KPI View.
D6. Re-run GUI and observe messages.
D7. Decide whether to normalize week keys or revise forward execution consumer contract.
```

This sequence follows the WOM Knowledge Increment style:

```text
observe
    ↓
diagnose
    ↓
document
    ↓
characterize with tests
    ↓
then change behavior
```

---

## 20. Relationship to Future Behavior Fixes

This diagnostic is not the final fix.

It prepares future fixes such as:

```text
week key normalization:
    2027-W40 -> index 0

capacity context shape conversion:
    product_node_type_week_map_v1 -> product_node_type_week_list_v0

scenario-specific sample data:
    iPhone demo forward capacity sample
    Japanese Rice Case runner alignment

explicit capacity applicability status:
    capacity present but not applied
    capacity absent and unlimited fallback
    capacity applied and blocking
```

Without the diagnostic, those fixes risk becoming local patches with unclear semantics.

With the diagnostic, later behavior changes can be justified by observed, testable mismatch states.

---

## 21. Summary

The next issue is no longer just:

```text
Is capacity context present?
```

The next issue is:

```text
Is capacity context semantically aligned with the runtime scenario?
```

This memo defines a diagnostic layer to make that alignment visible.

The diagnostic should inspect:

```text
selected product
capacity product set
runtime node names
capacity node names
week key domain
capacity shape version
sample source / scenario
```

and produce:

```text
structured alignment status
warning messages
future behavior-fix evidence
```

This is the correct next step before changing capacity enforcement behavior.

In short:

```text
Do not only make WOM run.
Make WOM explain what context it is actually using.
```
