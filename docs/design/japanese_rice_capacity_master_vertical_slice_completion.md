# Japanese Rice Capacity Master Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_capacity_master_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_capacity_master_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_capacity_master_vertical_slice_request.md
```

**Related capacity foundation docs:**

```text
docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_scenario_package_control_model.md
```

---

## 1. Purpose

This completion memo records the first successful Japanese Rice Case capacity master vertical slice.

The completed vertical slice is:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
diagnostic["capacity_weekly_rows_source"]
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
diagnostic["runtime_attachment"]
```

This is the first concrete case-modeling entrance for Japanese Rice Case.

It proves that a real scenario package master file can enter WOM, become canonical `WeeklyCapacityRow` rows, be attached to `env`, and become visible through source and runtime diagnostics.

This is not yet a full PSI planning run.

It is the first successful capacity master-data test flight.

---

## 2. Key Commit

Implementation commit:

```text
d017bc1 Add Japanese rice capacity vertical slice
```

Related preceding commits:

```text
f46038e Add Japanese Rice capacity master vertical slice Codex request
824de22 Add Japanese Rice capacity master vertical slice design
f2385c8 Add WOM capacity weekly rows source diagnostic completion memo
f9856e4 Add capacity weekly rows source diagnostic
856491a Add WOM capacity weekly rows source diagnostic Codex request
f5b839a Add WOM capacity weekly rows source diagnostic design
abb8db5 Add WOM capacity source Explicit KPI preflight wiring completion memo
34080fc Wire capacity source into explicit KPI preflight
8886c03 Add capacity weekly rows env source helper
```

---

## 3. Files Added

This implementation added:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

No production code was changed.

No planner behavior was changed.

No capacity enforcement behavior was changed.

No GUI layout was changed.

No existing data CSV files were modified.

---

## 4. Added Scenario Package File

The new Japanese Rice capacity master file is:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

It contains exactly:

```text
9 data rows
```

Product:

```text
JAPANESE_RICE_STANDARD
```

Nodes:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
```

Weeks:

```text
2027-W40
2027-W41
2027-W42
```

Capacity types:

```text
P
S
```

Scenario ID:

```text
JAPANESE_RICE_VSLICE_001
```

Calendar ID:

```text
CAL_JP_STD
```

Unit:

```text
lot
```

Capacity mode:

```text
hard
```

---

## 5. Business Meaning of the First Sample

The sample encodes a minimal Japanese Rice supply chain capacity story:

```text
FARM_REGION_A:
  harvest / supply availability = 120 lots/week

RICE_MILL_A:
  milling / processing capacity = 100 lots/week

DC_KANTO:
  outbound shipment capacity = 90 lots/week
```

The simple narrative is:

```text
Farm supply is higher than milling capacity.
Milling capacity is higher than DC outbound capacity.
DC_KANTO can become a downstream bottleneck candidate.
```

However, this vertical slice does not yet implement or assert bottleneck planning behavior.

Its purpose is source loading and diagnostic visibility.

---

## 6. Confirmed WOM Route

The focused tests confirmed that the repository sample is loaded through:

```python
load_capacity_weekly_rows_to_env(
    env,
    scenario_root=SCENARIO_ROOT,
)
```

The source helper resolves:

```text
scenario_root / "masters" / "capacity_master.csv"
```

and attaches:

```text
env.capacity_weekly_rows
env.capacity_weekly_rows_load_summary
env.capacity_weekly_rows_source_kind
env.capacity_weekly_rows_source_path
```

Confirmed source kind:

```text
scenario_package_capacity_master
```

Confirmed row count:

```text
9
```

---

## 7. Confirmed Source Diagnostic

The vertical slice confirmed:

```text
diagnostic["capacity_weekly_rows_source"]
```

reports the Japanese Rice sample correctly.

Confirmed properties include:

```text
available = True
summary_available = True
row_count = 9
env_rows_present = True
env_row_count = 9
row_count_matches_env = True
```

This means the diagnostic console can now explain where the Japanese Rice capacity rows came from.

---

## 8. Confirmed Runtime Attachment Diagnostic

The vertical slice confirmed that runtime attachment preflight consumes all 9 rows.

Confirmed route:

```text
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

Confirmed runtime diagnostic properties include:

```text
summary_available = True
input_row_count = 9
shape = product_node_type_week_qty_v1
```

The attached forward runtime context includes the expected Japanese Rice domains:

```text
product:
  JAPANESE_RICE_STANDARD

nodes:
  FARM_REGION_A
  RICE_MILL_A
  DC_KANTO

capacity types:
  P
  S

weeks:
  2027-W40
  2027-W41
  2027-W42
```

Representative quantities are also verified by tests.

---

## 9. Tests Added

Focused test file:

```text
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

The tests cover:

```text
repository sample file exists
source helper loads sample through scenario_root
row count is 9
loaded row domains preserve product / nodes / weeks / capacity types
source diagnostic reports row_count=9
runtime attachment preflight consumes the rows
runtime diagnostic reports input_row_count=9
attached forward runtime context includes expected domains and representative quantities
```

---

## 10. Tests Executed

Focused vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Observed result:

```text
5 passed
```

Capacity weekly rows source helper test:

```bat
python -m pytest tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py
```

Observed result:

```text
8 passed
```

Capacity source Explicit KPI preflight wiring test:

```bat
python -m pytest tests/test_wom_capacity_source_explicit_kpi_preflight_wiring.py
```

Observed result:

```text
6 passed
```

Capacity weekly rows source diagnostic test:

```bat
python -m pytest tests/test_wom_capacity_weekly_rows_source_diagnostic.py
```

Observed result:

```text
9 passed
```

Runtime attachment diagnostic integration test:

```bat
python -m pytest tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py
```

Observed result:

```text
6 passed
```

Explicit pipeline capacity scenario alignment test:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Observed result:

```text
11 passed
```

Capacity regression tests:

```bat
python -m pytest tests/test_capacity_report_hook.py tests/test_capacity_report_hook_runner_option.py tests/test_capacity_planning_basic.py tests/test_capacity_master_io.py tests/test_capacity_input_granularity_adapter.py
```

Observed result:

```text
28 passed
```

---

## 11. Safety Boundaries Honored

This phase did not change:

```text
planner behavior
capacity enforcement behavior
blocked lot behavior
runtime capacity context logic
source loader behavior
GUI behavior
GUI layout
Management Cockpit layout
existing data CSV files
week-key normalization
calendar conversion
scenario runner behavior
legacy PySI V0R8 adapter dispatch
```

This phase only added:

```text
new Japanese Rice example capacity master
focused vertical slice tests
```

---

## 12. Current Architecture After This Phase

The Japanese Rice Case now has its first real scenario package input:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

The working architecture is:

```text
Japanese Rice capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
source diagnostic
    ↓
runtime attachment preflight
    ↓
runtime attachment diagnostic
```

This proves the first master-data entrance route:

```text
business capacity assumption
    ↓
capacity_master.csv
    ↓
canonical WOM row
    ↓
preflight diagnostic
```

---

## 13. Development Meaning

This completion is important because WOM development has now moved from infrastructure back to visible case modeling.

Before this phase, WOM had the runway:

```text
capacity loader
env attachment
Explicit KPI preflight wiring
source diagnostic
runtime diagnostic
```

After this phase, WOM has the first Japanese Rice cargo:

```text
Japanese Rice capacity_master.csv
```

and that cargo successfully moves through the runway route.

In short:

```text
The Rice Case test aircraft lifted off.
```

It is still a small test flight.

It is not yet a full commercial route.

But the case is now visible as data, not only as design intent.

---

## 14. Still Deferred

The following remain intentionally deferred.

### 14.1 Full Japanese Rice network master

Not yet implemented:

```text
network / node master
tree structure
routing
lead time
transport lane definition
```

### 14.2 Demand master

Not yet implemented:

```text
market demand rows
demand anchored lots
sales / shipment demand signal
```

### 14.3 Full PSI planning run

Not yet implemented:

```text
end-to-end PSI calculation for Japanese Rice Case
forward / backward planning execution
capacity constrained planning result
blocked / accepted lot reporting
```

### 14.4 Cost / price / KPI model

Not yet implemented:

```text
cost master
price master
profit simulation
cash / KPI view
```

### 14.5 Real-world unit conversion

Not yet implemented:

```text
kg
ton
bag
pallet
lot conversion
```

### 14.6 Public demo polishing

Not yet implemented:

```text
README narrative
note / YouTube demo story
Cockpit screen capture
public-facing scenario explanation
```

---

## 15. Recommended Next Step

The recommended next design is:

```text
docs/design/japanese_rice_demand_master_vertical_slice.md
```

Reason:

```text
Capacity defines supply-side capability.
Demand defines why lots should flow.
```

The next visible slice should introduce a small demand master for the Japanese Rice Case and connect it to the existing planning / diagnostic route.

Alternative next step:

```text
docs/design/japanese_rice_network_master_vertical_slice.md
```

if the project needs to define node / route structure before demand.

Recommended order:

```text
1. Capacity master vertical slice  ← completed
2. Demand master vertical slice
3. Network / node master vertical slice
4. Leadtime / calendar vertical slice
5. PSI planning run vertical slice
6. KPI / issue vertical slice
7. Public demo story
```

A practical next step is to define demand for:

```text
MARKET_TOKYO
JAPANESE_RICE_STANDARD
2027-W40 to 2027-W42
```

with small demand quantities that intentionally interact with the existing capacity values.

---

## 16. Recommended Next Codex / Design Pair

Recommended design file:

```text
docs/design/japanese_rice_demand_master_vertical_slice.md
```

Recommended Codex request after design:

```text
docs/codex_requests/japanese_rice_demand_master_vertical_slice_request.md
```

Potential first demand sample:

```text
MARKET_TOKYO demand:
  2027-W40 = 80 lots
  2027-W41 = 95 lots
  2027-W42 = 110 lots
```

This would create a simple story:

```text
week 40 demand is below DC capacity
week 41 demand exceeds DC capacity slightly
week 42 demand exceeds DC capacity clearly
```

This can later be used to show:

```text
capacity bottleneck
accepted / blocked lots
inventory / carry-over
KPI impact
```

---

## 17. Acceptance Summary

Completed:

```text
Japanese Rice scenario capacity_master.csv added
row count is exactly 9
product is JAPANESE_RICE_STANDARD
nodes are FARM_REGION_A, RICE_MILL_A, DC_KANTO
weeks are 2027-W40, 2027-W41, 2027-W42
capacity types are P and S
load_capacity_weekly_rows_to_env loads it through scenario_root
diagnostic["capacity_weekly_rows_source"] reports row_count=9
runtime attachment preflight consumes the rows
diagnostic["runtime_attachment"] reports input_row_count=9
focused test passed
related tests passed
capacity regression tests passed
planner behavior unchanged
capacity enforcement unchanged
GUI layout unchanged
existing data CSV files unchanged
```

---

## 18. Summary

This phase successfully completes the first Japanese Rice Case capacity master vertical slice:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
diagnostic["capacity_weekly_rows_source"]
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
diagnostic["runtime_attachment"]
```

The result is not yet a full Rice PSI model.

But it is the first concrete proof that Japanese Rice Case can enter WOM through master data and become visible in diagnostics.

This is the first successful WOM modeling entrance test for Japanese Rice Case.
