# WOM Knowledge Increment Session Index 260528

**Version:** v0r1  
**Date:** 2026-05-28  
**Status:** Session milestone index  
**Target path:** `docs/design/wom_knowledge_increment_session_index_260528.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo is a compact session index for the important WOM development milestone reached on 2026-05-28.

It is intended to preserve the essential knowledge from parallel ChatGPT sessions before closing the older session opened at:

```text
https://chatgpt.com/c/69fe0e75-ddb8-83e9-afb0-a0579b155ff7
```

This document is not a raw chat log.

It is a repo-safe milestone index that points to the design memos, completion memos, commits, and learning increments that should remain as durable WOM development assets.

---

## 2. Why This Session Needed an Index

The session contained several important knowledge events:

```text
1. The first visible moment when WOM began to speak through Explicit KPI View.
2. The clarification that ctx is WOMPlanningContext / runtime semantic context.
3. The role change of Codex from code generator to operational-semantics observer.
4. The first formal WOM Knowledge Increment for Explicit Pipeline Capacity Context.
```

A raw chat log is useful as local archive material, but it is not ideal as a public repo artifact.

The repo should preserve distilled, design-level knowledge through markdown design documents, completion memos, and characterization tests.

---

## 3. Session Closure Policy

The older ChatGPT session can be closed after this index is committed.

Recommended preservation policy:

```text
Raw chatlog:
    keep locally if needed

Repo artifact:
    keep summarized design / completion / observation md files

URL:
    record as reference only
    do not rely on URL as the primary knowledge store
```

Reason:

```text
URL is an entry point, not durable project knowledge.
Repo design docs and tests are the durable knowledge assets.
```

---

## 4. Milestone 1: 新生 WOM の生まれた日

### 4.1 Event

After adding the forward weekly capacity sample CSV and running:

```bat
python -m main
```

the Explicit Pipeline Management Cockpit began to display diagnostic output.

The cockpit moved from:

```text
missing context / unavailable
```

to:

```text
Available = Yes
Explicit Pipeline Result = Yes
Capacity Report = Yes
Issue Candidates = Yes
Cost / KPI Bundle = Yes
```

Observed GUI behavior included:

```text
Summary tab displayed values
Graphs tab rendered issue severity distribution
Top Issues tab displayed blocked_lot / service_risk rows
Messages tab displayed management warnings and explanation messages
```

This was treated as the first visible moment where WOM began to speak.

---

### 4.2 Key Commit

```text
c0d9a42 Add explicit pipeline forward weekly capacity sample CSV
```

---

### 4.3 Related Files

```text
data/explicit_pipeline_forward_weekly_capacity.csv
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md
```

---

### 4.4 Meaning

This milestone confirmed that the path below became operational:

```text
Explicit KPI ON
    ↓
GUI preflight
    ↓
backward capability attach
    ↓
forward weekly capacity attach
    ↓
ctx guard pass
    ↓
explicit pipeline result
    ↓
management cockpit view model
    ↓
GUI display
```

The meaning was not that all KPI semantics were complete.

The meaning was:

```text
WOM can now surface planning diagnostics in the management cockpit.
```

---

## 5. Milestone 2: ctx as WOMPlanningContext

### 5.1 Concept

The session clarified that `ctx` should be understood as:

```text
WOMPlanningContext
```

not merely as a Python dictionary.

In WOM, ctx is the runtime semantic context that carries:

```text
model state
scenario state
constraint state
decision state
evaluation state
trace state
```

into the planning and reporting pipeline.

---

### 5.2 Layering

The conceptual layering is:

```text
1. WOM Modeling Language
   Defines the supply chain model.
   Examples: Node, Flow, Lot, Demand, Capacity, Cost, Scenario, Policy, Event.

2. WOM Planning Context
   Carries the runtime semantic context for executing the model.

3. WOM Planning Engine
   Uses the context to generate PSI plans, blocked lots, issues, diagnostics, and KPI outputs.

4. WOM Event Trace / Management Cockpit
   Converts runtime results and decision traces into management interpretation.

5. WOM AI Navigator
   Uses structured WOM context to explain, diagnose, and support customization.
```

---

### 5.3 Related Files

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
```

---

### 5.4 Meaning

This shifted the development view from:

```text
ctx = data carrier
```

to:

```text
ctx = runtime semantic context of WOM Planning Language
```

This is the basis for treating later work as operational semantics learning.

---

## 6. Milestone 3: Codex Role Change

### 6.1 Previous Role

In earlier phases, Codex mainly acted as:

```text
small-scope code generator
adapter implementer
test writer
CSV sample creator
```

Examples:

```text
F1: forward weekly capacity adapter
F2: GUI preflight wiring
F3: forward sample CSV
```

---

### 6.2 New Role

In the observation phase, Codex acted as:

```text
code reader
non-invasive observer
operational semantics recorder
WOM Planning Context grammar analyst
WOM Knowledge Increment editor
characterization test writer
```

This was an intentional role shift.

The request explicitly asked Codex to avoid behavior changes and instead capture the current runtime behavior.

---

### 6.3 Related Files

```text
docs/codex_requests/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_request.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

---

### 6.4 Meaning

This established a new development pattern:

```text
not only write code,
but also observe, document, characterize, and preserve operational semantics.
```

In other words, Codex became part of the WOM learning loop.

---

## 7. Milestone 4: First WOM Knowledge Increment

### 7.1 Event

The first formal WOM Knowledge Increment was created for:

```text
Explicit Pipeline Capacity Context
```

The observation memo and characterization tests captured how the pipeline currently interprets capacity context after the cockpit began to speak.

---

### 7.2 Key Commit

```text
1209199 Add explicit pipeline capacity shape observation and characterization tests
```

---

### 7.3 Completion Memo Commit

```text
e57bcbf Add explicit pipeline capacity shape observation completion memo
```

---

### 7.4 Related Files

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation_completion.md
```

---

### 7.5 Key Observations

Codex observed and recorded:

```text
forward capacity producer shape and consumer expectation are not fully aligned
selected product comes from explicit_pipeline_product
missing selected product does not yet create a clear scenario alignment diagnostic
week key normalization is not present
node matching is exact-name based
blocked_lot issue rows do not carry capacity_type
warnings = planning warnings + management warnings
Cost/KPI composition is unavailable when executive totals are zero/non-positive
Weekly Issue Count is unavailable when issue rows have empty/missing week fields
```

---

### 7.6 Meaning

This milestone transformed a confusing GUI result into structured knowledge.

Before this phase:

```text
WOM showed 92,422 management issues and 184,844 warnings.
```

After this phase:

```text
The issue-count lineage and likely scenario/product/context alignment ambiguity were documented.
```

This is the first clear example of WOM learning through:

```text
observation
    ↓
context dictionary update
    ↓
operational semantics rule candidate
    ↓
diagnostic pattern
    ↓
characterization test
    ↓
completion memo
```

---

## 8. WOM Learning Loop Established

This session established the following learning loop:

```text
1. Run scenario
2. Capture ctx snapshot or attach result
3. Capture issue / KPI output
4. Compare expected vs actual semantics
5. Generate observation memo
6. Propose grammar / ctx update
7. Generate characterization test
8. Commit as WOM Knowledge Increment
```

Important principle:

```text
Learning is not raw chat accumulation.
Learning is the conversion of observed behavior into ctx, grammar, tests, and design knowledge.
```

---

## 9. Current Knowledge Assets Created Around This Milestone

Important design and completion documents include:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_forward_weekly_capacity_context_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight.md
docs/design/explicit_pipeline_forward_weekly_capacity_gui_preflight_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md
docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv_completion.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment_observation_completion.md
```

Important test files include:

```text
tests/test_explicit_pipeline_forward_capacity_context.py
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
```

Important runtime sample CSV files include:

```text
data/explicit_pipeline_backward_weekly_capability.csv
data/explicit_pipeline_forward_weekly_capacity.csv
```

---

## 10. Important Commits

Key commits in this milestone sequence:

```text
aa74d2a Extend explicit KPI ctx guard with forward weekly capacity key
8ca8093 Add explicit pipeline forward weekly capacity context guard completion memo
ce373ea Add explicit pipeline forward weekly capacity context design
f88dcc5 Add explicit pipeline forward weekly capacity context Codex request
c0d9a42 Add explicit pipeline forward weekly capacity sample CSV
0f7da5e Add explicit pipeline forward weekly capacity sample CSV completion memo
adcfeb7 Add explicit pipeline capacity shape and scenario alignment design
f8fcff4 Add explicit pipeline capacity shape and scenario alignment Codex request
13d0b84 Update explicit pipeline capacity shape and scenario alignment Codex request
1209199 Add explicit pipeline capacity shape observation and characterization tests
e57bcbf Add explicit pipeline capacity shape observation completion memo
```

---

## 11. What This Index Replaces

This index does not replace detailed design memos.

It replaces the need to keep a ChatGPT browser session open merely as memory.

The canonical development memory should now be:

```text
Git commits
design md files
completion md files
characterization tests
local raw chat archives if needed
```

The ChatGPT session can be closed after this index is committed and pushed.

---

## 12. What This Index Does Not Include

This index intentionally does not include:

```text
full raw chat transcript
private or personal chat context
large log output
generated GUI output files
temporary batch files
```

Those should remain outside the repo unless explicitly needed.

The public repo should keep summarized, design-level, reusable knowledge.

---

## 13. Next Main Line

The next recommended design topic is:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
```

Purpose:

```text
Define how WOM should speak when the selected product and capacity context do not align.
```

Key question:

```text
If selected product is absent from forward capacity context, should WOM treat this as:

A. scenario mismatch / unavailable diagnostic
B. zero capacity / all lots blocked
C. fallback to global capacity
```

Current recommendation:

```text
A. scenario mismatch / unavailable diagnostic
```

because it is safest and most explainable.

---

## 14. Summary

The 2026-05-28 session marks the transition from:

```text
WOM implementation debugging
```

to:

```text
WOM operational semantics learning
```

The cockpit began to speak.

The development team recorded what it said.

Codex began to act not only as implementer, but as operational-semantics observer and WOM Knowledge Increment editor.

The next phase is to improve how WOM speaks when scenario, product, node, week, and capacity context are not aligned.

This file is the session index that allows the old ChatGPT session to be closed safely.
