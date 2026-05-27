# Explicit Pipeline Forward Weekly Capacity Context Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-27  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_forward_weekly_capacity_context.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the design direction for:

```text
explicit_pipeline_forward_weekly_capacity
```

The immediate motivation is the current Explicit KPI ON path.

The system now safely detects missing context keys before running the explicit bridge capacity pipeline:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The backward capability side has already been supplied by:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

for the Japanese Rice Case sample.

The remaining missing context is:

```text
explicit_pipeline_forward_weekly_capacity
```

This memo defines what that context should mean, what shape it should have, where it should come from, and how it should be implemented safely.

---

## 2. Current State

Current completed pieces:

```text
Explicit KPI ON checkbox
demo flag preset helper
ctx guard
ctx guard diagnostics view
backward capability context adapter
backward capability CSV attach helper
GUI preflight attach wiring
Japanese Rice Case backward capability sample CSV
forward weekly capacity ctx guard
manual GUI validation that Run Full Plan no longer crashes
```

Current GUI behavior:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
backward capability is loaded / attached
    ↓
forward weekly capacity is missing
    ↓
ctx guard skips explicit pipeline safely
    ↓
Explicit KPI View shows:
        Missing Context: explicit_pipeline_forward_weekly_capacity
```

This is the correct safe intermediate state.

The next task is to define and supply:

```text
env.explicit_pipeline_forward_weekly_capacity
```

---

## 3. Conceptual Meaning

`explicit_pipeline_forward_weekly_capacity` represents the **capacity available during forward execution simulation**.

In WOM planning terms:

```text
backward planning:
    defines ideal / required positioning from demand backward

forward planning:
    executes actual flow under weekly capacity constraints
```

Therefore:

```text
explicit_pipeline_backward_weekly_capability
```

answers:

```text
What capability assumption is needed or available when looking backward from demand?
```

while:

```text
explicit_pipeline_forward_weekly_capacity
```

answers:

```text
What weekly capacity limits the actual forward execution of lots?
```

In simple terms:

```text
backward capability = planning-side required or available capability context
forward capacity    = execution-side weekly capacity constraint
```

---

## 4. Important Design Separation

This memo intentionally separates three concepts:

```text
1. backward weekly capability
2. forward weekly capacity
3. monetary KPI / price-cost-profit evaluation
```

The forward capacity context is about **quantity and lot execution constraints**.

It is not about:

```text
revenue
cost
profit
tariff
price propagation
inventory valuation
```

Those belong to the PSI monetary evaluation layer and should remain outside this specific context design.

---

## 5. Why This Context Is Needed

The explicit bridge capacity pipeline currently requires:

```text
explicit_pipeline_backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
```

The backward side can now be supplied.

The forward side is needed so the explicit pipeline can compare:

```text
planned / required lots
against
available weekly capacity
```

and then generate:

```text
capacity report
capacity violations
lot exceptions
issue candidates
replan candidates
Cost/KPI impact candidates
```

Without forward capacity, the pipeline cannot determine whether a lot flow is feasible in execution.

---

## 6. Candidate Canonical Shape

The most important design question is the shape of:

```python
env.explicit_pipeline_forward_weekly_capacity
```

Two candidate shapes exist.

---

## 7. Candidate A: Node-First Shape

Node-first shape:

```python
{
    node: {
        product: {
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
    "MILL_EAST": {
        "PACKAGED_RICE_STANDARD": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

Advantages:

```text
aligns with backward capability adapter shape direction
natural for node capacity master
easy to inspect by physical capacity owner
```

Disadvantages:

```text
may not match existing explicit bridge capacity pipeline expectations
```

---

## 8. Candidate B: Product-First Shape

Product-first shape:

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

Advantages:

```text
matches patterns already seen in some explicit capacity pipeline tests
natural when the pipeline evaluates a selected product first
aligns with GUI selected product context
```

Disadvantages:

```text
different from the backward capability adapter shape
less natural for capacity-owner master data
```

---

## 9. Recommended Canonical Runtime Shape

Recommended runtime shape for `explicit_pipeline_forward_weekly_capacity`:

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

That is:

```text
product-first
```

Reason:

```text
1. Existing explicit pipeline tests have used product-first forward capacity-like structures.
2. GUI execution is product-selected.
3. The explicit bridge pipeline likely receives / operates against a selected product.
4. Capacity type P/S/I needs a level in the structure.
```

Therefore, for the runtime env context, use:

```text
product → node → capacity_type → week → capacity_lots
```

This does not mean that CSV or master data must be product-first internally.

CSV can remain row-based.

The adapter should convert row-based master input into the product-first runtime shape.

---

## 10. Capacity Type

The forward capacity context should explicitly include:

```text
capacity_type
```

Recommended values:

```text
P = production / processing capacity
S = shipping / sales / outbound capacity
I = inventory / storage capacity
```

For the Japanese Rice Case sample:

```text
MILL_EAST
PACKAGED_RICE_STANDARD
2027-W40 / 2027-W41
capacity_type = P
```

Reason:

```text
MILL_EAST is a milling / processing capacity proxy.
```

The CSV may use a more descriptive value such as:

```text
capacity_type=P
```

or:

```text
capacity_type=production
```

but the runtime canonical context should use a normalized type.

Recommended MVP:

```text
accept P
accept production and normalize to P
accept output and normalize to P only if clearly intended
```

However, to avoid ambiguity, the Phase 1 forward capacity sample should use:

```text
capacity_type=P
```

not `output`.

---

## 11. Unit

Recommended unit:

```text
lot
```

MVP behavior:

```text
blank unit => lot
unit=lot => accepted
other units => skip in non-strict mode / raise in strict mode
```

This mirrors the backward capability adapter behavior.

Future extensions may support:

```text
kg
case
pallet
ton
hour
machine_hour
```

but those should require explicit conversion rules.

---

## 12. Source Master

The forward capacity context should be generated from capacity input rows.

Known Japanese Rice Case capacity-related row concept:

```text
scenario_id = RICE_AS_IS
product_id = PACKAGED_RICE_STANDARD
capacity_owner_type = node
capacity_owner_id = MILL_EAST
week = 2027-W40 / 2027-W41
capacity_type = P
capacity_qty = 5.0 / 6.0
```

For runtime default preflight compatibility, the CSV can use:

```text
scenario = base
```

as done for backward capability.

However, the semantic source remains:

```text
Japanese Rice Case / RICE_AS_IS
```

Recommended source fields:

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

---

## 13. Proposed CSV Schema

Proposed CSV path for forward capacity:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Proposed columns:

```text
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
```

Example:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

This CSV is product-first in column order, but row-based.

The adapter should build:

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

---

## 14. Adapter Functions

Recommended module:

```text
pysi/plan/explicit_pipeline_forward_capacity_context.py
```

or, if keeping all explicit capacity context logic together:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended MVP location:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
backward capability helper already lives there
smaller patch
fewer imports
easy shared validation behavior
```

Recommended functions:

```python
build_explicit_pipeline_forward_weekly_capacity(...)
load_explicit_pipeline_forward_weekly_capacity_csv(...)
attach_explicit_pipeline_forward_weekly_capacity_to_env(...)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)
```

The helper should attach:

```python
env.explicit_pipeline_forward_weekly_capacity = context
```

---

## 15. Build Function

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

Input rows may include:

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

Required fields:

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

---

## 16. Loader Function

Recommended signature:

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

---

## 17. Attach Helper

Recommended signature:

```python
def attach_explicit_pipeline_forward_weekly_capacity_to_env(
    env: Any,
    context: Mapping[str, Mapping[str, Mapping[str, Mapping[Any, Any]]]],
) -> Any:
    env.explicit_pipeline_forward_weekly_capacity = context
    return env
```

---

## 18. Optional Runtime Attach Helper

Recommended signature:

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

Recommended result map:

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
"" when attached
file_missing
empty_context
```

Do not attach empty context.

Do not overwrite an existing context on failed attach.

---

## 19. Counting Rules

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

Counts:

```text
product_count = 1
node_count = 1
capacity_type_count = 1
record_count = 2
```

For:

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

Counts:

```text
product_count = 1
node_count = 2
capacity_type_count = 3
record_count = 4
```

Recommended interpretation:

```text
node_count = number of product/node pairs
capacity_type_count = number of product/node/capacity_type paths
record_count = number of product/node/capacity_type/week entries
```

This is deterministic and consistent with product-first nested context.

---

## 20. Env Diagnostics

Optional attach helper should record:

```text
explicit_pipeline_forward_weekly_capacity_attach_result
explicit_pipeline_forward_weekly_capacity_source_path
explicit_pipeline_forward_weekly_capacity_source_scenario
explicit_pipeline_forward_weekly_capacity_attached
```

Example attached:

```python
env.explicit_pipeline_forward_weekly_capacity_attached = True
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

---

## 21. GUI Preflight Wiring

After the forward capacity optional attach helper is implemented, the GUI preflight should call it before ctx guard.

Current preflight order:

```text
apply demo flags
attach backward capability from CSV
ctx guard check
```

Future preflight order:

```text
apply demo flags
attach backward capability from CSV
attach forward weekly capacity from CSV
ctx guard check
```

Recommended private method:

```python
WOMCockpit._maybe_attach_explicit_pipeline_forward_weekly_capacity()
```

that delegates to:

```python
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(self.env)
```

This should mirror the backward helper structure.

---

## 22. Relationship to Backward Capability

Backward capability currently uses a node-first runtime shape:

```python
{
    node: {
        product: {
            week: capability_lots
        }
    }
}
```

Forward capacity is recommended as product-first:

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

This asymmetry is acceptable if it reflects the explicit pipeline’s actual expectations.

However, it should be documented clearly.

Interpretation:

```text
backward capability:
    capacity owner perspective / planning requirement context

forward capacity:
    selected product execution perspective / capacity check context
```

If later pipeline review shows both should use the same shape, a separate refactor should handle that.

---

## 23. Japanese Rice Case vs iPhone GUI Demo

Important observation:

```text
Manual GUI currently defaults to product IPHONE_NM_2028_BASE.
The sample backward capability CSV is for PACKAGED_RICE_STANDARD.
```

This means:

```text
Rice Case sample CSV may clear ctx guard presence,
but may not produce meaningful iPhone GUI explicit KPI results.
```

Therefore, the next implementation must separate two validation goals.

### 23.1 Context Guard Validation

Goal:

```text
ensure required env keys can be attached and Run Full Plan does not crash
```

This can use Japanese Rice Case sample values.

### 23.2 Meaningful Pipeline Result Validation

Goal:

```text
capacity report / issue candidates / KPI view populate meaningfully
```

This requires scenario alignment:

```text
product
node
week
tree
capacity rows
```

For iPhone GUI demo, a separate iPhone-specific forward capacity sample may be needed.

For Japanese Rice Case, a Rice-specific runner or GUI scenario selection may be needed.

---

## 24. Implementation Phases

Recommended implementation should be staged.

### Phase F1: Forward Capacity Adapter

Implement:

```text
build_explicit_pipeline_forward_weekly_capacity
load_explicit_pipeline_forward_weekly_capacity_csv
attach_explicit_pipeline_forward_weekly_capacity_to_env
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv
tests
```

No GUI change.

No sample CSV.

### Phase F2: GUI Preflight Attach

Wire:

```text
WOMCockpit._maybe_attach_explicit_pipeline_forward_weekly_capacity()
```

before ctx guard.

No sample CSV.

### Phase F3: Forward Capacity Sample CSV

Add:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

with Japanese Rice Case sample rows.

Add loader / attach tests.

### Phase F4: Manual GUI Validation

Run:

```text
Explicit KPI ON
Run Full Plan
Explicit KPI View
```

Expected first success:

```text
missing explicit_pipeline_forward_weekly_capacity disappears
```

If view remains empty, proceed to pipeline shape / scenario alignment diagnosis.

---

## 25. Tests for Phase F1

Recommended tests:

```text
tests/test_explicit_pipeline_forward_capacity_context.py
```

Coverage:

```text
builds product-first nested context
filters scenario base by default
scenario=None includes all rows
blank scenario treated as base
invalid rows skipped in non-strict mode
invalid rows raise in strict mode
unit handling lot only
duplicate rows last valid wins
attach helper sets env.explicit_pipeline_forward_weekly_capacity
maybe attach helper missing file returns file_missing
maybe attach helper valid file attaches
failed attach preserves existing context
```

---

## 26. Tests for Phase F2

Update:

```text
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

Coverage:

```text
Explicit KPI OFF does not call forward attach
Explicit KPI ON calls backward attach then forward attach then ctx guard
backward only => forward missing
backward + forward => guard pass
```

---

## 27. Tests for Phase F3

Potential test:

```text
tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
```

Coverage:

```text
sample CSV exists
sample CSV loads non-empty product-first context
maybe attach helper attaches context
ctx guard passes when backward and forward samples are both available
```

The final test may call both attach helpers:

```python
maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(env)
maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(env)
assert get_missing_explicit_pipeline_demo_ctx_keys(env) == []
```

---

## 28. Manual GUI Expected Behavior After All Forward Phases

After F1-F3:

```text
Explicit KPI ON
Run Full Plan
```

Expected:

```text
ctx guard no longer reports missing backward capability
ctx guard no longer reports missing forward weekly capacity
explicit pipeline is allowed to run
```

Then one of two things happens.

### Case A: Pipeline accepts shape and scenario

```text
capacity report / issue candidates may appear
```

### Case B: Pipeline still unavailable or errors

Likely cause:

```text
shape mismatch
product mismatch
node mismatch
week mismatch
additional implicit requirements
```

At that point, inspect:

```text
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 29. Safety Boundaries

Forward capacity context work must not implement:

```text
Price-Cost-Profit propagation
tariff simulation
cold-chain shelf-life modeling
automatic replanning
ReplanCommand execution
OR optimization
database persistence
large GUI redesign
```

This context is only the quantity-side capacity input for explicit pipeline execution.

---

## 30. Summary

Recommended canonical runtime shape:

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

Recommended first CSV path:

```text
data/explicit_pipeline_forward_weekly_capacity.csv
```

Recommended Japanese Rice Case sample rows:

```csv
scenario,product,node,capacity_type,week,capacity_lots,unit,source,note
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W40,5,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
base,PACKAGED_RICE_STANDARD,MILL_EAST,P,2027-W41,6,lot,japanese_rice_case_sample,Japanese Rice Case forward production capacity proxy from RICE_AS_IS weekly capacity
```

Recommended implementation sequence:

```text
F1 adapter
F2 GUI preflight attach
F3 sample CSV
F4 manual validation
```

This provides the next missing runtime context while keeping the implementation incremental and safe.
