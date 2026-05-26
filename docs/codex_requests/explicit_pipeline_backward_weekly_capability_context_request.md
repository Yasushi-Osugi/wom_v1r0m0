# Codex Request: Implement Explicit Pipeline Backward Weekly Capability Context Phase 1

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The following design memos have already been added:

```text
docs/design/plan_with_capacity_context_and_planning_story.md
docs/design/explicit_pipeline_backward_weekly_capability_context.md
```

Please read these design memos first.

The current GUI behavior is:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard checks env.explicit_pipeline_backward_weekly_capability
    ↓
if missing:
        explicit pipeline is safely skipped
        Explicit KPI View shows missing context diagnostic
```

The current missing key shown in the cockpit is:

```text
explicit_pipeline_backward_weekly_capability
```

This request implements the first concrete capability-context layer so that WOM can eventually move from:

```text
diagnostic unavailable state
```

toward:

```text
capacity-aware planning output
```

---

## 2. Main Objective

Implement a pure, deterministic context builder for:

```text
explicit_pipeline_backward_weekly_capability
```

The MVP context means:

```text
MOM node / product / week capability in lot count
```

Recommended canonical context:

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
    "MOM_JP_FG": {
        "RICE_5KG": {
            "202601": 100,
            "202602": 100,
            "202603": 80,
        }
    }
}
```

This request should focus on **pure adapter / loader / env attach helper**.

Do **not** wire this into the GUI yet unless explicitly requested in a later phase.

---

## 3. Scope of This Request

Implement Phase 1 only:

```text
1. build canonical capability context from records
2. load capability context from CSV
3. attach capability context to env
4. tests for builder / loader / env attach
```

Do not implement GUI integration in this request.

Do not modify the existing Run Full Plan path in this request.

---

## 4. Important Constraints

Please follow these constraints strictly:

```text
1. Do not modify cockpit_tk.py in this phase.
2. Do not change Explicit KPI ON checkbox behavior.
3. Do not bypass or remove ctx guard.
4. Do not generate dummy capability values silently.
5. Do not run planning from the loader.
6. Do not run exports.
7. Do not execute ReplanCommand.
8. Do not implement automatic replanning.
9. Do not implement OR optimization.
10. Do not implement Price-Cost-Profit propagation.
11. Do not implement Cost / KPI context generation.
12. Do not implement tariff simulation.
13. Do not implement process-level capacity.
14. Do not implement cold-chain shelf-life logic.
15. Do not add new dependencies.
```

This request is only for:

```text
explicit_pipeline_backward_weekly_capability context construction
```

---

## 5. Files to Add / Modify

Recommended new module:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended new test file:

```text
tests/test_explicit_pipeline_capacity_context.py
```

Optional package export if project style supports it:

```text
pysi/plan/__init__.py
```

Only modify `pysi/plan/__init__.py` if it is already used for public exports.

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

unless a tiny compatibility issue is unavoidable.

---

## 6. Recommended Public Functions

Implement these functions.

### 6.1 build_explicit_pipeline_backward_weekly_capability

```python
def build_explicit_pipeline_backward_weekly_capability(
    records: Iterable[Mapping[str, Any]],
    *,
    scenario: str | None = "base",
    strict: bool = False,
) -> dict[str, dict[str, dict[Any, int]]]:
    ...
```

Responsibilities:

```text
read record-like mappings
optionally filter by scenario
validate required fields
coerce capability_lots to int
skip invalid records when strict=False
raise ValueError for invalid records when strict=True
return nested canonical dict
```

Canonical result:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

### 6.2 load_explicit_pipeline_backward_weekly_capability_csv

```python
def load_explicit_pipeline_backward_weekly_capability_csv(
    path: str | Path,
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, dict[str, dict[Any, int]]]:
    ...
```

Responsibilities:

```text
read CSV file
pass rows to builder
return canonical context
```

Use Python standard library only:

```python
csv.DictReader
pathlib.Path
```

### 6.3 attach_explicit_pipeline_backward_weekly_capability_to_env

```python
def attach_explicit_pipeline_backward_weekly_capability_to_env(
    env: Any,
    context: Mapping[str, Mapping[str, Mapping[Any, Any]]],
) -> Any:
    ...
```

Responsibilities:

```text
set env.explicit_pipeline_backward_weekly_capability = context
return env
```

This makes chaining and testing easy.

---

## 7. CSV Schema

Expected CSV columns:

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

Required columns for MVP:

```text
node
product
week
capability_lots
```

Optional columns:

```text
scenario
capability_type
unit
source
note
```

Default scenario behavior:

```text
scenario="base"
```

If a row has no scenario value, treat it as:

```text
base
```

If `scenario=None`, do not filter by scenario.

---

## 8. Field Semantics

### 8.1 node

Required.

Blank node is invalid.

### 8.2 product

Required.

Blank product is invalid.

### 8.3 week

Required.

Blank week is invalid.

Preserve the week key as provided by CSV / record for MVP.

Do not force conversion to int unless current project conventions clearly require it.

### 8.4 capability_lots

Required.

Must be numeric and non-negative.

Recommended MVP conversion:

```python
int(float(value))
```

Examples:

```text
"100"   -> 100
"100.0" -> 100
100     -> 100
```

Invalid examples:

```text
"abc"
""
None
-1
```

### 8.5 unit

MVP unit should be:

```text
lot
```

If unit is blank, treat as `lot`.

If unit is non-blank and not `lot`, recommended MVP behavior:

```text
strict=True:
    raise ValueError

strict=False:
    skip the row
```

Reason:

```text
unit conversion from pieces/kg/pallets to lots is out of scope for this phase
```

### 8.6 capability_type

Optional.

MVP accepts any value but does not use it.

Default meaning:

```text
output
```

---

## 9. Duplicate Row Behavior

Duplicate means same:

```text
scenario / node / product / week
```

Recommended MVP behavior:

```text
last valid row wins
```

This is simple and deterministic.

Do not sum duplicates in this phase unless design explicitly changes later.

---

## 10. Strict vs Non-Strict Behavior

### 10.1 strict=False

Default.

Invalid rows should be skipped.

The function should not fail on one bad row.

### 10.2 strict=True

Invalid row should raise `ValueError` with a useful message.

The message should include the reason, such as:

```text
missing node
missing product
missing week
invalid capability_lots
negative capability_lots
unsupported unit
```

Do not over-engineer row-number reporting unless easy.

---

## 11. Empty Input Behavior

If records are empty or no valid records remain:

```python
{}
```

should be returned.

Do not raise by default.

In strict mode, empty input may still return `{}` unless a required file/records policy is explicitly defined later.

---

## 12. Env Attach Behavior

Given:

```python
context = {
    "MOM_A": {
        "P1": {
            "202601": 100
        }
    }
}
```

After:

```python
attach_explicit_pipeline_backward_weekly_capability_to_env(env, context)
```

Expected:

```python
env.explicit_pipeline_backward_weekly_capability == context
```

This should make the existing guard helper return no missing key:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

Use an existing guard helper in tests if importable:

```python
from pysi.reporting.explicit_pipeline_kpi_demo_flags import (
    get_missing_explicit_pipeline_demo_ctx_keys,
)
```

---

## 13. Tests to Add

Add:

```text
tests/test_explicit_pipeline_capacity_context.py
```

Recommended tests:

### 13.1 Build simple nested context

Input:

```python
[
    {
        "node": "MOM_A",
        "product": "P1",
        "week": "202601",
        "capability_lots": "100",
    }
]
```

Expected:

```python
{"MOM_A": {"P1": {"202601": 100}}}
```

### 13.2 Scenario filtering

Input has `base` and `constrained`.

With `scenario="base"`, only base rows are included.

With `scenario=None`, all rows are included.

### 13.3 Blank scenario defaults to base

Row with `scenario=""` is included when `scenario="base"`.

### 13.4 Duplicate last row wins

Two rows for same node/product/week.

Expected capability equals later row.

### 13.5 Invalid numeric skipped in non-strict

Input has one invalid row and one valid row.

Expected only valid row remains.

### 13.6 Invalid numeric raises in strict

With `strict=True`, invalid numeric raises `ValueError`.

### 13.7 Negative capability handling

Negative capability skipped in non-strict.

Negative capability raises in strict.

### 13.8 Unsupported unit handling

`unit="piece"` is skipped in non-strict.

`unit="piece"` raises in strict.

### 13.9 CSV loader

Use `tmp_path` to create CSV file.

Load and assert canonical nested context.

### 13.10 Env attach clears existing guard missing key

Create `SimpleNamespace()`.

Before attach:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

contains:

```text
explicit_pipeline_backward_weekly_capability
```

After attach:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

---

## 14. Existing Tests to Run

Run new tests:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_context.py
```

Then run related guard / cockpit tests:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
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

## 15. Manual Validation Not Required Yet

Manual GUI validation is not required for this Phase 1 pure adapter request.

Reason:

```text
this request does not wire CSV loading into GUI / Run Full Plan
```

Manual GUI validation will be needed in a later phase once:

```text
CSV load / env attach
```

is connected to:

```text
Explicit KPI ON preflight
```

---

## 16. Safety Boundaries

Please preserve these safety boundaries:

```text
no GUI wiring
no Run Full Plan change
no planning execution
no export execution
no ReplanCommand execution
no automatic fallback dummy context
no monetary KPI calculation
```

This is a pure data-context builder patch.

---

## 17. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Public functions added
3. Canonical context schema implemented
4. CSV schema supported
5. Scenario filtering behavior
6. Strict / non-strict invalid row behavior
7. Unit handling behavior
8. Duplicate row behavior
9. Env attach behavior
10. Tests added
11. Test commands executed
12. Test results
13. Skipped tests and why
14. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
main PR
GUI preflight wiring
sample CSV master commit
price-cost-profit propagation
tariff simulation
cold-chain shelf-life logic
```

This request is only for:

```text
Explicit Pipeline Backward Weekly Capability Context Phase 1
```
