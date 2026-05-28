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
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md
```

Phase F3 succeeded. The Explicit Pipeline Management Cockpit now displays diagnostic output after:

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

The next work is not to make the pipeline “speak.” It now speaks. The next work is to understand what it is saying.

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

This request is primarily:

```text
inspection + characterization + WOM Knowledge Increment creation
```

not behavior change.

---

## 3. WOM Knowledge Increment Framing

This observation is not a bug-fix task.

Treat this as the first **WOM Knowledge Increment** for:

```text
Explicit Pipeline Capacity Context
```

The purpose is not merely to describe code behavior. The purpose is to convert observed runtime behavior into reusable WOM knowledge.

The observation output should be structured so it can later be reused as:

```text
Case Observation
Context Dictionary Update
Operational Semantics Rule
Diagnostic Pattern
Characterization Test Candidate
Grammar / Context Delta Proposal
Design Memo
```

In other words, the deliverable should help WOM learn.

Here, “learning” does not mean the software magically becomes smarter. Learning means:

```text
observed behavior
    ↓
ctx dictionary entry
    ↓
operational semantics rule
    ↓
diagnostic pattern
    ↓
characterization test
    ↓
design memo
    ↓
future behavior / future case reuse
```

This request should therefore create documentation that answers:

```text
What did WOM see?
What ctx did WOM receive?
What did WOM interpret as capacity?
What did WOM call blocked_lot?
What did WOM convert into issue / KPI output?
What ambiguity was discovered?
What knowledge should be preserved for future cases?
```

---

## 4. Relationship to WOM Planning Language

Please treat `ctx` as:

```text
WOMPlanningContext
```

That means:

```text
ctx is not just a Python dictionary.
ctx is the runtime semantic context of WOM.
```

For this request, distinguish clearly between:

```text
WOM Modeling Language:
    the language for defining supply chain models
    Node / Flow / Lot / Demand / Capacity / Cost / Scenario / Policy / Event

WOM Planning Context:
    the runtime semantic context that carries model state,
    scenario state, constraints, decisions, evaluation context,
    and trace context into the planning / reporting pipeline

WOM Planning Engine:
    the execution system that uses the context to generate plans,
    issues, diagnostics, and management cockpit outputs
```

This request should characterize the **operational semantics** of the current Explicit Pipeline Capacity Context.

Operational semantics means:

```text
how the ctx is interpreted at runtime
```

Example:

```text
Syntax:
    explicit_pipeline_forward_weekly_capacity[product][node][capacity_type][week] = capacity_lots

Operational semantics:
    the explicit bridge capacity pipeline interprets this as forward execution capacity
    for selected or referenced product/node/week,
    and emits blocked_lot or capacity-related issues when capacity is insufficient or missing.
```

If the actual implementation differs from this expectation, document the actual behavior.

---

## 5. Current Scenario Facts

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

This request should determine how the current pipeline behaves in this mismatch case.

---

## 6. Scope of This Request

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

This request should not attempt to fix the behavior yet.

---

## 7. Files to Inspect

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

## 8. Questions to Answer in the Observation Memo

The observation memo should answer the following, with code references by file/function names.

### 8.1 Pipeline entry points

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
which ctx dictionary fields are assembled
which result objects are produced
```

### 8.2 Required ctx shape

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

### 8.3 Selected product handling

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

### 8.4 Missing selected product behavior

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

### 8.5 Week-key handling

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

### 8.6 Node handling

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

### 8.7 Capacity type handling

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

### 8.8 Issue count lineage

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

### 8.9 blocked_lot issue generation

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

### 8.10 Cost / KPI Impact Composition unavailable

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

### 8.11 Weekly Issue Count unavailable

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

## 9. Required WOM Knowledge Increment Section

The observation memo must include a section named:

```text
WOM Knowledge Increment
```

This section should contain the following subsections.

### 9.1 Case Observation

Document:

```text
Case name
Input / active GUI product
Attached ctx keys
CSV sample products / nodes / weeks
Observed cockpit output
```

### 9.2 Context Dictionary Update

For each relevant ctx key, document:

```text
ctx key
owner / producer
consumer
shape
semantic meaning
missing behavior
observed issue
future rule candidate
```

At minimum include:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

### 9.3 Operational Semantics Rule Candidate

Document rule candidates such as:

```text
If selected product is absent from forward capacity context,
the pipeline should either:
    A. emit scenario alignment diagnostic
    B. explicitly treat capacity as zero and explain blocked_lot explosion
```

Do not implement the rule in this request.

### 9.4 Diagnostic Pattern

Document diagnostic patterns found in this case.

Example:

```text
Pattern:
    active product missing from capacity context
Symptoms:
    blocked_lot issues
    service_risk impact category
    zero estimated impact
    no capacity violations
Interpretation:
    possible product / capacity context mismatch
```

### 9.5 Characterization Test Candidate

List candidate tests that should preserve current behavior or future desired behavior.

Include:

```text
product mismatch behavior
week key mismatch behavior
issue count lineage
missing graph data behavior
```

### 9.6 Grammar / Context Delta Proposal

List potential future changes to ctx grammar, if needed.

Examples:

```text
explicit scenario_alignment_diagnostic field
selected_product_capacity_presence flag
capacity_context_product_set
week_key_format metadata
capacity_context_node_level metadata
```

Do not implement these fields in this request.

---

## 10. Recommended Observation Memo Structure

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
17. WOM Knowledge Increment
18. Recommended next sample data strategy
19. Recommended next behavior changes, if any
20. Safety boundaries
21. Summary
```

The memo should clearly separate:

```text
observed current behavior
inferred likely behavior
recommended future change
```

---

## 11. Characterization Tests

Add tests only if they can be done without changing runtime behavior.

Potential test file:

```text
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

Suggested tests:

### 11.1 Product mismatch characterization

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

### 11.2 Forward capacity shape characterization

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

### 11.3 Week mismatch characterization

If feasible, test behavior when plan week is integer and capacity week is string.

If too brittle, document in memo only.

### 11.4 Issue count lineage characterization

If existing functions convert:

```text
lot exceptions -> planning issues -> management issues
```

add a small test proving current count multiplication behavior.

---

## 12. Do Not Overfit Tests

Avoid brittle tests that require the full GUI.

Prefer pure functions.

If the pipeline cannot be tested without a large scenario setup, do not force a test.

Document the limitation.

---

## 13. Safety Boundaries

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

## 14. Expected Files Changed

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

## 15. Tests to Run

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

## 16. Expected Response from Codex

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
15. WOM Knowledge Increment summary
16. Context Dictionary Update summary
17. Operational Semantics Rule candidates
18. Diagnostic Patterns found
19. Grammar / Context Delta proposals
20. Test commands executed
21. Test results
22. Safety boundaries preserved
23. Recommended next engineering step
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

and should be treated as a WOM Knowledge Increment creation task.
