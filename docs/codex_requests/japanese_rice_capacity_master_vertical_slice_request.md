# Codex Request: Japanese Rice Capacity Master Vertical Slice

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_capacity_master_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_master_vertical_slice.md
```

**Related design / completion docs:**

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md
docs/design/wom_capacity_weekly_rows_source_diagnostic.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_scenario_package_control_model.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first Japanese Rice Case capacity master vertical slice.

This request should add a minimal scenario package capacity master sample and focused tests proving the following path:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
Explicit KPI preflight
    ↓
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
```

This is the first visible WOM modeling entrance test flight for Japanese Rice Case.

The implementation should remain narrow.

Do not change planner behavior.

Do not change capacity enforcement.

Do not change GUI layout.

Do not change runtime capacity logic.

Do not add full Japanese Rice network / demand / cost / price masters.

Do not introduce ton/kg conversion.

Do not normalize week keys.

---

## 2. Why This Request Exists

WOM now has the necessary infrastructure:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
Explicit KPI preflight
    ↓
capacity source diagnostic
runtime attachment diagnostic
```

The remaining need is to run a real but minimal business case through this route.

The Japanese Rice Case is the first selected business case.

This request does not try to complete Japanese Rice Case.

It only creates the first capacity master vertical slice.

In short:

```text
Create the Rice Case capacity cargo.
Load it through the existing WOM route.
Confirm the diagnostic console sees it.
```

---

## 3. Source Documents to Read First

Please read:

```text
docs/design/japanese_rice_capacity_master_vertical_slice.md
docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
```

Please inspect existing implementation and tests:

```text
pysi/capacity/capacity_weekly_rows_source.py
pysi/capacity/capacity_master_loader.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
pysi/gui/cockpit_tk.py
tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
tests/test_wom_capacity_weekly_rows_source_diagnostic.py
tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Reuse existing helpers:

```python
load_capacity_weekly_rows_to_env(...)
load_capacity_master_csv(...)
apply_capacity_runtime_attachment_preflight(...)
build_capacity_weekly_rows_source_diagnostic(...)
build_capacity_runtime_attachment_diagnostic(...)
```

Do not duplicate those implementations.

---

## 4. Implementation Scope

### Required files to add

Add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

### Optional files

No optional files are expected.

Do not change production code unless a real bug is found.

If production code must be changed, keep it minimal and explain clearly.

---

## 5. Explicit Non-Scope

Do not implement:

```text
full Japanese Rice network master
full Japanese Rice demand master
cost master
price master
inventory master
transport / leadtime master
real-world rice statistics
ton/kg/bag/pallet conversion
complete PSI planning run
optimization
GUI layout changes
new GUI widgets
planner behavior changes
capacity enforcement changes
runtime capacity context logic changes
source loader behavior changes
week-key normalization
scenario runner integration
```

This request is a capacity master vertical slice only.

---

## 6. Scenario Package Location

Create this directory and file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Scenario root:

```text
examples/scenarios/japanese_rice_vslice_001
```

This path is intentional because the current source helper resolves:

```text
scenario_root / "masters" / "capacity_master.csv"
```

---

## 7. Capacity Master Schema

Use the canonical capacity master schema supported by the current loader:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

Do not add extra columns unless already accepted by the loader.

Do not remove required columns.

Do not use localized Japanese column names.

---

## 8. Capacity Master Rows

Add exactly these rows unless current loader tests reveal a strict requirement requiring minor formatting changes:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
JAPANESE_RICE_VSLICE_001,inbound,FARM_REGION_A,JAPANESE_RICE_STANDARD,2027-W40,P,120,hard,lot,1,CAL_JP_STD,Harvest availability for week 40
JAPANESE_RICE_VSLICE_001,inbound,FARM_REGION_A,JAPANESE_RICE_STANDARD,2027-W41,P,120,hard,lot,1,CAL_JP_STD,Harvest availability for week 41
JAPANESE_RICE_VSLICE_001,inbound,FARM_REGION_A,JAPANESE_RICE_STANDARD,2027-W42,P,120,hard,lot,1,CAL_JP_STD,Harvest availability for week 42
JAPANESE_RICE_VSLICE_001,inbound,RICE_MILL_A,JAPANESE_RICE_STANDARD,2027-W40,P,100,hard,lot,1,CAL_JP_STD,Milling capacity for week 40
JAPANESE_RICE_VSLICE_001,inbound,RICE_MILL_A,JAPANESE_RICE_STANDARD,2027-W41,P,100,hard,lot,1,CAL_JP_STD,Milling capacity for week 41
JAPANESE_RICE_VSLICE_001,inbound,RICE_MILL_A,JAPANESE_RICE_STANDARD,2027-W42,P,100,hard,lot,1,CAL_JP_STD,Milling capacity for week 42
JAPANESE_RICE_VSLICE_001,outbound,DC_KANTO,JAPANESE_RICE_STANDARD,2027-W40,S,90,hard,lot,1,CAL_JP_STD,Outbound shipment capacity for week 40
JAPANESE_RICE_VSLICE_001,outbound,DC_KANTO,JAPANESE_RICE_STANDARD,2027-W41,S,90,hard,lot,1,CAL_JP_STD,Outbound shipment capacity for week 41
JAPANESE_RICE_VSLICE_001,outbound,DC_KANTO,JAPANESE_RICE_STANDARD,2027-W42,S,90,hard,lot,1,CAL_JP_STD,Outbound shipment capacity for week 42
```

Expected row count:

```text
9
```

Expected product:

```text
JAPANESE_RICE_STANDARD
```

Expected nodes:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

Expected capacity types:

```text
P
S
```

---

## 9. Business Meaning of the Sample

The minimal sample means:

```text
FARM_REGION_A:
  harvest / supply availability = 120 lots/week

RICE_MILL_A:
  milling / processing capacity = 100 lots/week

DC_KANTO:
  outbound shipment capacity = 90 lots/week
```

This creates a simple supply-chain story:

```text
farm supply is higher than milling capacity
milling capacity is higher than DC outbound capacity
DC may become downstream bottleneck
```

However, this request should not implement bottleneck logic.

This request only proves the capacity master entrance and diagnostics.

---

## 10. Test File

Add:

```text
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

The tests should use the repository sample file, not only temporary CSV content.

This is important because this request creates a real scenario package sample.

---

## 11. Required Tests

### 11.1 Sample file exists and loads through source helper

Test that:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

exists.

Call:

```python
load_capacity_weekly_rows_to_env(
    env,
    scenario_root=scenario_root,
)
```

Assert:

```text
env.capacity_weekly_rows exists
len(env.capacity_weekly_rows) == 9
env.capacity_weekly_rows_load_summary["available"] is True
env.capacity_weekly_rows_load_summary["row_count"] == 9
env.capacity_weekly_rows_source_kind == "scenario_package_capacity_master"
```

If the exact source kind differs in current implementation, assert the actual current implementation value, but keep the test meaningful.

### 11.2 Loaded rows preserve product / node / week / type

Assert the loaded rows include:

```text
product_id or product_name: JAPANESE_RICE_STANDARD
capacity_owner_id or node_name: FARM_REGION_A, RICE_MILL_A, DC_KANTO
week: 2027-W40, 2027-W41, 2027-W42
capacity_type: P, S
```

Use the actual `WeeklyCapacityRow` attributes currently provided by the implementation.

### 11.3 Source diagnostic reports the sample

After source loading, call the existing scenario alignment diagnostic builder or the specific source diagnostic helper.

Assert:

```text
diagnostic["capacity_weekly_rows_source"]["available"] is True
diagnostic["capacity_weekly_rows_source"]["summary_available"] is True
diagnostic["capacity_weekly_rows_source"]["row_count"] == 9
diagnostic["capacity_weekly_rows_source"]["env_rows_present"] is True
diagnostic["capacity_weekly_rows_source"]["env_row_count"] == 9
diagnostic["capacity_weekly_rows_source"]["row_count_matches_env"] is True
```

### 11.4 Runtime attachment consumes the rows

Call:

```python
apply_capacity_runtime_attachment_preflight(env)
```

or exercise the existing Explicit KPI preflight route if the current test helper pattern already supports it simply.

Assert:

```text
env.capacity_runtime_attachment_preflight_result["applied"] is True
env.capacity_runtime_attachment_summary exists
```

Then build or inspect diagnostic and assert:

```text
diagnostic["runtime_attachment"]["summary_available"] is True
diagnostic["runtime_attachment"]["input_row_count"] == 9
```

If the current runtime attachment summary uses a different field name for row count, use the existing actual field.

### 11.5 Runtime context shape includes expected product/node/type/week

Assert the attached forward context or runtime attachment diagnostic indicates:

```text
product_node_type_week_qty_v1
```

and includes the expected product/node/type/week domain if exposed.

Do not overfit to internal dict shape if current diagnostic already checks shape.

### 11.6 No planner execution required

Do not require a full PSI planning run.

The vertical slice is a preflight / diagnostic slice.

---

## 12. Optional Explicit KPI Preflight Test

If existing test utilities for `WOMCockpit` preflight can be reused with low risk, add one test that sets:

```text
env.scenario_root = examples/scenarios/japanese_rice_vslice_001
```

and runs the Explicit KPI preflight method.

Assert:

```text
env.capacity_weekly_rows_load_summary["row_count"] == 9
env.capacity_runtime_attachment_preflight_result["applied"] is True
```

If this test becomes fragile due to GUI/Tk dependencies, skip it and rely on source helper + runtime preflight tests.

Do not add GUI layout testing.

---

## 13. Test Commands

Run the focused Japanese Rice vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Run related source / diagnostic tests:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
python -m pytest tests/test_wom_capacity_weekly_rows_source_diagnostic.py
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Run capacity regression tests:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

---

## 14. Safety Boundaries

Expected changed / added files:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
pysi/capacity/capacity_weekly_rows_source.py
pysi/capacity/capacity_master_loader.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Do not modify existing data CSV files.

Adding the new example scenario CSV is allowed.

---

## 15. Acceptance Criteria

This request is complete when:

```text
Japanese Rice scenario capacity_master.csv is added
row count is exactly 9
source helper loads the sample via scenario_root
env.capacity_weekly_rows is populated
source diagnostic reports available=True and row_count=9
runtime attachment preflight consumes the rows
runtime diagnostic reports input row count 9
expected product/node/week/capacity_type domains are verified
focused test passes
related source/diagnostic tests pass
capacity regression tests pass
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
no existing data CSV files changed
```

---

## 16. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the Japanese Rice capacity_master.csv added?
How many rows does it contain?
What product does it use?
What nodes does it use?
What weeks does it use?
What capacity types does it use?
Does load_capacity_weekly_rows_to_env load it through scenario_root?
Does diagnostic["capacity_weekly_rows_source"] report row_count=9?
Does runtime attachment preflight consume the rows?
Does diagnostic["runtime_attachment"] report input row count 9?
Did you change planner behavior?
Did you change capacity enforcement?
Did you change GUI layout?
Did you change existing data CSV files?
Which tests passed?
```

---

## 17. Development Meaning

This request moves WOM from capacity infrastructure back to case modeling.

It creates the first visible Japanese Rice Case master-data entrance:

```text
business capacity assumption
    ↓
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
preflight diagnostics
```

This is intentionally small.

It is the first Rice Case test flight, not the full airline schedule.

Do not make the aircraft bigger before proving it can take off.
