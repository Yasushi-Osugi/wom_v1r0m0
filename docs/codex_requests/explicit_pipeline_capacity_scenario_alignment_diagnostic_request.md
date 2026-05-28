# Codex Request: Explicit Pipeline Capacity Scenario Alignment Diagnostic

**Version:** v0r1  
**Date:** 2026-05-28  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/explicit_pipeline_capacity_scenario_alignment_diagnostic_request.md`  
**Related design memo:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`  
**Design commit:** `f55b9a4 Add explicit pipeline capacity scenario alignment diagnostic design`

---

## 1. Request Summary

Please implement a **non-invasive capacity scenario alignment diagnostic** for the Explicit Pipeline.

The purpose is to let WOM explain whether the attached capacity context is semantically aligned with the currently selected runtime scenario.

This request is diagnostic-only.

Do not change capacity enforcement behavior.

Do not change the planning engine.

Do not normalize week keys yet.

Do not convert forward capacity dict week maps into list-indexed arrays yet.

The goal is to make the current semantic mismatch visible and testable before any behavior fix.

---

## 2. Background

The Explicit Bridge Capacity Pipeline now depends on the following runtime context keys:

```text
explicit_pipeline_outbound_root
explicit_pipeline_inbound_root
explicit_pipeline_product
explicit_pipeline_mom_policy
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The ctx guard can now check whether these keys exist.

However, existence is not enough.

A capacity context can be present but semantically misaligned.

Examples:

```text
selected product:
    IPHONE_NM_2028_BASE

forward capacity product:
    PACKAGED_RICE_STANDARD
```

```text
forward capacity week keys:
    2027-W40
    2027-W41

current forward execution week domain:
    integer index 0, 1, 2, ...
```

```text
capacity node:
    MILL_EAST

runtime nodes:
    MOM_final_assy_ASIA
    DAD_FAS_APAC
    DAD_FAS_EURO
    DAD_FAS_AMER
    ...
```

In such cases, ctx guard may pass, but the capacity context may not be meaningful for the active scenario.

This diagnostic should identify such cases clearly.

---

## 3. Primary Implementation Scope

Please add a new diagnostic module:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Please add tests:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

The implementation should be pure and side-effect free.

It should inspect supplied roots and context dictionaries and return a structured diagnostic dictionary.

---

## 4. Do Not Modify

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py
data/explicit_pipeline_forward_weekly_capacity.csv
data/explicit_pipeline_backward_weekly_capability.csv
```

Do not change:

```text
capacity enforcement behavior
planning behavior
sample CSV values
GUI scenario selection
warning count semantics
Cost/KPI enrichment logic
existing graph behavior
```

This request is an inspection / diagnostic step only.

---

## 5. Required Public Functions

Please implement the following functions.

### 5.1 classify_week_key_domain

```python
def classify_week_key_domain(keys) -> str:
    ...
```

Expected output values:

```text
integer_index
integer_string_index
label_week
date
mixed
empty
unknown
```

Suggested rules:

```text
empty:
    no keys

integer_index:
    all keys are int

integer_string_index:
    all keys are digit-only strings such as "0", "1", "2"

label_week:
    all keys look like YYYY-Www, for example "2027-W40"

date:
    all keys look like YYYY-MM-DD

mixed:
    multiple recognizable domains

unknown:
    none of the above
```

No external dependencies.

Use standard library only.

---

### 5.2 extract_runtime_node_names

```python
def extract_runtime_node_names(*roots) -> set[str]:
    ...
```

The helper should walk tree-like root objects.

Expected assumptions:

```text
node.name may exist
node.children may exist
children may be missing or None
root may be None
```

The helper should be defensive and should not raise for unusual objects.

Recommended traversal:

```text
depth-first or stack-based traversal
```

---

### 5.3 infer_backward_capability_shape_version

```python
def infer_backward_capability_shape_version(context: dict | None) -> str:
    ...
```

Expected values:

```text
node_product_week_map_v1
empty
unknown
not_available
```

Current backward capability expected shape:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

---

### 5.4 infer_forward_capacity_shape_version

```python
def infer_forward_capacity_shape_version(context: dict | None) -> str:
    ...
```

Expected values:

```text
product_node_type_week_map_v1
product_node_type_week_list_v0
empty
unknown
not_available
```

Current forward capacity producer shape:

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

Current forward capacity consumer expectation:

```python
{
    product: {
        node: {
            capacity_type: [
                capacity_lots_for_week_0,
                capacity_lots_for_week_1,
            ]
        }
    }
}
```

The diagnostic should identify whether the deepest capacity_type value is a dict or a list.

---

### 5.5 build_explicit_pipeline_capacity_scenario_alignment_diagnostic

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

This is the main function.

It should return a structured dictionary similar to the design memo.

---

## 6. Required Diagnostic Shape

The output does not need to match this example exactly, but it should include the following top-level keys:

```python
{
    "available": True,
    "severity": "warning" | "info" | "error",
    "selected_product": "...",

    "forward_capacity": {...},
    "backward_capability": {...},
    "runtime_tree": {...},
    "consumer_expectation": {...},
    "alignment": {...},
    "messages": [...],
}
```

### 6.1 forward_capacity section

Include:

```text
available
product_set
selected_product_present
node_set
capacity_type_set
week_key_sample
week_key_domain
shape_version
```

### 6.2 backward_capability section

Include:

```text
available
product_set
selected_product_present
node_set
week_key_sample
week_key_domain
shape_version
```

### 6.3 runtime_tree section

Include:

```text
runtime_node_count
runtime_node_sample
capacity_node_match_count
capacity_node_unmatched
```

### 6.4 consumer_expectation section

Include:

```text
forward_capacity_week_domain
forward_capacity_shape_version
```

### 6.5 alignment section

Include:

```text
product_alignment
node_alignment
week_domain_alignment
shape_alignment
scenario_alignment
effective_capacity_application
```

### 6.6 messages section

Include readable messages for detected issues.

Examples:

```text
Selected product IPHONE_NM_2028_BASE is not present in forward capacity context product set [PACKAGED_RICE_STANDARD].
```

```text
Forward capacity uses label week keys such as 2027-W40, while the current forward capacity consumer expects integer week indexes.
```

```text
Forward capacity producer shape appears to be product_node_type_week_map_v1, while consumer expectation is product_node_type_week_list_v0.
```

---

## 7. Expected Alignment Semantics

### 7.1 Product alignment

If selected product is missing or unknown:

```text
product_alignment = unknown
```

If selected product appears in both available contexts:

```text
product_alignment = aligned
```

If selected product is absent from any available capacity context:

```text
product_alignment = mismatch
```

If one context matches and one context does not:

```text
product_alignment = partial_match
```

---

### 7.2 Node alignment

Compare runtime node names against capacity node names.

If no runtime roots are supplied:

```text
node_alignment = unknown
```

If capacity node set intersects runtime node set:

```text
node_alignment = partial_match
```

If all capacity nodes are included in runtime node set:

```text
node_alignment = aligned
```

If capacity nodes exist but none match runtime node names:

```text
node_alignment = mismatch
```

---

### 7.3 Week domain alignment

Compare forward capacity week key domain with consumer expected week domain.

If forward capacity week domain equals consumer expected week domain:

```text
week_domain_alignment = aligned
```

If forward capacity week domain is empty or unknown:

```text
week_domain_alignment = unknown
```

If different:

```text
week_domain_alignment = mismatch
```

---

### 7.4 Shape alignment

Compare inferred forward capacity shape version with consumer expected shape version.

If equal:

```text
shape_alignment = aligned
```

If unavailable or unknown:

```text
shape_alignment = unknown
```

If different:

```text
shape_alignment = mismatch
```

---

### 7.5 Scenario alignment

For MVP, infer scenario alignment indirectly.

If product mismatch and node mismatch exist:

```text
scenario_alignment = mismatch_or_sample_only
```

If product aligned and node aligned or partial:

```text
scenario_alignment = likely_aligned
```

Otherwise:

```text
scenario_alignment = unknown
```

---

### 7.6 Effective capacity application

For MVP:

```text
applied
not_applied
uncertain_or_not_applied
not_evaluated
```

Recommended rules:

```text
If product/shape/week all aligned:
    applied

If product mismatch or shape mismatch or week mismatch:
    uncertain_or_not_applied

If context unavailable:
    not_evaluated
```

---

## 8. Required Tests

Please create:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

The test file should be focused and not require GUI.

Use simple dummy tree nodes.

Example dummy node:

```python
class _Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []
```

### 8.1 Week key classification tests

Cover:

```text
[] -> empty
[0, 1] -> integer_index
["0", "1"] -> integer_string_index
["2027-W40", "2027-W41"] -> label_week
["2027-10-04"] -> date
[0, "2027-W40"] -> mixed
```

### 8.2 Product mismatch diagnostic

Input:

```python
selected_product = "IPHONE_NM_2028_BASE"
forward_weekly_capacity = {
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5
            }
        }
    }
}
```

Expected:

```text
forward_capacity.selected_product_present == False
alignment.product_alignment in {"mismatch", "partial_match"}
messages include selected product missing warning
```

### 8.3 Product match diagnostic

Input:

```python
selected_product = "PACKAGED_RICE_STANDARD"
forward_weekly_capacity includes PACKAGED_RICE_STANDARD
```

Expected:

```text
forward_capacity.selected_product_present == True
```

### 8.4 Node mismatch diagnostic

Runtime tree:

```text
supply_point
└─ MOM_final_assy_ASIA
```

Capacity node:

```text
MILL_EAST
```

Expected:

```text
runtime_tree.capacity_node_match_count == 0
alignment.node_alignment == mismatch
```

### 8.5 Node partial match diagnostic

Runtime tree contains:

```text
MILL_EAST
```

Expected:

```text
alignment.node_alignment in {"aligned", "partial_match"}
```

### 8.6 Week domain mismatch diagnostic

Forward capacity week key:

```text
2027-W40
```

Consumer expected:

```text
integer_index
```

Expected:

```text
alignment.week_domain_alignment == mismatch
```

### 8.7 Shape mismatch diagnostic

Forward capacity producer shape:

```text
product_node_type_week_map_v1
```

Consumer expected:

```text
product_node_type_week_list_v0
```

Expected:

```text
alignment.shape_alignment == mismatch
```

### 8.8 List-indexed forward capacity shape diagnostic

Forward capacity:

```python
{
    "P1": {
        "N1": {
            "P": [1, 2, 3]
        }
    }
}
```

Expected:

```text
forward_capacity.shape_version == product_node_type_week_list_v0
alignment.shape_alignment == aligned
```

### 8.9 Backward capability diagnostic

Backward capability:

```python
{
    "MILL_EAST": {
        "PACKAGED_RICE_STANDARD": {
            "2027-W40": 5
        }
    }
}
```

Expected:

```text
backward_capability.available == True
backward_capability.shape_version == node_product_week_map_v1
```

---

## 9. Suggested Implementation Details

### 9.1 Product extraction

Forward product set:

```python
set((forward_weekly_capacity or {}).keys())
```

Backward product set:

```python
for node_map in backward_weekly_capability.values():
    collect node_map.keys()
```

### 9.2 Forward node extraction

Forward node set:

```python
for product_map in forward_weekly_capacity.values():
    collect product_map.keys()
```

### 9.3 Backward node extraction

Backward node set:

```python
set(backward_weekly_capability.keys())
```

### 9.4 Capacity type extraction

```python
for product -> node -> type_map:
    collect type_map.keys()
```

### 9.5 Week key extraction

Forward:

```python
for product -> node -> capacity_type -> week_map_or_list:
    if dict: collect keys
    if list: collect integer range indexes or classify as integer_index
```

Backward:

```python
for node -> product -> week_map:
    collect keys
```

### 9.6 Sampling

Keep samples small and deterministic.

Recommended sample limit:

```text
10
```

Sort string values where possible.

---

## 10. Integration Scope for This Request

Minimum acceptable implementation:

```text
new diagnostic module
new tests
no GUI integration
no env integration
```

Optional if small and safe:

```text
export module from pysi/reporting/__init__.py
```

Do not wire into cockpit_tk.py in this request unless it is extremely small and covered by tests.

The preferred approach is to keep this request as a pure diagnostic builder first.

A later request can attach the diagnostic to env and surface messages in Explicit KPI View.

---

## 11. Acceptance Criteria

The request is complete when:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py exists
tests/test_explicit_pipeline_capacity_scenario_alignment.py exists
pytest for the new test file passes
existing explicit pipeline tests still pass
no planning behavior changes were made
diagnostic output clearly identifies product / node / week / shape mismatch
```

Required test command:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Recommended regression commands:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

If time is limited, at minimum run:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
```

---

## 12. Expected Codex Summary

Please include in your final summary:

```text
Files added
Functions implemented
Main diagnostic keys
Tests added
Test results
Safety boundaries honored
Any intentionally deferred integration
```

Please explicitly answer:

```text
Does the diagnostic detect selected product mismatch?
Does the diagnostic detect node mismatch?
Does the diagnostic detect week-domain mismatch?
Does the diagnostic detect forward capacity shape mismatch?
Does the diagnostic remain side-effect free?
```

---

## 13. Safety Reminder

This request is a diagnostic phase.

Do not fix the mismatch yet.

The correct sequence is:

```text
diagnose
    ↓
characterize with tests
    ↓
surface messages
    ↓
then decide behavior fix
```

The goal is not to silence the symptom.

The goal is to let WOM explain what context it is actually using.

