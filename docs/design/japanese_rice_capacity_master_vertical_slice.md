# Japanese Rice Capacity Master Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-05-31  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_capacity_master_vertical_slice.md`

**Strategic role:** WOM modeling entrance design / master data generation starting point  
**Primary case:** Japanese Rice Case  
**Initial master focus:** `capacity_master.csv`  
**Initial execution target:** Explicit KPI preflight capacity source / runtime diagnostic path

---

## 1. Purpose

This memo defines the first visible vertical slice for the Japanese Rice Case using the newly completed WOM capacity source and diagnostic route.

The immediate objective is not to complete the full Japanese Rice Case.

The immediate objective is to create the smallest meaningful capacity master input that can pass through the current WOM route:

```text
Japanese Rice Case capacity_master.csv
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
load_capacity_master_csv(...)
    ↓
env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
```

This memo also defines the broader design meaning:

```text
WOM case modeling starts by turning real-world business assumptions
into canonical master data rows that WOM can load, diagnose, and simulate.
```

Therefore, this is not only a Japanese Rice design memo.

It is also the first concrete WOM modeling entrance design.

---

## 2. Why This Memo Matters

WOM has recently established the capacity master loading and diagnostic foundation:

```text
capacity_master.csv / scenario package capacity input
    ↓
load_capacity_weekly_rows_to_env(...)
    ↓
env.capacity_weekly_rows_load_summary
    ↓
diagnostic["capacity_weekly_rows_source"]

env.capacity_weekly_rows
    ↓
apply_capacity_runtime_attachment_preflight(...)
    ↓
env.capacity_runtime_attachment_summary
    ↓
diagnostic["runtime_attachment"]
```

This means WOM can now answer two important preflight questions:

```text
1. Where did the capacity rows come from?
2. Were they attached as runtime capacity contexts?
```

The next step is to stop extending abstract infrastructure and run a visible business case through it.

The Japanese Rice Case is the right first case because it is understandable, public-facing, and supply-chain-native:

```text
rice farm / collection
    ↓
rice milling
    ↓
regional DC
    ↓
market demand
```

This is simple enough for a demo and rich enough to show capacity constraints, bottlenecks, weekly planning, and KPI implications.

---

## 3. Current Completed Technical Foundation

Implemented foundation:

```text
load_capacity_master_csv(path)
load_capacity_weekly_rows_to_env(...)
apply_capacity_runtime_attachment_preflight(...)
build_capacity_weekly_rows_source_diagnostic(env)
build_capacity_runtime_attachment_diagnostic(env)
Explicit KPI preflight source wiring
```

Meaning:

```text
capacity_master.csv can now become WeeklyCapacityRow rows,
be attached to env,
be consumed by Explicit KPI preflight,
and be explained by diagnostics.
```

The missing piece is a concrete Japanese Rice capacity master sample.

---

## 4. Design Position in WOM Development

This memo sits at the boundary between WOM infrastructure development and WOM case modeling.

The case modeling entrance is:

```text
business story
    ↓
case scope
    ↓
nodes / products / weeks
    ↓
master data rows
    ↓
WOM preflight
    ↓
diagnostics
    ↓
planning / KPI
```

For the first vertical slice, only the capacity master is targeted:

```text
business capacity assumptions
    ↓
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
Explicit KPI preflight diagnostics
```

This creates a reusable pattern for other cases:

```text
Japanese Rice Case
Vaccine Distribution Case
EV Battery Supply Chain Case
Disaster Relief Supply Case
Imported Food Supply Case
Semiconductor Capacity Case
```

Each case should begin with a minimal master-data vertical slice, not with a large model.

---

## 5. Vertical Slice Definition

A vertical slice means:

```text
the smallest set of master data and tests that proves one business route
can enter WOM and become visible in diagnostics.
```

For this memo, the target vertical slice is:

```text
Japanese Rice capacity_master.csv
    ↓
source diagnostic visible
    ↓
runtime attachment diagnostic visible
```

The first slice does not need to produce a full planning result.

It only needs to prove:

```text
capacity master source can be loaded
WeeklyCapacityRow rows are created
env.capacity_weekly_rows is populated
Explicit KPI preflight consumes the rows
source diagnostic reports the source
runtime diagnostic reports the attached context
```

---

## 6. Initial Japanese Rice Case Story

The initial business story is intentionally simple.

```text
Farm / harvest region
    ↓
Rice mill
    ↓
Kanto distribution center
    ↓
Tokyo market
```

Initial product:

```text
JAPANESE_RICE_STANDARD
```

Initial weeks:

```text
2027-W40
2027-W41
2027-W42
```

Initial scenario:

```text
JAPANESE_RICE_VSLICE_001
```

Initial objective:

```text
Make capacity source and runtime diagnostics visible for a minimal Japanese Rice Case.
```

---

## 7. Initial Nodes

Recommended minimal node set:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
MARKET_TOKYO
```

### FARM_REGION_A

Representative rice producing region.

Initial role:

```text
source / upstream supply node
```

Capacity concept:

```text
weekly harvest / shipment availability
```

### RICE_MILL_A

Representative rice milling / processing facility.

Initial role:

```text
processing bottleneck candidate
```

Capacity concept:

```text
weekly milling capacity
```

### DC_KANTO

Representative Kanto distribution center.

Initial role:

```text
distribution / inventory / shipment node
```

Capacity concept:

```text
weekly outbound shipment capacity
```

### MARKET_TOKYO

Representative demand-side market.

Initial role:

```text
market / consumption node
```

For the first capacity slice, MARKET_TOKYO does not need capacity rows unless a market receiving constraint is intentionally tested.

---

## 8. Initial Product

Initial product:

```text
JAPANESE_RICE_STANDARD
```

Meaning:

```text
standard packaged Japanese table rice
```

This product is intentionally generic.

It is not yet divided into:

```text
brown rice
milled rice
packaged rice
premium rice
business-use rice
rice flour
feed rice
```

Those can be added later.

The first objective is not product richness.

The first objective is a working master-data entrance.

---

## 9. Initial Week Horizon

Recommended first weeks:

```text
2027-W40
2027-W41
2027-W42
```

Reason:

```text
three weeks are enough to test multiple week keys,
duplicate aggregation behavior,
and diagnostic row counts without creating a large dataset.
```

The exact calendar year is not important for the first vertical slice.

The important part is preserving the canonical week key string:

```text
YYYY-Www
```

No week-key normalization should be introduced in this slice.

---

## 10. Initial capacity_type Policy

Use capacity types already compatible with the current capacity route.

Recommended first capacity types:

```text
P
S
```

`P` means production / processing / purchase capacity.

Use `P` for:

```text
FARM_REGION_A harvest availability
RICE_MILL_A milling capacity
```

`S` means shipment / sales / supply-side movement capacity.

Use `S` for:

```text
DC_KANTO outbound shipment capacity
```

If existing code currently expects only `P` in some downstream path, the first implementation may use only `P` and defer `S`.

Recommended business-visible version:

```text
P capacity for FARM_REGION_A and RICE_MILL_A
S capacity for DC_KANTO
```

---

## 11. Initial capacity_qty Values

Use small numbers that are easy to inspect.

Example:

```text
FARM_REGION_A: 120 lots/week
RICE_MILL_A: 100 lots/week
DC_KANTO: 90 lots/week
```

This creates a simple capacity story:

```text
farm supply is larger than milling capacity
milling is larger than DC outbound capacity
DC may become the downstream bottleneck
```

For the first diagnostic slice, bottleneck behavior is not the main target.

The main target is source loading and diagnostic visibility.

---

## 12. Initial cap_mode and unit Policy

Use:

```text
cap_mode = hard
unit = lot
```

Reason:

```text
hard capacity is explicit and easy to understand.
lot is aligned with WOM's lot-based planning model.
```

Do not introduce kilograms, tons, pallets, or bags in the first slice.

Future versions may define unit conversion:

```text
kg -> bag -> pallet -> lot
ton -> lot
```

but that is out of scope here.

---

## 13. Initial capacity_master.csv Schema

Use the canonical schema currently supported by the capacity master loader.

Recommended header:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

Column meanings:

```text
scenario_id:
  scenario identifier

tree_side:
  inbound / outbound / both

node_name:
  WOM node name

product_name:
  product identifier

week:
  canonical business week key

capacity_type:
  P / S / future capacity types

capacity_qty:
  numeric capacity quantity

cap_mode:
  hard / soft / future mode

unit:
  lot

priority:
  integer priority for future selection / diagnostics

calendar_id:
  calendar identifier

comment:
  human-readable explanation
```

---

## 14. Initial capacity_master.csv Sample

Recommended first sample:

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

This is large enough to show:

```text
multiple nodes
multiple weeks
multiple capacity types
source diagnostic row_count
runtime context product/node/type/week shape
```

but small enough to inspect manually.

---

## 15. Recommended Scenario Package Location

Recommended path:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Potential scenario root:

```text
examples/scenarios/japanese_rice_vslice_001
```

Then the current source helper can resolve:

```text
scenario_root / "masters" / "capacity_master.csv"
```

This matches the recently implemented source resolution route.

Alternative direct path for testing:

```text
examples/scenarios/japanese_rice_vslice_001/capacity_master.csv
```

But the preferred scenario package layout is:

```text
masters/capacity_master.csv
```

---

## 16. Expected Source Diagnostic

After loading the sample file, expected source diagnostic:

```text
diagnostic["capacity_weekly_rows_source"]["available"] == True
diagnostic["capacity_weekly_rows_source"]["summary_available"] == True
diagnostic["capacity_weekly_rows_source"]["source_kind"] == "scenario_package_capacity_master"
diagnostic["capacity_weekly_rows_source"]["row_count"] == 9
diagnostic["capacity_weekly_rows_source"]["env_rows_present"] == True
diagnostic["capacity_weekly_rows_source"]["env_row_count"] == 9
diagnostic["capacity_weekly_rows_source"]["row_count_matches_env"] == True
```

Expected source message:

```text
Capacity weekly rows source: loaded 9 rows from capacity_master.csv.
```

The exact message may vary depending on current helper wording.

---

## 17. Expected Runtime Attachment Diagnostic

After runtime attachment preflight, expected runtime diagnostic:

```text
diagnostic["runtime_attachment"]["summary_available"] == True
diagnostic["runtime_attachment"]["input_row_count"] == 9
diagnostic["runtime_attachment"]["forward_shape"] == "product_node_type_week_qty_v1"
diagnostic["runtime_attachment"]["backward_canonical_shape"] == "product_node_type_week_qty_v1"
```

Expected runtime context product:

```text
JAPANESE_RICE_STANDARD
```

Expected runtime context nodes:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
```

Expected capacity types:

```text
P
S
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

---

## 18. Acceptance Criteria for Vertical Slice

This vertical slice is successful when:

```text
capacity_master.csv exists for Japanese Rice Case
load_capacity_weekly_rows_to_env(...) loads it
env.capacity_weekly_rows has expected row count
Explicit KPI preflight consumes env.capacity_weekly_rows
diagnostic["capacity_weekly_rows_source"] reports source available
diagnostic["runtime_attachment"] reports runtime attachment available
no planner behavior change is required
no capacity enforcement behavior change is required
no GUI layout change is required
tests pass
```

This vertical slice is not required to:

```text
generate complete PSI plan
calculate rice demand
optimize allocation
show final KPI cockpit
handle real ton/kg conversion
model all rice supply chain nodes
```

---

## 19. Proposed Test Scope

Recommended focused test file:

```text
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Test should create a temporary scenario package:

```text
tmp_path/
  japanese_rice_vslice_001/
    masters/
      capacity_master.csv
```

Then call the existing functions or GUI preflight helper path to verify:

```text
source loading
runtime attachment
diagnostic visibility
```

### 19.1 Source helper level test

Call:

```python
load_capacity_weekly_rows_to_env(
    env,
    scenario_root=scenario_root,
)
```

Assert:

```text
len(env.capacity_weekly_rows) == 9
env.capacity_weekly_rows_load_summary["available"] is True
env.capacity_weekly_rows_load_summary["row_count"] == 9
```

### 19.2 Explicit KPI preflight level test

Use the existing test style for `WOMCockpit` preflight.

Attach:

```text
env.scenario_root = scenario_root
```

Run Explicit KPI preflight.

Assert:

```text
diagnostic["capacity_weekly_rows_source"]["row_count"] == 9
diagnostic["runtime_attachment"]["input_row_count"] == 9
```

### 19.3 No planner execution required

Do not require full planning execution.

This is a preflight vertical slice.

---

## 20. Proposed Implementation Scope

Recommended first Codex request should add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Do not modify planner.

Do not modify GUI layout.

Do not modify runtime capacity logic.

Do not modify capacity loader behavior unless a bug is found.

---

## 21. Non-Goals

This vertical slice does not include:

```text
full Japanese Rice network master
full demand master
cost master
price master
inventory master
transport leadtime master
real-world rice statistics
ton/kg to lot conversion
optimization
complete PSI plan execution
public demo screen polish
```

These are future layers.

The first vertical slice focuses only on:

```text
capacity master entrance
source diagnostic
runtime attachment diagnostic
```

---

## 22. Relationship to Future WOM Modeling Entrance Design

This memo can become the template for other case entrance designs.

Future case entrance pattern:

```text
1. Define case story.
2. Define minimal node set.
3. Define minimal product set.
4. Define minimal week horizon.
5. Define first master file.
6. Load into canonical rows.
7. Attach to env.
8. Run preflight.
9. Confirm diagnostics.
10. Expand to planning / KPI.
```

For each master type:

```text
capacity_master.csv
demand_master.csv
cost_master.csv
price_master.csv
network_master.csv
leadtime_master.csv
inventory_master.csv
```

WOM should follow the same discipline:

```text
master input
    ↓
canonical row/model
    ↓
env attachment
    ↓
preflight diagnostic
    ↓
runtime behavior
```

This is the emerging WOM modeling entrance architecture.

---

## 23. Future Expansion Path

After this capacity vertical slice, the Japanese Rice Case can expand in this order:

```text
1. Capacity master vertical slice
2. Demand master vertical slice
3. Network / node master vertical slice
4. Leadtime and calendar vertical slice
5. Inventory / buffer vertical slice
6. Cost and price master vertical slice
7. PSI planning run
8. KPI / issue diagnostic
9. Cockpit-visible demo
10. Public README / note / video scenario
```

This keeps development grounded in visible working increments.

---

## 24. Recommended Next Codex Request

Recommended next request file:

```text
docs/codex_requests/japanese_rice_capacity_master_vertical_slice_request.md
```

Scope:

```text
add minimal Japanese Rice capacity_master.csv sample
add focused vertical slice tests
verify source diagnostic
verify runtime attachment diagnostic
no planner behavior change
no GUI layout change
no data CSV changes outside the new example scenario path
```

---

## 25. Development Meaning

This memo marks an important transition.

Before this point, the work was mostly infrastructure:

```text
capacity loader
env attachment
preflight wiring
diagnostics
```

From this point, the work returns to case modeling:

```text
Japanese Rice Case
    ↓
master data
    ↓
WOM diagnostics
    ↓
visible demo
```

This is the right direction if the goal is to make WOM visible and publishable.

In short:

```text
The runway is ready.
This memo defines the first Rice Case test flight.
```

---

## 26. Summary

This memo defines the first Japanese Rice Case capacity vertical slice:

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

The goal is to prove the modeling entrance:

```text
business case assumption
    ↓
master data row
    ↓
canonical WOM row
    ↓
preflight diagnostic
```

This is the first step toward making Japanese Rice Case visible.

Recommended next request:

```text
docs/codex_requests/japanese_rice_capacity_master_vertical_slice_request.md
```
