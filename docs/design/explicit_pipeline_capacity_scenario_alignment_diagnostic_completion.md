# Explicit Pipeline Capacity Scenario Alignment Diagnostic Completion Memo

**Version:** v0r1  
**Date:** 2026-05-28  
**Status:** Completed  
**Target path:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This completion memo records the implementation and validation of the Explicit Pipeline Capacity Scenario Alignment Diagnostic.

This phase followed the design memo and Codex request:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/codex_requests/explicit_pipeline_capacity_scenario_alignment_diagnostic_request.md
```

The purpose of this phase was to add a non-invasive diagnostic module that can inspect whether the capacity context attached to the Explicit Pipeline is semantically aligned with the currently selected WOM runtime scenario.

The diagnostic answers questions such as:

```text
Does the selected product exist in the capacity context?
Do capacity node names match runtime node names?
Do capacity week keys match the consumer's expected week domain?
Does the forward capacity producer shape match the consumer expectation?
```

This phase intentionally did not change capacity enforcement behavior.

---

## 2. Key Commit

Implementation commit:

```text
fd7f92b Add explicit pipeline capacity scenario alignment diagnostic module and tests
```

Preceding design/request commits:

```text
f55b9a4 Add explicit pipeline capacity scenario alignment diagnostic design
92340a2 Add explicit pipeline capacity scenario alignment diagnostic Codex request
```

---

## 3. Files Added

### 3.1 Diagnostic module

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

This module provides pure diagnostic helpers for capacity scenario alignment.

### 3.2 Tests

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

This test file validates week-key classification, product alignment, node alignment, shape alignment, and backward capability shape detection.

---

## 4. Public Functions Implemented

The following requested public functions were implemented:

```python
classify_week_key_domain(...)
extract_runtime_node_names(...)
infer_backward_capability_shape_version(...)
infer_forward_capacity_shape_version(...)
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

---

## 5. Diagnostic Capability Added

The diagnostic can now detect and report the following alignment conditions.

### 5.1 Selected product mismatch

Example pattern:

```text
selected product:
    IPHONE_NM_2028_BASE

forward capacity product set:
    PACKAGED_RICE_STANDARD
```

Diagnostic capability:

```text
selected_product_present = False
product_alignment = mismatch or partial_match
```

### 5.2 Node mismatch

Example pattern:

```text
runtime nodes:
    supply_point
    MOM_final_assy_ASIA

capacity node:
    MILL_EAST
```

Diagnostic capability:

```text
capacity_node_match_count = 0
node_alignment = mismatch
```

### 5.3 Week-domain mismatch

Example pattern:

```text
capacity week key:
    2027-W40

consumer expected week domain:
    integer_index
```

Diagnostic capability:

```text
week_key_domain = label_week
week_domain_alignment = mismatch
```

### 5.4 Forward capacity shape mismatch

Example pattern:

```text
producer:
    product -> node -> capacity_type -> week_label -> capacity_lots

consumer:
    product -> node -> capacity_type -> list[index] -> capacity_lots
```

Diagnostic capability:

```text
producer_shape_version = product_node_type_week_map_v1
consumer_shape_version = product_node_type_week_list_v0
shape_alignment = mismatch
```

### 5.5 Backward capability shape detection

Example shape:

```text
node -> product -> week -> capability_lots
```

Diagnostic capability:

```text
backward_capability.shape_version = node_product_week_map_v1
```

---

## 6. Structured Output

The diagnostic returns a structured dictionary with the following major sections:

```text
available
severity
selected_product

forward_capacity
backward_capability
runtime_tree
consumer_expectation
alignment
messages
```

This structure allows the result to be used later by:

```text
env / ctx attach
Explicit KPI View messages
Management Cockpit Summary tab
future scenario alignment reports
future behavior-fix evidence
```

---

## 7. Safety Boundaries Honored

This phase was intentionally diagnostic-only.

The following were not changed:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py
data/explicit_pipeline_forward_weekly_capacity.csv
data/explicit_pipeline_backward_weekly_capability.csv
GUI scenario selection
capacity enforcement behavior
week key normalization behavior
forward capacity dict-to-list conversion behavior
Cost/KPI enrichment behavior
warning count semantics
```

The diagnostic remains side-effect free:

```text
pure computation over inputs
no file I/O
no mutation of env
no mutation of ctx
no mutation of planning roots
no mutation of capacity context dictionaries
```

---

## 8. Tests Executed

The following tests were executed successfully.

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Observed test results:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py                 9 passed
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py 3 passed
tests/test_explicit_pipeline_forward_capacity_context.py                   12 passed
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py          4 passed
tests/test_explicit_pipeline_capacity_context.py                           16 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                              7 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                    8 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py                10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py           9 passed
```

Total observed:

```text
78 passed
```

---

## 9. Explicit Answers Confirmed

The implementation explicitly satisfies the requested checks.

```text
Does the diagnostic detect selected product mismatch?
    Yes.

Does the diagnostic detect node mismatch?
    Yes.

Does the diagnostic detect week-domain mismatch?
    Yes.

Does the diagnostic detect forward capacity shape mismatch?
    Yes.

Does the diagnostic remain side-effect free?
    Yes.
```

---

## 10. Development Meaning

Before this phase, WOM could check:

```text
Is capacity context present?
```

After this phase, WOM can begin to answer:

```text
Is the capacity context semantically aligned with the runtime scenario?
```

This is an important shift.

The capacity context may exist, but still be wrong for the active runtime scenario.

The diagnostic makes that previously hidden mismatch visible.

This prepares the next stage:

```text
diagnostic module
    ↓
env / ctx attach
    ↓
Explicit KPI View message surfacing
    ↓
manual GUI observation
    ↓
future week-key normalization or shape conversion decision
```

---

## 11. Deferred Work

The following work was intentionally deferred.

### 11.1 Env / ctx attach

A later phase should attach the diagnostic to:

```text
env.explicit_pipeline_capacity_scenario_alignment_diagnostic
```

and/or:

```text
ctx["explicit_pipeline_capacity_scenario_alignment_diagnostic"]
```

### 11.2 GUI / Management Cockpit message surfacing

A later phase should surface diagnostic messages in the Explicit KPI View, likely in the Messages tab.

### 11.3 Behavior fix

This phase did not fix the underlying shape/week mismatch.

Potential later behavior changes include:

```text
week key normalization:
    2027-W40 -> integer index

forward capacity shape conversion:
    product_node_type_week_map_v1 -> product_node_type_week_list_v0

scenario-specific sample data:
    iPhone demo sample
    Japanese Rice Case runner alignment

capacity applicability status:
    present but not applied
    applied and blocking
    absent and unlimited fallback
```

These should be considered only after the diagnostic is visible in runtime output.

---

## 12. Recommended Next Step

Recommended next design topic:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach.md
```

or directly:

```text
docs/codex_requests/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_request.md
```

Recommended implementation scope for the next phase:

```text
attach diagnostic result to env/ctx
include diagnostic messages in Explicit KPI View messages
do not change capacity enforcement
do not normalize week keys
do not convert capacity shape yet
```

The next phase should connect the diagnostic "stethoscope" to the Management Cockpit so that WOM can visibly report product/node/week/shape mismatch to the user.

---

## 13. Summary

This phase completed the diagnostic module and tests for Explicit Pipeline Capacity Scenario Alignment.

The implementation added:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

It validated:

```text
product mismatch
node mismatch
week-domain mismatch
shape mismatch
backward capability shape detection
list-indexed forward capacity alignment
```

The phase preserved safety boundaries and avoided behavior changes.

In short:

```text
WOM can now inspect the capacity context alignment.
The next task is to make WOM speak that diagnostic in the cockpit.
```
