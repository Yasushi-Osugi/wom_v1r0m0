# Codex Request: Inspect Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design and completion documents already exist:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_forward_weekly_capacity_context_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
```

Please read especially:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
```

Phase F3 succeeded.

The Explicit KPI Management Cockpit now displays diagnostic output after:

```text
Explicit KPI ON
Run Full Plan
Explicit KPI View
```

Observed high-level result:

```text
Available = Yes
Explicit Pipeline Result = Yes
Capacity Report = Yes
Issue Candidates = Yes
Cost / KPI Bundle = Yes
```

However, the cockpit also shows large issue counts:

```text
Management Issues: 92,422
Warnings: 184,844
Top Issues: blocked_lot / service_risk
Cost / KPI Impact Composition: not available
Weekly Issue Count: not available
```

The next work is not to make the pipeline “speak.”

It now speaks.

The next work is to understand what it is saying.

---

## 2. Main Objective

Inspect and characterize the current behavior of the Explicit Pipeline Capacity Pipeline.

The goal is to answer:

```text
1. What runtime ctx shapes does explicit_bridge_capacity_pipeline.py expect?
2. How does it use selected product?
3. How does it use forward weekly capacity?
4. How does it handle selected product not found in capacity context?
5. How does it handle week-key mismatch?
6. Why are blocked_lot issues generated for IPHONE_NM_2028_BASE?
7. Why are warnings exactly twice management issues?
8. Why are Cost / KPI Impact Composition and Weekly Issue Count unavailable?
```

This request is primarily **inspection + characterization**, not behavior change.

---

## 3. Important Current Scenario Facts

The manual GUI run showed active product:

```text
IPHONE_NM_2028_BASE
```

The current sample forward capacity CSV is:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

with product:

```text
PACKAGED_RICE_STANDARD
```

and node:

```text
MILL_EAST
```

This means there is likely a scenario/product mismatch:

```text
active GUI product = IPHONE_NM_2028_BASE
forward capacity sample product = PACKAGED_RICE_STANDARD
```

This mismatch may be acceptable for ctx guard validation, but it is not necessarily meaningful for business diagnostics.

---

## 4. Scope of This Request

Please implement a **non-invasive diagnostic / characterization patch**.

Preferred scope:

```text
1. Inspect relevant code.
2. Add a design observation memo documenting current behavior.
3. Add focused characterization tests if they can be added without changing runtime behavior.
4. Do not change business logic unless a tiny testability-only change is necessary.
```

Expected deliverable document:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
```

Potential test file, if useful:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

This request should not attempt to “fix” the behavior yet.

---

## 5. Files to Inspect

Please inspect the following files:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_reporting_stack.py
tests/test_explicit_pipeline_forward_capacity_context.py
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

If other files are relevant, inspect them and list them in the summary.

---

## 6. Questions to Answer in the Observation Memo

The observation memo should answer the following, with code references by file/function names.

### 6.1 Pipeline entry points

Identify:

```text
maybe_run_explicit_bridge_capacity_pipeline_from_env(...)
maybe_run_explicit_bridge_capacity_pipeline(...)
```

or equivalent functions.

Document:

```text
which ctx keys are required
which env attributes are read
which result objects are produced
```

---

### 6.2 Required ctx shape

Document the expected shapes for:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

Current known shapes:

Backward:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

Forward:

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

Please verify whether the pipeline actually consumes these exact shapes.

If the pipeline expects a different shape, document the mismatch.

---

### 6.3 Selected product handling

Answer:

```text
Does the explicit pipeline use env.product_selected?
Does it use a product passed through ctx?
Does it infer product from planning result?
Does it ignore product and process all lots?
Does it filter capacity context by product?
```

Especially confirm what happens when:

```text
selected product = IPHONE_NM_2028_BASE
capacity context only has PACKAGED_RICE_STANDARD
```

---

### 6.4 Missing selected product behavior

Determine the current behavior when selected product is absent from forward capacity context.

Possibilities:

```text
A. pipeline marks result unavailable
B. pipeline emits diagnostic warning
C. pipeline treats missing capacity as zero capacity
D. pipeline ignores capacity context product key
E. pipeline falls back to another default
```

Document the actual behavior.

Do not change it in this request unless needed for characterization tests.

---

### 6.5 Week-key handling

Determine whether the pipeline expects week keys like:

```text
2027-W40
2027-W41
```

or internal integer weeks like:

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

Answer:

```text
Are week keys normalized?
Are string and integer week keys treated as different?
What happens if capacity weeks do not match plan weeks?
```

This is important because the current sample CSV uses ISO-like week strings while planning logs show integer week indexes.

---

### 6.6 Node handling

Determine what node level the pipeline expects capacity for.

Possibilities:

```text
MOM nodes
DAD nodes
leaf nodes
capacity owner nodes
process nodes
any node key found in context
```

Current sample node:

```text
MILL_EAST
```

Observed iPhone plan nodes include:

```text
MOM_final_assy_ASIA
MOM_final_assy_EURO
DAD_FAS_APAC
DAD_FAS_EURO
DAD_FAS_AMER
```

Document whether the pipeline attempts to match node names.

---

### 6.7 Capacity type handling

Determine how the pipeline uses:

```text
capacity_type
```

Current forward sample uses:

```text
P
```

Answer:

```text
Does the pipeline expect P/S/I?
Does it use production/shipping/inventory labels?
Does capacity_type propagate into issue candidates?
Why does the UI capacity_type column appear blank for blocked_lot issues?
```

---

### 6.8 Issue count lineage

Observed:

```text
Lot Exceptions = 92,422
Planning Issues = 92,422
Management Issues = 92,422
Warnings = 184,844
```

Please inspect and document how these counts are generated.

Possible lineage:

```text
lot exceptions -> planning issues -> management issues
warnings = planning issues + management issues
```

Determine whether the 184,844 warnings are expected double-layer counting or unintended duplication.

---

### 6.9 blocked_lot issue generation

Document how `blocked_lot` issues are generated.

Answer:

```text
What input produces blocked_lot?
Is blocked_lot generated per lot?
per node/week/product?
per lot exception?
per planning issue?
```

Also document why estimated impact is:

```text
0.00
```

if this is visible from the code.

---

### 6.10 Cost / KPI Impact Composition unavailable

Graphs tab shows:

```text
No Cost / KPI impact composition is available.
```

Please inspect and document:

```text
which view-model key is required
which cost/kpi bundle field is expected
why current data does not populate it
whether all impacts are zero
whether issue records lack impact categories or cost values
```

---

### 6.11 Weekly Issue Count unavailable

Graphs tab shows:

```text
No week-level issue data is available.
```

Please inspect and document:

```text
which issue field is required for weekly graph
whether issue records have week fields
whether the key name differs from the graph view expectation
whether the current issue list is summary-level only
```

---

## 7. Recommended Observation Memo Structure

Please create:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
```

Suggested sections:

```text
1. Purpose
2. Files inspected
3. Pipeline entry points
4. Required ctx keys
5. Backward capability shape actually consumed
6. Forward capacity shape actually consumed
7. Product selection and filtering behavior
8. Missing selected product behavior
9. Week-key handling
10. Node matching behavior
11. Capacity type handling
12. blocked_lot issue generation
13. Issue count lineage
14. Graph data requirements
15. Cost / KPI composition requirements
16. Current interpretation of the 92,422 / 184,844 result
17. Recommended next sample data strategy
18. Recommended next behavior changes, if any
19. Safety boundaries
20. Summary
```

The memo should clearly separate:

```text
observed current behavior
inferred likely behavior
recommended future change
```

---

## 8. Characterization Tests

Add tests only if they can be done without changing runtime behavior.

Potential test file:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

Suggested tests:

### 8.1 Product mismatch characterization

Construct minimal ctx where:

```text
selected product = IPHONE_NM_2028_BASE
forward capacity context only has PACKAGED_RICE_STANDARD
```

Run the relevant pipeline function if feasible.

Assert the current observed behavior:

```text
result available / unavailable
blocked_lot count
diagnostic messages
or specific fallback behavior
```

Only add this test if the setup is not too large or brittle.

---

### 8.2 Forward capacity shape characterization

Construct minimal forward capacity context in product-first shape:

```python
{
    "P1": {
        "N1": {
            "P": {
                "W1": 1
            }
        }
    }
}
```

Verify the pipeline or helper consumes it as currently expected.

---

### 8.3 Week mismatch characterization

If feasible, test behavior when plan week is integer and capacity week is string.

If too brittle, document in memo only.

---

### 8.4 Issue count lineage characterization

If existing functions convert:

```text
lot exceptions -> planning issues -> management issues
```

add a small test proving current count multiplication behavior.

---

## 9. Do Not Overfit Tests

Avoid brittle tests that require the full GUI.

Prefer pure functions.

If the pipeline cannot be tested without a large scenario setup, do not force a test. Document the limitation.

---

## 10. Safety Boundaries

Please preserve these boundaries:

```text
1. Do not change explicit bridge capacity pipeline behavior.
2. Do not change planning engine behavior.
3. Do not change GUI behavior.
4. Do not change CSV sample data.
5. Do not change cost/kpi calculations.
6. Do not add scenario selector.
7. Do not add iPhone capacity sample yet.
8. Do not add Japanese Rice GUI scenario wiring yet.
9. Do not execute exports.
10. Do not execute ReplanCommand.
11. Do not commit generated output files.
```

This request is primarily:

```text
code inspection + documentation + optional characterization tests
```

---

## 11. Expected Files Changed

Expected primary file:

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
```

Optional test file:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

Avoid changing code files.

If code files must be changed, explain why.

---

## 12. Tests to Run

If a new test file is added:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

Run related existing tests:

```bat
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

If no tests are added, run at least:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

and any relevant tests touched by imports.

---

## 13. Expected Response from Codex

After implementation, please summarize:

```text
1. Files inspected
2. Files changed
3. Whether tests were added
4. Pipeline entry points identified
5. Forward capacity shape actually consumed
6. Selected product handling
7. Missing selected product behavior
8. Week-key handling
9. Node matching behavior
10. Capacity type handling
11. Issue count lineage
12. Why 92,422 management issues / 184,844 warnings likely appear
13. Why Cost / KPI Impact Composition is unavailable
14. Why Weekly Issue Count is unavailable
15. Test commands executed
16. Test results
17. Safety boundaries preserved
18. Recommended next engineering step
```

Please do not proceed into:

```text
behavior fix
iPhone capacity sample
Japanese Rice GUI scenario
scenario selector
cost/kpi enrichment
pipeline refactor
main PR
completion memo
```

This request is only for:

```text
Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment Observation
```
