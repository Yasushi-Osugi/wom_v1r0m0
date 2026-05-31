# Japanese Rice Demand Master Vertical Slice Completion Memo

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Completed  
**Target path:** `docs/design/japanese_rice_demand_master_vertical_slice_completion.md`

**Parent design doc:**

```text
docs/design/japanese_rice_demand_master_vertical_slice.md
```

**Related Codex request:**

```text
docs/codex_requests/japanese_rice_demand_master_vertical_slice_request.md
```

**Related docs:**

```text
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice.md
docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
```

---

## 1. Purpose

This completion memo records the successful completion of the first Japanese Rice Case demand master vertical slice.

The completed demand-side vertical slice is:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
    ↓
load_weekly_demand_master_csv(...)
    ↓
WeeklyDemandRow
    ↓
generate_demand_anchored_lots(...)
    ↓
DemandAnchoredLot
    ↓
product-specific outbound-tree leaf plan_node compatibility shape
    ↓
psi4demand[week]["S"] = list[lot_ID]
```

This phase proves that final-market demand for Japanese Rice Case can enter WOM as deterministic demand anchored lots.

This phase does not execute a full PSI plan.

This phase does not change planner behavior.

This phase does not change GUI layout.

This phase does not implement monthly `S_month_data.csv` compatibility.

---

## 2. Key Commits

Implementation commit:

```text
a6334e4 Add Japanese rice demand vertical slice
```

Important request clarification commit:

```text
0598d53 Clarify demand lot leaf plan node anchor in Japanese Rice request
```

Related preceding commits:

```text
3ffd0e5 Revise Japanese Rice demand master vertical slice Codex request
45f172e Add Japanese Rice demand master vertical slice design
920d98d Add Japanese Rice capacity master vertical slice completion memo
d017bc1 Add Japanese rice capacity vertical slice
f46038e Add Japanese Rice capacity master vertical slice Codex request
824de22 Add Japanese Rice capacity master vertical slice design
```

---

## 3. Files Added

This implementation added:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
pysi/demand/__init__.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
tests/test_japanese_rice_demand_master_vertical_slice.py
```

No existing production planner file was changed.

No GUI file was changed.

No capacity enforcement file was changed.

No original PySI `S_month_data.csv` behavior was changed.

---

## 4. Added Demand Master

The new demand master file is:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

It contains exactly:

```text
3 data rows
```

Product:

```text
JAPANESE_RICE_STANDARD
```

Demand node:

```text
MARKET_TOKYO
```

Weeks:

```text
2027-W40
2027-W41
2027-W42
```

Demand quantities:

```text
2027-W40 = 80 lots
2027-W41 = 95 lots
2027-W42 = 110 lots
```

Total demand:

```text
285 lots
```

Scenario ID:

```text
JAPANESE_RICE_VSLICE_001
```

Unit:

```text
lot
```

Source granularity:

```text
weekly
```

---

## 5. Business Meaning

The demand sample represents final demand from the Tokyo market:

```text
MARKET_TOKYO wants standard Japanese rice over three weekly buckets.
```

The demand quantities were intentionally chosen to interact with the existing capacity vertical slice.

Existing capacity sample:

```text
DC_KANTO outbound capacity = 90 lots/week
```

Demand sample:

```text
2027-W40 demand = 80 lots
2027-W41 demand = 95 lots
2027-W42 demand = 110 lots
```

Business interpretation:

```text
2027-W40:
  demand is below DC_KANTO capacity

2027-W41:
  demand slightly exceeds DC_KANTO capacity

2027-W42:
  demand clearly exceeds DC_KANTO capacity
```

This prepares the Japanese Rice Case for a future capacity-constrained PSI demonstration.

This phase only creates the demand lot source.

It does not yet perform the constrained PSI run.

---

## 6. WeeklyDemandRow

Implemented in:

```text
pysi/demand/demand_master_loader.py
```

Primary function:

```python
load_weekly_demand_master_csv(...)
```

Purpose:

```text
Load weekly demand_master.csv rows into canonical WeeklyDemandRow objects.
```

Important behavior:

```text
week keys are preserved as strings
weekly source_granularity is preserved
legacy S_month_data.csv is not read
monthly-to-weekly allocation is not performed
planner behavior is not changed
```

This is intentionally a weekly-demand source path only.

---

## 7. DemandAnchoredLot

Implemented in:

```text
pysi/demand/demand_lot_generator.py
```

Primary function:

```python
generate_demand_anchored_lots(...)
```

Purpose:

```text
Generate deterministic demand anchored lots from WeeklyDemandRow records.
```

Default lot policy:

```text
lot_size = 1
```

Therefore:

```text
80 demand quantity  -> 80 lots
95 demand quantity  -> 95 lots
110 demand quantity -> 110 lots
```

Total generated lots:

```text
285
```

The generated lots are:

```text
deterministic
unique
anchored to final demand
```

---

## 8. Leaf plan_node psi4demand S-slot Adapter

Implemented in:

```text
pysi/demand/demand_lot_generator.py
```

Primary function:

```python
attach_demand_lots_to_leaf_plan_node_psi4demand(...)
```

Purpose:

```text
Represent or apply the compatibility bridge from DemandAnchoredLot IDs
to the demand PSI S slot of the product-specific outbound-tree leaf plan_node.
```

The important contract is:

```text
Demand lot IDs are not merely stored in a generic env-level dictionary.
They are attached to the S slot of the demand PSI on the outbound-tree leaf plan_node.
```

Legacy-compatible meaning:

```python
plan_node.psi4demand[week][0] = list[lot_ID]
```

Symbolic equivalent:

```python
plan_node.psi4demand[week]["S"] = list[lot_ID]
```

For Japanese Rice Case:

```text
product-specific outbound_tree:
  JAPANESE_RICE_STANDARD

leaf plan_node:
  MARKET_TOKYO

target PSI:
  psi4demand

target slot:
  S
```

This is the key semantic bridge to original PySI / WOM demand PSI behavior.

---

## 9. Anchor Semantics

The implementation confirms that demand lots carry or imply:

```text
anchor_tree_side = outbound
anchor_node = MARKET_TOKYO
target_psi_layer = demand
target_psi_slot = S
```

This matches the WOM principle:

```text
Lot is born at final demand.
```

In business terms, `MARKET_TOKYO` represents the terminal demand channel where actual demand occurs.

Examples of equivalent real-world terminal demand points include:

```text
OTC retail counters
supermarket storefronts
EC channels
dealer stores
sales outlets
final market channels
```

This is why `DemandAnchoredLot` is anchored at the outbound-tree leaf plan_node.

---

## 10. Tests Added

Focused test file:

```text
tests/test_japanese_rice_demand_master_vertical_slice.py
```

The tests verify:

```text
demand_master.csv exists
load_weekly_demand_master_csv(...) loads exactly 3 rows
row domains preserve product / demand node / weeks / quantities
generate_demand_anchored_lots(...) generates 285 lots
lot IDs are deterministic and unique
weekly lot counts are 80 / 95 / 110
leaf plan_node psi4demand compatibility shape is produced
psi4demand[week]["S"] contains the generated lot IDs
legacy bridge meaning is explicitly tested
lots carry outbound / MARKET_TOKYO / demand / S anchor semantics
```

---

## 11. Tests Executed

Focused demand vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_demand_master_vertical_slice.py
```

Observed result:

```text
7 passed
```

Japanese Rice capacity vertical slice test:

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

## 12. Current Japanese Rice Case Master-Data Entrance

After this phase, Japanese Rice Case has both supply capability and final demand entrance.

### Capacity side

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
capacity runtime diagnostic
```

### Demand side

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO outbound leaf plan_node compatibility shape
    ↓
psi4demand[week]["S"]
```

This is a major modeling milestone.

WOM now has:

```text
supply capability entrance
final demand lot source
```

for the Japanese Rice Case.

---

## 13. Relationship to Original PySI V0R8 Demand Loading

Original PySI V0R8 behavior remains conceptually preserved:

```text
S_month_data.csv
    ↓
monthly-to-weekly conversion
    ↓
weekly lot_ID generation
    ↓
outbound leaf plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

This phase does not modify that path.

Instead, it introduces a weekly-demand path:

```text
demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
outbound leaf plan_node.psi4demand[w]["S"] = list[lot_ID]
```

Both paths should eventually converge on the same destination:

```text
outbound leaf plan_node.psi4demand[w][0:"S"]
```

Future work should define the monthly compatibility adapter explicitly.

---

## 14. Safety Boundaries Honored

This phase did not change:

```text
original PySI S_month_data.csv behavior
monthly-to-weekly conversion behavior
planner behavior
capacity enforcement behavior
GUI layout
full PSI run behavior
scenario runner behavior
capacity source loading behavior
capacity runtime diagnostics
existing data CSV files
```

This phase only added:

```text
Japanese Rice weekly demand master
minimal demand loader
minimal demand lot generator
leaf plan_node psi4demand compatibility adapter
focused vertical slice tests
```

---

## 15. Important Future Theme: MOM Weekly Demand-Supply Balance Line

A major future visualization hypothesis has been identified:

```text
At MOM nodes, weekly demand and supply balance should be visualized as time-series lines.
```

The purpose is to help humans recognize the demand-supply situation visually and instantly.

The hypothesis:

```text
Humans can understand complex supply-demand imbalance much faster
through weekly line-pattern recognition than through tables alone.
```

Potential future graph:

```text
x-axis:
  week

series:
  demand pressure reaching MOM
  supply capability / available capacity at MOM
  accepted lots
  blocked lots
  backlog / carry-over
  balance gap = supply - demand
```

For Japanese Rice Case, a future MOM balance graph could show:

```text
RICE_MILL_A:
  weekly milling capacity
  demand pressure from MARKET_TOKYO
  potential shortfall

DC_KANTO:
  weekly outbound capacity
  Tokyo demand
  shipment gap
```

This should not be implemented immediately in the demand master vertical slice.

Recommended timing:

```text
after demand + capacity + network/node + first PSI run are connected
```

Reason:

```text
Balance Line visualization requires computed weekly series,
not just master input rows.
```

Recommended future design doc:

```text
docs/design/japanese_rice_mom_weekly_balance_line_visualization.md
```

or a more general reusable design:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

This should be treated as a high-value future GUI / cockpit enhancement.

---

## 16. Still Deferred

The following remain intentionally deferred.

### 16.1 Monthly demand compatibility

Not yet implemented:

```text
S_month_data.csv compatibility
monthly-to-weekly conversion
legacy monthly demand adapter
```

### 16.2 Network / node master

Not yet implemented:

```text
outbound tree actual node instantiation
MARKET_TOKYO as actual tree leaf node
RICE_MILL_A / DC_KANTO network routing
```

### 16.3 Full PSI planning run

Not yet implemented:

```text
end-to-end PSI planning execution
forward / backward lot propagation
capacity-constrained accepted / blocked lot behavior
```

### 16.4 Demand diagnostics integration

Not yet implemented:

```text
diagnostic["demand_source"]
diagnostic["demand_anchored_lots"]
diagnostic["psi4demand_attachment"]
```

### 16.5 GUI / Cockpit demand display

Not yet implemented:

```text
demand lot visibility in GUI
MOM balance line graph
weekly demand-supply line visualization
```

---

## 17. Recommended Next Step

The recommended next design depends on priority.

### Option A: Continue master-data entrance

Recommended if the next objective is to complete the Japanese Rice scenario package:

```text
docs/design/japanese_rice_network_master_vertical_slice.md
```

Purpose:

```text
Define the actual network / node structure that connects MARKET_TOKYO,
DC_KANTO, RICE_MILL_A, and FARM_REGION_A.
```

This is likely the next natural step before full PSI run.

### Option B: Define demand diagnostics

Recommended if the next objective is explainability:

```text
docs/design/japanese_rice_demand_diagnostic_vertical_slice.md
```

Purpose:

```text
Expose demand source, lot generation, and psi4demand attachment diagnostics.
```

### Option C: Define MOM balance visualization

Recommended if the next objective is future GUI direction:

```text
docs/design/wom_mom_weekly_demand_supply_balance_line.md
```

Purpose:

```text
Define weekly time-series visualization of demand-supply balance at MOM nodes.
```

This is high value, but should probably wait until the first PSI run generates actual weekly balance series.

Recommended practical order:

```text
1. Network / node master vertical slice
2. First Japanese Rice PSI run vertical slice
3. Demand / capacity / PSI diagnostics
4. MOM weekly demand-supply balance line visualization
```

---

## 18. Completion Summary

Completed:

```text
Japanese Rice demand_master.csv added
3 demand rows added
total demand quantity = 285
WeeklyDemandRow implemented
load_weekly_demand_master_csv(...) implemented
DemandAnchoredLot implemented
generate_demand_anchored_lots(...) implemented
attach_demand_lots_to_leaf_plan_node_psi4demand(...) implemented
285 deterministic unique demand lots generated
psi4demand[2027-W40]["S"] has 80 lot IDs
psi4demand[2027-W41]["S"] has 95 lot IDs
psi4demand[2027-W42]["S"] has 110 lot IDs
outbound / MARKET_TOKYO / demand / S anchor semantics confirmed
original PySI S_month_data.csv behavior unchanged
monthly compatibility not implemented
planner behavior unchanged
GUI layout unchanged
focused tests passed
related capacity tests passed
capacity regression tests passed
```

Current milestone:

```text
Japanese Rice Case now has both:
  supply capability entrance
  final demand lot source
```

This is a major step toward a visible Japanese Rice WOM demo.

The next structural step is likely:

```text
Japanese Rice network / node master vertical slice
```

The next future visualization theme is:

```text
MOM weekly demand-supply balance line
```
