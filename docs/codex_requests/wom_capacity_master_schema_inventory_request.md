# Codex Request: WOM Capacity Master Schema Inventory

**Version:** v0r1  
**Date:** 2026-05-29  
**Status:** Codex inventory request  
**Target path:** `docs/codex_requests/wom_capacity_master_schema_inventory_request.md`  
**Parent design memo:** `docs/design/wom_capacity_master_schema_consolidation.md`  
**Related master data memo:** `docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md`  
**Related scenario memo:** `docs/design/wom_scenario_package_control_model.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please inventory the current repository for all capacity-related assets.

This request is intentionally **inventory-only**.

Do not implement new capacity logic.

Do not change planner behavior.

Do not change CSV files.

Do not change GUI behavior.

Do not normalize week keys.

Do not convert capacity shape.

Do not refactor runtime context.

The purpose is to identify what already exists before any further design or implementation.

The output should be a new design/inventory report:

```text
docs/design/wom_capacity_master_schema_inventory.md
```

---

## 2. Why This Request Exists

Capacity-related design and implementation already exist in multiple places.

The current problem is not absence of capacity design.

The current problem is fragmentation.

Existing capacity-related concepts may appear as:

```text
capacity master file layout
legacy monthly capacity input
WeeklyCapacityRow normalization
env.weekly_capability
explicit pipeline forward weekly capacity context
explicit pipeline backward capability context
capacity diagnostics
capacity usage / violation objects
GUI / KPI messages
tests
sample CSV files
```

Before implementation continues, please create a repository inventory that maps what exists.

---

## 3. Source Design Documents to Read First

Please read these design documents first, if present:

```text
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md
docs/design/wom_capacity_input_granularity_adapter.md
docs/design/capacity_input_granularity_adapter_v0r1_completion.md
docs/design/capacity_provider_monthly_csv_adapter_v0r2.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md
```

If any document is missing, record it as missing in the inventory report.

---

## 4. Scope of Inventory

Please inspect the repository and report capacity-related assets in the following categories.

```text
1. Design documents
2. CSV / sample data files
3. Loader / adapter modules
4. Dataclasses / typed rows / structured payloads
5. Planner / engine capacity consumers
6. Runtime env / ctx attributes
7. Explicit pipeline capacity contexts
8. Diagnostics
9. GUI / KPI / cockpit surfacing
10. Tests
11. Output / reporting files
12. Gaps and risks
```

---

## 5. Search Keywords

Please search for at least the following keywords and patterns:

```text
capacity
capability
weekly_capability
capacity_master
capacity_qty
capacity_type
cap_mode
CapacityUsage
CapacityViolation
WeeklyCapacityRow
MonthlyCapacityInputRow
WeeklyCapacityInputRow
sku_P_month_data
forward_weekly_capacity
backward_weekly_capability
explicit_pipeline_forward_weekly_capacity
explicit_pipeline_backward_weekly_capability
capacity_scenario_alignment
capacity_applicability
blocked_lot
blocked_lots
capacity_clip
```

Also inspect likely directories:

```text
pysi/
pysi/plan/
pysi/reporting/
pysi/gui/
pysi/plugins/
pysi/io/
pysi/io_adapters/
pysi/runners/
data/
tests/
docs/design/
docs/codex_requests/
```

---

## 6. Required Output File

Create:

```text
docs/design/wom_capacity_master_schema_inventory.md
```

This should be a human-readable inventory report.

Do not create code changes unless absolutely required to generate the report.

Do not add tests.

Do not modify existing tests.

---

## 7. Required Report Structure

The report should have the following sections.

```text
# WOM Capacity Master Schema Inventory

1. Purpose
2. Inventory Summary
3. Design Documents Found
4. Capacity CSV / Sample Data Files
5. Loader and Adapter Modules
6. Dataclasses and Canonical Row Structures
7. Runtime Capacity Contexts
8. Planner / Engine Capacity Consumers
9. Explicit Pipeline Capacity Contexts
10. Diagnostics and Cockpit Surfacing
11. Tests Found
12. Existing Mapping to Consolidation Memo
13. Gaps Against Target Architecture
14. Recommended Next Implementation Step
15. No-Behavior-Change Confirmation
```

---

## 8. Specific Inventory Questions

Please explicitly answer these questions.

### 8.1 Capacity master file layout

Is there an implemented or documented `capacity_master.csv` loader?

If yes, report:

```text
file path
function name
required columns
optional columns
tests
runtime destination
```

If no, report:

```text
documented but not implemented
or not found
```

### 8.2 WeeklyCapacityRow

Is `WeeklyCapacityRow` implemented?

If yes, report:

```text
file path
class/dataclass definition
fields
conversion functions
tests
```

If no, report whether it exists only in design docs.

### 8.3 Legacy sku_P_month_data.csv path

Is there an adapter or loader for `sku_P_month_data.csv`?

If yes, report:

```text
file path
loader function
expected columns
monthly-to-weekly conversion behavior
runtime destination
tests
```

### 8.4 env.weekly_capability

Is `env.weekly_capability` used?

If yes, report:

```text
where attached
where consumed
expected shape
tests
```

### 8.5 explicit forward weekly capacity

Is `env.explicit_pipeline_forward_weekly_capacity` used?

If yes, report:

```text
where attached
where consumed
expected shape
shape version if available
tests
```

### 8.6 explicit backward weekly capability

Is `env.explicit_pipeline_backward_weekly_capability` used?

If yes, report:

```text
where attached
where consumed
expected shape
shape version if available
tests
```

### 8.7 Capacity diagnostics

Which diagnostic modules inspect capacity alignment?

Report:

```text
file path
function names
diagnostic payload keys
message behavior
GUI surfacing path
tests
```

### 8.8 Planner behavior

Which planner or engine modules actually consume capacity and may block lots?

Report:

```text
file path
function names
input capacity shape
output blocked lots / issues
tests
```

### 8.9 Capacity usage / violation

Are `CapacityUsage` or `CapacityViolation` implemented?

If yes, report:

```text
file path
class/dataclass fields
export behavior
tests
```

If no, report whether they exist only in design docs.

### 8.10 Capacity applicability status

Is capacity applicability status implemented?

Examples:

```text
absent_unlimited_fallback
present_aligned_applied
present_misaligned_product
present_misaligned_node
present_misaligned_week_domain
present_misaligned_shape
applied_and_blocking
```

If not implemented, report as a gap.

---

## 9. Required Mapping Table

Include a table like this:

| Target concept | Existing implementation | Existing design doc | Status | Gap |
|---|---|---|---|---|
| capacity_master.csv | TBD | with_capacity_forward_push... | documented / implemented / missing | TBD |
| WeeklyCapacityRow | TBD | wom_capacity_input_granularity_adapter.md | documented / implemented / missing | TBD |
| sku_P_month_data adapter | TBD | capacity_provider_monthly_csv_adapter_v0r2.md | documented / implemented / missing | TBD |
| env.weekly_capability | TBD | capacity_input_granularity... | documented / implemented / missing | TBD |
| explicit forward capacity | TBD | explicit_pipeline_forward_weekly_capacity_context.md | documented / implemented / missing | TBD |
| diagnostic | TBD | explicit_pipeline_capacity_scenario_alignment_diagnostic.md | documented / implemented / missing | TBD |
| planner capacity consumption | TBD | with_capacity... | documented / implemented / missing | TBD |
| capacity applicability status | TBD | wom_capacity_master_schema_consolidation.md | documented / implemented / missing | TBD |

---

## 10. Expected Findings Style

Please distinguish the following states clearly:

```text
implemented:
    code exists and is used

implemented but possibly unused:
    code exists but usage path is unclear

documented only:
    design exists but no code found

legacy:
    old path exists and should be preserved

runtime-only:
    context shape exists but no master file loader

gap:
    target concept has no clear current implementation
```

Avoid vague statements like:

```text
capacity seems to be supported
```

Prefer specific statements:

```text
env.explicit_pipeline_forward_weekly_capacity is attached in pysi/gui/cockpit_tk.py by function X and consumed by Y.
```

---

## 11. Safety Boundaries

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
data/*.csv
tests/*.py
```

unless the only change is necessary documentation reference correction.

This request should create only:

```text
docs/design/wom_capacity_master_schema_inventory.md
```

No code behavior changes.

No CSV changes.

No test changes.

---

## 12. Optional: Mention Suspicious Duplicates

If multiple modules appear to define overlapping capacity concepts, list them.

Examples:

```text
multiple capacity loaders
multiple weekly capability shapes
multiple blocked_lot formats
multiple capacity_type meanings
multiple week-domain assumptions
```

Do not resolve them yet.

Only report them.

---

## 13. Recommended Next Step After Inventory

At the end of the inventory report, recommend the next implementation step.

Likely candidates:

```text
1. implement capacity_master.csv -> WeeklyCapacityRow loader
2. consolidate sku_P_month_data.csv legacy adapter
3. implement WeeklyCapacityRow -> explicit forward/backward runtime context adapter
4. add capacity applicability status diagnostic
5. add scenario package capacity master loading
```

The recommendation should be based on actual repository findings.

---

## 14. Testing Requirement

No tests are required for this inventory-only request.

However, after creating the inventory markdown file, please run:

```bat
git diff -- docs/design/wom_capacity_master_schema_inventory.md
```

If the repository has markdown linting or documentation tests, run them only if already standard in this repo.

Do not run broad test suites unless needed.

---

## 15. Acceptance Criteria

This request is complete when:

```text
docs/design/wom_capacity_master_schema_inventory.md is created
the report lists existing capacity-related files and functions
the report classifies each asset as implemented / documented only / legacy / runtime-only / gap
the report includes the required mapping table
the report explicitly answers all inventory questions
no code behavior changes are made
no CSV files are changed
no tests are changed
```

---

## 16. Codex Summary Requirements

In the Codex final summary, please explicitly answer:

```text
Did you create docs/design/wom_capacity_master_schema_inventory.md?
Did you change any code?
Did you change any data CSVs?
Did you change any tests?
What are the most important existing capacity implementation files?
What are the most important documented-only capacity concepts?
What is the most important next implementation step?
```

---

## 17. Development Meaning

This request is the bridge between design consolidation and safe implementation.

WOM already has many capacity-related pieces.

Before adding more, we must know exactly what exists.

In short:

```text
Do not dig.
Survey the ground first.
```
