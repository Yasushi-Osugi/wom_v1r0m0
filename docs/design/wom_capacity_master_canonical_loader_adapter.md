# WOM Capacity Master Canonical Loader Adapter

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_master_canonical_loader_adapter.md`

**Parent design docs:**

```text
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_capacity_master_schema_inventory.md
```

---

## 1. Purpose

This memo defines the design direction for a canonical capacity loader / adapter layer in WOM.

The purpose is to consolidate the existing capacity input paths into one canonical row flow.

The target flow is:

```text
capacity_master.csv
legacy sku_P_month_data.csv
other weekly/monthly capacity inputs
    ↓
canonical WeeklyCapacityRow list
    ↓
runtime capacity adapters
    ↓
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
    ↓
diagnostics
    ↓
capacity-aware planning / cockpit / reports
```

This memo is not an implementation request yet.

It defines the shape of the implementation that should follow the capacity schema inventory.

---

## 2. Background

The capacity inventory confirmed that WOM already has several capacity-related implementation and design assets.

Important existing implementation areas include:

```text
pysi/capacity/capacity_master_loader.py
pysi/planning/capacity_master.py
pysi/adapters/capacity_input_granularity.py
pysi/plugins/capacity_provider_monthly_csv/plugin.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Important existing design concepts include:

```text
capacity_master.csv
WeeklyCapacityRow
sku_P_month_data.csv legacy adapter
env.weekly_capability
explicit forward weekly capacity context
explicit backward weekly capability context
capacity scenario alignment diagnostic
capacity applicability status
```

The next step is to connect these assets through one canonical adapter architecture.

---

## 3. Core Design Principle

The core principle is:

```text
There should be one canonical capacity row representation.
All capacity input paths should normalize into it.
All runtime capacity contexts should be derived from it.
```

In this memo, that canonical representation is:

```text
WeeklyCapacityRow
```

This does not mean all user-facing master files must look like `WeeklyCapacityRow`.

It means all capacity inputs should pass through `WeeklyCapacityRow` before becoming runtime context.

---

## 4. Non-Goals

This memo does not propose:

```text
planner behavior changes
capacity enforcement changes
week-key normalization behavior changes inside the planner
forward capacity shape conversion inside the planner
GUI redesign
CSV sample data changes
new optimization logic
deletion of legacy PySI V0R8 loaders
```

The adapter should be additive and compatibility-preserving.

---

## 5. Layered Architecture

Capacity should be handled in the following layers.

```text
1. Source input layer
2. Canonical row layer
3. Validation / diagnostic layer
4. Runtime context adapter layer
5. Planner consumer layer
6. Reporting / cockpit layer
```

### 5.1 Source input layer

Examples:

```text
capacity_master.csv
sku_P_month_data.csv
weekly capacity CSV
monthly capacity CSV
scenario override CSV
```

### 5.2 Canonical row layer

```text
WeeklyCapacityRow
```

### 5.3 Validation / diagnostic layer

Examples:

```text
required column validation
week-domain classification
product / node alignment
shape version inference
capacity applicability status
```

### 5.4 Runtime context adapter layer

Examples:

```text
WeeklyCapacityRow -> env.weekly_capability
WeeklyCapacityRow -> env.explicit_pipeline_forward_weekly_capacity
WeeklyCapacityRow -> env.explicit_pipeline_backward_weekly_capability
```

### 5.5 Planner consumer layer

Examples:

```text
weekly_forward_push_with_capacity
capacity_aware_inbound_backward
explicit_bridge_capacity_pipeline
```

### 5.6 Reporting / cockpit layer

Examples:

```text
capacity usage report
capacity violation report
Explicit KPI messages
Management Cockpit diagnostics
```

---

## 6. Canonical Row: WeeklyCapacityRow

The canonical row should represent one scenario / product / node / week / capacity type quantity.

Recommended fields:

```text
scenario_id
product_id
capacity_owner_type
capacity_owner_id
tree_side
week
capacity_type
capacity_qty
cap_mode
unit
priority
calendar_id
source_granularity
source_id
source_file
comment
```

### 6.1 scenario_id

Scenario identity.

Examples:

```text
Baseline
RICE_AS_IS
IPHONE_AS_IS
TESLA_AS_IS
```

### 6.2 product_id

Product identity.

This may map from legacy `product_name`.

Wildcard is allowed but diagnostic-visible:

```text
*
```

### 6.3 capacity_owner_type

Recommended values:

```text
node
resource
lane
buffer
```

Near-term default:

```text
node
```

### 6.4 capacity_owner_id

The node or resource to which capacity applies.

Near-term mapping:

```text
node_name -> capacity_owner_id
```

### 6.5 tree_side

Recommended values:

```text
IN
OUT
BOTH
UNKNOWN
```

### 6.6 week

Canonical week key.

This may be:

```text
business week label
integer week index
monthly label before normalization
```

However, before planner consumption, week-domain mapping must be explicit.

### 6.7 capacity_type

Initial values:

```text
P
S
I
```

Future values:

```text
TRANSPORT
LABOR
MACHINE
PALLET
COLD
```

### 6.8 capacity_qty

Capacity quantity.

### 6.9 cap_mode

Recommended values:

```text
hard
soft
warning_only
unlimited
flex_with_penalty
```

### 6.10 unit

Initial value:

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

### 6.11 source_granularity

Recommended values:

```text
weekly
monthly
runtime
scenario_override
legacy_monthly
```

### 6.12 source_id / source_file

Traceability fields.

These are important for diagnostics and future cockpit explanation.

---

## 7. Source Input 1: capacity_master.csv

The near-term formal capacity master candidate is:

```text
capacity_master.csv
```

Recommended header:

```csv
scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment
```

### 7.1 Mapping to WeeklyCapacityRow

| capacity_master.csv | WeeklyCapacityRow |
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

Additional canonical fields:

```text
capacity_owner_type = "node"
source_granularity = "weekly" or inferred
source_file = path
source_id = deterministic row id
```

### 7.2 Loader target

Recommended function:

```python
load_capacity_master_csv(path: str | Path) -> list[WeeklyCapacityRow]
```

### 7.3 Validation

Required columns:

```text
scenario_id
tree_side
node_name
product_name
week
capacity_type
capacity_qty
cap_mode
unit
```

Optional columns:

```text
priority
calendar_id
comment
```

---

## 8. Source Input 2: Legacy sku_P_month_data.csv

PySI V0R8-derived implementations already use monthly production / capability style input.

Representative legacy shape:

```csv
product_name,node_name,year,m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12
```

This should remain supported.

### 8.1 Mapping flow

```text
sku_P_month_data.csv
    ↓
MonthlyCapacityInputRow
    ↓
monthly_capacity_to_weekly_rows
    ↓
WeeklyCapacityRow
```

### 8.2 Loader target

Recommended function:

```python
load_legacy_sku_p_month_capacity_csv(path: str | Path) -> list[MonthlyCapacityInputRow]
```

### 8.3 Conversion target

Recommended function:

```python
legacy_monthly_capacity_csv_to_weekly_rows(
    path: str | Path,
    *,
    scenario_id: str,
    calendar: object | None = None,
    tree_side: str = "IN",
    capacity_type: str = "P",
    cap_mode: str = "hard",
    unit: str = "lot",
) -> list[WeeklyCapacityRow]
```

### 8.4 Policy

Legacy monthly capacity remains a compatibility input.

It should not be treated as inferior or obsolete.

It should be treated as:

```text
PySI V0R8 proven input spine
```

---

## 9. Source Input 3: Scenario Capacity Override

Future scenario packages may add:

```text
scenario_capacity_override.csv
```

Conceptual fields:

```csv
scenario_id,resource_id,node_name,product_name,week,override_capacity,reason,comment
```

This should not be implemented in the first adapter step unless already present.

But the canonical row should be able to represent override results through:

```text
source_granularity = scenario_override
source_id = override id
```

---

## 10. Week Domain Adapter

Capacity input may use different week domains.

Observed / expected domains:

```text
integer_index:
    0, 1, 2

business_week_label:
    2027-W40

monthly_label:
    2027-01, 2027-02
```

The adapter must not hide week conversion.

Recommended functions:

```python
classify_week_key_domain(week_key: object) -> str
map_capacity_week_to_engine_index(week_key: object, calendar: object) -> int
map_engine_index_to_business_week(index: int, calendar: object) -> str
```

Near-term policy:

```text
Capacity master and scenario package may use business-readable labels.
Runtime engine may use integer week indexes.
Conversion should happen at adapter boundary, not inside planner core.
```

Diagnostics should report:

```text
source_week_domain
target_week_domain
conversion_applied
conversion_failed
```

---

## 11. Runtime Adapter 1: env.weekly_capability

`env.weekly_capability` is a generic weekly capability runtime structure.

Recommended adapter:

```python
weekly_capacity_rows_to_weekly_capability(
    rows: list[WeeklyCapacityRow],
    *,
    week_domain: str = "engine_index",
    calendar: object | None = None,
) -> dict
```

Possible shape:

```text
node -> product -> week -> capacity_qty
```

or current existing implementation shape if already established.

The adapter should preserve current expected shape unless deliberately changed in a later implementation request.

---

## 12. Runtime Adapter 2: explicit forward weekly capacity

`env.explicit_pipeline_forward_weekly_capacity` is used by the Explicit Pipeline forward capacity context.

Recommended adapter:

```python
weekly_capacity_rows_to_explicit_forward_capacity(
    rows: list[WeeklyCapacityRow],
    *,
    week_domain: str = "engine_index",
    calendar: object | None = None,
) -> dict
```

Target runtime shape should be explicit.

Current known / recommended shape:

```text
product -> node -> capacity_type -> week -> capacity_lots
```

If consumer expects list-indexed capacity, the adapter should produce or convert to that shape explicitly.

Do not leave conversion implicit.

---

## 13. Runtime Adapter 3: explicit backward weekly capability

`env.explicit_pipeline_backward_weekly_capability` is used by the Explicit Pipeline backward capability context.

Recommended adapter:

```python
weekly_capacity_rows_to_explicit_backward_capability(
    rows: list[WeeklyCapacityRow],
    *,
    week_domain: str = "engine_index",
    calendar: object | None = None,
) -> dict
```

The exact target shape should be based on current consumer expectation.

The adapter should declare:

```text
shape_version
week_domain
product_domain
node_domain
```

either in returned metadata or diagnostic payload.

---

## 14. Unified Loader API

Recommended top-level API:

```python
load_capacity_rows_from_source(
    source_path: str | Path,
    *,
    source_kind: str,
    scenario_id: str | None = None,
    calendar: object | None = None,
    defaults: dict | None = None,
) -> list[WeeklyCapacityRow]
```

Supported source_kind values:

```text
capacity_master_csv
legacy_sku_p_month_csv
weekly_capacity_csv
monthly_capacity_csv
```

Recommended dispatcher behavior:

```text
capacity_master_csv
    -> load_capacity_master_csv

legacy_sku_p_month_csv
    -> legacy_monthly_capacity_csv_to_weekly_rows

weekly_capacity_csv
    -> weekly input row loader

monthly_capacity_csv
    -> monthly input row loader + conversion
```

---

## 15. Unified Runtime Attachment API

Recommended top-level API:

```python
attach_capacity_contexts_to_env_from_weekly_rows(
    env,
    rows: list[WeeklyCapacityRow],
    *,
    selected_product: str | None = None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    calendar: object | None = None,
    attach_weekly_capability: bool = True,
    attach_explicit_forward: bool = True,
    attach_explicit_backward: bool = True,
    attach_diagnostic: bool = True,
) -> dict
```

Expected behavior:

```text
1. Build env.weekly_capability if requested.
2. Build env.explicit_pipeline_forward_weekly_capacity if requested.
3. Build env.explicit_pipeline_backward_weekly_capability if requested.
4. Run capacity scenario alignment diagnostic if requested.
5. Attach diagnostic result to env.
6. Return attachment summary.
```

This function should be the primary bridge from canonical capacity rows to runtime context.

---

## 16. Attachment Summary

The unified attachment API should return a summary dictionary.

Recommended keys:

```text
available
row_count
source_kinds
scenario_ids
product_count
node_count
week_domain
runtime_contexts_attached
diagnostic_available
messages
```

Example:

```python
{
    "available": True,
    "row_count": 52,
    "source_kinds": ["capacity_master_csv"],
    "scenario_ids": ["RICE_AS_IS"],
    "product_count": 1,
    "node_count": 1,
    "week_domain": "business_week_label",
    "runtime_contexts_attached": [
        "weekly_capability",
        "explicit_pipeline_forward_weekly_capacity",
        "explicit_pipeline_backward_weekly_capability",
    ],
    "diagnostic_available": True,
    "messages": [],
}
```

---

## 17. Capacity Applicability Status

The adapter should prepare for first-class applicability status.

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

This may initially be reported only in diagnostics.

It does not need to change planner behavior in the first implementation.

---

## 18. Diagnostics Integration

After runtime contexts are attached, run:

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

or a future generalized diagnostic.

The diagnostic should inspect:

```text
selected product
capacity product set
runtime node set
capacity node set
week-domain alignment
runtime shape version
consumer expectation
```

The adapter should not suppress diagnostic messages.

The adapter should help the diagnostic become more precise by attaching metadata:

```text
source_kind
source_file
week_domain
shape_version
conversion_applied
row_count
```

---

## 19. Metadata Contract

Runtime capacity contexts should carry or be accompanied by metadata.

Recommended env attributes:

```text
env.capacity_weekly_rows
env.capacity_source_summary
env.capacity_runtime_attachment_summary
env.explicit_pipeline_capacity_scenario_alignment_diagnostic
```

Optional:

```text
env.capacity_shape_metadata
env.capacity_week_domain_metadata
env.capacity_applicability_status
```

Near-term implementation should avoid too many new env attributes unless needed.

But the attachment summary should be returned and optionally attached.

---

## 20. Error Handling

Adapter behavior should be deterministic.

### 20.1 Missing file

Return or raise a clear error depending on caller policy.

Recommended for loader:

```text
raise FileNotFoundError
```

Recommended for high-level env attach:

```text
attach unavailable diagnostic and return summary
```

### 20.2 Missing columns

Raise:

```text
ValueError
```

with missing column list.

### 20.3 Invalid numeric capacity

Raise:

```text
ValueError
```

or record invalid rows if tolerant mode is enabled.

### 20.4 Unknown week domain

Do not silently coerce.

Report:

```text
week_domain = unknown
conversion_failed
```

### 20.5 Duplicate rows

Recommended near-term policy:

```text
same scenario/product/node/week/capacity_type:
    aggregate capacity_qty by sum
```

Alternative policies may be implemented later:

```text
last_wins
error
priority_based
```

Aggregation should be diagnostic-visible.

---

## 21. Backward Compatibility

The existing command path should remain valid:

```bat
python main.py --backend mvp --skip-orchestrate --csv data --scenario Baseline --ui cockpit
```

Existing PySI V0R8 CSV assets should remain usable.

The canonical adapter should be introduced without breaking current startup.

Legacy path:

```text
sku_P_month_data.csv
    ↓
legacy adapter
    ↓
WeeklyCapacityRow
    ↓
runtime contexts
```

New path:

```text
capacity_master.csv
    ↓
capacity master loader
    ↓
WeeklyCapacityRow
    ↓
runtime contexts
```

Both paths converge at:

```text
WeeklyCapacityRow
```

---

## 22. Scenario Package Integration

Future scenario package:

```yaml
scenario:
  scenario_id: RICE_AS_IS
  case_id: japanese_rice

masters:
  capacity_master: masters/capacity_master.csv

legacy:
  pysi_v0r8_csv_dir: data/
```

The scenario loader should be able to choose:

```text
canonical capacity_master.csv
```

or:

```text
legacy sku_P_month_data.csv from pysi_v0r8_csv_dir
```

Near-term rule:

```text
If capacity_master.csv is present, prefer it.
If not present, fall back to legacy sku_P_month_data.csv if configured.
```

Fallback should be diagnostic-visible.

---

## 23. Testing Strategy

### 23.1 Unit tests: capacity_master.csv loader

Test cases:

```text
loads required columns
rejects missing required columns
maps node_name to capacity_owner_id
maps product_name to product_id
preserves cap_mode
handles optional priority/calendar/comment
```

### 23.2 Unit tests: legacy sku_P_month_data.csv adapter

Test cases:

```text
loads product_name/node_name/year/m1...m12
converts monthly values to WeeklyCapacityRow
preserves scenario_id default
uses IN / P / hard / lot defaults
```

### 23.3 Unit tests: runtime adapters

Test cases:

```text
WeeklyCapacityRow -> env.weekly_capability
WeeklyCapacityRow -> explicit forward capacity
WeeklyCapacityRow -> explicit backward capability
week-domain metadata is present
shape is deterministic
```

### 23.4 Unit tests: diagnostics

Test cases:

```text
aligned capacity reports no mismatch messages
product mismatch remains visible
node mismatch remains visible
week-domain conversion is reported
shape conversion is reported
```

### 23.5 Regression tests

Run existing tests around:

```text
capacity input granularity
explicit pipeline forward capacity context
capacity scenario alignment diagnostic
with-capacity forward push planner
management cockpit KPI messages
```

---

## 24. Suggested Implementation Files

Potential implementation locations:

```text
pysi/capacity/canonical_capacity_loader.py
pysi/capacity/capacity_master_loader.py
pysi/adapters/capacity_input_granularity.py
pysi/plan/explicit_pipeline_capacity_context.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Preferred direction:

```text
Reuse existing modules where possible.
Avoid creating parallel duplicate loaders.
```

If `pysi/capacity/capacity_master_loader.py` already exists, extend or consolidate it rather than adding another equivalent loader.

---

## 25. Suggested Public Functions

```python
load_capacity_master_csv(path) -> list[WeeklyCapacityRow]

legacy_sku_p_month_capacity_csv_to_weekly_rows(
    path,
    *,
    scenario_id,
    calendar=None,
    defaults=None,
) -> list[WeeklyCapacityRow]

weekly_capacity_rows_to_weekly_capability(rows, *, calendar=None) -> dict

weekly_capacity_rows_to_explicit_forward_capacity(rows, *, calendar=None) -> dict

weekly_capacity_rows_to_explicit_backward_capability(rows, *, calendar=None) -> dict

attach_capacity_contexts_to_env_from_weekly_rows(
    env,
    rows,
    *,
    selected_product=None,
    outbound_root=None,
    inbound_root=None,
    calendar=None,
) -> dict
```

---

## 26. Implementation Order

Recommended safe implementation order:

```text
1. Add or consolidate load_capacity_master_csv -> WeeklyCapacityRow.
2. Add focused tests for capacity_master.csv parsing.
3. Add adapter WeeklyCapacityRow -> explicit forward capacity context.
4. Add adapter WeeklyCapacityRow -> explicit backward capability context.
5. Add adapter WeeklyCapacityRow -> env.weekly_capability if not already stable.
6. Add unified env attachment helper.
7. Add diagnostics metadata and applicability status.
8. Add scenario package integration later.
```

Do not implement all phases at once.

---

## 27. Safety Boundaries for Next Codex Request

The next Codex implementation request should not change:

```text
planner capacity enforcement behavior
weekly_forward_push_with_capacity semantics
capacity_aware_inbound_backward semantics
sample CSV data
GUI layout
cost / money evaluation
scenario selection
```

It should focus on:

```text
loader / adapter
canonical rows
runtime context conversion
tests
```

---

## 28. Acceptance Criteria for Future Implementation

A first implementation phase is complete when:

```text
capacity_master.csv can be parsed into WeeklyCapacityRow
legacy sku_P_month_data.csv path remains supported
WeeklyCapacityRow can produce explicit forward capacity runtime context
tests pass
no planning behavior changes occur
diagnostic visibility is preserved
```

A later phase is complete when:

```text
WeeklyCapacityRow can produce all required runtime contexts
capacity applicability status is reported
scenario package can reference capacity_master.csv
Japanese Rice Case capacity can be loaded through the canonical path
```

---

## 29. Summary

The canonical capacity adapter should make this true:

```text
Many capacity inputs.
One canonical row.
Many runtime destinations.
One diagnostic story.
```

Near-term:

```text
capacity_master.csv
sku_P_month_data.csv
    ↓
WeeklyCapacityRow
    ↓
explicit forward/backward capacity context
    ↓
diagnostic
```

Long-term:

```text
scenario package capacity master
    ↓
canonical capacity rows
    ↓
all WOM planning/runtime/reporting contexts
```

In short:

```text
Capacity should stop being a set of parallel tunnels.
It should become one railway junction.
