# Japanese Rice Demand Master Vertical Slice

**Version:** v0r1 draft  
**Date:** 2026-05-31  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_demand_master_vertical_slice.md`

**Strategic role:** WOM modeling entrance design for demand-side master data  
**Primary case:** Japanese Rice Case  
**Initial master focus:** demand master / demand source loading  
**Initial execution target:** Demand source -> weekly demand rows -> demand anchored lot generation -> `psi4demand[w]["S"]`

---

## 1. Purpose

This memo defines the next Japanese Rice Case vertical slice: demand master loading.

The immediate objective is to clarify how the new WOM demand master entrance relates to the original PySI V0R8 demand loading process:

```text
S_month_data.csv
    ↓
monthly-to-weekly conversion
    ↓
weekly lot_ID generation
    ↓
Plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

The conclusion is:

```text
The original PySI V0R8 demand loading process should not be discarded.

It should be preserved as a legacy monthly-demand adapter path, then gradually wrapped
by a canonical WOM demand loading entrance that can handle both monthly and weekly
demand sources.
```

This means the future WOM architecture should support:

```text
monthly demand source
    ↓
canonical demand rows
    ↓
weekly allocation / conversion
    ↓
demand anchored lot generation
    ↓
psi4demand[w]["S"]

weekly demand source
    ↓
canonical demand rows
    ↓
demand anchored lot generation
    ↓
psi4demand[w]["S"]
```

This memo does not request implementation yet.

It defines the design position and the first Japanese Rice demand vertical slice.

---

## 2. Relationship to Original PySI V0R8 Demand Loading

### 2.1 Original PySI V0R8 process

The original PySI V0R8 demand loading process can be summarized as:

```text
1. Load S_month_data.csv.
2. Interpret it as monthly demand data.
3. Convert monthly demand quantities into weekly demand.
4. Generate lot_IDs from weekly demand quantities.
5. Attach those lot_IDs to the leaf / plan node demand PSI:
   Plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

This original process is important because it already embodies WOM's most essential demand-side idea:

```text
demand is converted into lots,
and those lots become the primary objects that flow through PSI.
```

The original process is not a throwaway mechanism.

It is the ancestor of WOM's demand anchored lot generation.

---

## 3. Difference Between Original PySI and New WOM Demand Master Entrance

The difference is not the final target.

Both processes ultimately aim to set:

```text
psi4demand[w]["S"] = list[lot_ID]
```

The difference is the architectural layer before that point.

### 3.1 Original PySI V0R8

Original PySI is more direct:

```text
S_month_data.csv
    ↓
monthly-to-weekly conversion
    ↓
lot generation
    ↓
node.psi4demand[w]["S"]
```

Characteristics:

```text
CSV shape and runtime behavior are relatively close.
Monthly demand is the dominant input.
The conversion and lot generation are tightly coupled.
The output is directly attached to node PSI state.
```

### 3.2 New WOM direction

The WOM direction should introduce a canonical entrance layer:

```text
demand source
    ↓
canonical demand rows
    ↓
source-granularity adapter
    ↓
weekly demand rows
    ↓
demand anchored lot generation
    ↓
node.psi4demand[w]["S"]
```

Characteristics:

```text
Monthly and weekly demand sources can be handled under one architecture.
Legacy S_month_data.csv can be supported through an adapter.
The canonical row layer makes diagnostics and future scenario package design easier.
Lot generation remains central.
The final PSI attachment remains compatible with existing WOM/PySI runtime semantics.
```

---

## 4. Is the Original Demand Process Rewritten?

Not immediately.

The correct design stance is:

```text
Do not rewrite the original demand loading process in one step.
```

Instead:

```text
1. Preserve original PySI V0R8 monthly demand behavior.
2. Define it as a legacy monthly-demand adapter.
3. Add canonical WOM demand rows around it.
4. Add weekly demand source support as a peer path.
5. Keep the final output contract compatible:
   psi4demand[w]["S"] = list[lot_ID].
```

So the answer is:

```text
The original demand process is not replaced immediately.

It is refactored into a compatibility layer and eventually becomes one source path
inside a broader unified WOM demand loading process.
```

---

## 5. Unified Monthly / Weekly Demand Loading Concept

The future WOM demand loading architecture should support both monthly and weekly inputs.

### 5.1 Monthly demand source

Example:

```text
S_month_data.csv
monthly_demand_master.csv
```

Flow:

```text
monthly demand source
    ↓
MonthlyDemandRow
    ↓
monthly-to-weekly allocation
    ↓
WeeklyDemandRow
    ↓
lot generation
    ↓
DemandAnchoredLot
    ↓
psi4demand[w]["S"]
```

### 5.2 Weekly demand source

Example:

```text
weekly_demand_master.csv
demand_master.csv with source_granularity=weekly
```

Flow:

```text
weekly demand source
    ↓
WeeklyDemandRow
    ↓
lot generation
    ↓
DemandAnchoredLot
    ↓
psi4demand[w]["S"]
```

### 5.3 Unified output

Both paths should converge into:

```text
DemandAnchoredLot
    ↓
Plan_node.psi4demand[w]["S"] = list[lot_ID]
```

This output contract is essential for backward compatibility.

---

## 6. Design Principle

The demand master entrance should follow the same pattern as the recently completed capacity master entrance.

Capacity path:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
    ↓
runtime context
    ↓
diagnostic
```

Demand path should become:

```text
demand_master.csv / S_month_data.csv
    ↓
CanonicalDemandRow
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
env.demand_anchored_lots or node.psi4demand[w]["S"]
    ↓
diagnostic
```

The common WOM modeling entrance pattern is:

```text
business assumption
    ↓
master data source
    ↓
canonical row
    ↓
runtime object
    ↓
diagnostic
    ↓
planning behavior
```

---

## 7. Japanese Rice Demand Vertical Slice Objective

The Japanese Rice demand vertical slice should prove the first demand-side entrance:

```text
Japanese Rice demand source
    ↓
weekly demand rows
    ↓
demand anchored lot generation
    ↓
diagnostic visibility
```

The first slice should be small.

It should not try to implement full demand planning or forecasting.

The first slice should prove:

```text
MARKET_TOKYO demand for JAPANESE_RICE_STANDARD can become weekly lots.
```

---

## 8. Initial Japanese Rice Demand Story

The initial demand story is:

```text
Tokyo market requires standard Japanese rice over three weeks.
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

Example weekly demand:

```text
2027-W40 = 80 lots
2027-W41 = 95 lots
2027-W42 = 110 lots
```

This intentionally interacts with the existing capacity sample:

```text
DC_KANTO outbound capacity = 90 lots/week
```

Interpretation:

```text
2027-W40 demand is below DC capacity.
2027-W41 demand slightly exceeds DC capacity.
2027-W42 demand clearly exceeds DC capacity.
```

This will eventually make capacity bottleneck behavior visible.

For the first demand vertical slice, however, the target is only to load demand and generate lots.

---

## 9. Initial Demand Master Options

There are two possible first implementations.

### Option A: Weekly demand master first

Create:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

with weekly demand rows.

Example schema:

```csv
scenario_id,demand_node,product_name,week,demand_qty,unit,source_granularity,priority,calendar_id,comment
```

Example rows:

```csv
scenario_id,demand_node,product_name,week,demand_qty,unit,source_granularity,priority,calendar_id,comment
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W40,80,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 40
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W41,95,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 41
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,JAPANESE_RICE_STANDARD,2027-W42,110,lot,weekly,1,CAL_JP_STD,Tokyo market demand week 42
```

Advantages:

```text
simple
directly aligned with current weekly planning horizon
does not require monthly-to-weekly allocation logic
good first vertical slice
```

Disadvantage:

```text
does not yet prove compatibility with original S_month_data.csv
```

### Option B: Monthly demand compatibility first

Create:

```text
examples/scenarios/japanese_rice_vslice_001/masters/S_month_data.csv
```

or:

```text
monthly_demand_master.csv
```

and verify the legacy monthly-to-weekly path.

Advantages:

```text
directly validates original PySI V0R8 demand loading compatibility
```

Disadvantages:

```text
may require more knowledge of current legacy input shape
risks turning the first vertical slice into a refactoring task
less direct than weekly source for a visible test flight
```

### Recommended first choice

Use Option A first:

```text
weekly demand master first
```

Then add Option B as the next compatibility slice:

```text
legacy S_month_data.csv monthly demand adapter
```

Reason:

```text
The immediate goal is to make Japanese Rice Case visible.
The original monthly process should be preserved, but not allowed to block the first demand slice.
```

---

## 10. Proposed First Demand Master Schema

Recommended first weekly demand master schema:

```csv
scenario_id,demand_node,product_name,week,demand_qty,unit,source_granularity,priority,calendar_id,comment
```

Column meanings:

```text
scenario_id:
  scenario identifier

demand_node:
  final demand node / leaf node

product_name:
  product identifier

week:
  canonical weekly demand bucket

demand_qty:
  demand quantity in lot units

unit:
  lot

source_granularity:
  weekly

priority:
  optional demand priority

calendar_id:
  calendar identifier

comment:
  human-readable explanation
```

This schema is intentionally similar in style to capacity master.

Future monthly schema may include:

```text
month
monthly_demand_qty
allocation_policy
```

---

## 11. Proposed First Demand Sample

Recommended sample:

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

Expected total demand:

```text
285 lots
```

Expected lot generation:

```text
285 demand anchored lots
```

if one lot corresponds to one demand unit.

If current WOM lot size logic groups quantity into larger lots, the expected lot count should follow the current configured lot size.

---

## 12. Demand Anchored Lot Policy

The demand vertical slice should maintain WOM's core principle:

```text
Lot is the subject.
```

Therefore, weekly demand rows should generate:

```text
DemandAnchoredLot
```

or compatible lot dictionaries / lot IDs.

Each lot should carry at least:

```text
lot_id
scenario_id
demand_node
product_id / product_name
demand_week
source_granularity
source_id
quantity or lot_size
```

Minimum acceptable first implementation:

```text
deterministic lot IDs are generated from weekly demand rows
those lot IDs are placed into psi4demand[w]["S"]
```

---

## 13. psi4demand Attachment Contract

The legacy-compatible output should remain:

```text
Plan_node.psi4demand[w][0:"S"] = list[lot_ID]
```

More explicitly:

```text
psi4demand[week]["S"] = [lot_ID_001, lot_ID_002, ...]
```

or in the legacy numeric index style:

```text
psi4demand[week][0] = [lot_ID_001, lot_ID_002, ...]
```

The design should not force an immediate rewrite of PSI internal structures.

Instead, introduce an adapter boundary:

```text
DemandAnchoredLot rows
    ↓
psi4demand adapter
    ↓
legacy-compatible psi4demand slot
```

This lets the existing planning engine continue to work.

---

## 14. Source Granularity Policy

The unified demand loading design should define:

```text
source_granularity = weekly
source_granularity = monthly
```

For the first Japanese Rice demand vertical slice:

```text
source_granularity = weekly
```

For original PySI compatibility:

```text
source_granularity = monthly
```

The future loader should route by this field or by source file type.

Expected future architecture:

```text
load_demand_source_to_env(...)
    ↓
detect weekly / monthly source
    ↓
weekly source adapter OR monthly source adapter
    ↓
env.weekly_demand_rows
    ↓
env.demand_anchored_lots
    ↓
psi4demand attachment
```

---

## 15. Relationship to S_month_data.csv

The original file:

```text
S_month_data.csv
```

should be treated as:

```text
legacy monthly demand source
```

It should eventually be supported by a monthly demand adapter:

```text
S_month_data.csv
    ↓
MonthlyDemandRow
    ↓
monthly-to-weekly conversion
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
psi4demand[w]["S"]
```

This means the new demand master process should not invalidate `S_month_data.csv`.

Instead, it should make its semantics explicit.

Original PySI behavior becomes one path under WOM:

```text
legacy_monthly_demand_adapter
```

This is important for backward compatibility.

---

## 16. Diagnostic Design Direction

The demand entrance should eventually have diagnostics parallel to capacity diagnostics.

Capacity diagnostics:

```text
diagnostic["capacity_weekly_rows_source"]
diagnostic["runtime_attachment"]
```

Demand diagnostics should eventually include:

```text
diagnostic["demand_source"]
diagnostic["weekly_demand_rows"]
diagnostic["demand_anchored_lots"]
diagnostic["psi4demand_attachment"]
```

For the first demand vertical slice, a focused diagnostic can be minimal:

```text
demand source loaded
weekly demand row count
total demand quantity
lot count generated
weeks covered
demand node covered
product covered
psi4demand S slot attached
```

---

## 17. Initial Test Strategy

Recommended first test file:

```text
tests/test_japanese_rice_demand_master_vertical_slice.py
```

Expected test stages:

```text
1. Repository demand_master.csv exists.
2. Demand source loads as weekly demand rows.
3. Weekly demand rows preserve product / node / week / quantity.
4. Demand anchored lots are generated.
5. Lot IDs are deterministic.
6. Lots are attached to psi4demand[w]["S"] or equivalent structure.
7. Diagnostics report row count, total demand quantity, and lot count.
```

If demand loader infrastructure does not yet exist, the first Codex request should be explicitly scoped to create a minimal pure adapter first, not full GUI wiring.

---

## 18. Proposed Implementation Scope for First Demand Slice

The first Codex implementation should likely add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
pysi/demand/demand_master_loader.py
pysi/demand/demand_lot_generator.py
tests/test_japanese_rice_demand_master_vertical_slice.py
```

Possibly:

```text
pysi/demand/__init__.py
```

But it should not yet modify the full planning engine unless required.

A safe first implementation path:

```text
load_weekly_demand_master_csv(path)
    ↓
list[WeeklyDemandRow]
    ↓
generate_demand_anchored_lots(rows)
    ↓
dict[week][S] = list[lot_id]
```

This can be tested as a pure function before wiring into the main engine.

---

## 19. Non-Goals for First Demand Slice

Do not implement:

```text
full monthly-to-weekly S_month_data.csv compatibility
full original PySI demand loader rewrite
complete PSI planning run
GUI wiring
scenario runner wiring
forecasting
demand planning optimization
cost / price / KPI integration
network routing
leadtime shift
inventory calculation
capacity blocking based on demand
```

The first demand slice should prove the demand entrance, not the full plan.

---

## 20. Recommended Development Sequence

Recommended sequence:

```text
1. Define Japanese Rice weekly demand_master.csv.
2. Implement pure weekly demand loader.
3. Implement pure demand lot generator.
4. Implement psi4demand attachment adapter.
5. Add focused Japanese Rice demand vertical slice tests.
6. Add completion memo.
7. Then design monthly S_month_data.csv compatibility adapter.
```

This keeps the work visible and avoids breaking the original demand loading process.

---

## 21. Position of Monthly Demand Compatibility

Monthly compatibility should come after the weekly demand vertical slice.

Recommended future design:

```text
docs/design/wom_legacy_monthly_demand_adapter.md
```

or:

```text
docs/design/japanese_rice_monthly_demand_compatibility_slice.md
```

Purpose:

```text
Map original S_month_data.csv semantics into the new canonical demand row / lot generation architecture.
```

This is where the original PySI V0R8 behavior should be preserved and documented in detail.

---

## 22. Acceptance Criteria for This Design

This design is accepted if it clarifies:

```text
original PySI S_month_data.csv process is not immediately replaced
original process becomes a legacy monthly adapter path
new WOM demand entrance should support both weekly and monthly demand sources
first Japanese Rice demand vertical slice should use weekly demand for simplicity
final output remains legacy-compatible psi4demand[w]["S"] = list[lot_ID]
monthly S_month_data.csv compatibility is deferred but explicitly preserved
```

---

## 23. Summary

The Japanese Rice Demand Master Vertical Slice should not be understood as a sudden rewrite of original PySI demand loading.

It should be understood as the first step toward a unified WOM demand entrance:

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
psi4demand[w]["S"]
```

For the first Japanese Rice demand slice, the recommended approach is:

```text
weekly demand_master.csv first
legacy S_month_data.csv compatibility second
```

This gives WOM a visible Japanese Rice demand entrance while preserving the original PySI logic as a compatibility path.
