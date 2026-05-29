# WOM Capacity Master Canonical Loader Adapter Completion Memo

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Completed  
**Target path:** `docs/design/wom_capacity_master_canonical_loader_adapter_completion.md`

**Related design docs:**

```text
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

**Related Codex request:**

```text
docs/codex_requests/wom_capacity_master_canonical_loader_adapter_request.md
```

---

## 1. Purpose

This completion memo records the completion of the first implementation phase of the WOM capacity canonical loader adapter.

The completed scope is intentionally narrow:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

This phase establishes the first canonical capacity-loader station.

It does not attach capacity rows to runtime contexts yet.

It does not change planning behavior.

It does not change GUI behavior.

It does not change sample CSV data.

---

## 2. Key Commit

Implementation commit:

```text
31d6d8e Add canonical capacity master loader
```

Related preceding commits:

```text
5c54c7d Add WOM capacity master schema consolidation design
1213461 Add WOM capacity master schema inventory Codex request
69f6717 Add WOM capacity schema inventory
4b7ffc8 Add WOM capacity master canonical loader adapter design
0b2799a Add WOM capacity master canonical loader adapter Codex request
```

---

## 3. Implementation Summary

The implementation added or consolidated:

```text
load_capacity_master_csv(path) -> list[WeeklyCapacityRow]
```

in:

```text
pysi/capacity/capacity_master_loader.py
```

The loader parses a consolidated capacity master CSV with fields:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

and maps rows to the existing canonical capacity row:

```text
pysi.adapters.capacity_input_granularity.WeeklyCapacityRow
```

No second competing `WeeklyCapacityRow` class was created.

---

## 4. Files Changed

The implementation changed the following files:

```text
pysi/adapters/capacity_input_granularity.py
pysi/capacity/capacity_master_loader.py
tests/test_capacity_planning_basic.py
tests/test_capacity_report_hook.py
tests/test_wom_capacity_master_canonical_loader_adapter.py
tools/smoke_capacity_report_hook.py
```

### 4.1 capacity_input_granularity.py

The existing `WeeklyCapacityRow` was reused.

Small optional metadata fields and compatibility aliases were added:

```text
tree_side
priority
calendar_id
source_file
node_name property alias
product_name property alias
```

These additions support the canonical capacity master loader while preserving the existing row concept.

### 4.2 capacity_master_loader.py

Implemented / consolidated:

```python
load_capacity_master_csv(path)
```

The loader:

```text
validates required columns
raises ValueError for missing required columns
raises ValueError for invalid capacity_qty
parses capacity_qty as numeric
preserves row order
preserves week keys as provided
maps node_name to capacity_owner_id
maps product_name to product_id
sets capacity_owner_type = "node"
sets source_granularity = "weekly"
records deterministic source_id
records source_file
does not attach rows to runtime contexts
```

### 4.3 tests

A focused new test file was added:

```text
tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Existing capacity report / smoke helper tests were adjusted to include the now-required `tree_side` column in generated test-only capacity-master CSVs.

The sample CSV data itself was not modified.

---

## 5. Field Mapping Confirmed

The canonical loader implements the following mapping:

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

Additional values:

```text
capacity_owner_type = "node"
source_granularity = "weekly"
source_file = input path
source_id = deterministic row id
```

---

## 6. Tests Executed

The following focused test passed:

```bat
python -m pytest tests/test_wom_capacity_master_canonical_loader_adapter.py
```

Observed result:

```text
6 passed
```

The following related capacity / explicit pipeline tests passed:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_capacity_input_granularity_adapter.py
```

Observed results:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py    11 passed
tests/test_explicit_pipeline_forward_capacity_context.py       12 passed
tests/test_explicit_pipeline_capacity_context.py               16 passed
tests/test_capacity_input_granularity_adapter.py               11 passed
```

The following related regression set also passed:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_wom_capacity_master_canonical_loader_adapter.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
34 passed
```

---

## 7. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
explicit_bridge_capacity_pipeline behavior
GUI behavior
sample CSV data
scenario selection
week-key normalization
runtime capacity shape conversion
Explicit KPI messages
Management Cockpit layout
```

This phase only added:

```text
canonical capacity master CSV loader
small WeeklyCapacityRow metadata compatibility
focused tests
test/smoke helper compatibility updates
```

---

## 8. Week Key Policy

Week keys remain unnormalized.

Examples preserved by the loader:

```text
2027-W40
0
```

This is intentional.

Week-domain conversion is deferred to a later adapter boundary phase.

This phase only loads capacity master rows into `WeeklyCapacityRow`.

It does not decide whether the planning engine should use business week labels or integer week indexes.

---

## 9. Current Architecture After This Phase

The completed phase makes this path real:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

The following paths are still future work:

```text
WeeklyCapacityRow
    ↓
env.weekly_capability

WeeklyCapacityRow
    ↓
env.explicit_pipeline_forward_weekly_capacity

WeeklyCapacityRow
    ↓
env.explicit_pipeline_backward_weekly_capability

WeeklyCapacityRow
    ↓
capacity applicability status

WeeklyCapacityRow
    ↓
scenario package capacity loading
```

---

## 10. Development Meaning

Before this phase, WOM had several capacity tunnels:

```text
legacy sku_P_month_data.csv
capacity_master_loader variants
WeeklyCapacityRow adapter
explicit forward capacity context
explicit backward capability context
diagnostic context
```

After this phase, WOM has a first canonical station:

```text
capacity_master.csv -> WeeklyCapacityRow
```

This is a small but important consolidation step.

It allows future work to derive runtime capacity contexts from one canonical row representation instead of maintaining parallel capacity interpretations.

---

## 11. Deferred Work

The following work remains intentionally deferred.

### 11.1 Runtime adapter

```text
WeeklyCapacityRow -> env.weekly_capability
```

### 11.2 Explicit Pipeline forward adapter

```text
WeeklyCapacityRow -> env.explicit_pipeline_forward_weekly_capacity
```

### 11.3 Explicit Pipeline backward adapter

```text
WeeklyCapacityRow -> env.explicit_pipeline_backward_weekly_capability
```

### 11.4 Applicability status

Introduce first-class capacity applicability statuses such as:

```text
absent_unlimited_fallback
present_aligned_applied
present_misaligned_product
present_misaligned_node
present_misaligned_week_domain
present_misaligned_shape
applied_and_blocking
```

### 11.5 Scenario package integration

Allow future scenario yaml to reference:

```yaml
masters:
  capacity_master: masters/capacity_master.csv
```

### 11.6 Legacy adapter convergence

Eventually connect legacy PySI V0R8 input:

```text
sku_P_month_data.csv
    ↓
WeeklyCapacityRow
```

and make it converge with the new canonical path.

---

## 12. Recommended Next Step

Recommended next design document:

```text
docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md
```

Purpose:

```text
Define how WeeklyCapacityRow should be converted into:
  env.weekly_capability
  env.explicit_pipeline_forward_weekly_capacity
  env.explicit_pipeline_backward_weekly_capability
without changing planner behavior.
```

Recommended next Codex request after that:

```text
docs/codex_requests/wom_capacity_weekly_rows_runtime_context_adapter_request.md
```

The implementation should remain narrow:

```text
WeeklyCapacityRow -> explicit forward capacity context
focused tests
no planner behavior changes
```

---

## 13. Summary

This phase successfully completed the first canonical capacity loader step.

Completed:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

Not yet completed:

```text
WeeklyCapacityRow
    ↓
runtime capacity contexts
```

The implementation reused the existing `WeeklyCapacityRow`, preserved week keys, avoided planner behavior changes, avoided GUI changes, and passed focused plus related regression tests.

In short:

```text
The first canonical capacity station is now built.
The next step is to connect it to runtime tracks.
```
