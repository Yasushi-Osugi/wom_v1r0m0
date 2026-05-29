# Codex Request: WOM Capacity Master Canonical Loader Adapter

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/wom_capacity_master_canonical_loader_adapter_request.md`

**Parent design docs:**

```text
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first small phase of the WOM capacity canonical loader adapter.

This request is intentionally narrow.

Implement:

```text
capacity_master.csv -> WeeklyCapacityRow
```

Do not implement runtime attach yet.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI behavior.

Do not change existing sample CSV files.

Do not normalize or convert existing explicit pipeline runtime capacity shapes in this request.

The goal is to establish one canonical capacity row loader that can later feed all runtime capacity contexts.

---

## 2. Why This Request Exists

Recent design and inventory work established the following direction:

```text
capacity_master.csv
legacy sku_P_month_data.csv
other weekly/monthly capacity inputs
    ↓
WeeklyCapacityRow
    ↓
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
    ↓
capacity diagnostics
    ↓
planner / cockpit / reports
```

This request implements only the first stable station:

```text
capacity_master.csv -> WeeklyCapacityRow
```

This should create a canonical loader foundation without changing current WOM planning behavior.

---

## 3. Source Documents to Read First

Please read these documents before editing code:

```text
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

Also inspect existing code referenced by the inventory report, especially if present:

```text
pysi/capacity/capacity_master_loader.py
pysi/planning/capacity_master.py
pysi/adapters/capacity_input_granularity.py
tests/
```

Reuse existing modules and dataclasses where possible.

Avoid creating a parallel duplicate loader if an appropriate loader module already exists.

---

## 4. Implementation Scope

### Required

Implement or consolidate:

```python
load_capacity_master_csv(path) -> list[WeeklyCapacityRow]
```

The loader should parse a CSV with header:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

and return canonical `WeeklyCapacityRow` objects.

### Required behavior

The loader should:

```text
read capacity_master.csv
validate required columns
map CSV fields to WeeklyCapacityRow
convert capacity_qty to numeric
preserve week as provided
preserve cap_mode
preserve unit
preserve optional priority, calendar_id, comment
set capacity_owner_type = "node"
set capacity_owner_id from node_name
set product_id from product_name
set source_granularity to "weekly" unless another value is available
set source_file or source_id if existing pattern supports it
raise clear ValueError for missing required columns
raise clear ValueError for invalid capacity_qty
return deterministic row order
```

---

## 5. Explicit Non-Scope

Do not implement:

```text
WeeklyCapacityRow -> env.weekly_capability
WeeklyCapacityRow -> explicit_pipeline_forward_weekly_capacity
WeeklyCapacityRow -> explicit_pipeline_backward_weekly_capability
scenario package loader integration
runtime env attachment
capacity applicability status
planner behavior changes
blocked lot behavior changes
week-key normalization
shape conversion
GUI / KPI message changes
sample CSV changes
```

Those are later phases.

---

## 6. Expected Field Mapping

| capacity_master.csv field | WeeklyCapacityRow field |
|---|---|
| scenario_id | scenario_id |
| tree_side | tree_side |
| node_name | capacity_owner_id |
| product_name | product_id |
| week | week |
| capacity_type | capacity_type |
| capacity_qty | capacity_qty |
| cap_mode | cap_mode |
| unit | unit |
| priority | priority |
| calendar_id | calendar_id |
| comment | comment |

Additional fields:

```text
capacity_owner_type = "node"
source_granularity = "weekly"
source_file = input path, if field exists
source_id = deterministic row id, if field exists
```

If the existing `WeeklyCapacityRow` dataclass does not have all optional fields, do not force a large dataclass refactor.

Prefer one of these safe approaches:

```text
1. Use existing fields only and document omitted fields in comments/tests.
2. Add only small optional fields if clearly compatible and low-risk.
3. If adding fields risks breaking existing tests, avoid changing the dataclass.
```

---

## 7. Required Columns

Required columns:

```text
scenario_id
tree_side
node_name
product_name
week
capacity_type
capacity_qty
cap_mode
unit
```

Optional columns:

```text
priority
calendar_id
comment
```

If optional columns are missing, loader should still work with safe defaults:

```text
priority = None or ""
calendar_id = None or ""
comment = ""
```

---

## 8. Validation Rules

### 8.1 Missing required columns

Raise `ValueError`.

Message should include:

```text
missing required columns
```

and list the missing columns.

### 8.2 Invalid capacity_qty

Raise `ValueError`.

Message should include:

```text
capacity_qty
```

and identify the row or value.

### 8.3 Empty required values

Recommended behavior:

```text
empty scenario_id / node_name / product_name / week / capacity_type:
    raise ValueError
```

### 8.4 Duplicate rows

Do not implement aggregation in this request unless already existing.

Near-term acceptable behavior:

```text
preserve duplicate rows as separate WeeklyCapacityRow objects
```

or, if existing loader already aggregates:

```text
keep existing deterministic aggregation behavior
```

Document actual behavior in tests.

### 8.5 Week key

Do not normalize week keys in this request.

Preserve the value as provided.

Examples:

```text
2027-W40
0
1
```

---

## 9. Preferred Implementation Location

Preferred existing or new location:

```text
pysi/capacity/capacity_master_loader.py
```

If this file already exists and has related logic, extend it.

If a better existing module exists based on inventory findings, use it and explain in summary.

Avoid adding a new module with overlapping responsibility unless no suitable module exists.

---

## 10. Compatibility With Existing WeeklyCapacityRow

The inventory suggests that `WeeklyCapacityRow` may already exist in:

```text
pysi/adapters/capacity_input_granularity.py
```

Please inspect existing definition and use it.

Do not create a second incompatible `WeeklyCapacityRow`.

If the existing dataclass uses different field names, add a minimal adapter function or constructor helper.

The key is:

```text
one canonical row concept
not two competing row classes
```

---

## 11. Required Tests

Add focused tests.

Preferred test file:

```text
tests/test_wom_capacity_master_canonical_loader_adapter.py
```

or, if an existing capacity loader test file is more appropriate, extend it.

### 11.1 Happy path

Create an in-test temporary CSV with rows such as:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,P,5,hard,lot,1,JP_445,weekly milling capacity
RICE_AS_IS,IN,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W41,P,6,hard,lot,1,JP_445,next week capacity
```

Assert:

```text
len(rows) == 2
rows[0].scenario_id == "RICE_AS_IS"
rows[0].product_id or equivalent == "PACKAGED_RICE_STANDARD"
rows[0].capacity_owner_id or equivalent == "MILL_EAST"
rows[0].capacity_type == "P"
rows[0].capacity_qty == 5
rows[0].cap_mode == "hard"
rows[0].unit == "lot"
week is preserved as "2027-W40" or existing row semantics
```

### 11.2 Missing required columns

Create a CSV missing `capacity_qty`.

Assert:

```text
load_capacity_master_csv raises ValueError
message contains missing required columns
message contains capacity_qty
```

### 11.3 Invalid capacity_qty

Create a CSV with:

```text
capacity_qty = abc
```

Assert:

```text
ValueError
message contains capacity_qty
```

### 11.4 Optional columns absent

Create a CSV with only required columns.

Assert:

```text
loader succeeds
priority/calendar/comment defaults are safe
```

### 11.5 Week key preservation

Use both:

```text
2027-W40
0
```

Assert:

```text
loader does not normalize or reinterpret week keys
```

---

## 12. Test Commands

Run focused tests:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Also run existing related capacity tests if present:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
```

If repository has existing capacity input granularity tests, run them too:

```bat
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

If that file does not exist, report it as not present.

---

## 13. Safety Boundaries

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
data/*.csv
```

Unless an import path adjustment is strictly necessary, avoid touching runtime planner / GUI files.

This request should be loader + tests only.

---

## 14. Expected Output Files

Likely changed/new files:

```text
pysi/capacity/capacity_master_loader.py
tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Possibly changed if needed:

```text
pysi/adapters/capacity_input_granularity.py
```

Do not add sample data CSVs in this request.

Use temporary CSVs in tests.

---

## 15. Acceptance Criteria

This request is complete when:

```text
load_capacity_master_csv exists
load_capacity_master_csv returns WeeklyCapacityRow objects or existing canonical equivalent
required column validation works
invalid capacity_qty validation works
optional columns can be absent
week keys are preserved
focused tests pass
no planner behavior changes are made
no data CSV files are changed
no GUI files are changed
```

---

## 16. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where is load_capacity_master_csv implemented?
Which WeeklyCapacityRow class is used?
Did you create a new row class or reuse the existing one?
Did you change planner behavior?
Did you change any data CSVs?
Did you change GUI files?
Do week keys remain unnormalized?
Which tests passed?
```

---

## 17. Development Meaning

This request builds the first canonical rail junction for WOM capacity.

It should make this true:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
```

Later requests can build:

```text
WeeklyCapacityRow
    ↓
env.weekly_capability
    ↓
explicit forward/backward capacity context
    ↓
diagnostics and applicability status
```

Do not build the whole railway today.

Build the first station correctly.
