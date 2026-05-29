# WOM Capacity Master Schema Consolidation

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_master_schema_consolidation.md`  
**Parent memo:** `docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md`  
**Related memo:** `docs/design/wom_scenario_package_control_model.md`

---

## 1. Purpose

This memo consolidates WOM capacity master schema discussions that already exist across multiple design documents and implementations.

The purpose is not to invent yet another capacity schema.

The purpose is to:

```text
collect existing capacity-related specs
    ↓
classify them into master schema / adapter / runtime context / diagnostic
    ↓
identify the near-term formal capacity master candidate
    ↓
define the mapping from PySI V0R8 capacity inputs to WOM canonical capacity rows
    ↓
prepare scenario-package-compatible capacity master design
```

This memo is a child document of:

```text
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

The parent memo defines the overall master data architecture.

This memo focuses only on capacity.

---

## 2. Key Design Position

Capacity is not a standalone feature.

Capacity is one part of the WOM master data architecture.

It connects:

```text
physical resource / operational capability
    ↓
product / node / scenario / week
    ↓
planning capacity context
    ↓
capacity-aware PSI planning
    ↓
blocked lots / utilization / shortage / issue detection
    ↓
Management Cockpit / diagnostic messages
```

Therefore, capacity schema must be designed across four layers:

```text
1. Master file layer
2. Canonical intermediate row layer
3. Runtime context layer
4. Diagnostic / applicability layer
```

---

## 3. Important Rule: Do Not Redefine from Zero

Existing WOM docs already contain capacity master and adapter definitions.

This memo consolidates them.

The current problem is not absence of design.

The current problem is fragmentation:

```text
capacity file layout exists in one memo
capacity normalization exists in another memo
monthly CSV adapter exists in another memo
explicit pipeline runtime shape exists elsewhere
diagnostic logic exists in a newer module
```

This memo creates the map.

---

## 4. Existing Capacity-Related Documents

The following documents should be treated as source material.

```text
docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md
docs/design/wom_capacity_input_granularity_adapter.md
docs/design/capacity_input_granularity_adapter_v0r1_completion.md
docs/design/capacity_provider_monthly_csv_adapter_v0r2.md
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_scenario_package_control_model.md
```

---

## 5. Role Classification of Existing Specs

### 5.1 Formal capacity master candidate

```text
docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md
```

Role:

```text
capacity_master.csv file layout candidate
capacity lookup contract
capacity usage / violation structure
hard / soft capacity policy
missing capacity policy
product wildcard fallback
duplicate record policy
```

This is the closest existing document to a formal capacity master CSV schema.

---

### 5.2 Canonical intermediate normalization

```text
docs/design/wom_capacity_input_granularity_adapter.md
docs/design/capacity_input_granularity_adapter_v0r1_completion.md
```

Role:

```text
monthly / weekly / case-specific capacity input normalization
MonthlyCapacityInputRow
WeeklyCapacityInputRow
WeeklyCapacityRow
weekly_capacity_rows_to_weekly_capability
```

This layer should be treated as canonical intermediate representation.

It is not the user-facing scenario package master schema by itself.

---

### 5.3 Legacy PySI V0R8 monthly capacity adapter

```text
docs/design/capacity_provider_monthly_csv_adapter_v0r2.md
```

Role:

```text
adapter from existing sku_P_month_data.csv
or product_name / node_name / year / m1...m12 style CSV
to canonical weekly capacity rows
```

This is a compatibility adapter.

It should remain valid while WOM migrates to scenario packages.

---

### 5.4 Explicit Pipeline runtime context

```text
docs/design/explicit_pipeline_forward_weekly_capacity_context.md
```

Role:

```text
runtime shape for explicit pipeline forward capacity context
```

Representative runtime shape:

```text
product -> node -> capacity_type -> week -> capacity_lots
```

This is a runtime context contract.

It is not the master file layout.

---

### 5.5 Shape / scenario alignment diagnostics

```text
docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md
```

Role:

```text
diagnose selected product mismatch
diagnose capacity node mismatch
diagnose week-domain mismatch
diagnose forward capacity shape mismatch
diagnose backward capability shape
surface messages in Explicit KPI View
```

Diagnostics should remain even after adapters are introduced.

Adapters should not silently hide mismatch.

---

## 6. Capacity Concepts

WOM capacity has several meanings that must not be collapsed.

### 6.1 Capability

Capability is the available ability of a node/resource to perform a planning action.

Examples:

```text
MOM node production capability
factory processing capability
warehouse shipping capability
inventory storage capability
```

### 6.2 Capacity

Capacity is the weekly or period-based quantity limit used by the planning engine.

Examples:

```text
weekly production lots
weekly shipment lots
maximum inventory lots
available machine hours
available labor hours
```

### 6.3 Consumption

Consumption defines how much capacity a lot consumes.

Examples:

```text
1 product lot consumes 1 production capacity lot
1 pallet consumes warehouse storage capacity
1 vehicle consumes one final assembly slot
```

### 6.4 Policy

Policy defines how capacity is interpreted.

Examples:

```text
hard cap
soft cap
flex with overtime
unlimited for demo
warning only
blocked lot
```

### 6.5 Runtime applicability

Applicability means whether the capacity context actually affects the current planning run.

Examples:

```text
capacity present but product mismatch
capacity present but node mismatch
capacity present but week-domain mismatch
capacity present but shape mismatch
capacity applied and blocking
capacity absent and treated as unlimited
```

---

## 7. Capacity Type Taxonomy

The near-term capacity type taxonomy should align with PSI buckets.

Recommended initial values:

```text
P = production / processing / purchase capability
S = shipment / sales / dispatch capability
I = inventory / storage capability
```

Optional future extensions:

```text
CO = on-order / purchase order / committed order handling capacity
TRANSPORT = transport lane capacity
LABOR = labor-hour capacity
MACHINE = machine-hour capacity
PALLET = pallet storage capacity
COLD = cold-chain capacity
```

Near-term rule:

```text
Keep P/S/I as the primary canonical capacity types.
Do not over-generalize before the P/S/I path is stable.
```

---

## 8. Formal Capacity Master Candidate

The near-term consolidated capacity master candidate should be:

```text
capacity_master.csv
```

Recommended header:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

This schema comes from existing with-capacity forward push planning design.

It is the closest existing file-layout-level specification.

---

## 9. capacity_master.csv Field Semantics

### 9.1 scenario_id

The scenario to which this capacity row applies.

Examples:

```text
Baseline
RICE_AS_IS
RICE_TO_BE
IPHONE_AS_IS
TESLA_AS_IS
```

### 9.2 tree_side

Which planning side this capacity belongs to.

Recommended values:

```text
IN
OUT
BOTH
```

Typical interpretation:

```text
IN:
    inbound / supply / MOM-side capacity

OUT:
    outbound / distribution / DAD-side capacity

BOTH:
    shared logical capacity or compatibility row
```

### 9.3 node_name

Planning node to which capacity applies.

Examples:

```text
MOMCAL
MILL_EAST
MOM_final_assy_ASIA
WH_TOKYO
DAD_RICE
```

### 9.4 product_name

Product to which capacity applies.

Examples:

```text
CAL_RICE_1
PACKAGED_RICE_STANDARD
IPHONE_NM_2028_BASE
```

Wildcard policy:

```text
*
```

may be allowed as product wildcard.

However, wildcard use should be diagnostic-visible.

### 9.5 week

Week or period key.

Supported domains:

```text
integer_index:
    0, 1, 2, ...

business_week_label:
    2027-W40, 2027-W41, ...

monthly_label:
    2027-01, 2027-02, ...
```

Near-term policy:

```text
Master data may use business-readable labels.
Engine boundary adapter may convert to integer index.
```

### 9.6 capacity_type

Recommended values:

```text
P
S
I
```

See capacity type taxonomy.

### 9.7 capacity_qty

Available capacity quantity.

Initial unit may be lot.

### 9.8 cap_mode

How the planning engine should interpret the capacity.

Recommended values:

```text
hard
soft
warning_only
unlimited
flex_with_penalty
```

### 9.9 unit

Unit of capacity.

Initial values:

```text
lot
```

Future values:

```text
kg
ton
case
pallet
machine_hour
labor_hour
line_hour
```

### 9.10 priority

Optional priority for allocation or conflict handling.

Examples:

```text
1
10
high
normal
low
```

### 9.11 calendar_id

Optional calendar reference.

Examples:

```text
JP_445
ISO_WEEK
FACTORY_ASIA_CAL
RICE_HARVEST_CAL
```

### 9.12 comment

Human-readable note.

---

## 10. Canonical Intermediate: WeeklyCapacityRow

The canonical intermediate row should remain:

```text
WeeklyCapacityRow
```

Recommended fields:

```text
scenario_id
product_id
capacity_owner_type
capacity_owner_id
week
capacity_type
capacity_qty
cap_mode
unit
source_granularity
source_id
comment
```

### 10.1 Purpose

`WeeklyCapacityRow` is not the same as the final scenario package file.

It is the normalized intermediate row.

It can be produced from:

```text
capacity_master.csv
sku_P_month_data.csv
weekly capacity input CSV
monthly capacity input CSV
scenario override
```

It can feed:

```text
env.weekly_capability
explicit pipeline forward capacity context
explicit pipeline backward capability context
capacity usage report
capacity diagnostic
```

---

## 11. Legacy Adapter: PySI V0R8 sku_P_month_data.csv

PySI V0R8-derived implementations historically use capacity-like input such as:

```text
sku_P_month_data.csv
```

or equivalent monthly capability input.

Representative shape:

```text
product_name,node_name,year,m1,m2,m3,...,m12
```

This should be preserved as a legacy input.

Mapping:

```text
sku_P_month_data.csv
    ↓
MonthlyCapacityInputRow
    ↓
WeeklyCapacityRow
    ↓
runtime capacity context
```

This adapter should remain supported because the existing WOM V0R1M0 / PySI V0R8 implementation is already working with CSV-based input assets.

---

## 12. Weekly / Monthly Granularity Policy

Capacity input may come in multiple granularities.

Supported source granularities:

```text
monthly
weekly
case_specific
runtime_precomputed
```

Canonical policy:

```text
All capacity input should normalize to weekly representation before planning.
```

Monthly to weekly conversion should be explicit.

Do not hide conversion assumptions.

Recommended metadata:

```text
source_granularity
source_id
calendar_id
conversion_method
```

Candidate conversion methods:

```text
even_spread
working_day_weighted
front_loaded
back_loaded
custom_calendar
```

---

## 13. Runtime Capacity Contexts

WOM currently has several runtime capacity destinations.

### 13.1 env.weekly_capability

Purpose:

```text
generic weekly capability runtime structure
```

Used by capacity-aware planning or older with-capacity flow.

### 13.2 env.explicit_pipeline_forward_weekly_capacity

Purpose:

```text
explicit pipeline forward capacity context
```

Representative shape:

```text
product -> node -> capacity_type -> week/index -> capacity_lots
```

### 13.3 env.explicit_pipeline_backward_weekly_capability

Purpose:

```text
explicit pipeline backward capability context
```

Representative shape may differ from forward capacity context.

The diagnostic layer should identify shape version explicitly.

### 13.4 Capacity usage / violation outputs

Potential runtime/reporting structures:

```text
CapacityUsage
CapacityViolation
capacity_usage.csv
capacity_violations.csv
```

---

## 14. Runtime Shape Contract

Runtime shape is not master schema.

This distinction is critical.

Example:

```text
capacity_master.csv:
    scenario_id,node_name,product_name,week,capacity_type,capacity_qty

runtime:
    product -> node -> capacity_type -> week -> capacity_lots
```

The adapter is responsible for converting master rows to runtime shape.

Diagnostics should confirm:

```text
producer shape
consumer expectation
shape version
shape alignment
```

---

## 15. Week Domain Contract

Capacity master may use:

```text
business week label:
    2027-W40

monthly label:
    2027-01

integer index:
    0
```

Planning engine may expect:

```text
integer week index
```

Therefore, the adapter must own week-domain conversion.

Recommended rule:

```text
Master and scenario package:
    business-readable labels preferred

Engine internal:
    integer index allowed

Adapter:
    explicit conversion and diagnostic reporting required
```

Do not silently convert without trace.

---

## 16. Product and Node Alignment Rules

Capacity is only meaningful if it aligns with the current scenario.

Required checks:

```text
selected product is present in capacity product set
capacity nodes match runtime planning tree nodes
capacity week keys match or convert to engine week domain
capacity type matches consumer expectation
capacity shape matches or is adapted
```

If not aligned, WOM should report:

```text
capacity present but not applied
```

or:

```text
capacity context mismatch
```

not merely:

```text
capacity exists
```

---

## 17. Capacity Applicability Status

WOM should eventually define explicit capacity applicability status.

Recommended values:

```text
absent_unlimited_fallback
present_aligned_applied
present_aligned_warning_only
present_misaligned_product
present_misaligned_node
present_misaligned_week_domain
present_misaligned_shape
present_but_not_consumed
applied_and_blocking
applied_no_bottleneck
adapter_failed
```

This status should be visible in:

```text
diagnostic payload
Explicit KPI View messages
Management Cockpit
scenario report
```

---

## 18. Capacity Diagnostic Continuity

The recently implemented capacity scenario alignment diagnostic should remain part of the architecture.

It currently detects categories such as:

```text
selected product mismatch
backward capability product mismatch
node mismatch
week-domain mismatch
forward capacity shape mismatch
```

This diagnostic should not be removed after adapter implementation.

Instead, it should evolve to say:

```text
capacity master loaded
week-domain adapter applied
runtime shape converted
capacity effectively applied
blocked lots observed
```

---

## 19. Scenario Package Capacity Structure

In the future scenario package, capacity may be represented in two levels.

### 19.1 Simple consolidated capacity file

```text
masters/capacity_master.csv
```

with fields:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

This is the recommended near-term V1-compatible path.

### 19.2 Decomposed capacity master set

For more robust modeling:

```text
masters/capacity_resource_master.csv
masters/capacity_calendar.csv
masters/product_capacity_consumption.csv
masters/capacity_policy.csv
masters/scenario_capacity_override.csv
```

This is the future extensible path.

---

## 20. Decomposed Capacity Master Set

### 20.1 capacity_resource_master.csv

Defines capacity resources.

Recommended fields:

```text
resource_id
node_name
capacity_type
resource_name
unit
base_capacity
active
comment
```

### 20.2 capacity_calendar.csv

Defines weekly availability.

Recommended fields:

```text
scenario_id
resource_id
week
available_capacity
unit
calendar_id
source
comment
```

### 20.3 product_capacity_consumption.csv

Defines capacity consumption per lot.

Recommended fields:

```text
product_name
node_name
capacity_type
resource_id
capacity_per_lot
unit
comment
```

### 20.4 capacity_policy.csv

Defines capacity interpretation.

Recommended fields:

```text
scenario_id
node_name
capacity_type
policy
severity
allocation_rule
comment
```

### 20.5 scenario_capacity_override.csv

Defines scenario-specific changes.

Recommended fields:

```text
scenario_id
resource_id
week
override_capacity
reason
comment
```

---

## 21. Consolidated vs Decomposed Policy

Recommended policy:

```text
Use consolidated capacity_master.csv for near-term implementation.
Design decomposed capacity master set as future extension.
```

Reason:

```text
capacity_master.csv is closer to existing design and easier to map to current runtime contexts.
decomposed capacity master set is better for long-term scenario management but larger in scope.
```

Migration path:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
runtime capacity context

future:
capacity_resource_master + capacity_calendar + product_capacity_consumption + capacity_policy
    ↓
WeeklyCapacityRow
    ↓
runtime capacity context
```

---

## 22. PySI V0R8 to WOM V1 Capacity Mapping

### 22.1 Current input

```text
sku_P_month_data.csv
```

### 22.2 Legacy adapter

```text
capacity_provider_monthly_csv_adapter
```

### 22.3 Canonical intermediate

```text
MonthlyCapacityInputRow
WeeklyCapacityRow
```

### 22.4 Runtime destinations

```text
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
```

### 22.5 Diagnostics

```text
capacity scenario alignment diagnostic
capacity applicability status
capacity usage / violation report
```

Full mapping:

```text
sku_P_month_data.csv
    ↓
MonthlyCapacityInputRow
    ↓
monthly_capacity_to_weekly_rows
    ↓
WeeklyCapacityRow
    ↓
weekly_capacity_rows_to_weekly_capability
    ↓
runtime capacity context
    ↓
capacity-aware planner
    ↓
capacity usage / blocked lots / diagnostics
```

---

## 23. Candidate Adapter Interfaces

### 23.1 legacy monthly CSV to canonical rows

```python
load_legacy_sku_p_month_capacity_csv(path) -> list[MonthlyCapacityInputRow]
```

### 23.2 monthly rows to weekly rows

```python
monthly_capacity_to_weekly_rows(rows, calendar) -> list[WeeklyCapacityRow]
```

### 23.3 capacity master CSV to weekly rows

```python
load_capacity_master_csv(path) -> list[WeeklyCapacityRow]
```

### 23.4 weekly rows to runtime context

```python
weekly_capacity_rows_to_weekly_capability(rows) -> dict
weekly_capacity_rows_to_explicit_forward_capacity(rows) -> dict
weekly_capacity_rows_to_explicit_backward_capability(rows) -> dict
```

### 23.5 runtime diagnostic

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

---

## 24. Testing Strategy

Capacity schema consolidation should be tested by layers.

### 24.1 Master CSV parsing tests

```text
capacity_master.csv parses required columns
missing required columns are detected
duplicate rows are handled deterministically
```

### 24.2 Legacy CSV adapter tests

```text
sku_P_month_data.csv maps to MonthlyCapacityInputRow
monthly rows map to weekly rows
conversion is deterministic
```

### 24.3 Runtime context tests

```text
WeeklyCapacityRow maps to env.weekly_capability
WeeklyCapacityRow maps to explicit forward capacity context
shape version is detected
```

### 24.4 Diagnostic tests

```text
product mismatch detected
node mismatch detected
week-domain mismatch detected
shape mismatch detected
aligned capacity reports present_aligned_applied
```

### 24.5 Regression tests

Existing explicit pipeline and capacity tests should remain valid.

---

## 25. Migration Roadmap

### Phase C1: Consolidation memo

This document.

### Phase C2: Inventory existing code and CSVs

Create Codex request:

```text
docs/codex_requests/wom_capacity_master_schema_inventory_request.md
```

Expected output:

```text
current capacity-related files
current loader functions
current dataclasses
current tests
current runtime destinations
gaps against this memo
```

### Phase C3: Formal capacity master loader

Implement or consolidate:

```text
capacity_master.csv -> WeeklyCapacityRow
```

### Phase C4: Legacy adapter preservation

Keep:

```text
sku_P_month_data.csv -> WeeklyCapacityRow
```

### Phase C5: Runtime context adapters

Implement or consolidate:

```text
WeeklyCapacityRow -> env.weekly_capability
WeeklyCapacityRow -> explicit_pipeline_forward_weekly_capacity
WeeklyCapacityRow -> explicit_pipeline_backward_weekly_capability
```

### Phase C6: Applicability diagnostic

Extend diagnostic to report:

```text
capacity applicability status
adapter applied
runtime shape converted
capacity actually consumed by planner
```

### Phase C7: Scenario package capacity support

Allow:

```text
scenario.yaml
    masters:
        capacity_master: masters/capacity_master.csv
```

---

## 26. Open Questions

### 26.1 Should capacity_master.csv use node_name or node_id?

Near-term:

```text
node_name
```

because existing PySI V0R8 assets use names.

Future:

```text
node_id
```

may be introduced with stable identity mapping.

### 26.2 Should product wildcard be allowed?

Yes, but with diagnostics.

Wildcard capacity should not silently mask product-specific gaps.

### 26.3 Should master weeks be labels or indexes?

Recommended:

```text
master data:
    business labels

engine:
    indexes

adapter:
    explicit conversion
```

### 26.4 Should inbound and outbound capacity share one schema?

Yes.

Use:

```text
tree_side
capacity_type
node_name
```

to distinguish meaning.

### 26.5 Should decomposed capacity master be implemented now?

No.

Near-term implementation should use consolidated `capacity_master.csv`.

Decomposed master set remains a future extension.

---

## 27. Acceptance Criteria

This consolidation is accepted when the team agrees that:

```text
1. capacity_master.csv is the near-term formal capacity master candidate.
2. WeeklyCapacityRow is the canonical intermediate representation.
3. sku_P_month_data.csv remains supported as PySI V0R8 legacy input.
4. explicit_pipeline_forward_weekly_capacity is runtime context, not master schema.
5. diagnostics remain mandatory even after adapters are implemented.
6. master week labels may differ from engine week indexes, but adapters must be explicit.
7. capacity applicability status should become a first-class diagnostic concept.
```

---

## 28. Recommended Next Document

Recommended next document:

```text
docs/codex_requests/wom_capacity_master_schema_inventory_request.md
```

Purpose:

```text
Ask Codex to inspect the repository and list all current capacity-related files,
functions, dataclasses, tests, and runtime destinations.
```

This should be done before implementation changes.

The next implementation should not start by writing new capacity logic.

It should start by inventorying what already exists.

---

## 29. Summary

WOM already has many capacity design fragments.

The next step is not invention.

The next step is consolidation.

The near-term formal capacity master candidate is:

```text
capacity_master.csv
```

with fields:

```text
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

The canonical intermediate representation is:

```text
WeeklyCapacityRow
```

The legacy input path remains:

```text
sku_P_month_data.csv
```

The runtime contexts include:

```text
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
```

The diagnostic layer must remain:

```text
capacity scenario alignment diagnostic
capacity applicability status
capacity usage / violation reporting
```

In short:

```text
Do not dig another capacity well.
Connect the wells already dug into one water system.
```
