# Codex Request: Implement Explicit Pipeline Backward Weekly Capability Env Attach Phase 2A

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design memos and completion memo have already been added:

```text
docs/design/plan_with_capacity_context_and_planning_story.md
docs/design/explicit_pipeline_backward_weekly_capability_context.md
docs/design/explicit_pipeline_backward_weekly_capability_context_completion.md
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
```

Please read these documents first, especially:

```text
docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md
```

Phase 1 already implemented the pure capability context adapter:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

with:

```python
build_explicit_pipeline_backward_weekly_capability(...)
load_explicit_pipeline_backward_weekly_capability_csv(...)
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

This request implements **Phase 2A only**:

```text
runtime attach helper from optional CSV
```

Do not implement GUI preflight wiring in this request.

---

## 2. Main Objective

Add a safe helper that optionally loads:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

and attaches the loaded context to:

```python
env.explicit_pipeline_backward_weekly_capability
```

only when the CSV exists and produces a non-empty valid context.

The helper must preserve current safe behavior:

```text
If the CSV is missing:
    do not crash
    do not attach anything
    return reason="file_missing"

If the CSV exists but yields no valid context:
    do not attach anything
    return reason="empty_context"

If the CSV exists and yields valid non-empty context:
    attach it to env
    return attached=True
```

This request should not modify `cockpit_tk.py`.

---

## 3. Scope of This Request

Implement Phase 2A:

```text
1. maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)
2. deterministic result map
3. env diagnostics
4. focused tests
```

Do not implement:

```text
GUI preflight wiring
Run Full Plan path changes
sample CSV master
manual GUI flow
```

Those are later phases.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Do not modify pysi/gui/cockpit_tk.py in this phase.
2. Do not change Explicit KPI ON checkbox behavior.
3. Do not change ctx guard behavior.
4. Do not bypass ctx guard.
5. Do not generate dummy capability values.
6. Do not create default capability CSV in this request.
7. Do not run planning from the helper.
8. Do not run exports.
9. Do not execute ReplanCommand.
10. Do not implement automatic replanning.
11. Do not implement OR optimization.
12. Do not implement Price-Cost-Profit propagation.
13. Do not implement PSI monetary KPI evaluation.
14. Do not implement tariff simulation.
15. Do not implement process-level capacity.
16. Do not implement cold-chain shelf-life logic.
17. Do not add new dependencies.
```

This request is only for:

```text
optional runtime attach helper + tests
```

---

## 5. Files to Modify

Modify:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_capacity_context.py
```

Avoid modifying:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 6. New Helper Function

Add this function to:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended signature:

```python
def maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env: Any,
    path: str | Path = "data/explicit_pipeline_backward_weekly_capability.csv",
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, Any]:
    ...
```

The helper should use the existing loader:

```python
load_explicit_pipeline_backward_weekly_capability_csv(...)
```

and existing attach helper:

```python
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
```

---

## 7. Return Map Schema

Return a deterministic dictionary with these keys:

```python
{
    "path": str,
    "scenario": scenario,
    "file_exists": bool,
    "attached": bool,
    "record_count": int,
    "node_count": int,
    "product_count": int,
    "reason": str,
}
```

Recommended meanings:

```text
path:
    string form of the input path

scenario:
    scenario argument passed to helper

file_exists:
    whether CSV path exists

attached:
    whether context was attached to env

record_count:
    number of capability entries in canonical nested context

node_count:
    number of top-level nodes in canonical nested context

product_count:
    number of node/product combinations in canonical nested context

reason:
    "" when attached=True
    "file_missing" when path does not exist
    "empty_context" when context is empty
    "load_error" if strict=False and a recoverable load error is caught
```

MVP can avoid `load_error` if the implementation prefers to let unexpected errors raise. But missing file must not raise.

---

## 8. Counting Rules

Given canonical context:

```python
{
    "MOM_A": {
        "P1": {
            "202601": 100,
            "202602": 100,
        },
        "P2": {
            "202601": 50,
        },
    },
    "MOM_B": {
        "P1": {
            "202601": 80,
        },
    },
}
```

Expected counts:

```text
node_count = 2
product_count = 3
record_count = 4
```

Where:

```text
record_count = count of node/product/week capability entries
product_count = count of node/product pairs
```

Keep this deterministic.

---

## 9. Missing File Behavior

If the path does not exist:

```text
do not call loader
do not attach context
record env diagnostics
return attached=False, file_exists=False, reason="file_missing"
```

Expected:

```python
{
    "file_exists": False,
    "attached": False,
    "record_count": 0,
    "node_count": 0,
    "product_count": 0,
    "reason": "file_missing",
}
```

Do not create the file.

Do not create dummy context.

---

## 10. Empty Context Behavior

If file exists but loaded context is `{}`:

```text
do not attach context
record env diagnostics
return attached=False, file_exists=True, reason="empty_context"
```

This preserves ctx guard behavior.

Reason:

```text
an empty capability context should not be treated as a valid fuel supply
```

---

## 11. Valid Context Behavior

If file exists and loaded context is non-empty:

```text
attach context to env
record env diagnostics
return attached=True, reason=""
```

Expected env:

```python
env.explicit_pipeline_backward_weekly_capability = context
```

This should make the existing ctx guard helper pass for this key:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

---

## 12. Env Diagnostics

The helper should set these fields on `env` in all cases:

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

Example missing file case:

```python
env.explicit_pipeline_backward_weekly_capability_attached = False
env.explicit_pipeline_backward_weekly_capability_attach_result = {
    "attached": False,
    "reason": "file_missing",
    ...
}
```

Do not overwrite an existing `env.explicit_pipeline_backward_weekly_capability` when the new attach attempt fails due to missing file or empty context.

This avoids accidentally removing a manually attached context.

---

## 13. Strict Behavior

Default:

```python
strict=False
```

This should be GUI-safe later.

Behavior:

```text
strict=False:
    loader skips invalid rows based on existing builder behavior

strict=True:
    loader / builder may raise ValueError for invalid rows
```

The new helper does not need to catch strict=True validation errors.

For strict=False, if the CSV exists but all rows are invalid, loader returns `{}` and helper returns:

```text
reason="empty_context"
```

---

## 14. Tests to Add

Update:

```text
tests/test_explicit_pipeline_capacity_context.py
```

Add tests for the new helper.

### 14.1 Missing CSV does not attach

Use `tmp_path / "missing.csv"`.

Expected:

```text
result["attached"] is False
result["file_exists"] is False
result["reason"] == "file_missing"
result["record_count"] == 0
not hasattr(env, "explicit_pipeline_backward_weekly_capability")
env.explicit_pipeline_backward_weekly_capability_attached is False
```

### 14.2 Valid CSV attaches context

Create temp CSV:

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,MOM_A,P1,202601,100,output,lot,demo,ok
base,MOM_A,P1,202602,80,output,lot,demo,ok
```

Expected:

```text
result["attached"] is True
result["file_exists"] is True
result["reason"] == ""
result["record_count"] == 2
result["node_count"] == 1
result["product_count"] == 1
env.explicit_pipeline_backward_weekly_capability == {"MOM_A": {"P1": {"202601": 100, "202602": 80}}}
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

### 14.3 Empty / invalid-only CSV does not attach

Create temp CSV with invalid capability:

```csv
scenario,node,product,week,capability_lots,unit
base,MOM_A,P1,202601,abc,lot
```

Expected with strict=False:

```text
result["attached"] is False
result["file_exists"] is True
result["reason"] == "empty_context"
not hasattr(env, "explicit_pipeline_backward_weekly_capability")
ctx guard still reports explicit_pipeline_backward_weekly_capability missing
```

### 14.4 Scenario filtering in attach helper

CSV contains base and constrained rows.

Call:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env,
    csv_path,
    scenario="constrained",
)
```

Expected only constrained context is attached.

### 14.5 Failed attach does not overwrite existing context

Given env already has:

```python
env.explicit_pipeline_backward_weekly_capability = {"EXISTING": {"P": {"W": 1}}}
```

Call helper with missing file.

Expected:

```text
existing context remains unchanged
result["attached"] is False
```

### 14.6 Diagnostics recorded on env

Assert for each path:

```text
explicit_pipeline_backward_weekly_capability_attach_result
explicit_pipeline_backward_weekly_capability_source_path
explicit_pipeline_backward_weekly_capability_source_scenario
explicit_pipeline_backward_weekly_capability_attached
```

---

## 15. Existing Tests to Run

Run focused tests:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_context.py
```

Then related tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Optional related cockpit tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
```

Optional broader tests:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
```

If optional tests are not run, state so clearly.

If Tk tests are skipped, state so clearly.

---

## 16. Manual GUI Validation Not Required

Manual GUI validation is not required for this Phase 2A request.

Reason:

```text
this request does not wire helper into GUI / Run Full Plan
```

Manual GUI validation will be required in Phase 2B or 2C.

---

## 17. Safety Boundaries

Please preserve:

```text
no GUI wiring
no Run Full Plan change
no planning execution
no export execution
no ReplanCommand execution
no automatic dummy context
no sample CSV commit
no monetary KPI calculation
```

This is a runtime attach helper patch only.

---

## 18. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. New helper added
3. Return map schema
4. Missing file behavior
5. Empty context behavior
6. Valid context attach behavior
7. Env diagnostics
8. Existing context preservation behavior
9. Tests added / updated
10. Test commands executed
11. Test results
12. Skipped tests and why
13. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
GUI preflight wiring
sample CSV master commit
manual GUI validation
price-cost-profit propagation
tariff simulation
cold-chain shelf-life logic
```

This request is only for:

```text
Explicit Pipeline Backward Weekly Capability Env Attach Phase 2A
```
