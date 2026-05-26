# Explicit Pipeline Backward Weekly Capability Context Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-26  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_context_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of **Explicit Pipeline Backward Weekly Capability Context Phase 1**.

The purpose of this phase was to implement the first pure data-context layer for:

```text
explicit_pipeline_backward_weekly_capability
```

This context is required by the explicit bridge capacity pipeline and had previously appeared in the Explicit KPI View as a missing context key.

This phase did not wire the context into the GUI or Run Full Plan.

It implemented the pure adapter / loader / env attach helper that defines the shape of the capability context and makes it available to later phases.

---

## 2. Background

Before this phase, the cockpit behavior was:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard checks env.explicit_pipeline_backward_weekly_capability
    ↓
missing key detected
    ↓
explicit pipeline is safely skipped
    ↓
Explicit KPI View shows diagnostic:
       explicit_pipeline_backward_weekly_capability
```

This behavior was safe and understandable, but the missing capability context had not yet been implemented as a concrete data object.

The design memo:

```text
docs/design/explicit_pipeline_backward_weekly_capability_context.md
```

defined the intended context.

This phase implemented the first code-level adapter for that design.

---

## 3. Implemented Commit

The implementation was committed as:

```text
dfece92 Add explicit pipeline backward weekly capability context adapter
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

The implementation added two files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_capacity_context.py
```

No GUI files were changed.

No Run Full Plan wiring was changed.

No planning execution logic was changed.

No export or replan logic was changed.

---

## 5. Public Functions Added

The new module:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

adds three public helper functions.

### 5.1 build_explicit_pipeline_backward_weekly_capability

```python
build_explicit_pipeline_backward_weekly_capability(
    records,
    *,
    scenario="base",
    strict=False,
)
```

Purpose:

```text
Build canonical nested capability context from record-like mappings.
```

Canonical output:

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
    "MOM_A": {
        "P1": {
            "202601": 100
        }
    }
}
```

### 5.2 load_explicit_pipeline_backward_weekly_capability_csv

```python
load_explicit_pipeline_backward_weekly_capability_csv(
    path,
    *,
    scenario="base",
    strict=False,
    encoding="utf-8-sig",
)
```

Purpose:

```text
Load CSV rows using Python standard library csv.DictReader,
then delegate to the builder.
```

### 5.3 attach_explicit_pipeline_backward_weekly_capability_to_env

```python
attach_explicit_pipeline_backward_weekly_capability_to_env(env, context)
```

Purpose:

```text
Attach the canonical context to env.explicit_pipeline_backward_weekly_capability
and return env.
```

---

## 6. Canonical Context Schema

The implemented canonical context schema is:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

The MVP interpretation is:

```text
MOM node / product / week capability in lot count
```

This context is the first concrete “fuel shape” for the explicit bridge capacity pipeline.

---

## 7. CSV Schema Supported

The loader supports the MVP CSV schema defined by the design memo.

Expected columns:

```text
scenario
node
product
week
capability_lots
capability_type
unit
source
note
```

Required fields for actual context construction:

```text
node
product
week
capability_lots
```

Optional fields:

```text
scenario
capability_type
unit
source
note
```

`capability_type`, `source`, and `note` are accepted as CSV columns but are not used by the MVP builder.

---

## 8. Scenario Filtering Behavior

Scenario behavior was implemented as follows:

```text
default scenario filter = "base"
blank or missing row scenario = "base"
scenario=None = include all scenarios
```

Examples:

```text
scenario="base":
    includes rows with scenario="base" and rows with blank scenario

scenario="constrained":
    includes only constrained rows

scenario=None:
    includes base, constrained, and all other scenario rows
```

This makes the adapter scenario-ready without adding GUI scenario selection yet.

---

## 9. Validation Behavior

The adapter validates:

```text
node is not blank
product is not blank
week is not blank
capability_lots is numeric
capability_lots is non-negative
unit is blank or lot
```

`capability_lots` is converted using:

```text
int(float(value))
```

This supports values such as:

```text
100
100.0
"100"
"100.0"
```

---

## 10. Strict / Non-Strict Behavior

### 10.1 strict=False

Default behavior.

Invalid rows are skipped.

This allows a partially valid CSV to still produce a usable context.

### 10.2 strict=True

Invalid rows raise `ValueError`.

Error messages include useful reasons such as:

```text
missing node
missing product
missing week
invalid capability_lots
negative capability_lots
unsupported unit
```

---

## 11. Unit Handling

MVP supported unit:

```text
lot
```

Blank unit is treated as:

```text
lot
```

Unsupported non-blank units, such as:

```text
piece
kg
pallet
hour
```

are handled as:

```text
strict=False:
    skip row

strict=True:
    raise ValueError("unsupported unit")
```

Unit conversion is intentionally out of scope for this phase.

---

## 12. Duplicate Row Behavior

Duplicate rows are defined as rows with the same:

```text
node
product
week
```

The implemented MVP behavior is:

```text
last valid row wins
```

This is deterministic and simple.

The adapter does not sum duplicate rows in this phase.

---

## 13. Env Attach Behavior

The env attach helper sets:

```python
env.explicit_pipeline_backward_weekly_capability = context
```

and returns:

```python
env
```

This behavior was tested against the existing ctx guard helper.

Before attach:

```text
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

contains:

```text
explicit_pipeline_backward_weekly_capability
```

After attach:

```text
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

This confirms that the new adapter can supply the context expected by the existing guard.

---

## 14. Tests Added

New test file:

```text
tests/test_explicit_pipeline_capacity_context.py
```

The test file covers:

```text
simple nested context build
scenario filtering
scenario=None includes all scenarios
blank scenario defaults to base
duplicate last row wins
invalid numeric skipped in non-strict mode
invalid numeric raises in strict mode
negative capability handling
unsupported unit handling
CSV loader behavior
env attach clears existing guard missing key
```

---

## 15. Test Results

The following tests were executed successfully.

```bat
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

Observed results:

```text
tests/test_explicit_pipeline_capacity_context.py                         10 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                            6 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                  5 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py              10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py         9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py  3 passed, 1 skipped
tests/test_explicit_pipeline_reporting_stack_insertion.py                 7 passed
tests/test_explicit_pipeline_reporting_flags.py                          10 passed
tests/test_covid_vaccine_with_capacity_push.py                            1 passed
```

Total observed result:

```text
61 passed, 1 skipped
```

The single skipped test is a Tk rendering environment skip and is not a failure.

---

## 16. Scope Boundaries Preserved

This phase intentionally did not implement:

```text
GUI preflight wiring
Run Full Plan path changes
default CSV auto-load
sample CSV master commit
planning execution
export execution
ReplanCommand execution
automatic replanning
Price-Cost-Profit propagation
Cost / KPI context generation
tariff simulation
cold-chain shelf-life logic
process-level capability
resource-level capability
unit conversion
```

This was a pure context adapter phase.

---

## 17. Meaning of This Milestone

Before this phase:

```text
WOM knew that explicit_pipeline_backward_weekly_capability was missing.
But there was no pure adapter to build that context.
```

After this phase:

```text
WOM has a deterministic builder / CSV loader / env attach helper
for explicit_pipeline_backward_weekly_capability.
```

This moves the implementation from:

```text
diagnostic missing-key awareness
```

to:

```text
capability context construction readiness
```

The cockpit still does not automatically load the context.

That is the next phase.

---

## 18. Current State

Current state:

```text
ctx guard exists
ctx guard diagnostics are visible in Explicit KPI View
capacity context design exists
capacity context adapter exists
tests pass
GUI auto-load is not yet wired
```

Therefore:

```text
Explicit KPI ON can still show missing context
unless env.explicit_pipeline_backward_weekly_capability is attached by some future path.
```

This is expected.

---

## 19. Recommended Next Step

The next design should define Phase 2:

```text
how to load capability context from CSV and attach it to env
before Explicit KPI ctx guard runs
```

Recommended next design memo:

```text
docs/design/explicit_pipeline_backward_weekly_capability_gui_preset.md
```

or:

```text
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
```

Recommended contents:

```text
default CSV path
sample CSV file strategy
when to attach to env
whether GUI preflight should load it
whether scenario selection is needed
how to preserve current guard behavior if file is absent
manual GUI validation flow
```

Recommended safe behavior:

```text
If default CSV exists:
    load and attach context before ctx guard check.

If default CSV does not exist:
    keep current ctx guard diagnostic behavior.
```

---

## 20. Later Work

After env attach is wired, later phases can include:

```text
sample capability master
GUI scenario selection
forward capacity simulation integration
dwell-time calculation
cold-chain shelf-life modeling
PSI monetary KPI evaluation
Price-Cost-Profit propagation
tariff scenario evaluation
```

These should remain separate design topics.

---

## 21. Summary

Explicit Pipeline Backward Weekly Capability Context Phase 1 is complete.

Implemented:

```text
pure context builder
CSV loader
env attach helper
focused tests
```

The canonical context is:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

The key env attribute is:

```python
env.explicit_pipeline_backward_weekly_capability
```

This phase created the fuel container and adapter.

The next phase will define where the fuel file lives and when it is loaded into the WOM runtime.
