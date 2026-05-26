# Explicit Pipeline Backward Weekly Capability Context Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-26  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_backward_weekly_capability_context.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo defines the concrete context design for:

```text
explicit_pipeline_backward_weekly_capability
```

This context is currently required by the explicit bridge capacity pipeline and is shown in the Explicit KPI View diagnostics when missing.

The previous upper-level memo:

```text
docs/design/plan_with_capacity_context_and_planning_story.md
```

defined the planning story.

This memo moves one level down and defines:

```text
1. conceptual meaning
2. canonical context schema
3. master CSV schema
4. adapter / normalizer behavior
5. env attach timing
6. validation rules
7. test cases
8. manual GUI validation flow
```

The goal is to move from:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
ctx guard skipped
    ↓
Explicit KPI View shows missing:
        explicit_pipeline_backward_weekly_capability
```

to:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
explicit_pipeline_backward_weekly_capability is attached to env
    ↓
explicit bridge capacity pipeline can run
    ↓
Explicit KPI View can show capacity-aware reporting data
```

---

## 2. Scope

This memo focuses only on the **capacity context** required by Plan with Capacity.

It does not define the PSI monetary evaluation master.

It does not define price-cost-profit propagation.

It does not define tariff simulation.

Those are separate design areas.

This memo covers:

```text
Plan with Capacity
    ↓
Backward weekly capability context
    ↓
explicit bridge capacity pipeline input
```

---

## 3. Key Scope Separation

The following two layers must remain separate.

```text
A. Plan with Capacity Context
    quantity-side planning context
    weekly capacity
    bottleneck capability
    lot acceptance / blocking
    timing shift
    dwell / delay

B. PSI Monetary Evaluation Context
    price
    cost structure
    profit
    tariff
    waste loss
    business KPI
```

`explicit_pipeline_backward_weekly_capability` belongs to **A. Plan with Capacity Context**.

It can later feed monetary evaluation indirectly, because capacity shortage and delay create monetary impact.

But it is not itself a cost or price master.

---

## 4. Conceptual Meaning

`explicit_pipeline_backward_weekly_capability` represents the weekly capability constraint used by the explicit pipeline for backward capacity planning.

MVP definition:

```text
For each constrained MOM node / product / week,
how many MEO lots can be output, shipped, or accepted.
```

In other words:

```text
node
product
week
capability_lots
```

This context answers the question:

```text
At this node, for this product, in this week,
how many lots can the plan realistically pass through?
```

For the MVP, this should be interpreted primarily as:

```text
MOM node finished-goods output / shipment capability
```

It is a bottleneck proxy.

---

## 5. Why MOM Node Capability First

The real bottleneck may be:

```text
inbound process
internal manufacturing line
quality inspection
cold-chain storage
packing process
shipping dock
supplier capacity
```

However, modeling all process-level constraints in the first implementation is too broad.

Recommended MVP:

```text
represent the effective bottleneck as MOM node weekly output capability
```

This gives WOM a practical and testable Plan with Capacity foundation.

Future expansion can decompose MOM capability into:

```text
process capability
resource capability
shift calendar
supplier capability
warehouse capability
cold-chain storage capability
```

---

## 6. Relationship to Backward Planning

Backward Plan with Capacity starts from demand and works upstream.

The capability context constrains the backward allocation position.

Example planning story:

```text
Demand requires 120 lots in week W10.
MOM node can output only 100 lots in W10.
Therefore 20 lots must be shifted, delayed, pre-built, or blocked depending on planning policy.
```

The context enables the pipeline to detect:

```text
accepted lots
blocked lots
capacity shortage
required pre-build
demand allocation position shift
bottleneck week
```

---

## 7. Relationship to Forward Planning

Although this context is named `backward_weekly_capability`, it also supports the broader Plan with Capacity story.

Forward Plan with Capacity uses capacity to simulate execution:

```text
available lots
    ↓
weekly capability
    ↓
accepted / blocked movement
    ↓
dwell / delay / backlog
```

The same capability master can be reused or adapted for forward execution simulation.

However, for this memo, the first integration target remains:

```text
explicit bridge capacity pipeline
```

---

## 8. Canonical Context Shape

Recommended canonical Python shape:

```python
{
    "MOM_NODE_ID": {
        "PRODUCT_NAME": {
            "YYYYWW": capability_lots
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

Alternative week keys may be accepted if the current engine uses week indexes:

```python
{
    "MOM_JP_FG": {
        "RICE_5KG": {
            1: 100,
            2: 100,
            3: 80,
        }
    }
}
```

Recommended MVP:

```text
preserve whatever week key format current explicit pipeline tests expect
```

If current tests use integer weeks, use integer weeks.

If GUI / CSV uses `YYYYWW`, adapter should normalize to the engine-expected format.

---

## 9. Flat Record Shape

For CSV and adapter work, the flat record shape is easier.

Recommended flat schema:

```python
[
    {
        "node": "MOM_JP_FG",
        "product": "RICE_5KG",
        "week": "202601",
        "capability_lots": 100,
        "capability_type": "output",
        "scenario": "base",
    }
]
```

The adapter converts flat records to canonical nested context.

---

## 10. Recommended CSV Master Schema

Recommended CSV file:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Recommended columns:

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

### 10.1 Column Definitions

| Column | Required | Meaning |
|---|---:|---|
| scenario | No | scenario name such as `base`, `constrained`, `cold_chain_case` |
| node | Yes | constrained node id, typically MOM node |
| product | Yes | product name / product id |
| week | Yes | week bucket |
| capability_lots | Yes | weekly capability in lot count / MEO count |
| capability_type | No | `output`, `ship`, `process`, `storage`, etc. |
| unit | No | usually `lot` for MVP |
| source | No | origin of assumption |
| note | No | free text |

Recommended MVP defaults:

```text
scenario = base
capability_type = output
unit = lot
```

---

## 11. Minimal CSV Example

```csv
scenario,node,product,week,capability_lots,capability_type,unit,source,note
base,MOM_JP_FG,RICE_5KG,202601,100,output,lot,demo,MOM output capability
base,MOM_JP_FG,RICE_5KG,202602,100,output,lot,demo,MOM output capability
base,MOM_JP_FG,RICE_5KG,202603,80,output,lot,demo,temporary bottleneck
```

Adapter output:

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

---

## 12. Latest WOM Master vs Original Master

WOM has two master orientations:

```text
1. PySI V0R8 / WOM original master
2. latest WOM master
```

The planning engine should consume canonical context.

The user-facing master may be more readable.

Recommended architecture:

```text
latest WOM capability master
    ↓
adapter / normalizer
    ↓
explicit_pipeline_backward_weekly_capability
    ↓
env attach
    ↓
explicit bridge capacity pipeline
```

The adapter is responsible for resolving differences such as:

```text
node name vs node id
product name vs product id
week format
scenario filtering
unit conversion
missing values
```

---

## 13. Adapter Responsibility

Recommended adapter function:

```python
load_explicit_pipeline_backward_weekly_capability_csv(path, *, scenario="base") -> dict
```

or:

```python
build_explicit_pipeline_backward_weekly_capability(records, *, scenario="base") -> dict
```

Responsibilities:

```text
read records
filter by scenario
validate required columns
coerce capability_lots to int or float
ignore or reject invalid rows according to strictness
group by node / product / week
return canonical nested dict
```

Recommended MVP module location:

```text
pysi/reporting/explicit_pipeline_capacity_context.py
```

or, if this is considered planning input rather than reporting:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Recommended first choice:

```text
pysi/plan/explicit_pipeline_capacity_context.py
```

Reason:

```text
this is planning context, not reporting output
```

---

## 14. Env Attach Contract

The context should be attached to `env` before the explicit bridge capacity pipeline runs.

Required env attribute:

```python
env.explicit_pipeline_backward_weekly_capability = capability_context
```

The current guard checks for this attribute.

After attachment:

```text
get_missing_explicit_pipeline_demo_ctx_keys(env)
```

should return:

```python
[]
```

Then:

```text
Explicit KPI ON
```

can keep the explicit pipeline flags enabled.

---

## 15. Attach Timing

Recommended timing options:

### Option A: During GUI preflight

When `Explicit KPI ON` is checked and `Run Full Plan` starts:

```text
GUI preflight
    ↓
load capability context from default CSV if available
    ↓
attach to env
    ↓
apply / keep demo flags
```

Advantages:

```text
simple demo path
user sees cockpit populated without CLI work
```

Disadvantages:

```text
GUI preflight starts doing data loading
```

### Option B: During environment initialization

When env is created:

```text
env setup
    ↓
load capability context
    ↓
attach once
```

Advantages:

```text
cleaner runtime
context exists before GUI action
```

Disadvantages:

```text
requires knowing env construction path
```

### Option C: Explicit runner / scenario loader

When scenario is loaded:

```text
scenario loader
    ↓
load all related master data
    ↓
attach capability context
```

Advantages:

```text
best long-term architecture
```

Disadvantages:

```text
larger integration scope
```

Recommended MVP:

```text
Option A or B, depending on the current code shape.
```

Recommended long-term:

```text
Option C.
```

---

## 16. Recommended MVP Attach Strategy

For the next implementation phase, use a minimal and safe approach:

```text
If a default CSV exists:
    load it and attach to env before Run Full Plan when Explicit KPI ON is checked.
If it does not exist:
    keep current ctx guard behavior.
```

This preserves current safety.

No automatic dummy capability should be invented silently.

Recommended default path:

```text
data/explicit_pipeline_backward_weekly_capability.csv
```

Alternative:

```text
pysi/master_data/explicit_pipeline_backward_weekly_capability_sample.csv
```

For demo purposes, a sample file may be useful.

---

## 17. Validation Rules

Recommended validation rules:

```text
node must not be blank
product must not be blank
week must not be blank
capability_lots must be numeric
capability_lots must be >= 0
```

Duplicate rows:

```text
same scenario / node / product / week
```

Recommended MVP behavior:

```text
last row wins
```

or:

```text
raise ValueError in strict mode
```

Recommended adapter signature:

```python
build_explicit_pipeline_backward_weekly_capability(records, *, strict=False)
```

MVP:

```text
strict=False
```

Tests should cover deterministic behavior.

---

## 18. Missing / Empty Context Semantics

The ctx guard currently treats missing as:

```text
attribute absent
or attribute is None
```

It does not treat `{}` as missing.

For this capability context, an empty dict technically exists but is not useful.

Recommended enhancement after MVP:

```text
warn if context is empty
```

But do not change guard semantics in this memo.

For loading, if CSV is empty, the loader can return `{}` and optionally attach a warning message.

---

## 19. Scenario Handling

Capability is scenario-dependent.

Examples:

```text
base
capacity_down_20pct
bottleneck_mom
cold_chain_constraint
disruption_case
```

CSV should allow:

```text
scenario
```

The adapter should filter by scenario.

MVP default:

```text
scenario = base
```

Later, GUI can expose scenario selection.

---

## 20. Unit Handling

MVP unit:

```text
lot
```

Because WOM lot / MEO is the planning unit.

Later unit expansion may include:

```text
piece
case
pallet
kg
hour
machine_hour
```

If units are not lot, adapter must convert to lot count using lot size / conversion master.

For MVP:

```text
reject or ignore non-lot units unless explicitly supported
```

---

## 21. Relationship to Dwell / Delay

Once capability context is available, the explicit pipeline can produce facts such as:

```text
accepted lots
blocked lots
capacity shortage
delayed lots
bottleneck week
```

These facts can support later dwell and delay modeling.

Important point:

```text
capability context does not itself calculate dwell.
It enables planning results from which dwell can be derived.
```

Dwell calculation belongs to planning result analysis or event tracing.

---

## 22. Relationship to Monetary Evaluation

Capability context is quantity-side.

It can later feed monetary evaluation indirectly.

Examples:

```text
blocked lots → lost sales or delayed revenue
delayed lots → service penalty
capacity shortage → overtime or external sourcing cost
dwell weeks → inventory holding cost
excess dwell for cold chain → disposal loss
```

This memo does not define those calculations.

Recommended later memo:

```text
docs/design/psi_monetary_kpi_evaluation_master_context.md
```

---

## 23. Integration with Existing Guard

Current guard behavior:

```text
if env.explicit_pipeline_backward_weekly_capability is missing:
    explicit pipeline skipped
    diagnostic shown
```

After this context is attached:

```text
if env.explicit_pipeline_backward_weekly_capability exists:
    guard does not skip
    explicit pipeline can run
```

Therefore, this context is the missing bridge from:

```text
diagnostic unavailable state
```

to:

```text
capacity-aware reporting state
```

---

## 24. Recommended Test Cases

### 24.1 Adapter builds nested context

Input records:

```python
[
    {"node": "MOM_A", "product": "P1", "week": "202601", "capability_lots": "100"}
]
```

Expected:

```python
{
    "MOM_A": {
        "P1": {
            "202601": 100
        }
    }
}
```

### 24.2 Scenario filtering

Records include `base` and `constrained`.

Adapter with `scenario="base"` returns only base rows.

### 24.3 Invalid numeric value

If `capability_lots = "abc"`:

```text
strict=True raises ValueError
strict=False skips row or records warning
```

### 24.4 Negative capability

If `capability_lots = -1`:

```text
strict=True raises ValueError
strict=False skips or clamps according to defined rule
```

Recommended MVP:

```text
strict=False skips invalid rows
strict=True raises
```

### 24.5 Env attach clears guard

Given env with no capability:

```text
get_missing_explicit_pipeline_demo_ctx_keys(env)
returns missing key
```

After attach:

```text
env.explicit_pipeline_backward_weekly_capability = context
get_missing_explicit_pipeline_demo_ctx_keys(env)
returns []
```

### 24.6 GUI preflight with CSV available

If MVP integration loads from CSV during preflight:

```text
Explicit KPI ON
default CSV exists
Run Full Plan preflight attaches context
ctx guard does not skip
```

---

## 25. Manual GUI Validation Target

After implementation:

```text
1. create data/explicit_pipeline_backward_weekly_capability.csv
2. python -m main
3. check Explicit KPI ON
4. Run Full Plan
5. Explicit KPI View opens
6. no missing context diagnostic for explicit_pipeline_backward_weekly_capability
7. capacity report / issue candidate sections become available if pipeline produces data
```

If the pipeline still does not produce full data, inspect downstream required contexts or pipeline logic.

---

## 26. Completion Criteria

This context design is implemented when:

```text
[OK] capability CSV schema is defined
[OK] adapter builds canonical nested context
[OK] env.explicit_pipeline_backward_weekly_capability can be attached
[OK] ctx guard no longer reports this key when context is attached
[OK] invalid records are handled deterministically
[OK] tests cover adapter behavior
[OK] tests cover env attach behavior
[OK] manual GUI validation confirms missing-key diagnostic disappears when sample context is supplied
```

---

## 27. Implementation Boundaries

Do not implement in the first patch:

```text
process-level capacity
resource-level capacity
cold-chain storage capacity
shelf-life master
monetary KPI calculation
price-cost-profit propagation
tariff simulation
scenario GUI selector
automatic fallback dummy context
```

The first patch should only create a reliable capability context path.

---

## 28. Recommended Implementation Phases

### Phase 1: Pure adapter

```text
build_explicit_pipeline_backward_weekly_capability(records)
load_explicit_pipeline_backward_weekly_capability_csv(path)
tests
```

### Phase 2: Env attach helper

```text
attach_explicit_pipeline_backward_weekly_capability_from_csv(env, path)
tests
```

### Phase 3: GUI / Run Full Plan integration

```text
if Explicit KPI ON and default CSV exists:
    attach context before ctx guard check
```

### Phase 4: Sample master

```text
add sample CSV for demo scenario
```

### Phase 5: Manual GUI validation

```text
Explicit KPI View no longer shows missing key
```

---

## 29. Summary

`explicit_pipeline_backward_weekly_capability` is the first concrete capacity context needed by the explicit pipeline.

Its MVP meaning is:

```text
MOM node / product / week capability in lot count
```

Recommended master shape:

```text
scenario,node,product,week,capability_lots,capability_type,unit,source,note
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

The context should be attached to:

```python
env.explicit_pipeline_backward_weekly_capability
```

before the explicit bridge capacity pipeline runs.

This moves WOM from:

```text
safe diagnostic unavailable state
```

toward:

```text
capacity-aware planning output and KPI cockpit visibility
```
