# WOM Capacity Input Granularity Adapter Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-19  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_input_granularity_adapter.md`

**Related design documents:**

- `docs/design/current_wom_backward_planning_and_capacity_flow_mapping.md`
- `docs/design/wom_plan_input_granularity_adapter.md`
- `docs/design/wom_plan_input_granularity_adapter_v0r2.md`
- `docs/design/wom_plan_input_granularity_adapter_v0r3_plan_node_seeding.md`
- `docs/design/legacy_pysi_v0r8_input_loader_mapping.md`
- `docs/design/rice_case_backward_planning_after_seed.md`
- `docs/design/rice_case_actual_prod_tree_seed_integration.md`

---

## 1. Purpose

This memo defines the **WOM Capacity Input Granularity Adapter**.

The purpose is to normalize different capacity input granularities into a canonical weekly capacity structure that can be consumed by WOM Planning Engine components.

The main target is:

```text
monthly capacity input
or
weekly capacity input
    ↓
Canonical WeeklyCapacityRow
    ↓
env.weekly_capability
    ↓
MOM capacity-aware planning / leveling
```

This memo is especially focused on the MOM production capacity path:

```text
P_capacity_month / P_capacity_week
    ↓
weekly capability
    ↓
MOM capacity-constrained planning
```

This is separate from demand or production plan input.

---

## 2. Background

Current WOM already has a capacity provider plugin:

```text
pysi/plugins/capacity_provider_monthly_csv/plugin.py
```

This plugin reads:

```text
sku_P_month_data.csv
```

and builds:

```text
env.weekly_capability[product][MOMxxx] = [cap_lot per week]
env.weekly_capability_df
```

This confirms that a monthly capacity to weekly capability path already exists.

However, the current implementation uses a simplified rule:

```text
1 month = 4 weeks
```

where:

```text
month offset = (month - 1) * 4
```

This differs from the newer Plan Input Granularity Adapter, which defines a 4-4-5 calendar adapter.

Therefore, capacity input should be normalized with the same discipline as plan input.

---

## 3. Key Design Principle

The key design principle is:

```text
Capacity input should be normalized independently from demand / supply plan input.

Demand / supply plan:
    describes what is required or planned

Capacity:
    describes what is possible
```

Therefore, WOM should clearly distinguish:

```text
P_month plan:
    production requirement / planned production quantity

P_capacity_month:
    production capacity limit for MOM / production node

S_month supply:
    supply / shipment / sales quantity depending on context
```

The term `P_month` should not be overloaded.

---

## 4. Current Problem

### 4.1 `sku_P_month_data.csv` is overloaded

In some contexts, `sku_P_month_data.csv` may mean production plan.

In the current `capacity_provider_monthly_csv` plugin, it is treated as monthly capacity input.

This is functional but semantically ambiguous.

### 4.2 Monthly-to-weekly rule is inconsistent

Current capacity provider:

```text
1 month = 4 weeks
```

New plan input adapter:

```text
4-4-5 planning calendar
```

This creates potential inconsistency between:

```text
weekly demand / plan rows
weekly capacity rows
```

### 4.3 Capacity input is not yet canonical

The current capacity provider directly builds `env.weekly_capability`.

It does not expose a reusable canonical weekly capacity table.

This makes testing and future extension harder.

---

## 5. Desired Capacity Input Pipeline

The desired capacity input pipeline is:

```text
Raw Capacity Input
    ↓
Calendar / Granularity Normalization
    ↓
Canonical WeeklyCapacityRow
    ↓
weekly_capability mapping
    ↓
Planning Engine / MOM capacity logic
```

This mirrors the plan input pipeline:

```text
Raw Plan Input
    ↓
WeeklyPlanRow
    ↓
LotHeader
    ↓
PsiSeedRecord
    ↓
PlanNode PSI seed
```

---

## 6. Capacity Input Modes

The adapter should support multiple capacity input modes.

```text
monthly_capacity:
    monthly capacity rows

weekly_capacity:
    weekly capacity rows

case_weekly_capacity:
    case-specific weekly capacity dataset
```

Optional future mode:

```text
constraint_json:
    weekly_constraints.json style input
```

---

## 7. Canonical WeeklyCapacityRow

### 7.1 Purpose

`WeeklyCapacityRow` is the canonical intermediate representation of weekly capacity.

### 7.2 Suggested dataclass

```python
from dataclasses import dataclass


@dataclass
class WeeklyCapacityRow:
    scenario_id: str
    product_id: str
    capacity_owner_type: str  # node / lane / flow
    capacity_owner_id: str
    week: str
    capacity_type: str        # P / S / I / transport / storage / process
    capacity_qty: float
    cap_mode: str = "hard"    # hard / soft
    unit: str = "LOT"
    source_granularity: str = "weekly"
    source_id: str = ""
    comment: str = ""
```

### 7.3 Required fields

```text
scenario_id
product_id
capacity_owner_type
capacity_owner_id
week
capacity_type
capacity_qty
```

---

## 8. Monthly Capacity Input

### 8.1 Suggested dataclass

```python
@dataclass
class MonthlyCapacityInputRow:
    scenario_id: str
    product_id: str
    capacity_owner_type: str
    capacity_owner_id: str
    month: str
    capacity_type: str
    capacity_qty: float
    cap_mode: str = "hard"
    unit: str = "LOT"
    source_id: str = ""
    comment: str = ""
```

Example:

```python
MonthlyCapacityInputRow(
    scenario_id="BASE",
    product_id="PRODUCT_X",
    capacity_owner_type="node",
    capacity_owner_id="MOM_CHINA",
    month="2026-M01",
    capacity_type="P",
    capacity_qty=400.0,
)
```

---

## 9. Weekly Capacity Input

### 9.1 Suggested dataclass

```python
@dataclass
class WeeklyCapacityInputRow:
    scenario_id: str
    product_id: str
    capacity_owner_type: str
    capacity_owner_id: str
    week: str
    capacity_type: str
    capacity_qty: float
    cap_mode: str = "hard"
    unit: str = "LOT"
    source_id: str = ""
    comment: str = ""
```

Example:

```python
WeeklyCapacityInputRow(
    scenario_id="RICE_AS_IS",
    product_id="PACKAGED_RICE_STANDARD",
    capacity_owner_type="node",
    capacity_owner_id="MILL_EAST",
    week="2027-W40",
    capacity_type="P",
    capacity_qty=5.0,
)
```

---

## 10. Calendar Conversion

### 10.1 Monthly capacity to weekly capacity

Monthly capacity should be converted to weekly capacity using an explicit calendar rule.

Supported calendar modes:

```text
445:
    WOM 4-4-5 planning calendar

four_week_month:
    legacy capacity_provider_monthly_csv behavior

calendar_month:
    future calendar-month day-based distribution
```

### 10.2 4-4-5 mode

Use the same mapping as Plan Input Granularity Adapter.

```text
Q1:
    M01 = W01-W04
    M02 = W05-W08
    M03 = W09-W13

Q2:
    M04 = W14-W17
    M05 = W18-W21
    M06 = W22-W26

Q3:
    M07 = W27-W30
    M08 = W31-W34
    M09 = W35-W39

Q4:
    M10 = W40-W43
    M11 = W44-W47
    M12 = W48-W52
```

### 10.3 Legacy four-week-month mode

This mode preserves current plugin behavior.

```text
M01 = W01-W04
M02 = W05-W08
...
M12 = W45-W48
```

This should exist only for backward compatibility.

### 10.4 Distribution rule

Default:

```text
even
```

Monthly capacity should be evenly divided across weeks in the selected calendar bucket.

Example:

```text
capacity_qty = 400
2026-M01 = 4 weeks
weekly capacity = 100
```

For 5-week months under 4-4-5:

```text
capacity_qty = 500
2026-M03 = 5 weeks
weekly capacity = 100
```

---

## 11. Monthly Capacity Conversion Function

Suggested function:

```python
def monthly_capacity_to_weekly_rows(
    monthly_rows: list[MonthlyCapacityInputRow],
    *,
    calendar_mode: str = "445",
    distribution_rule: str = "even",
) -> list[WeeklyCapacityRow]:
    ...
```

Expected behavior:

```text
1. use calendar adapter to get weeks in month
2. distribute monthly capacity into weekly capacity
3. produce WeeklyCapacityRow per week
4. preserve capacity_owner_type / capacity_owner_id
5. preserve cap_mode / unit / source_id / comment
```

---

## 12. Weekly Capacity Pass-through

Suggested function:

```python
def weekly_capacity_to_weekly_rows(
    weekly_rows: list[WeeklyCapacityInputRow],
    *,
    source_granularity: str = "weekly",
) -> list[WeeklyCapacityRow]:
    ...
```

Behavior:

```text
week key is preserved
capacity_qty is preserved
capacity_type is preserved
```

This is especially important for case_weekly inputs such as Rice and Vaccine cases.

---

## 13. Capacity Input Dispatcher

Suggested dispatcher:

```python
def normalize_capacity_input_to_weekly_rows(
    *,
    input_mode: str,
    monthly_rows: list[MonthlyCapacityInputRow] | None = None,
    weekly_rows: list[WeeklyCapacityInputRow] | None = None,
    calendar_mode: str = "445",
    distribution_rule: str = "even",
) -> list[WeeklyCapacityRow]:
    ...
```

Supported input modes:

```text
monthly_capacity
weekly_capacity
case_weekly_capacity
```

Invalid input mode should raise `ValueError`.

---

## 14. Mapping to `env.weekly_capability`

### 14.1 Purpose

Convert canonical weekly capacity rows into WOM runtime capability dictionary.

Current expected structure:

```python
env.weekly_capability[product][MOM_node] = [cap_lot_per_week]
```

### 14.2 Suggested function

```python
def weekly_capacity_rows_to_weekly_capability(
    rows: list[WeeklyCapacityRow],
    *,
    weeks_count: int,
    product_key: str | None = None,
    normalize_owner_name: bool = True,
) -> dict[str, dict[str, list[int]]]:
    ...
```

### 14.3 Owner name normalization

Current capacity provider normalizes:

```text
DADxxx → MOMxxx
```

This should be supported as a configurable option.

Suggested function:

```python
def normalize_capacity_owner_name(owner_id: str) -> str:
    ...
```

MVP behavior:

```text
if owner starts with DAD:
    return MOM + owner[3:]
else:
    return owner
```

### 14.4 Capacity type filter

For `env.weekly_capability`, initially focus on:

```text
capacity_type = P
```

Future versions may support:

```text
S capacity
I capacity
transport capacity
storage capacity
```

with separate runtime structures.

---

## 15. Relationship to MOM Capacity Leveling

The primary consumer is:

```text
level_mom_demand_with_capacity(...)
```

and / or legacy:

```text
inbound_MOM_leveling_vs_capacity(...)
```

These functions expect weekly capacity by MOM.

Conceptual connection:

```text
P_capacity_month / P_capacity_week
    ↓
WeeklyCapacityRow
    ↓
env.weekly_capability
    ↓
MOM capacity-constrained backward planning
```

---

## 16. Relationship to Existing Plugin

### 16.1 Existing plugin

```text
pysi/plugins/capacity_provider_monthly_csv/plugin.py
```

Current behavior:

```text
sku_P_month_data.csv
    ↓
1 month = 4 weeks
    ↓
env.weekly_capability
```

### 16.2 New adapter role

The new adapter should not immediately replace this plugin.

Instead:

```text
1. implement capacity input adapter as isolated module
2. add tests
3. later refactor capacity_provider_monthly_csv to call the new adapter
```

---

## 17. Suggested Files

Suggested new files:

```text
pysi/adapters/capacity_input_granularity.py
tests/test_capacity_input_granularity_adapter.py
```

Optional future update:

```text
pysi/plugins/capacity_provider_monthly_csv/plugin.py
```

Do not modify the plugin in v0r1 unless explicitly requested.

---

## 18. Test Policy

### 18.1 4-4-5 tests

```text
1. monthly capacity M01 expands to W01-W04
2. monthly capacity M03 expands to W09-W13
3. 12 months cover 52 weeks in 4-4-5 mode
```

### 18.2 Legacy four-week mode tests

```text
1. M01 expands to W01-W04
2. M12 starts at W45
3. four-week mode does not claim to cover all 52 weeks
```

### 18.3 Weekly pass-through tests

```text
1. weekly input preserves week key
2. weekly input preserves capacity_qty
3. case_weekly_capacity input preserves Rice W40 / W41 boundary
```

### 18.4 weekly_capability mapping tests

```text
1. WeeklyCapacityRow maps to env.weekly_capability-like dict
2. product key is preserved
3. owner normalization DADxxx → MOMxxx works
4. capacity values are stored in correct week index
5. duplicate rows add capacity rather than overwrite
```

---

## 19. Completion Criteria

This design is complete when future implementation can show:

```text
[OK] MonthlyCapacityInputRow exists
[OK] WeeklyCapacityInputRow exists
[OK] WeeklyCapacityRow exists
[OK] monthly capacity converts to weekly rows
[OK] weekly capacity passes through
[OK] 4-4-5 calendar is supported
[OK] legacy four-week-month mode is supported
[OK] weekly rows map to env.weekly_capability structure
[OK] DAD→MOM owner normalization is supported
[OK] tests pass
[OK] existing capacity provider plugin remains untouched in v0r1
```

---

## 20. Future Refactor Path

### v0r1

```text
new capacity input adapter module
tests only
no plugin modification
```

### v0r2

```text
capacity_provider_monthly_csv plugin calls new adapter
```

### v0r3

```text
support weekly capacity CSV directly
```

### v0r4

```text
support lane / flow capacity structures
```

### v0r5

```text
connect capacity inputs to E2E Evaluation / Management Issue
```

---

## 21. Summary

The capacity input layer should follow the same principle as the plan input layer.

```text
If weekly capacity exists, keep it weekly.

If only monthly capacity exists, convert it explicitly using a calendar adapter.
```

The current capacity provider proves that a path already exists:

```text
sku_P_month_data.csv
    ↓
env.weekly_capability
```

However, the implementation is currently tied to a 4-week-per-month simplification.

The new capacity input granularity adapter should provide a clean, tested, and explicit bridge:

```text
P_capacity_month / P_capacity_week
    ↓
WeeklyCapacityRow
    ↓
env.weekly_capability
```

This will align capacity input handling with the new WOM plan input normalization architecture.
