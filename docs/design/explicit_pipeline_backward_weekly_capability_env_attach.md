# Explicit Pipeline Backward Weekly Capability Env Attach Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines Phase 2 for:

```text
explicit_pipeline_backward_weekly_capability
```

Phase 1 implemented the pure context adapter:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

with:

```python
build_explicit_pipeline_backward_weekly_capability(...)
load_explicit_pipeline_backward_weekly_capability_csv(...)
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

Phase 2 defines how to attach the capability context to `env` before the Explicit KPI ctx guard runs.

The goal is to move from:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard reports missing:
        explicit_pipeline_backward_weekly_capability
```

to:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
default capability CSV is loaded if present
    ↓
env.explicit_pipeline_backward_weekly_capability is attached
    ↓
ctx guard can pass
    ↓
explicit bridge capacity pipeline may run
```

This memo is about runtime attachment.

It is not about price, cost, profit, tariff, or monetary KPI evaluation.

---

## 2. Current State

Current completed components:

```text
Explicit KPI ON checkbox
demo flag helper
required ctx guard
ctx guard diagnostics view
capability context adapter
CSV loader
env attach helper
```

Current missing runtime link:

```text
default CSV
    ↓
loader
    ↓
env.explicit_pipeline_backward_weekly_capability
    ↓
ctx guard
```

The capability adapter exists, but the GUI / Run Full Plan path does not yet use it.

---

## 3. Scope

This Phase 2 should implement a safe, optional env attach path.

Target behavior:

```text
If default capability CSV exists:
    load it
    attach context to env
    allow ctx guard to pass for this key

If default capability CSV does not exist:
    preserve current ctx guard diagnostic behavior
```

This means:

```text
no file = no crash
bad file in non-strict mode = skip invalid rows
empty context = attach or skip according to design
```

Recommended MVP:

```text
If CSV exists and loaded context is non-empty:
    attach context

If CSV does not exist or context is empty:
    do not attach
    keep ctx guard diagnostic behavior
```

This avoids silently claiming capacity context exists when it contains no usable data.

---

## 4. Non-Goals

This phase must not implement:

```text
Price-Cost-Profit propagation
PSI monetary KPI evaluation
tariff simulation
cold-chain shelf-life modeling
process-level capacity
resource-level capacity
scenario GUI selector
export execution
ReplanCommand execution
automatic replanning
OR optimization
database persistence
large GUI redesign
```

This phase only connects:

```text
default capability CSV
    ↓
env.explicit_pipeline_backward_weekly_capability
```

---

## 5. Default CSV Path

Recommended default path:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Reason:

```text
data/ is already used for runtime / demo CSV inputs
the file is user-editable
the path is easy to inspect during manual GUI validation
```

Alternative future location:

```text
pysi/master_data/explicit_pipeline_backward_weekly_capability_sample.csv
```

Recommended Phase 2 approach:

```text
Use data/explicit_pipeline_backward_weekly_capability.csv as the runtime default.
Do not commit scenario-specific generated output files accidentally.
```

A later sample-master phase can add a sample file intentionally.

---

## 6. Recommended Runtime Helper

Add a small helper near the existing adapter module:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended function:

```python
def maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env: Any,
    path: str | Path = "data/explicit_pipeline_backward_weekly_capability.csv",
    *,
    scenario: str | None = "base",
    strict: bool = False,
) -> dict[str, Any]:
    ...
```

Recommended behavior:

```text
if path does not exist:
    record diagnostic on env
    return result map with attached=False and reason="file_missing"

if path exists:
    load context using load_explicit_pipeline_backward_weekly_capability_csv
    if context is non-empty:
        attach to env
        record diagnostic on env
        return attached=True
    if context is empty:
        record diagnostic on env
        return attached=False and reason="empty_context"
```

Recommended return shape:

```python
{
    "path": "data/explicit_pipeline_backward_weekly_capability.csv",
    "scenario": "base",
    "file_exists": True,
    "attached": True,
    "record_count": 3,
    "node_count": 1,
    "product_count": 1,
    "reason": "",
}
```

For missing file:

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

For empty context:

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

## 7. Env Diagnostics

The attach helper should record diagnostic fields on `env`.

Recommended fields:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_source_path
explicit_pipeline_backward_weekly_capability_source_scenario
explicit_pipeline_backward_weekly_capability_attached
```

Example when attached:

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

Example when missing:

```python
env.explicit_pipeline_backward_weekly_capability_attached = False
env.explicit_pipeline_backward_weekly_capability_attach_result = {
    "attached": False,
    "reason": "file_missing",
    ...
}
```

These diagnostics can later be surfaced in the Explicit KPI View if desired.

---

## 8. GUI / Run Full Plan Integration Point

Current method:

```python
WOMCockpit._maybe_apply_explicit_kpi_demo_flags()
```

currently:

```text
checks Explicit KPI ON
applies demo flags
checks missing ctx
if missing, disables flags and records ctx guard diagnostic
```

Recommended integration:

```text
Inside _maybe_apply_explicit_kpi_demo_flags(),
after confirming Explicit KPI ON is checked,
but before get_missing_explicit_pipeline_demo_ctx_keys(self.env):
    maybe attach capability context from default CSV
```

Pseudo-flow:

```python
if not Explicit KPI ON:
    return None

applied = apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)

maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    self.env,
    path="data/explicit_pipeline_backward_weekly_capability.csv",
    scenario="base",
    strict=False,
)

missing_ctx_keys = get_missing_explicit_pipeline_demo_ctx_keys(self.env)
if missing_ctx_keys:
    guard skip
else:
    keep flags enabled
```

This preserves current guard behavior.

If the CSV is absent, nothing breaks.

If the CSV is present and valid, the guard can pass.

---

## 9. Scenario Selection

MVP scenario:

```text
base
```

No GUI scenario selector in this phase.

Recommended future extension:

```text
env.explicit_pipeline_backward_weekly_capability_scenario
```

or a GUI variable:

```text
var_explicit_pipeline_capability_scenario
```

But for Phase 2:

```text
hardcode scenario="base"
```

This is enough to prove the attachment path.

---

## 10. Sample CSV Strategy

This memo does not require adding a sample CSV in the same implementation patch.

However, manual validation will require a CSV.

Recommended sample content:

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,MOM_A,P1,202601,100,output,lot,demo,MOM output capability
```

For a meaningful WOM GUI scenario, the node/product/week values must match the actual running scenario.

Therefore, Phase 2 can be split into:

```text
Phase 2A:
    implement optional attach helper and GUI preflight hook

Phase 2B:
    create scenario-specific sample CSV
```

This avoids committing an incorrect sample master.

---

## 11. Important Risk: Context Exists but Pipeline Still Fails

Attaching `explicit_pipeline_backward_weekly_capability` clears the current missing ctx guard key.

However, the explicit pipeline may still fail if:

```text
the context shape does not match exact pipeline expectations
node names do not match scenario node ids
product names do not match scenario product ids
week keys do not match engine week buckets
other required ctx values are discovered later
```

Therefore, Phase 2 should preserve safe behavior and tests.

If the pipeline fails after attach, the next step should be to inspect the expected shape in:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Do not remove the guard.

---

## 12. Validation Rules for Runtime Attach

Recommended runtime attach behavior:

```text
strict=False
```

Reason:

```text
GUI demo should not crash due to one bad row
invalid rows should be skipped
if nothing valid remains, context is not attached
ctx guard diagnostic remains visible
```

For CLI or developer testing, strict mode may be used separately.

---

## 13. Tests to Add

Recommended test file:

```text
tests/test_explicit_pipeline_capacity_context.py
```

Add tests for the new helper.

### 13.1 Missing CSV does not attach

Given temp path that does not exist:

```python
env = SimpleNamespace()
result = maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env, missing_path)
```

Expected:

```text
result["attached"] is False
result["reason"] == "file_missing"
not hasattr(env, "explicit_pipeline_backward_weekly_capability")
```

### 13.2 Valid CSV attaches context

Given temp CSV with valid row:

```text
base,MOM_A,P1,202601,100,output,lot,demo,ok
```

Expected:

```text
result["attached"] is True
env.explicit_pipeline_backward_weekly_capability == {"MOM_A": {"P1": {"202601": 100}}}
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

### 13.3 Empty CSV / invalid only does not attach

Given CSV with invalid rows only:

```text
capability_lots=abc
```

Expected:

```text
result["attached"] is False
result["reason"] == "empty_context"
ctx guard still reports missing key
```

### 13.4 Scenario filter

Given CSV with base and constrained rows:

```text
scenario="constrained"
```

Expected constrained row is attached.

### 13.5 Diagnostics recorded on env

Assert:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_attached
source path
scenario
```

---

## 14. GUI Wiring Tests

Recommended test file:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Add a focused test only if the GUI preflight is modified in the implementation phase.

Test idea:

```text
Explicit KPI ON
default CSV path monkeypatched or helper monkeypatched to attach context
_maybe_apply_explicit_kpi_demo_flags(fake)
ctx guard does not skip
enable_explicit_bridge_capacity_pipeline remains True
```

However, because default path is hardcoded, tests should avoid depending on real `data/` file.

Recommended approach:

```text
monkeypatch the attach helper imported/called by _maybe_apply_explicit_kpi_demo_flags
```

or keep Phase 2A as helper only and defer GUI preflight test to Phase 2B.

---

## 15. Completion Criteria

Phase 2 design is complete when implementation can achieve:

```text
[OK] default CSV attach helper exists
[OK] missing file does not crash
[OK] valid CSV attaches env.explicit_pipeline_backward_weekly_capability
[OK] invalid-only CSV does not attach and preserves ctx guard behavior
[OK] attach diagnostics are recorded on env
[OK] strict=False is used for GUI-safe path
[OK] no dummy capability is generated
[OK] no planning/export/replan execution is added
[OK] focused tests pass
```

If GUI preflight is included:

```text
[OK] Explicit KPI ON attempts optional attach before ctx guard
[OK] no file keeps current diagnostic behavior
[OK] valid file can let guard pass
```

---

## 16. Manual GUI Validation Target

After implementation and sample CSV preparation:

```text
1. create data/explicit_pipeline_backward_weekly_capability.csv
2. python -m main
3. check Explicit KPI ON
4. Run Full Plan
5. open Explicit KPI View
6. confirm missing context diagnostic for explicit_pipeline_backward_weekly_capability disappears
```

If the explicit pipeline then produces reports:

```text
Capacity Report: Yes
Issue Candidates: Yes
Cost / KPI Bundle: maybe, depending on other flags/context
```

If it still fails or remains unavailable, inspect:

```text
pipeline-required shape
node/product/week mismatch
other required context keys
```

---

## 17. Recommended Implementation Phases

Recommended next implementation split:

### Phase 2A: Runtime attach helper only

```text
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
tests
```

No GUI change.

### Phase 2B: GUI preflight optional attach

```text
call helper before ctx guard in _maybe_apply_explicit_kpi_demo_flags()
tests
```

### Phase 2C: Scenario-specific sample CSV

```text
add sample file after confirming correct node/product/week values
manual GUI validation
```

This staged approach keeps each patch small and reversible.

---

## 18. Summary

Phase 1 created the adapter.

Phase 2 should create the runtime attachment path.

The safe rule is:

```text
If capability CSV exists and yields non-empty context:
    attach it to env

If not:
    preserve current ctx guard diagnostic behavior
```

This moves WOM from:

```text
fuel adapter exists
```

to:

```text
fuel can be loaded into the runtime before the explicit pipeline starts
```

The next implementation should still remain conservative: no dummy data, no planning side effects, and no monetary KPI expansion.
