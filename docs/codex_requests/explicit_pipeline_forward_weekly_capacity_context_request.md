# Codex Request: Implement Explicit Pipeline Forward Weekly Capacity Context Adapter Phase F1

## 1. Background

We are working on branch:

```text
feature/explicit-kpi-demo-flag-preset-v0r1
```

The repository is expected to be clean except for local helper `.bat` files.

The following design / completion documents already exist:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard.md
docs/design/explicit_pipeline_forward_weekly_capacity_ctx_guard_completion.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
```

Please read especially:

```text
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
```

The current Explicit KPI ON path now safely detects the following required context keys before running the explicit bridge capacity pipeline:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The backward capability side already has:

```text
build/load/attach/maybe_attach helpers
data/explicit_pipeline_backward_weekly_capability.csv
GUI preflight attach wiring
ctx guard diagnostics
```

The current missing runtime context is:

```text
explicit_pipeline_forward_weekly_capacity
```

This request implements **Phase F1 only**:

```text
forward weekly capacity adapter + tests
```

Do not wire this into the GUI in this request.

---

## 2. Main Objective

Add forward weekly capacity adapter functions that can build, load, attach, and optionally attach:

```text
env.explicit_pipeline_forward_weekly_capacity
```

from a future CSV file.

The recommended runtime context shape is product-first:

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

Example:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

This request must not add the CSV file yet.

---

## 3. Scope of This Request

Implement only:

```text
1. build_explicit_pipeline_forward_weekly_capacity(...)
2. load_explicit_pipeline_forward_weekly_capacity_csv(...)
3. attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
4. maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
5. focused tests
```

Do not implement:

```text
GUI preflight wiring
forward capacity sample CSV
manual GUI validation
explicit bridge capacity pipeline changes
planning engine changes
```

---

## 4. Files to Modify

Expected code file:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Expected new test file:

```text
tests/test_explicit_pipeline_forward_capacity_context.py
```

Avoid modifying:

```text
pysi/gui/cockpit_tk.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
pysi/plan/explicit_bridge_capacity_pipeline.py
data/explicit_pipeline_backward_weekly_capability.csv
```

No data CSV should be added in this phase.

---

## 5. Canonical Runtime Shape

Use this runtime shape:

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

Meaning:

```text
product:
    product name or product id

node:
    capacity owner node id

capacity_type:
    normalized capacity type such as P, S, I

week:
    week bucket string or number preserved from input

capacity_lots:
    non-negative integer lot capacity
```

The first MVP should preserve the week key as string if the input is a string.

---

## 6. Capacity Type Normalization

Required input field:

```text
capacity_type
```

Recommended normalization:

```text
"P"           => "P"
"production"  => "P"
"process"     => "P"
"processing"  => "P"

"S"           => "S"
"shipping"    => "S"
"shipment"    => "S"
"sales"       => "S"

"I"           => "I"
"inventory"   => "I"
"storage"     => "I"
```

Case-insensitive.

Trim spaces.

Unsupported capacity types:

```text
strict=False:
    skip row

strict=True:
    raise ValueError
```

Do not silently map arbitrary values to P.

---

## 7. Unit Handling

Supported unit:

```text
lot
```

Behavior:

```text
blank or missing unit => lot
unit=lot => accepted
other unit => skip in strict=False / raise in strict=True
```

Do not add unit conversion in this request.

---

## 8. Build Function

Add this function to:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended signature:

```python
def build_explicit_pipeline_forward_weekly_capacity(
    rows: Iterable[Mapping[str, Any]],
    *,
    scenario: str | None = "base",
    strict: bool = False,
) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
    ...
```

Supported input row fields:

```text
scenario
product
node
capacity_type
week
capacity_lots
unit
source
note
```

Required logical fields:

```text
product
node
capacity_type
week
capacity_lots
```

Scenario behavior:

```text
blank/missing scenario => base
scenario="base" default filter
scenario=None disables filtering
```

Duplicate behavior:

```text
last valid row wins
```

Example rows:

```python
[
    {
        "scenario": "base",
        "product": "PACKAGED_RICE_STANDARD",
        "node": "MILL_EAST",
        "capacity_type": "P",
        "week": "2027-W40",
        "capacity_lots": "5",
        "unit": "lot",
    },
]
```

Expected context:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5
            }
        }
    }
}
```

---

## 9. Validation Rules

### 9.1 Required String Fields

These fields are required after trim:

```text
product
node
capacity_type
week
```

If missing / blank:

```text
strict=False => skip row
strict=True  => raise ValueError with useful reason
```

### 9.2 Capacity Lots

`capacity_lots` must be numeric and non-negative.

Recommended behavior:

```text
"5"   => 5
"5.0" => 5
5     => 5
5.0   => 5
```

If fractional non-integer value like `5.5`:

```text
strict=False => skip row
strict=True  => raise ValueError
```

If negative:

```text
strict=False => skip row
strict=True  => raise ValueError
```

### 9.3 Unsupported Unit

If unit is unsupported:

```text
strict=False => skip row
strict=True  => raise ValueError
```

### 9.4 Unsupported Capacity Type

If capacity type cannot be normalized:

```text
strict=False => skip row
strict=True  => raise ValueError
```

---

## 10. CSV Loader Function

Add:

```python
def load_explicit_pipeline_forward_weekly_capacity_csv(
    path: str | Path,
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
    ...
```

Use:

```text
csv.DictReader
pathlib.Path
standard library only
```

No pandas dependency.

The loader should delegate to:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
```

---

## 11. Env Attach Function

Add:

```python
def attach_explicit_pipeline_forward_weekly_capacity_to_env(
    env: Any,
    context: Mapping[str, Mapping[str, Mapping[str, Mapping[Any, Any]]]],
) -> Any:
    env.explicit_pipeline_forward_weekly_capacity = context
    return env
```

This should mirror the backward attach helper.

---

## 12. Optional Runtime Attach Helper

Add:

```python
def maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(
    env: Any,
    path: str | Path = "data/explicit_pipeline_forward_weekly_capacity.csv",
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, Any]:
    ...
```

Behavior:

```text
if file missing:
    do not attach
    do not overwrite existing context
    return reason="file_missing"

if file exists but context empty:
    do not attach
    do not overwrite existing context
    return reason="empty_context"

if file exists and context non-empty:
    attach context
    return reason=""
```

No dummy context generation.

No GUI calls.

No planning execution.

---

## 13. Return Map Schema

Return deterministic dictionary:

```python
{
    "path": str,
    "scenario": scenario,
    "file_exists": bool,
    "attached": bool,
    "record_count": int,
    "product_count": int,
    "node_count": int,
    "capacity_type_count": int,
    "reason": str,
}
```

Reasons:

```text
"" when attached=True
file_missing
empty_context
```

Optional `load_error` is not required unless already consistent with existing backward helper style.

---

## 14. Counting Rules

For context:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

Expected counts:

```text
product_count = 1
node_count = 1
capacity_type_count = 1
record_count = 2
```

For context:

```python
{
    "P1": {
        "N1": {
            "P": {"W1": 1, "W2": 2},
            "S": {"W1": 3},
        },
        "N2": {
            "P": {"W1": 4},
        },
    }
}
```

Expected counts:

```text
product_count = 1
node_count = 2
capacity_type_count = 3
record_count = 4
```

Interpretation:

```text
node_count = number of product/node paths
capacity_type_count = number of product/node/capacity_type paths
record_count = number of product/node/capacity_type/week entries
```

---

## 15. Env Diagnostics

The optional attach helper should record these fields on every invocation:

```text
explicit_pipeline_forward_weekly_capacity_attach_result
explicit_pipeline_forward_weekly_capacity_source_path
explicit_pipeline_forward_weekly_capacity_source_scenario
explicit_pipeline_forward_weekly_capacity_attached
```

Example attached:

```python
env.explicit_pipeline_forward_weekly_capacity_attached = True
env.explicit_pipeline_forward_weekly_capacity_source_path = "data/explicit_pipeline_forward_weekly_capacity.csv"
env.explicit_pipeline_forward_weekly_capacity_source_scenario = "base"
env.explicit_pipeline_forward_weekly_capacity_attach_result = {
    "attached": True,
    "reason": "",
    ...
}
```

Example missing file:

```python
env.explicit_pipeline_forward_weekly_capacity_attached = False
env.explicit_pipeline_forward_weekly_capacity_attach_result = {
    "attached": False,
    "reason": "file_missing",
    ...
}
```

Do not remove existing `env.explicit_pipeline_forward_weekly_capacity` on failed attach.

---

## 16. Tests to Add

Add:

```text
tests/test_explicit_pipeline_forward_capacity_context.py
```

### 16.1 Build product-first context

Input rows:

```python
[
    {
        "scenario": "base",
        "product": "PACKAGED_RICE_STANDARD",
        "node": "MILL_EAST",
        "capacity_type": "P",
        "week": "2027-W40",
        "capacity_lots": 5,
        "unit": "lot",
    },
    {
        "scenario": "base",
        "product": "PACKAGED_RICE_STANDARD",
        "node": "MILL_EAST",
        "capacity_type": "P",
        "week": "2027-W41",
        "capacity_lots": 6,
        "unit": "lot",
    },
]
```

Expected:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

### 16.2 Scenario filtering

Rows include:

```text
base
constrained
blank scenario
```

Expected:

```text
default scenario="base" includes base and blank
scenario="constrained" includes constrained only
scenario=None includes all valid rows
```

### 16.3 Capacity type normalization

Test aliases:

```text
P, production, processing
S, shipping, sales
I, inventory, storage
```

Expected normalized keys:

```text
P
S
I
```

### 16.4 Invalid rows skipped in non-strict mode

Invalid cases:

```text
missing product
missing node
missing week
missing capacity_type
capacity_lots=abc
capacity_lots=-1
capacity_lots=5.5
unit=kg
capacity_type=unknown
```

Expected:

```text
strict=False => invalid rows skipped
```

### 16.5 Invalid rows raise in strict mode

For one or more invalid cases:

```text
strict=True => ValueError
```

### 16.6 Duplicate last valid row wins

Same product/node/capacity_type/week appears twice.

Expected:

```text
last valid row overwrites earlier value
```

### 16.7 Loader reads CSV

Use tmp_path CSV.

Expected loaded context matches product-first shape.

### 16.8 Attach helper sets env key

Expected:

```python
env.explicit_pipeline_forward_weekly_capacity == context
```

### 16.9 Maybe attach missing file

Expected:

```text
attached=False
reason=file_missing
does not set env.explicit_pipeline_forward_weekly_capacity
diagnostics recorded
```

### 16.10 Maybe attach valid file

Expected:

```text
attached=True
record_count / product_count / node_count / capacity_type_count correct
env key set
diagnostics recorded
```

### 16.11 Failed attach preserves existing context

If env already has forward capacity and file missing:

```text
existing context remains unchanged
```

### 16.12 Guard clears when backward + forward present

Given env:

```python
attach_explicit_pipeline_backward_weekly_capability_to_env(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
```

Expected:

```python
get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

Use the existing backward attach helper for this test.

---

## 17. Existing Tests to Run

Run new focused test:

```bat
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
```

Run related tests:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py
```

Run cockpit / reporting regression tests:

```bat
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view_tk_rendering.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
```

Run scenario smoke tests:

```bat
python -m pytest tests/test_covid_vaccine_with_capacity_push.py
python -m pytest tests/test_japanese_rice_case_smoke.py
```

If any Tk tests are skipped because of environment, state it clearly.

---

## 18. Safety Boundaries

Please preserve these boundaries:

```text
1. Do not modify pysi/gui/cockpit_tk.py.
2. Do not wire GUI preflight in this request.
3. Do not add data/explicit_pipeline_forward_weekly_capacity.csv.
4. Do not modify explicit bridge capacity pipeline behavior.
5. Do not modify planning engine behavior.
6. Do not add dummy forward capacity.
7. Do not execute exports.
8. Do not execute ReplanCommand.
9. Do not implement price-cost-profit propagation.
10. Do not implement tariff simulation.
11. Do not implement cold-chain or shelf-life logic.
12. Do not add scenario selector.
13. Do not commit outputs/ generated files.
```

This request is only:

```text
forward weekly capacity adapter + tests
```

---

## 19. Expected Files Changed

Expected files:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_explicit_pipeline_forward_capacity_context.py
```

No GUI file should be changed.

No data CSV should be changed.

---

## 20. Expected Response from Codex

After implementation, please summarize:

```text
1. Files changed
2. Functions added
3. Runtime shape implemented
4. Capacity type normalization behavior
5. Scenario filtering behavior
6. Validation behavior strict=False / strict=True
7. Optional attach helper behavior
8. Env diagnostics
9. Tests added
10. Test commands executed
11. Test results
12. Skipped tests and why
13. Safety boundaries preserved
14. Limitations / follow-up
```

Please do not proceed into:

```text
completion memo
GUI preflight wiring
sample forward CSV
main PR
pipeline shape refactor
price-cost-profit propagation
tariff simulation
cold-chain shelf-life modeling
```

This request is only for:

```text
Explicit Pipeline Forward Weekly Capacity Context Adapter Phase F1
```
