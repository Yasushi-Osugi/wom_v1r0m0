# Explicit Pipeline Backward Weekly Capability Env Attach Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-26  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_env_attach_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of **Explicit Pipeline Backward Weekly Capability Env Attach Phase 2A**.

The purpose of Phase 2A was to add a safe runtime helper that can optionally load:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

and attach the loaded capability context to:

```python
env.explicit_pipeline_backward_weekly_capability
```

only when the file exists and produces a non-empty valid context.

This phase did **not** wire the helper into GUI preflight.

This phase did **not** modify `Run Full Plan`.

This phase did **not** add a sample CSV master.

The scope was intentionally limited to:

```text
optional CSV attach helper + tests
```

---

## 2. Background

Before this phase, Phase 1 had already implemented the pure adapter:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

with these functions:

```python
build_explicit_pipeline_backward_weekly_capability(...)
load_explicit_pipeline_backward_weekly_capability_csv(...)
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

That meant WOM had the ability to build and attach the context, but no safe helper existed for the common runtime pattern:

```text
if default CSV exists:
    load it
    attach it to env
else:
    preserve current ctx guard behavior
```

Phase 2A added that missing optional attach helper.

---

## 3. Implemented Commit

The implementation was committed as:

```text
bd8d2df Add optional CSV attach helper for explicit capability context
```

This commit was pushed to:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

---

## 4. Files Changed

The implementation changed two files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_capacity_context.py
```

No GUI files were changed.

No Run Full Plan path was changed.

No sample CSV file was added.

---

## 5. New Helper Added

The following helper was added:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
```

Expected signature:

```python
def maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env,
    path="data/explicit_pipeline_backward_weekly_capability.csv",
    *,
    scenario="base",
    strict=False,
    encoding="utf-8-sig",
) -> dict:
    ...
```

Purpose:

```text
Safely try to load capability context from CSV and attach it to env only when usable.
```

This helper uses the existing Phase 1 functions:

```python
load_explicit_pipeline_backward_weekly_capability_csv(...)
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

---

## 6. Return Map Schema

The helper returns a deterministic result map with the following keys:

```text
path
scenario
file_exists
attached
record_count
node_count
product_count
reason
```

Example successful return:

```python
{
    "path": "data/explicit_pipeline_backward_weekly_capability.csv",
    "scenario": "base",
    "file_exists": True,
    "attached": True,
    "record_count": 2,
    "node_count": 1,
    "product_count": 1,
    "reason": "",
}
```

Example missing-file return:

```python
{
    "path": "...",
    "scenario": "base",
    "file_exists": False,
    "attached": False,
    "record_count": 0,
    "node_count": 0,
    "product_count": 0,
    "reason": "file_missing",
}
```

Example empty-context return:

```python
{
    "path": "...",
    "scenario": "base",
    "file_exists": True,
    "attached": False,
    "record_count": 0,
    "node_count": 0,
    "product_count": 0,
    "reason": "empty_context",
}
```

---

## 7. Count Semantics

The helper counts canonical nested context entries using the schema:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

Counting rules:

```text
node_count:
    number of top-level nodes

product_count:
    number of node/product combinations

record_count:
    number of node/product/week capability entries
```

Example:

```python
{
    "MOM_A": {
        "P1": {
            "202601": 100,
            "202602": 80,
        }
    }
}
```

Counts:

```text
node_count = 1
product_count = 1
record_count = 2
```

---

## 8. Missing File Behavior

When the CSV file does not exist, the helper:

```text
does not crash
does not call the loader
does not attach context
does not create a dummy context
returns reason="file_missing"
records diagnostics on env
```

This preserves the current ctx guard behavior.

In this case, the existing `env.explicit_pipeline_backward_weekly_capability` is not modified.

---

## 9. Empty Context Behavior

When the CSV exists but yields an empty context, the helper:

```text
does not attach context
returns reason="empty_context"
records diagnostics on env
preserves current ctx guard behavior
```

An empty context can occur when:

```text
the CSV has no rows
the scenario filter excludes all rows
all rows are invalid under strict=False
all rows have unsupported units under strict=False
```

The important rule is:

```text
empty context is not treated as valid fuel
```

---

## 10. Valid Context Attach Behavior

When the CSV exists and yields a non-empty valid context, the helper:

```text
attaches context to env.explicit_pipeline_backward_weekly_capability
returns attached=True
returns reason=""
records diagnostics on env
```

This makes the existing ctx guard capable of passing for:

```text
explicit_pipeline_backward_weekly_capability
```

assuming no other required ctx is missing.

---

## 11. Existing Context Preservation

The helper preserves any existing context when a new attach attempt fails.

For example, if env already has:

```python
env.explicit_pipeline_backward_weekly_capability = {
    "EXISTING": {
        "P": {
            "W": 1
        }
    }
}
```

and the helper is called with a missing file, the existing context remains unchanged.

This avoids accidentally removing a manually attached or test-supplied capability context.

---

## 12. Env Diagnostics Added

The helper records diagnostics on `env` for every invocation.

Diagnostic fields:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_source_path
explicit_pipeline_backward_weekly_capability_source_scenario
explicit_pipeline_backward_weekly_capability_attached
```

Example attached case:

```python
env.explicit_pipeline_backward_weekly_capability_attached = True
env.explicit_pipeline_backward_weekly_capability_source_path = "data/explicit_pipeline_backward_weekly_capability.csv"
env.explicit_pipeline_backward_weekly_capability_source_scenario = "base"
env.explicit_pipeline_backward_weekly_capability_attach_result = {
    "attached": True,
    "reason": "",
    ...
}
```

Example missing-file case:

```python
env.explicit_pipeline_backward_weekly_capability_attached = False
env.explicit_pipeline_backward_weekly_capability_attach_result = {
    "attached": False,
    "reason": "file_missing",
    ...
}
```

---

## 13. Tests Added / Updated

The following test file was updated:

```text
tests/test_explicit_pipeline_capacity_context.py
```

The test count increased to 16.

New test coverage includes:

```text
missing CSV behavior
valid CSV attach behavior
invalid-only CSV behavior
scenario filtering in attach helper
failed attach does not overwrite existing context
diagnostics are recorded on env
```

---

## 14. Test Results

The following tests were executed successfully:

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
tests/test_explicit_pipeline_capacity_context.py                         16 passed
tests/test_explicit_pipeline_kpi_demo_flags.py                            6 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py                  5 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py              10 passed
tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py         9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py  4 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py                 7 passed
tests/test_explicit_pipeline_reporting_flags.py                          10 passed
tests/test_covid_vaccine_with_capacity_push.py                            1 passed
```

Total observed result:

```text
68 passed
```

No skipped tests were observed in this run.

---

## 15. Scope Boundaries Preserved

This phase intentionally did not implement:

```text
GUI preflight wiring
Run Full Plan path changes
default CSV creation
sample CSV master commit
manual GUI validation
planning execution
export execution
ReplanCommand execution
automatic replanning
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
process-level capacity
resource-level capacity
```

This phase remained a runtime attach helper patch only.

---

## 16. Meaning of This Milestone

Before this phase:

```text
WOM had a builder and CSV loader,
but no single safe helper for optional runtime attachment.
```

After this phase:

```text
WOM has a helper that can safely try to load the default capability CSV and attach the context to env.
```

This moves the implementation from:

```text
fuel container and adapter exist
```

to:

```text
fuel can be loaded into runtime when a CSV file exists
```

The GUI still does not automatically call the helper.

That is the next phase.

---

## 17. Current State

Current state:

```text
ctx guard exists
ctx guard diagnostics are visible in Explicit KPI View
capability context design exists
capability context adapter exists
optional CSV attach helper exists
tests pass
GUI preflight is not yet wired to the helper
sample capability CSV is not yet committed
```

Therefore:

```text
Explicit KPI ON can still show missing context in the GUI
unless a future path calls the attach helper before the ctx guard runs.
```

This is expected.

---

## 18. Recommended Next Step

The next design should define Phase 2B:

```text
call maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
from Explicit KPI ON preflight before ctx guard checks missing keys
```

Recommended next design memo:

```text
docs/design/explicit_pipeline_backward_weekly_capability_gui_preflight.md
```

Recommended safe behavior:

```text
if Explicit KPI ON is unchecked:
    do nothing

if Explicit KPI ON is checked:
    apply demo flags
    try optional capability CSV attach
    run ctx guard
```

If default CSV is missing:

```text
current diagnostic behavior remains unchanged
```

If default CSV is present and valid:

```text
env.explicit_pipeline_backward_weekly_capability is attached
ctx guard can pass
explicit pipeline can attempt to run
```

---

## 19. Later Work

After Phase 2B, later phases may include:

```text
scenario-specific sample CSV
manual GUI validation
node/product/week matching check
pipeline shape compatibility check
capacity report availability confirmation
scenario selector
PSI monetary KPI evaluation
dwell-time calculation
cold-chain shelf-life modeling
```

These should remain separate and incremental.

---

## 20. Summary

Explicit Pipeline Backward Weekly Capability Env Attach Phase 2A is complete.

Implemented:

```text
optional runtime CSV attach helper
deterministic result map
context counting
env diagnostics
existing-context preservation
focused tests
```

The new helper is the bridge from:

```text
CSV capability master
```

to:

```text
env.explicit_pipeline_backward_weekly_capability
```

The next phase will connect this helper to the Explicit KPI ON preflight.
