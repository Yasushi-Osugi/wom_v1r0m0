# WOM Capacity Weekly Rows Runtime Context Adapter

**Version:** v0r1 draft  
**Date:** 2026-05-29  
**Status:** Design memo  
**Target path:** `docs/design/wom_capacity_weekly_rows_runtime_context_adapter.md`

**Parent design docs:**

```text
docs/design/wom_capacity_master_canonical_loader_adapter.md
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
docs/design/wom_capacity_master_schema_inventory.md
docs/design/wom_capacity_master_schema_consolidation.md
docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md
```

---

## 1. Purpose

This memo defines the next adapter layer after the canonical capacity master loader.

The completed previous phase established:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(...)
    ↓
WeeklyCapacityRow
```

This memo defines how `WeeklyCapacityRow` should be converted into WOM runtime capacity contexts:

```text
WeeklyCapacityRow
    ↓
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
    ↓
capacity diagnostics
    ↓
planner / cockpit / reports
```

This is a design memo only.

It does not request implementation yet.

---

## 2. Core Design Principle

The core principle is:

```text
Canonical capacity rows are the source of truth.
Runtime capacity contexts are derived views.
```

Therefore:

```text
Do not create separate capacity truth sources.
Do not let env.weekly_capability and explicit_pipeline_* capacity contexts diverge silently.
Do not hide shape conversion inside planner code.
Do not remove diagnostics after conversion.
```

The adapter should make capacity context generation explicit, testable, and diagnosable.

---

## 3. Current Completed State

The current completed state is:

```text
capacity_master.csv
    ↓
load_capacity_master_csv(path)
    ↓
list[WeeklyCapacityRow]
```

Implemented in:

```text
pysi/capacity/capacity_master_loader.py
```

Using the existing canonical row class:

```text
pysi.adapters.capacity_input_granularity.WeeklyCapacityRow
```

Confirmed commit:

```text
31d6d8e Add canonical capacity master loader
```

Completion memo:

```text
docs/design/wom_capacity_master_canonical_loader_adapter_completion.md
```

---

## 4. Problem to Solve

WOM currently has multiple runtime capacity contexts.

Examples:

```text
env.weekly_capability
env.explicit_pipeline_forward_weekly_capacity
env.explicit_pipeline_backward_weekly_capability
```

These contexts may have different shapes, week-domain assumptions, and consumer expectations.

The next architecture step is to make the conversion explicit:

```text
WeeklyCapacityRow
    ↓
runtime context adapters
    ↓
diagnostic metadata
```

The adapter should answer:

```text
Which rows were used?
Which products were present?
Which nodes were present?
Which week domain was used?
Which runtime contexts were attached?
Which shape version was produced?
Was the capacity context applicable to the selected scenario?
```

---

## 5. Non-Goals

This memo does not propose:

```text
changing planner capacity enforcement
changing blocked lot behavior
changing weekly_forward_push_with_capacity semantics
changing capacity_aware_inbound_backward semantics
changing explicit_bridge_capacity_pipeline behavior
changing GUI layout
changing sample CSV data
changing scenario selection
implementing scenario package loader
implementing optimization logic
```

This memo is about runtime context adapter design.

---

## 6. Runtime Context Targets

The adapter should support three runtime destinations.

```text
1. env.weekly_capability
2. env.explicit_pipeline_forward_weekly_capacity
3. env.explicit_pipeline_backward_weekly_capability
```

Each destination should be treated as a derived view from `WeeklyCapacityRow`.

---

## 7. Input: WeeklyCapacityRow

The adapter input is:

```python
list[WeeklyCapacityRow]
```

Expected fields include:

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

Not every field must be consumed by every runtime context.

But all fields should remain available for diagnostics and metadata.

---

## 8. Runtime Target 1: env.weekly_capability

### 8.1 Purpose

`env.weekly_capability` is the generic weekly capability context.

It should represent capacity in a planner-consumable structure.

### 8.2 Adapter function

Recommended public function:

```python
weekly_capacity_rows_to_weekly_capability(
    rows: list[WeeklyCapacityRow],
    *,
    selected_scenario: str | None = None,
    selected_product: str | None = None,
    week_domain: str = "preserve",
    calendar: object | None = None,
) -> dict
```

### 8.3 Near-term shape policy

The adapter should preserve the current expected shape of `env.weekly_capability` if already established.

If the current implementation expects a specific shape, do not redesign it in the first implementation.

Instead, document the produced shape with metadata.

### 8.4 Recommended metadata

Attach or return:

```text
shape_name = weekly_capability_v0
week_domain
row_count
scenario_ids
product_ids
node_ids
capacity_types
```

---

## 9. Runtime Target 2: env.explicit_pipeline_forward_weekly_capacity

### 9.1 Purpose

`env.explicit_pipeline_forward_weekly_capacity` is the forward capacity runtime context used by the Explicit Pipeline path.

### 9.2 Adapter function

Recommended public function:

```python
weekly_capacity_rows_to_explicit_forward_capacity(
    rows: list[WeeklyCapacityRow],
    *,
    selected_scenario: str | None = None,
    selected_product: str | None = None,
    week_domain: str = "preserve",
    calendar: object | None = None,
) -> dict
```

### 9.3 Recommended target shape

The design target is:

```text
product_id
  -> node_id
    -> capacity_type
      -> week
        -> capacity_qty
```

Example:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5,
                "2027-W41": 6,
            }
        }
    }
}
```

### 9.4 Important distinction

This runtime shape is not the master schema.

Master schema:

```text
capacity_master.csv
```

Canonical row:

```text
WeeklyCapacityRow
```

Runtime shape:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

These are three different layers.

---

## 10. Runtime Target 3: env.explicit_pipeline_backward_weekly_capability

### 10.1 Purpose

`env.explicit_pipeline_backward_weekly_capability` is the backward capability runtime context used by the Explicit Pipeline path.

### 10.2 Adapter function

Recommended public function:

```python
weekly_capacity_rows_to_explicit_backward_capability(
    rows: list[WeeklyCapacityRow],
    *,
    selected_scenario: str | None = None,
    selected_product: str | None = None,
    week_domain: str = "preserve",
    calendar: object | None = None,
) -> dict
```

### 10.3 Recommended target shape

The exact consumer expectation should be verified against the current repository implementation.

Near-term policy:

```text
Use the existing backward capability consumer shape.
Do not redesign it without a separate request.
```

The adapter should expose metadata:

```text
shape_name
shape_version
week_domain
product_domain
node_domain
```

---

## 11. Filtering Policy

The adapter may support optional filters:

```text
selected_scenario
selected_product
tree_side
capacity_type
```

Recommended default:

```text
Do not filter unless explicitly requested.
```

Reason:

```text
Canonical rows may support multiple products and scenarios.
Diagnostics need to see when selected product/scenario mismatch exists.
```

Near-term implementation should allow selected filters, but not silently discard rows without metadata.

If rows are filtered, the attachment summary should report:

```text
input_row_count
filtered_row_count
filter_conditions
filtered_out_scenarios
filtered_out_products
```

---

## 12. Tree Side Policy

`WeeklyCapacityRow.tree_side` may be:

```text
IN
OUT
BOTH
UNKNOWN
```

or legacy values such as:

```text
INBOUND
OUTBOUND
```

Recommended normalization for metadata:

```text
INBOUND -> IN
OUTBOUND -> OUT
IN -> IN
OUT -> OUT
BOTH -> BOTH
blank -> UNKNOWN
```

However, do not rewrite the original row unless explicitly needed.

Use normalized tree side only inside adapter logic and metadata.

---

## 13. Week Domain Policy

Week values may be:

```text
2027-W40
0
1
2027-01
```

The previous phase intentionally preserved week keys.

This phase should also avoid silent normalization.

Recommended `week_domain` modes:

```text
preserve
engine_index
business_week_label
```

### 13.1 preserve

Use the row's week value as-is.

### 13.2 engine_index

Convert to integer week index using a supplied calendar.

If conversion is unavailable, report diagnostic metadata and fail safely.

### 13.3 business_week_label

Convert to business week label using a supplied calendar.

If conversion is unavailable, report diagnostic metadata and fail safely.

### 13.4 Near-term recommendation

First implementation should use:

```text
week_domain = preserve
```

Do not implement full calendar conversion in the first runtime adapter request.

---

## 14. Duplicate Row Policy

Duplicate key candidate:

```text
scenario_id
product_id
capacity_owner_id
week
capacity_type
tree_side
```

Recommended near-term behavior:

```text
aggregate capacity_qty by sum
```

Alternative:

```text
preserve duplicates as list
```

However, for runtime context dictionaries, aggregation is often necessary.

If aggregation is implemented, it must be metadata-visible:

```text
duplicate_rows_detected
duplicate_group_count
aggregation_method = sum
```

If aggregation is deferred, duplicate rows should raise or be reported.

Recommendation for first implementation:

```text
sum duplicates deterministically
```

because runtime dict shapes cannot represent duplicate scalar capacity values cleanly.

---

## 15. Cap Mode Policy

`cap_mode` values may include:

```text
hard
soft
warning_only
unlimited
flex_with_penalty
```

Runtime contexts that currently accept only capacity quantity should not lose `cap_mode` permanently.

Options:

```text
1. simple quantity-only runtime dict
2. quantity + metadata sidecar
3. richer runtime object
```

Near-term recommendation:

```text
Keep runtime capacity qty shape unchanged.
Store cap_mode in metadata or attachment summary when possible.
```

Do not force planner changes in this phase.

---

## 16. Metadata Sidecar

The adapter should return not only runtime context but also metadata.

Recommended structure:

```python
{
    "context": {...},
    "metadata": {
        "shape_name": "...",
        "shape_version": "...",
        "week_domain": "...",
        "row_count": 0,
        "scenario_ids": [],
        "product_ids": [],
        "node_ids": [],
        "capacity_types": [],
        "duplicate_rows_detected": False,
        "aggregation_method": "sum",
        "messages": [],
    },
}
```

If existing code expects a plain dict, the adapter can expose two functions:

```python
weekly_capacity_rows_to_explicit_forward_capacity(rows) -> dict

build_explicit_forward_capacity_context_from_weekly_rows(rows) -> CapacityContextBuildResult
```

where `CapacityContextBuildResult` contains context + metadata.

---

## 17. Recommended Dataclass: CapacityRuntimeContextBuildResult

A small dataclass may help:

```python
@dataclass(frozen=True)
class CapacityRuntimeContextBuildResult:
    context: dict
    metadata: dict
    messages: list[str]
```

This is optional.

If adding a dataclass increases risk, return a simple dictionary.

---

## 18. Env Attachment Helper

After the individual adapters are stable, introduce a helper:

```python
attach_capacity_runtime_contexts_to_env_from_weekly_rows(
    env,
    rows: list[WeeklyCapacityRow],
    *,
    selected_product: str | None = None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    attach_weekly_capability: bool = True,
    attach_explicit_forward: bool = True,
    attach_explicit_backward: bool = True,
    attach_diagnostic: bool = True,
) -> dict
```

This should:

```text
build requested runtime contexts
attach them to env
attach metadata summary
run diagnostic if requested
return attachment summary
```

This helper is a later phase.

Do not combine it with the first runtime adapter implementation unless intentionally scoped.

---

## 19. Diagnostics Integration

The runtime adapter should support existing diagnostic functions.

Current diagnostic direction:

```text
explicit_pipeline_capacity_scenario_alignment_diagnostic
```

The adapter should make diagnostics more precise by providing metadata:

```text
source_row_count
runtime_shape_name
runtime_shape_version
week_domain
scenario_ids
product_ids
node_ids
capacity_types
adapter_messages
```

Diagnostics should answer:

```text
capacity rows loaded?
runtime context built?
selected product present?
runtime tree nodes matched?
week-domain matched?
shape matched?
capacity applicable?
```

---

## 20. Capacity Applicability Status

Future adapter output should support:

```text
capacity_applicability_status
```

Candidate values:

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

Near-term implementation may only prepare metadata, not full status logic.

---

## 21. Recommended Implementation Phases

### Phase R1: WeeklyCapacityRow -> explicit forward capacity context

Implement:

```python
weekly_capacity_rows_to_explicit_forward_capacity(rows) -> dict
```

with focused tests.

No env attachment.

No planner behavior change.

### Phase R2: WeeklyCapacityRow -> explicit backward capability context

Implement:

```python
weekly_capacity_rows_to_explicit_backward_capability(rows) -> dict
```

with focused tests.

No env attachment.

No planner behavior change.

### Phase R3: WeeklyCapacityRow -> env.weekly_capability

Implement or consolidate:

```python
weekly_capacity_rows_to_weekly_capability(rows) -> dict
```

only after verifying current consumer shape.

### Phase R4: Env attachment helper

Attach contexts to env in one controlled helper.

### Phase R5: Diagnostic metadata integration

Extend diagnostic to read adapter metadata and report applicability status.

### Phase R6: Scenario package capacity integration

Allow scenario yaml to load capacity rows and attach runtime contexts.

---

## 22. Recommended First Codex Request After This Memo

Recommended first implementation request:

```text
docs/codex_requests/wom_capacity_weekly_rows_to_explicit_forward_context_request.md
```

Scope:

```text
WeeklyCapacityRow -> explicit forward capacity context
focused tests
no env attach
no planner changes
no GUI changes
no data CSV changes
```

This is the safest next implementation step.

Reason:

```text
The Explicit Pipeline forward capacity context is already involved in diagnostics.
A forward-only adapter gives immediate value without touching planner behavior.
```

---

## 23. Test Strategy

### 23.1 Forward context tests

Use temporary `WeeklyCapacityRow` objects.

Assert:

```text
product -> node -> capacity_type -> week -> capacity_qty
```

Example:

```python
rows = [
    WeeklyCapacityRow(
        scenario_id="RICE_AS_IS",
        product_id="PACKAGED_RICE_STANDARD",
        capacity_owner_type="node",
        capacity_owner_id="MILL_EAST",
        tree_side="IN",
        week="2027-W40",
        capacity_type="P",
        capacity_qty=5,
        cap_mode="hard",
        unit="lot",
    )
]
```

Expected:

```python
{
    "PACKAGED_RICE_STANDARD": {
        "MILL_EAST": {
            "P": {
                "2027-W40": 5
            }
        }
    }
}
```

### 23.2 Duplicate aggregation tests

Two rows with the same key should produce summed capacity if aggregation is implemented.

### 23.3 Product separation tests

Rows for different products should stay separated.

### 23.4 Node separation tests

Rows for different nodes should stay separated.

### 23.5 Week preservation tests

Weeks should remain as provided if `week_domain="preserve"`.

### 23.6 Cap mode non-loss test

If metadata sidecar is introduced, test that cap_mode appears in metadata.

If no metadata sidecar is introduced in R1, explicitly document that R1 produces quantity-only context.

---

## 24. Safety Boundaries for First Implementation

Do not modify:

```text
weekly_forward_push_with_capacity.py
capacity_aware_inbound_backward.py
explicit_bridge_capacity_pipeline.py
cockpit_tk.py
explicit_pipeline_management_cockpit_view.py
data/*.csv
```

Likely files for first implementation:

```text
pysi/plan/explicit_pipeline_capacity_context.py
tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py
```

or another existing capacity context module if more appropriate.

---

## 25. Acceptance Criteria for R1

R1 is complete when:

```text
WeeklyCapacityRow -> explicit forward capacity context adapter exists
adapter produces deterministic product/node/type/week nested dict
adapter preserves week keys
adapter separates products and nodes
adapter aggregates duplicates deterministically or documents duplicate policy
focused tests pass
no planner behavior changes occur
no GUI changes occur
no data CSV changes occur
```

---

## 26. Summary

The previous phase built the first station:

```text
capacity_master.csv -> WeeklyCapacityRow
```

This memo designs the next track:

```text
WeeklyCapacityRow -> runtime capacity contexts
```

The safest next step is forward-only:

```text
WeeklyCapacityRow
    ↓
env.explicit_pipeline_forward_weekly_capacity-compatible context
```

Then expand to:

```text
backward capability
weekly_capability
env attachment
diagnostic metadata
scenario package integration
```

In short:

```text
The canonical capacity row is now loaded.
The next job is to lay runtime tracks from that station.
```
