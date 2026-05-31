# Codex Request: Japanese Rice Demand Master Vertical Slice — Revised

**Version:** v0r2 revised  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_demand_master_vertical_slice_request.md`

**Revision note:**  
This revised version clarifies the most important target data structure: generated demand lot IDs must be attached to the **demand PSI S slot of the product-specific outbound-tree leaf `plan_node`**, not merely to a standalone env-level dictionary.

**Parent design doc:**

```text
docs/design/japanese_rice_demand_master_vertical_slice.md
```

**Related design / completion docs:**

```text
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice.md
docs/design/wom_capacity_weekly_rows_source_diagnostic_completion.md
docs/design/wom_capacity_source_explicit_kpi_preflight_wiring_completion.md
docs/design/wom_capacity_master_to_env_capacity_weekly_rows_source_completion.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the first Japanese Rice Case demand master vertical slice.

This request should add a minimal weekly demand master sample and focused tests proving the following path:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
    ↓
load_weekly_demand_master_csv(...)
    ↓
WeeklyDemandRow
    ↓
generate_demand_anchored_lots(...)
    ↓
resolve demand_node to product-specific outbound-tree leaf plan_node
    ↓
attach generated lot IDs to plan_node.psi4demand[week][0] or plan_node.psi4demand[week]["S"]
```

This is the first demand-side WOM modeling entrance test flight for Japanese Rice Case.

The implementation should remain narrow.

Use weekly demand first.

Do not implement monthly `S_month_data.csv` compatibility in this request.

Do not rewrite the original PySI V0R8 demand loading process.

Do not change planner behavior.

Do not change GUI layout.

Do not run or require a full PSI planning execution.

---

## 2. Critical Clarification: Target psi4demand Location

This clarification is mandatory.

The target `psi4demand` is **not** a standalone env-level dictionary.

The generated demand lot IDs must be attached to the demand PSI S slot of the **outbound-tree leaf `plan_node`** for the corresponding `product_name` and `demand_node`.

In legacy-compatible terms:

```python
plan_node.psi4demand[week][0] = list[lot_ID]
```

or, if the implementation exposes symbolic slot names:

```python
plan_node.psi4demand[week]["S"] = list[lot_ID]
```

Here:

```text
plan_node:
  product-specific planning-layer node generated on the outbound_tree for product_name

demand_node:
  final demand leaf node on that product-specific outbound_tree

S slot:
  Sales / shipment demand slot in demand PSI

DemandAnchoredLot:
  lot generated from real demand at that final demand leaf node
```

Therefore, for the Japanese Rice vertical slice:

```text
product_name = JAPANESE_RICE_STANDARD
demand_node = MARKET_TOKYO
```

means:

```text
Find / represent the MARKET_TOKYO leaf plan_node
on the outbound_tree for JAPANESE_RICE_STANDARD,
then attach generated lot IDs to:

MARKET_TOKYO.plan_node.psi4demand[2027-W40]["S"]
MARKET_TOKYO.plan_node.psi4demand[2027-W41]["S"]
MARKET_TOKYO.plan_node.psi4demand[2027-W42]["S"]
```

If the current vertical slice does not instantiate the full outbound tree, the implementation may provide a minimal pure adapter structure that explicitly models this contract, but tests and naming must preserve the meaning:

```text
product-specific outbound-tree leaf plan_node demand PSI S slot
```

Do not implement it as an unrelated generic dictionary without documenting this compatibility meaning.

---

## 3. Business Meaning of the Leaf plan_node

The outbound-tree leaf `plan_node` represents the actual final demand point.

In business terms, demand is generated at terminal demand channels such as:

```text
OTC retail counters
supermarket store fronts
EC channels
dealer stores
sales outlets
final market channels
```

For Japanese Rice Case:

```text
MARKET_TOKYO
```

is a representative final market leaf node.

It is not just an abstract region.

It represents the terminal market channel where rice demand occurs.

Therefore:

```text
DemandAnchoredLot is anchored at MARKET_TOKYO.
```

This is central to WOM:

```text
Lot is born at final demand.
```

---

## 4. Strategic Context

The Japanese Rice capacity vertical slice has already been completed:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows
    ↓
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
```

This request adds the demand-side entrance.

The target is to prove that Japanese Rice market demand can enter WOM as demand anchored lots and be placed in the product-specific outbound leaf `plan_node` demand PSI S slot.

The development meaning is:

```text
Capacity defines what supply can do.
Demand defines why lots should flow.
```

---

## 5. Relationship to Original PySI V0R8 Demand Loading

Original PySI V0R8 demand process:

```text
S_month_data.csv
    ↓
monthly-to-weekly conversion
    ↓
weekly lot_ID generation
    ↓
outbound leaf Plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

This request does **not** replace that process.

This request creates a new weekly-demand vertical slice that should eventually coexist with the original monthly process under a unified WOM demand entrance.

The future architecture should be:

```text
weekly demand source
monthly demand source / S_month_data.csv
    ↓
canonical demand rows
    ↓
weekly demand rows
    ↓
demand anchored lots
    ↓
outbound leaf plan_node.psi4demand[w]["S"] = list[lot_ID]
```

This request only implements the weekly source path.

Monthly `S_month_data.csv` compatibility is explicitly deferred to a future request.

The final destination remains compatible with original PySI:

```text
outbound leaf plan_node.psi4demand[w][0:"S"]
```

---

## 6. Source Documents to Read First

Please read:

```text
docs/design/japanese_rice_demand_master_vertical_slice.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice.md
```

Please inspect current code and existing tests to align style and avoid duplicate patterns:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
tests/test_japanese_rice_capacity_master_vertical_slice.py
pysi/capacity/capacity_weekly_rows_source.py
pysi/capacity/capacity_master_loader.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

If a demand package already exists, reuse or extend it minimally.

If no demand package exists, create a small isolated `pysi/demand` package.

---

## 7. Implementation Scope

### Required files to add

Add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
tests/test_japanese_rice_demand_master_vertical_slice.py
```

Add minimal demand implementation files if they do not already exist:

```text
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
pysi/demand/__init__.py
```

If equivalent modules already exist, reuse them instead of creating duplicates.

### Expected implementation units

Implement or reuse:

```python
load_weekly_demand_master_csv(path) -> list[WeeklyDemandRow]
generate_demand_anchored_lots(rows, *, lot_size=1) -> list[DemandAnchoredLot]
attach_demand_lots_to_leaf_plan_node_psi4demand(...)
```

The exact function names may be adjusted to match existing project naming style, but the behavior must remain clear and focused.

The attachment function must preserve the meaning:

```text
Attach generated lot IDs to the demand PSI S slot of the outbound-tree leaf plan_node.
```

---

## 8. Explicit Non-Scope

Do not implement:

```text
monthly S_month_data.csv compatibility
monthly-to-weekly conversion
full original PySI V0R8 demand loader rewrite
forecasting
demand planning optimization
complete PSI planning run
capacity blocking based on demand
network routing
leadtime shift
inventory calculation
cost / price / KPI integration
GUI wiring
scenario runner wiring
```

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

unless an existing import/test convention absolutely requires a small harmless package export.

---

## 9. Demand Master Location

Create:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

This sits beside the existing capacity file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

The scenario root remains:

```text
examples/scenarios/japanese_rice_vslice_001
```

---

## 10. Demand Master Schema

Use this weekly demand schema:

```csv
scenario_id,demand_node,product_name,week,demand_qty,unit,source_granularity,priority,calendar_id,comment
```

Column meanings:

```text
scenario_id:
  scenario identifier

demand_node:
  final demand node / market leaf node on the product-specific outbound_tree

product_name:
  product identifier used to resolve the product-specific outbound_tree

week:
  canonical weekly demand bucket

demand_qty:
  demand quantity in lot units

unit:
  lot

source_granularity:
  weekly

priority:
  demand priority

calendar_id:
  calendar identifier

comment:
  human-readable explanation
```

Do not use Japanese column names.

Do not add monthly columns in this request.

---

## 11. Demand Master Rows

Add exactly these rows unless a current loader convention requires a minor formatting adjustment:

```csv
scenario_id,demand_node,product_name,week,demand_qty,unit,source_granularity,priority,calendar_id,comment
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W40,80,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 40
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W41,95,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 41
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W42,110,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 42
```

Expected row count:

```text
3
```

Expected product:

```text
JAPANESE_RICE_STANDARD
```

Expected demand node:

```text
MARKET_TOKYO
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

Expected demand quantities:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

Expected total demand quantity:

```text
285 lots
```

---

## 12. Business Meaning of the Sample

The existing capacity sample includes:

```text
DC_KANTO outbound shipment capacity = 90 lots/week
```

The demand sample intentionally creates this simple future planning story:

```text
2027-W40:
  MARKET_TOKYO demand = 80 lots
  below DC_KANTO capacity 90

2027-W41:
  MARKET_TOKYO demand = 95 lots
  slightly above DC_KANTO capacity 90

2027-W42:
  MARKET_TOKYO demand = 110 lots
  clearly above DC_KANTO capacity 90
```

This sets up a future capacity-constrained planning demonstration.

This request should not implement the capacity-constrained planning demonstration yet.

---

## 13. WeeklyDemandRow Contract

If no existing canonical demand row class exists, add a minimal dataclass:

```python
@dataclass(frozen=True)
class WeeklyDemandRow:
    scenario_id: str
    demand_node: str
    product_id: str
    week: str
    demand_qty: int | float
    unit: str = "lot"
    source_granularity: str = "weekly"
    priority: int | None = None
    calendar_id: str | None = None
    comment: str | None = None
    source_id: str | None = None
    source_file: str | None = None
```

Compatibility aliases may be added if useful:

```python
node_name
product_name
```

The implementation should preserve week keys as strings.

Do not normalize:

```text
2027-W40
```

into an integer week index in this request.

---

## 14. DemandAnchoredLot Contract

If no existing demand lot class exists, add a minimal dataclass:

```python
@dataclass(frozen=True)
class DemandAnchoredLot:
    lot_id: str
    scenario_id: str
    demand_node: str
    product_id: str
    demand_week: str
    quantity: int | float = 1
    anchor_tree_side: str = "outbound"
    anchor_node: str | None = None
    target_psi_layer: str = "demand"
    target_psi_slot: str = "S"
    source_row_id: str | None = None
    source_granularity: str = "weekly"
```

For Japanese Rice Case:

```text
anchor_tree_side = outbound
anchor_node = MARKET_TOKYO
target_psi_layer = demand
target_psi_slot = S
```

The lot ID should be deterministic.

Recommended lot ID pattern:

```text
JAPANESE_RICE_VSLICE_001|MARKET_TOKYO|JAPANESE_RICE_STANDARD|2027-W40|000001
```

or a sanitized equivalent.

The exact format can differ, but tests should assert deterministic behavior and uniqueness.

---

## 15. Lot Generation Policy

For the first slice, use:

```text
lot_size = 1
```

Therefore:

```text
demand_qty = 80 -> 80 lots
demand_qty = 95 -> 95 lots
demand_qty = 110 -> 110 lots
```

Expected total lots:

```text
285
```

If the implementation supports a configurable `lot_size`, default it to 1.

Do not implement complex partial lot behavior unless already trivial.

If fractional demand quantities appear, raise a clear ValueError or handle only integer lot quantities for this slice.

The provided sample uses integer demand quantities.

---

## 16. Leaf plan_node psi4demand Attachment Contract

Implement a pure adapter that represents or applies the legacy-compatible demand PSI S-slot attachment.

Recommended function name:

```python
attach_demand_lots_to_leaf_plan_node_psi4demand(...)
```

Minimum pure returned shape if no actual `Plan_node` object is used:

```python
{
    "JAPANESE_RICE_STANDARD": {
        "MARKET_TOKYO": {
            "psi4demand": {
                "2027-W40": {"S": [lot_id, lot_id, ...]},
                "2027-W41": {"S": [lot_id, lot_id, ...]},
                "2027-W42": {"S": [lot_id, lot_id, ...]},
            }
        }
    }
}
```

This structure explicitly represents:

```text
product-specific outbound_tree
    ↓
leaf plan_node = MARKET_TOKYO
    ↓
psi4demand[week]["S"]
```

If current test style prefers a simpler shape, an additional helper may return:

```python
{
    "2027-W40": {"S": [lot_id, lot_id, ...]},
    "2027-W41": {"S": [lot_id, lot_id, ...]},
    "2027-W42": {"S": [lot_id, lot_id, ...]},
}
```

but tests must still document that this is the leaf plan_node `psi4demand` compatibility shape.

The target is not generic env storage.

The target is leaf plan_node demand PSI S slot compatibility.

---

## 17. Optional Actual PlanNode Support

If a lightweight existing `Plan_node` or node object is easy to instantiate, the adapter may support actual mutation:

```python
attach_demand_lots_to_leaf_plan_node_psi4demand(
    lots,
    outbound_leaf_plan_nodes={("JAPANESE_RICE_STANDARD", "MARKET_TOKYO"): plan_node},
)
```

and set:

```python
plan_node.psi4demand[week][0] = list[lot_ID]
```

or:

```python
plan_node.psi4demand[week]["S"] = list[lot_ID]
```

However, do not introduce fragile dependencies on the full GUI or full planning engine.

A pure compatibility shape is acceptable for this vertical slice if it is clearly named and tested.

---

## 18. Diagnostics

A minimal diagnostic helper may be added if useful, but it is not required to integrate with the existing capacity scenario alignment diagnostic in this request.

If added, keep it pure and local:

```python
build_demand_vertical_slice_diagnostic(rows, lots, psi4demand_by_product_leaf) -> dict
```

Minimum expected fields:

```text
row_count = 3
total_demand_qty = 285
lot_count = 285
product_count = 1
demand_node_count = 1
week_count = 3
weeks = ["2027-W40", "2027-W41", "2027-W42"]
demand_nodes = ["MARKET_TOKYO"]
products = ["JAPANESE_RICE_STANDARD"]
target_tree_side = "outbound"
target_node_role = "leaf_plan_node"
target_psi_layer = "demand"
target_psi_slot = "S"
```

Do not wire it into GUI.

Do not wire it into scenario runner.

---

## 19. Required Tests

Add:

```text
tests/test_japanese_rice_demand_master_vertical_slice.py
```

### 19.1 Demand master file exists and loads

Assert:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv exists
load_weekly_demand_master_csv(path) returns 3 rows
```

### 19.2 Loaded row domains are preserved

Assert:

```text
product is JAPANESE_RICE_STANDARD
demand_node is MARKET_TOKYO
weeks are 2027-W40, 2027-W41, 2027-W42
demand quantities are 80, 95, 110
source_granularity is weekly
```

### 19.3 Lot generation is deterministic

Generate lots.

Assert:

```text
lot_count == 285
all lot IDs are unique
calling generator twice gives the same first and last lot IDs
```

### 19.4 Weekly lot counts match demand

Assert:

```text
2027-W40 lot count == 80
2027-W41 lot count == 95
2027-W42 lot count == 110
```

### 19.5 Leaf plan_node psi4demand S-slot attachment

Build the compatibility structure.

Assert:

```text
product key includes JAPANESE_RICE_STANDARD
leaf node key includes MARKET_TOKYO
psi4demand["2027-W40"]["S"] has 80 lot IDs
psi4demand["2027-W41"]["S"] has 95 lot IDs
psi4demand["2027-W42"]["S"] has 110 lot IDs
```

If the adapter returns a direct leaf psi4demand structure, assert clearly that it represents the leaf plan_node.

### 19.6 Legacy compatibility meaning

At least one test name or assertion should explicitly state that this S-slot output is the compatibility bridge to:

```text
outbound leaf plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

Do not require an actual Plan_node object unless it is trivial and stable.

### 19.7 DemandAnchoredLot anchor semantics

Assert lots carry or imply:

```text
anchor_tree_side = outbound
anchor_node = MARKET_TOKYO
target_psi_layer = demand
target_psi_slot = S
```

If the dataclass does not include all fields, assert equivalent information from the adapter.

---

## 20. Test Commands

Run focused demand vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_demand_master_vertical_slice.py
```

Run the existing capacity vertical slice and capacity diagnostics to confirm no regression:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
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

## 21. Safety Boundaries

Expected changed / added files:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
pysi/demand/__init__.py
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
tests/test_japanese_rice_demand_master_vertical_slice.py
```

If equivalent demand modules already exist, modify/reuse those instead.

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Do not modify existing CSV data except adding the new `demand_master.csv` under the Japanese Rice scenario path.

---

## 22. Acceptance Criteria

This request is complete when:

```text
Japanese Rice demand_master.csv is added
row count is exactly 3
total demand quantity is 285
WeeklyDemandRow or equivalent canonical rows are loaded
demand anchored lots are generated
lot count is 285 with lot_size=1
lot IDs are deterministic and unique
lots are anchored to outbound / MARKET_TOKYO / demand / S semantics
leaf plan_node psi4demand S-slot compatibility structure is produced
weekly S-slot lot counts are 80, 95, and 110
original PySI S_month_data.csv process is not changed
monthly compatibility is not implemented yet
planner behavior unchanged
GUI layout unchanged
full PSI run not required
focused tests pass
capacity vertical slice and diagnostics tests still pass
```

---

## 23. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the Japanese Rice demand_master.csv added?
How many rows does it contain?
What total demand quantity does it represent?
What product / demand node / weeks does it use?
Where are WeeklyDemandRow and DemandAnchoredLot implemented or reused?
What loader function was added or reused?
What lot generator function was added or reused?
What leaf plan_node psi4demand S-slot adapter was added or reused?
Does it produce 285 deterministic lots?
Does the compatibility structure represent product-specific outbound_tree leaf plan_node psi4demand?
Does psi4demand[w]["S"] contain 80 / 95 / 110 lot IDs?
Do lots carry or imply outbound / MARKET_TOKYO / demand / S anchor semantics?
Did you change original PySI S_month_data.csv behavior?
Did you implement monthly compatibility?
Did you change planner behavior?
Did you change GUI layout?
Which tests passed?
```

---

## 24. Development Meaning

This request creates the first demand-side master-data entrance for Japanese Rice Case.

It does not replace original PySI monthly demand logic.

It creates a weekly demand path that can later coexist with monthly compatibility.

The result should prove:

```text
MARKET_TOKYO wants rice in week 40, 41, and 42.
That demand becomes deterministic lots.
Those lots are anchored at the MARKET_TOKYO outbound leaf plan_node.
Those lot IDs sit in the demand PSI S slot.
```

This is the next test flight after the capacity master slice.

The Rice Case now gets not only cargo capacity, but actual final-market demand.
