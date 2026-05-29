# WOM Capacity Master Schema Inventory

## 1. Purpose

This document inventories the current repository capacity-related assets before any further WOM capacity master schema consolidation work. It is intentionally inventory-only: it does not propose runtime behavior changes, CSV rewrites, week-key normalization, capacity-shape conversion, planner refactoring, or GUI behavior changes.

The inventory was built from the requested design documents plus repository searches for capacity-related names such as `capacity`, `capability`, `weekly_capability`, `capacity_master`, `capacity_qty`, `capacity_type`, `cap_mode`, `CapacityUsage`, `CapacityViolation`, `WeeklyCapacityRow`, `MonthlyCapacityInputRow`, `WeeklyCapacityInputRow`, `sku_P_month_data`, `forward_weekly_capacity`, `backward_weekly_capability`, `explicit_pipeline_forward_weekly_capacity`, `explicit_pipeline_backward_weekly_capability`, `capacity_scenario_alignment`, `capacity_applicability`, `blocked_lot`, `blocked_lots`, and `capacity_clip`.

## 2. Inventory Summary

Capacity support exists, but it is fragmented across several eras and shapes.

| Area | Current finding | State |
|---|---|---|
| `capacity_master.csv` style loader | Two implemented loaders exist: `pysi/capacity/capacity_master_loader.py` and `pysi/planning/capacity_master.py`; they target different dataclasses and column contracts. | implemented, suspicious duplicate |
| `WeeklyCapacityRow` canonical weekly adapter | Implemented in `pysi/adapters/capacity_input_granularity.py` with monthly and weekly input dataclasses and conversion helpers. | implemented |
| legacy `sku_P_month_data.csv` | Implemented by plugin `pysi/plugins/capacity_provider_monthly_csv/plugin.py`; it attaches `env.weekly_capability`. | legacy, implemented |
| `env.weekly_capability` | Attached by the monthly CSV plugin and consumed by inbound backward planning smoke/bridge flows. | legacy/runtime context |
| explicit backward capability | Implemented loader/builder/env-attach helpers in `pysi/plan/explicit_pipeline_capacity_context.py`; default CSV exists. | implemented/runtime context |
| explicit forward capacity | Implemented loader/builder/env-attach helpers in `pysi/plan/explicit_pipeline_capacity_context.py`; default CSV exists. Its producer shape is map-by-week but one diagnostic says the current forward consumer expects list-by-integer-week. | implemented, shape-risk |
| planner consumption | Multiple planners consume capacity: legacy capacity planning, forward push with capacity planner, PSI adapter, inbound backward capacity planning, explicit pipeline smoke wrapper, and weekly forward push with capacity. | implemented, fragmented |
| diagnostics | Explicit pipeline capacity scenario alignment diagnostic exists and is attached to `env`; management cockpit view surfaces its messages. | implemented |
| capacity applicability status | The exact target statuses such as `absent_unlimited_fallback` or `present_aligned_applied` are not implemented as a named status enum/payload. Existing diagnostic has `effective_capacity_application` values. | documented target / gap |

Primary risk: there are several capacity master/usage/violation dataclass families and several runtime shapes. Consolidation should start by choosing a canonical master row and adapters, not by adding another planner-specific capacity path.


### Specific Inventory Questions Answered

#### 8.1 Capacity master file layout

Yes, implemented loaders exist, but there is no single canonical `data/capacity_master.csv` scenario-package loader. `pysi/capacity/capacity_master_loader.py` exposes `load_capacity_master_csv(path)` and requires `scenario_id`, `node_name`, `product_name`, `week`, `capacity_type`, and `capacity_qty`; optional/defaulted fields are `cap_mode`, `unit`, `priority`, `calendar_id`, and `comment`; it returns `CapacityBucket` rows and is tested by `tests/test_capacity_planning_basic.py`. `pysi/planning/capacity_master.py` also exposes `load_capacity_master_csv(path)`, requires the same fields plus `tree_side`, has the same optional/defaulted metadata, returns `CapacityMasterRecord` rows, and feeds lookup helpers used by planner IO tests. Runtime destination is returned rows/lookups, not direct `env` attachment.

#### 8.2 WeeklyCapacityRow

Yes, `WeeklyCapacityRow` is implemented in `pysi/adapters/capacity_input_granularity.py` with fields `scenario_id`, `product_id`, `capacity_owner_type`, `capacity_owner_id`, `week`, `capacity_type`, `capacity_qty`, `cap_mode`, `unit`, `source_granularity`, `source_id`, and `comment`. Conversion helpers include `monthly_capacity_to_weekly_rows(...)`, `weekly_capacity_to_weekly_rows(...)`, `adapt_capacity_input_to_weekly_rows(...)`, and `weekly_capacity_rows_to_weekly_capability(...)`. Tests are in `tests/test_capacity_input_granularity_adapter.py`.

#### 8.3 Legacy `sku_P_month_data.csv` path

Yes, `pysi/plugins/capacity_provider_monthly_csv/plugin.py` implements `capacity_provider_monthly_csv(**ctx)` for `sku_P_month_data.csv`. Expected columns are `product_name`, `node_name`, `year`, and `m1` through `m12`. Positive monthly values become `MonthlyCapacityInputRow` objects, then weekly rows using even distribution; the plugin default calendar mode is `four_week_month` unless overridden. Runtime destination is `env.weekly_capability` plus `env.weekly_capability_df`. Tests are in `tests/test_capacity_provider_monthly_csv_plugin.py`.

#### 8.4 `env.weekly_capability`

Yes, `env.weekly_capability` is used. It is attached by `capacity_provider_monthly_csv(**ctx)` and consumed by `capacity_aware_inbound_backward_planning(..., weekly_capability=...)` through bridge smoke flows. Expected shape is `weekly_capability[product][owner][week_index] = capacity_lot_count`, with owner-name normalization available. Tests include monthly plugin, inbound backward capacity planning, and bridge smoke tests.

#### 8.5 Explicit forward weekly capacity

Yes, `env.explicit_pipeline_forward_weekly_capacity` is used. It is attached by `attach_explicit_pipeline_forward_weekly_capacity_to_env(...)` or `maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)` from `pysi/plan/explicit_pipeline_capacity_context.py`. Producer shape is `product -> node -> capacity_type -> week -> capacity_lots`; diagnostic shape version is usually `product_node_type_week_map_v1`, while list-shaped consumer-compatible data is `product_node_type_week_list_v0`. It is consumed by the explicit bridge capacity pipeline and ultimately by `weekly_forward_push_with_capacity(...)`. Tests include explicit forward context, sample CSV, shape alignment, explicit bridge pipeline, and GUI wiring tests.

#### 8.6 Explicit backward weekly capability

Yes, `env.explicit_pipeline_backward_weekly_capability` is used. It is attached by `attach_explicit_pipeline_backward_weekly_capability_to_env(...)` or `maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)` from `pysi/plan/explicit_pipeline_capacity_context.py`. Expected shape is `node -> product -> week -> capability_lots`; diagnostic shape version is `node_product_week_map_v1`. It is consumed by the explicit bridge capacity pipeline and ultimately by `capacity_aware_inbound_backward_planning(...)`. Tests include explicit capacity context, backward sample CSV, explicit bridge pipeline, and GUI wiring tests.

#### 8.7 Capacity diagnostics

Capacity alignment diagnostics are implemented in `pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py`. Key functions are `classify_week_key_domain(...)`, `infer_backward_capability_shape_version(...)`, `infer_forward_capacity_shape_version(...)`, `build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)`, and `attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(...)`. Payload keys include `forward_capacity`, `backward_capability`, `runtime_tree`, `consumer_expectation`, `alignment`, and `messages`. GUI surfacing runs through `pysi/gui/cockpit_tk.py` env attach and `pysi/gui/explicit_pipeline_management_cockpit_view.py` message rendering. Tests cover diagnostic builder, shape alignment, view-model messages, and GUI wiring.

#### 8.8 Planner behavior

Planner/engine modules that consume capacity and may block or backlog lots include `pysi/capacity/capacity_planning.py`, `pysi/planning/forward_push_with_capacity_planner.py`, `pysi/planning/capacity_io.py`, `pysi/planning/forward_push_with_capacity_psi_adapter.py`, `pysi/plan/capacity_aware_inbound_backward.py`, `pysi/plan/weekly_forward_push_with_capacity.py`, `pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py`, and `pysi/plan/explicit_bridge_capacity_pipeline.py`. Input shapes vary by module; outputs include `blocked_lots`, `blocked_lot_ids`, `blocked_p_lot_ids`, `blocked_s_lot_ids`, `backlog_lots`, `capacity_usage`, `capacity_violations`, `CapacityIssue`, and replan commands.

#### 8.9 Capacity usage / violation

Yes, `CapacityUsage` and `CapacityViolation` are implemented in both `pysi/capacity/capacity_model.py` and `pysi/planning/capacity_io.py`. Export behavior exists in `pysi/capacity/capacity_exporter.py` and `pysi/planning/capacity_io.py`, both writing usage and violation CSV columns for scenario/tree/node/product/week/type/capacity/usage/overflow/action fields. Tests include `tests/test_capacity_planning_basic.py`, dummy/real node capacity tests, and `tests/test_capacity_master_io.py`.

#### 8.10 Capacity applicability status

The requested named capacity applicability statuses are not implemented as a first-class enum or stable payload. The closest existing implementation is the alignment diagnostic field `alignment.effective_capacity_application`, whose values are `not_evaluated`, `uncertain_or_not_applied`, `applied`, and `not_applied`. Target statuses such as `absent_unlimited_fallback`, `present_aligned_applied`, `present_misaligned_product`, `present_misaligned_node`, `present_misaligned_week_domain`, `present_misaligned_shape`, and `applied_and_blocking` remain a gap.

## 3. Design Documents Found

All source design documents requested for this inventory are present.

| Requested document | Status | Notes |
|---|---:|---|
| `docs/design/wom_capacity_master_schema_consolidation.md` | found | Parent consolidation memo; documents target architecture and applicability-status ideas. |
| `docs/design/wom_master_data_schema_consolidation_and_pysi_v0r8_mapping.md` | found | Master data consolidation context. |
| `docs/design/wom_scenario_package_control_model.md` | found | Scenario package control context. |
| `docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md` | found | Capacity IO / forward push design lineage. |
| `docs/design/wom_capacity_input_granularity_adapter.md` | found | Weekly/monthly adapter design; maps to `WeeklyCapacityRow`. |
| `docs/design/capacity_input_granularity_adapter_v0r1_completion.md` | found | Completion note for adapter implementation. |
| `docs/design/capacity_provider_monthly_csv_adapter_v0r2.md` | found | Legacy monthly `sku_P_month_data.csv` adapter design. |
| `docs/design/explicit_pipeline_forward_weekly_capacity_context.md` | found | Explicit forward capacity context design. |
| `docs/design/explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.md` | found | Shape/scenario alignment design. |
| `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md` | found | Diagnostic design. |
| `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md` | found | Diagnostic completion note. |
| `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md` | found | Env attach completion note. |

Additional capacity-related design documents found include:

- `docs/design/with-capacity-psi-planning-engine-v0.1.md` through later capacity-engine notes.
- `docs/design/weekly_forward_push_with_capacity_psi_engine.md`.
- `docs/design/with_capacity_forward_push_planning_v0r2.md` and completion notes.
- `docs/design/with_capacity_forward_push_planning_v0r3_bottleneck_allocation.md`.
- `docs/design/capacity_aware_inbound_backward_planning_tobe.md` and completion notes.
- `docs/design/explicit_pipeline_backward_weekly_capability_context.md` and completion notes.
- `docs/design/explicit_pipeline_backward_weekly_capability_env_attach.md` and completion notes.
- `docs/design/explicit_pipeline_forward_weekly_capacity_sample_csv.md` and completion notes.
- `docs/design/explicit_pipeline_capacity_reporting.md` and completion notes.
- `docs/design/explicit_pipeline_issue_candidates.md`, `docs/design/explicit_pipeline_issue_candidate_cost_kpi_enrichment.md`, and completion notes.
- `docs/design/explicit_pipeline_management_cockpit_kpi_ctx_guard_diagnostics_view.md` and completion notes.
- `docs/design/legacy_pysi_v0r8_input_loader_mapping.md`.

No requested source design document was missing.

## 4. Capacity CSV / Sample Data Files

| File | Header / shape | Consumer or loader | State |
|---|---|---|---|
| `pysi/master_data/capacity_master_sample.csv` | `scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,cap_mode,unit,priority,calendar_id,comment` | Loaded by `pysi/capacity/capacity_master_loader.py` in `tests/test_capacity_planning_basic.py`; also compatible with `pysi/planning/capacity_master.py` because it includes `tree_side`. | implemented sample |
| `data/sku_P_month_data.csv` | BOM-bearing CSV with `product_name,node_name,year,m1...m12` | `pysi/plugins/capacity_provider_monthly_csv/plugin.py` default input. | legacy implemented |
| `data/data_BK260404_1118/sku_P_month_data.csv` | `product_name,node_name,year,m1...m12` | Backup/sample of the same legacy monthly shape. | legacy sample |
| `data/explicit_pipeline_backward_weekly_capability.csv` | `scenario,node,product,week,capability_lots,capability_type,unit,source,note` | `load_explicit_pipeline_backward_weekly_capability_csv()` and default attach helper. | implemented sample/runtime input |
| `data/explicit_pipeline_forward_weekly_capacity.csv` | `scenario,product,node,capacity_type,week,capacity_lots,unit,source,note` | `load_explicit_pipeline_forward_weekly_capacity_csv()` and default attach helper. | implemented sample/runtime input |
| `data/phone_v0/capacity_P.csv` | `month,node_name,value` | No current direct loader found in the primary searched code path; likely older/sample capacity data. | implemented status unclear / possibly unused |

No repository file named `data/capacity_master.csv` was found. The master-like sample is currently under `pysi/master_data/capacity_master_sample.csv`.

## 5. Loader and Adapter Modules

### `pysi/capacity/capacity_master_loader.py`

- Function: `load_capacity_master_csv(path)`.
- Output: `list[pysi.capacity.capacity_model.CapacityBucket]`.
- Required columns: `scenario_id`, `node_name`, `product_name`, `week`, `capacity_type`, `capacity_qty`.
- Optional/defaulted columns: `cap_mode` default `soft`, `unit` default `LOT`, `priority` default `100`, `calendar_id`, `comment`.
- Validation: requires header, existing file, capacity type in `P/S/I`, cap mode in `soft/hard`, integer `capacity_qty`, integer `priority`.
- Runtime destination: returned list of `CapacityBucket`; not attached to `env` by this loader.
- Tests: `tests/test_capacity_planning_basic.py` loads `pysi/master_data/capacity_master_sample.csv`.
- State: implemented, but it is one of multiple capacity master loaders.

### `pysi/planning/capacity_master.py`

- Dataclass: `CapacityMasterRecord`.
- Function: `load_capacity_master_csv(path)`.
- Required columns: `scenario_id`, `tree_side`, `node_name`, `product_name`, `week`, `capacity_type`, `capacity_qty`.
- Optional/defaulted columns: `cap_mode` default `soft`, `unit` default `LOT`, `priority` default `100`, `calendar_id`, `comment`.
- Helper functions: `build_capacity_lookup(records)` and `get_capacity_record(...)`.
- Runtime destination: lookup keyed by `(scenario_id, tree_side, node_name, product_name, week, capacity_type)` with product wildcard fallback to `*`.
- Tests: `tests/test_capacity_master_io.py`, `tests/test_forward_push_with_capacity_psi_adapter.py`, and bottleneck/forward-push tests construct or use records/lookups.
- State: implemented, but separate from `pysi/capacity/capacity_master_loader.py`.

### `pysi/adapters/capacity_input_granularity.py`

- Dataclasses: `WeeklyCapacityRow`, `MonthlyCapacityInputRow`, `WeeklyCapacityInputRow`.
- Conversion functions: `monthly_capacity_to_weekly_rows(...)`, `weekly_capacity_to_weekly_rows(...)`, `adapt_capacity_input_to_weekly_rows(...)`, and `weekly_capacity_rows_to_weekly_capability(...)`.
- Runtime destination helper: `weekly_capacity_rows_to_weekly_capability(...)` builds `env.weekly_capability`-compatible `dict[product][owner][week_index] = int_capacity`.
- Tests: `tests/test_capacity_input_granularity_adapter.py`.
- State: implemented canonical-row adapter, used by the monthly CSV plugin.

### `pysi/plugins/capacity_provider_monthly_csv/plugin.py`

- Function/action: `capacity_provider_monthly_csv(**ctx)` registered as `pipeline:before_planning`.
- Default filename: `sku_P_month_data.csv`.
- Required columns: `product_name`, `node_name`, `year`, `m1` ... `m12`.
- Behavior: reads monthly rows with pandas, creates `MonthlyCapacityInputRow` records for positive monthly quantities, converts monthly to weekly rows with `monthly_capacity_to_weekly_rows(...)`, builds `env.weekly_capability`, and attaches a debug dataframe `env.weekly_capability_df`.
- Calendar default: `four_week_month` unless context overrides `capacity_calendar_mode` or `calendar_mode`.
- Tests: `tests/test_capacity_provider_monthly_csv_plugin.py`.
- State: legacy implemented path.

### `pysi/plan/explicit_pipeline_capacity_context.py`

- Backward functions: `build_explicit_pipeline_backward_weekly_capability(...)`, `load_explicit_pipeline_backward_weekly_capability_csv(...)`, `attach_explicit_pipeline_backward_weekly_capability_to_env(...)`, `maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)`.
- Forward functions: `build_explicit_pipeline_forward_weekly_capacity(...)`, `load_explicit_pipeline_forward_weekly_capacity_csv(...)`, `attach_explicit_pipeline_forward_weekly_capacity_to_env(...)`, `maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)`.
- Default CSVs: `data/explicit_pipeline_backward_weekly_capability.csv`, `data/explicit_pipeline_forward_weekly_capacity.csv`.
- State: implemented explicit runtime context loader/attacher.

## 6. Dataclasses and Canonical Row Structures

| Structure | File | Fields / shape | State |
|---|---|---|---|
| `CapacityBucket` | `pysi/capacity/capacity_model.py` | `scenario_id`, `node_name`, `product_name`, `week`, `capacity_type`, `capacity_qty`, `cap_mode`, `unit`, `priority`, `calendar_id`, `comment`. | implemented |
| `CapacityUsage` | `pysi/capacity/capacity_model.py` | scenario/tree/node/product/week/type, capacity, used quantity, used lots, derived remaining/utilization. | implemented |
| `CapacityViolation` | `pysi/capacity/capacity_model.py` | scenario/tree/node/product/week/type/mode/capacity/required/overflow/violation type/overflow lots/action. | implemented |
| `CapacityMasterRecord` | `pysi/planning/capacity_master.py` | includes `tree_side` and capacity master fields. | implemented |
| `CapacityUsage` | `pysi/planning/capacity_io.py` | similar to `pysi.capacity` usage, but in planning namespace and string week. | implemented, suspicious duplicate |
| `CapacityViolation` | `pysi/planning/capacity_io.py` | similar to `pysi.capacity` violation, with defaults for lot ids/action. | implemented, suspicious duplicate |
| `CapacityUsageRecord` | `pysi/planning/forward_push_with_capacity_planner.py` | node/product/week requested/capacity/accepted/blocked/used/remaining. | implemented planner-local record |
| `CapacityIssue` | `pysi/planning/capacity_issue.py` | issue payload for planner capacity shortage, including blocked lot ids. | implemented |
| `WeeklyCapacityRow` | `pysi/adapters/capacity_input_granularity.py` | `scenario_id`, `product_id`, `capacity_owner_type`, `capacity_owner_id`, `week`, `capacity_type`, `capacity_qty`, `cap_mode`, `unit`, `source_granularity`, `source_id`, `comment`. | implemented canonical adapter row |
| `MonthlyCapacityInputRow` | `pysi/adapters/capacity_input_granularity.py` | monthly input fields including `month` and capacity metadata. | implemented |
| `WeeklyCapacityInputRow` | `pysi/adapters/capacity_input_granularity.py` | weekly input fields before canonical tagging. | implemented |
| `WeeklyForwardPushWithCapacityResult` | `pysi/plan/weekly_forward_push_with_capacity.py` | accepted/blocked/overflow counts and lot ids plus capacity usage, violations, replan commands, data-quality errors. | implemented |
| `CapacityAwareInboundBackwardPlanningResult` | `pysi/plan/capacity_aware_inbound_backward.py` | planned/checked/accepted/shifted/backlog counts, lot lists, capacity usage by MOM/week, errors. | implemented |
| `ExplicitBridgeCapacityPipelineResult` | `pysi/plan/explicit_bridge_capacity_pipeline.py` | source/missing/shifted/backlog/accepted/blocked/overflow lots, capacity usage/violations, replan commands, errors. | implemented |
| `ExplicitPipelineCapacityReport` | `pysi/reporting/explicit_pipeline_capacity_report.py` | report record lists and summary. | implemented reporting payload |
| `ExplicitPipelineIssueCandidateBundle` | `pysi/reporting/explicit_pipeline_issue_candidates.py` | planning/management/replan/health candidate lists and summary. | implemented reporting payload |

## 7. Runtime Capacity Contexts

### `env.weekly_capability`

- Attached by: `capacity_provider_monthly_csv(**ctx)` in `pysi/plugins/capacity_provider_monthly_csv/plugin.py`.
- Expected shape: `weekly_capability[product][MOM_or_owner][week_index] = int_capacity`, where owner names may normalize `DAD...` to `MOM...` via `normalize_capacity_owner_name(...)`.
- Debug companion: `env.weekly_capability_df` with product/node/week/capacity metadata.
- Consumed by: `capacity_aware_inbound_backward_planning(..., weekly_capability=...)` through bridge smoke flows, and older GUI snippets/backups also read it for capacity visuals.
- Tests: `tests/test_capacity_provider_monthly_csv_plugin.py`, `tests/test_capacity_aware_inbound_backward_planning.py`, and `tests/test_e2e_demand_to_supply_bridge_flow_smoke.py`.
- State: legacy runtime context, implemented.

### `env.explicit_pipeline_backward_weekly_capability`

- Attached by: `attach_explicit_pipeline_backward_weekly_capability_to_env(...)` or `maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(...)` in `pysi/plan/explicit_pipeline_capacity_context.py`.
- Expected shape: `context[node][product][week] = capability_lots`.
- Shape version in diagnostic: `node_product_week_map_v1`.
- Default CSV path: `data/explicit_pipeline_backward_weekly_capability.csv`.
- Consumed by: `maybe_run_explicit_bridge_capacity_pipeline(...)` and `run_explicit_bridge_capacity_pipeline(...)`, which pass it to `run_e2e_bridge_forward_capacity_smoke(...)`; that passes it as `weekly_capability` to `capacity_aware_inbound_backward_planning(...)`.
- GUI attach path: `pysi/gui/cockpit_tk.py` calls `_maybe_attach_explicit_pipeline_backward_weekly_capability()` when explicit KPI demo flags are applied.
- Tests: `tests/test_explicit_pipeline_capacity_context.py`, `tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py`, `tests/test_explicit_bridge_capacity_pipeline.py`, `tests/test_explicit_bridge_capacity_pipeline_feature_flag.py`, and GUI wiring tests.
- State: implemented runtime context.

### `env.explicit_pipeline_forward_weekly_capacity`

- Attached by: `attach_explicit_pipeline_forward_weekly_capacity_to_env(...)` or `maybe_attach_explicit_pipeline_forward_weekly_capacity_from_csv(...)` in `pysi/plan/explicit_pipeline_capacity_context.py`.
- Expected producer shape: `context[product][node][capacity_type][week] = capacity_lots`.
- Shape version in diagnostic: producer maps generally infer as `product_node_type_week_map_v1`; list-shaped forward contexts infer as `product_node_type_week_list_v0`.
- Default CSV path: `data/explicit_pipeline_forward_weekly_capacity.csv`.
- Consumed by: `maybe_run_explicit_bridge_capacity_pipeline(...)` and `run_explicit_bridge_capacity_pipeline(...)`, which pass it to `run_e2e_bridge_forward_capacity_smoke(...)`; that passes it as `weekly_capacity` to `weekly_forward_push_with_capacity(...)`.
- Important shape risk: `weekly_forward_push_with_capacity(...)` calls `_cap_for_week(node_caps.get("P"), w)` and expects a list-like capacity vector or `None` by integer week index. The explicit CSV builder creates a week-key dictionary. The diagnostic explicitly models this mismatch with default consumer expectation `product_node_type_week_list_v0` and `integer_index`.
- GUI attach path: `pysi/gui/cockpit_tk.py` calls `_maybe_attach_explicit_pipeline_forward_weekly_capacity()` when explicit KPI demo flags are applied.
- Tests: `tests/test_explicit_pipeline_forward_capacity_context.py`, `tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py`, scenario alignment tests, pipeline tests, and GUI wiring tests.
- State: implemented runtime context with known alignment/shape risk.

## 8. Planner / Engine Capacity Consumers

| File | Functions / class | Input capacity shape | Output / blocking behavior | Tests |
|---|---|---|---|---|
| `pysi/capacity/capacity_planning.py` | `with_capacity_forward_planning(...)`, `get_capacity_bucket(...)`, `split_lots_by_capacity(...)` | `list[CapacityBucket]` / lookup keyed by scenario-node-product-week-type. | Applies P/S/I capacity, writes supply lots, emits `CapacityUsage` and `CapacityViolation`; soft overflows carry forward or alert, hard overflows carry/block/waste depending type. | `tests/test_capacity_planning_basic.py`, `tests/test_capacity_planning_dummy_node.py`, `tests/test_capacity_planning_real_node.py`, small tree tests. |
| `pysi/planning/forward_push_with_capacity_planner.py` | `ForwardPushWithCapacityPlanner.consume_lots_with_capacity(...)` | scalar `capacity_qty` or `None`. | Missing capacity means unlimited; otherwise accepted/blocked lots and `CapacityIssue` with `blocked_lot_ids`. | `tests/test_forward_push_with_capacity_planner.py`. |
| `pysi/planning/capacity_io.py` | `run_forward_push_with_capacity_from_master(...)` | `CapacityMasterRecord` lookup from `pysi/planning/capacity_master.py`. | Returns planner result plus optional `CapacityUsage` and `CapacityViolation`; violation action is `BLOCK` for hard, `CARRY_OVER` for soft. | `tests/test_capacity_master_io.py`. |
| `pysi/planning/forward_push_with_capacity_psi_adapter.py` | `run_forward_push_with_capacity_psi_lists(...)`, `apply_capacity_to_node_psi_bucket(...)` | Capacity lookup keyed by master record fields. | Moves accepted lots into `psi4supply`, records blocked/carryover lots by key and usage/violation records. | `tests/test_forward_push_with_capacity_psi_adapter.py`. |
| `pysi/plan/capacity_aware_inbound_backward.py` | `capacity_aware_inbound_backward_planning(...)`, `resolve_mom_weekly_capacity(...)` | `weekly_capability` as `dict[product][mom]` or `dict[mom]`, with values as list/dict/scalar normalized to weekly vector. | Capacity-limits MOM production, shifts overflow earlier within window, otherwise records backlog lots. | `tests/test_capacity_aware_inbound_backward_planning.py`. |
| `pysi/plan/weekly_forward_push_with_capacity.py` | `weekly_forward_push_with_capacity(...)` | `weekly_capacity[product][node][P/S/I]` values expected as lists by integer week index or `None`. | Blocks P/S over capacity, flags I overflow, emits usage/violation dicts and replan commands. | `tests/test_weekly_forward_push_with_capacity.py`, bridge smoke tests. |
| `pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py` | `run_e2e_bridge_forward_capacity_smoke(...)` | Backward capability context plus forward weekly capacity context. | Runs Bridge A, MOM allocation, backward capacity planning, Bridge B, forward capacity push; returns blocked and overflow lot ids. | `tests/test_e2e_bridge_forward_capacity_smoke.py`. |
| `pysi/plan/explicit_bridge_capacity_pipeline.py` | `run_explicit_bridge_capacity_pipeline(...)`, `maybe_run_explicit_bridge_capacity_pipeline(...)`, `maybe_run_explicit_bridge_capacity_pipeline_from_env(...)` | `explicit_pipeline_backward_weekly_capability`, `explicit_pipeline_forward_weekly_capacity`. | Wraps smoke flow and normalizes blocked/overflow/missing result fields for reporting. | `tests/test_explicit_bridge_capacity_pipeline.py`, `tests/test_explicit_bridge_capacity_pipeline_feature_flag.py`. |

## 9. Explicit Pipeline Capacity Contexts

The explicit pipeline has two separate runtime capacity contexts:

1. **Backward capability context**: `node -> product -> week -> lots`.
2. **Forward capacity context**: `product -> node -> capacity_type -> week -> lots` from CSV builder, while the forward consumer currently expects `product -> node -> capacity_type -> week-index list`.

The explicit KPI demo flow in `pysi/gui/cockpit_tk.py` applies demo flags, attempts to attach both explicit capacity contexts from their default CSVs, attaches the capacity scenario alignment diagnostic, and then uses `get_missing_explicit_pipeline_demo_ctx_keys(...)` to guard execution when either explicit capacity context is absent.

The reporting stack then uses explicit pipeline results to build:

- capacity report records in `pysi/reporting/explicit_pipeline_capacity_report.py`;
- issue candidates in `pysi/reporting/explicit_pipeline_issue_candidates.py`;
- cost/KPI enrichment in `pysi/reporting/explicit_pipeline_issue_candidate_cost_kpi.py`;
- management cockpit KPI view model in `pysi/gui/explicit_pipeline_management_cockpit_view.py`.

State: implemented runtime-only contexts with default CSV loaders, but no common adapter from `WeeklyCapacityRow` to both explicit contexts was found.

## 10. Diagnostics and Cockpit Surfacing

### Capacity scenario alignment diagnostic

- File: `pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py`.
- Functions:
  - `classify_week_key_domain(keys)`.
  - `extract_runtime_node_names(*roots)`.
  - `infer_backward_capability_shape_version(context)`.
  - `infer_forward_capacity_shape_version(context)`.
  - `build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)`.
  - `attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(...)`.
- Payload keys include:
  - top-level: `available`, `severity`, `selected_product`, `forward_capacity`, `backward_capability`, `runtime_tree`, `consumer_expectation`, `alignment`, `messages`.
  - `forward_capacity`: availability, product/node/type sets, week-key sample/domain, shape version.
  - `backward_capability`: availability, product/node set, week-key sample/domain, shape version.
  - `alignment`: `product_alignment`, `node_alignment`, `week_domain_alignment`, `shape_alignment`, `scenario_alignment`, `effective_capacity_application`.
- Message behavior: returns warning messages for missing selected product in contexts, week-domain mismatch, shape mismatch, and unmatched capacity nodes.
- GUI surfacing path: `pysi/gui/cockpit_tk.py` attaches the diagnostic; `pysi/gui/explicit_pipeline_management_cockpit_view.py` appends diagnostic messages as `Capacity scenario alignment: ...` in the management KPI view model.
- Tests: `tests/test_explicit_pipeline_capacity_scenario_alignment.py`, `tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py`, `tests/test_explicit_pipeline_management_cockpit_kpi_view.py`, and GUI wiring tests.
- State: implemented.

### KPI context guard diagnostics

- File: `pysi/reporting/explicit_pipeline_kpi_demo_flags.py`.
- Function: `get_missing_explicit_pipeline_demo_ctx_keys(env)`.
- Required keys: `explicit_pipeline_backward_weekly_capability`, `explicit_pipeline_forward_weekly_capacity`.
- GUI behavior: `pysi/gui/cockpit_tk.py` sets `env.explicit_kpi_demo_flag_ctx_guard_skipped`, `env.explicit_kpi_demo_flag_missing_ctx_keys`, and `env.explicit_kpi_demo_flag_guard_message` and turns explicit reporting flags off if required context is missing.
- Surfacing: `pysi/gui/explicit_pipeline_management_cockpit_view.py` includes context guard status/messages in the view model.
- Tests: `tests/test_explicit_pipeline_kpi_demo_flags.py`, `tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py`, and management cockpit KPI view tests.
- State: implemented.

### Reporting / issue diagnostics

- File: `pysi/reporting/explicit_pipeline_capacity_report.py`.
  - Function: `build_explicit_pipeline_capacity_report(...)`.
  - Records: `capacity_usage`, `capacity_violation`, `lot_exception`, `replan_candidate`, `health_check`.
- File: `pysi/reporting/explicit_pipeline_issue_candidates.py`.
  - Converts capacity report and pipeline result objects into planning/management/replan/health issue candidate lists.
- File: `pysi/reporting/explicit_pipeline_issue_candidate_cost_kpi.py`.
  - Enriches issues with directional cost/KPI estimates and risk categories.
- State: implemented reporting/cockpit surfacing.

## 11. Tests Found

Capacity-related tests found include:

- `tests/test_capacity_input_granularity_adapter.py`.
- `tests/test_capacity_provider_monthly_csv_plugin.py`.
- `tests/test_capacity_master_io.py`.
- `tests/test_capacity_planning_basic.py`.
- `tests/test_capacity_planning_dummy_node.py`.
- `tests/test_capacity_planning_real_node.py`.
- `tests/test_capacity_planning_small_inbound_tree.py`.
- `tests/test_capacity_planning_small_outbound_tree.py`.
- `tests/test_forward_push_with_capacity_planner.py`.
- `tests/test_forward_push_with_capacity_psi_adapter.py`.
- `tests/test_weekly_forward_push_with_capacity.py`.
- `tests/test_capacity_aware_inbound_backward_planning.py`.
- `tests/test_e2e_bridge_forward_capacity_smoke.py`.
- `tests/test_e2e_demand_to_supply_bridge_flow_smoke.py`.
- `tests/test_explicit_pipeline_capacity_context.py`.
- `tests/test_explicit_pipeline_forward_capacity_context.py`.
- `tests/test_explicit_pipeline_backward_weekly_capability_sample_csv.py`.
- `tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py`.
- `tests/test_explicit_bridge_capacity_pipeline.py`.
- `tests/test_explicit_bridge_capacity_pipeline_feature_flag.py`.
- `tests/test_explicit_pipeline_capacity_scenario_alignment.py`.
- `tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py`.
- `tests/test_explicit_pipeline_capacity_reporting.py`.
- `tests/test_explicit_pipeline_capacity_report_attachment.py`.
- `tests/test_explicit_pipeline_capacity_report_export.py`.
- `tests/test_explicit_pipeline_issue_candidates.py` and export tests.
- `tests/test_explicit_pipeline_issue_candidate_cost_kpi.py` and export tests.
- `tests/test_explicit_pipeline_kpi_demo_flags.py`.
- `tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py`.
- `tests/test_explicit_pipeline_management_cockpit_kpi_view.py` and related cockpit rendering/graph/card tests.

No tests were added or modified for this inventory-only request.

## 12. Existing Mapping to Consolidation Memo

| Target concept | Existing implementation | Existing design doc | Status | Gap |
|---|---|---|---|---|
| `capacity_master.csv` | `pysi/capacity/capacity_master_loader.py`; `pysi/planning/capacity_master.py`; sample at `pysi/master_data/capacity_master_sample.csv`. | `docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md`; older `docs/design/with-capacity-psi-planning-engine-v0.1.md`; parent consolidation memo. | implemented, duplicated | No single canonical loader/dataclass; no scenario-package `data/capacity_master.csv` path found. |
| `WeeklyCapacityRow` | `pysi/adapters/capacity_input_granularity.py`. | `docs/design/wom_capacity_input_granularity_adapter.md`; completion memo. | implemented | Not wired as the sole canonical bridge into capacity master and explicit contexts. |
| `sku_P_month_data` adapter | `pysi/plugins/capacity_provider_monthly_csv/plugin.py`. | `docs/design/capacity_provider_monthly_csv_adapter_v0r2.md`; completion memo. | legacy implemented | Produces `env.weekly_capability`, not the explicit forward/backward contexts or capacity master records. |
| `env.weekly_capability` | Attached by monthly CSV plugin; consumed by inbound backward planning and smoke bridge flows. | `docs/design/capacity_input_granularity_adapter_v0r1_completion.md`; monthly adapter memo; legacy mapping memo. | legacy/runtime-only implemented | Shape differs from explicit backward capability; not a master-file destination. |
| explicit forward capacity | Loader/attacher in `pysi/plan/explicit_pipeline_capacity_context.py`; sample CSV in `data/explicit_pipeline_forward_weekly_capacity.csv`; consumed by explicit pipeline smoke wrapper and weekly forward push. | `docs/design/explicit_pipeline_forward_weekly_capacity_context.md`; shape alignment memo. | implemented/runtime-only | Producer map shape can mismatch list/index consumer expectation; no `WeeklyCapacityRow` adapter. |
| explicit backward capability | Loader/attacher in `pysi/plan/explicit_pipeline_capacity_context.py`; sample CSV in `data/explicit_pipeline_backward_weekly_capability.csv`; consumed by backward planning. | `docs/design/explicit_pipeline_backward_weekly_capability_context.md`; env attach memos. | implemented/runtime-only | Separate from `env.weekly_capability` and canonical master rows. |
| diagnostic | `pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py`; GUI view in `pysi/gui/explicit_pipeline_management_cockpit_view.py`. | `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md`; completion memos. | implemented | Diagnostic reports alignment/effective application but not full target applicability status taxonomy. |
| planner capacity consumption | `pysi/capacity/capacity_planning.py`, `pysi/planning/forward_push_with_capacity_planner.py`, `pysi/planning/capacity_io.py`, `pysi/planning/forward_push_with_capacity_psi_adapter.py`, `pysi/plan/capacity_aware_inbound_backward.py`, `pysi/plan/weekly_forward_push_with_capacity.py`, explicit bridge pipeline. | `docs/design/with_capacity_forward_push_planning_v0r2_m2_capacity_io.md`; `docs/design/weekly_forward_push_with_capacity_psi_engine.md`; explicit pipeline memos. | implemented | Multiple consumers expect different shapes and issue formats. |
| capacity applicability status | Partial diagnostic field `alignment.effective_capacity_application` values: `not_evaluated`, `uncertain_or_not_applied`, `applied`, `not_applied`. | `docs/design/wom_capacity_master_schema_consolidation.md`. | documented target / partial diagnostic | Missing explicit statuses such as `absent_unlimited_fallback`, `present_aligned_applied`, `present_misaligned_*`, `applied_and_blocking`. |

## 13. Gaps Against Target Architecture

1. **No single canonical capacity master loader was found.** There are at least two implemented master loaders with different dataclasses and required columns.
2. **No repository `data/capacity_master.csv` scenario-package input was found.** The sample is under `pysi/master_data/capacity_master_sample.csv`.
3. **`WeeklyCapacityRow` exists but is not the central runtime bridge.** It currently feeds the legacy `env.weekly_capability` path via monthly CSV adapter; it does not appear to feed capacity master records or explicit pipeline contexts.
4. **Explicit forward capacity shape mismatch risk remains documented and diagnosed.** The CSV builder produces week-key maps, while `weekly_forward_push_with_capacity(...)` expects list-like week-index vectors for normal capacity application.
5. **Capacity applicability status taxonomy is not implemented.** Existing diagnostic fields are useful but do not provide the requested named statuses.
6. **Capacity usage/violation structures are duplicated.** `pysi.capacity.capacity_model`, `pysi.planning.capacity_io`, `pysi.planning.forward_push_with_capacity_planner`, and `pysi/plan/weekly_forward_push_with_capacity.py` all represent usage/violation/issue concepts differently.
7. **Blocked lot formats vary.** Planner result objects use `blocked_lots`, weekly forward push uses `blocked_p_lot_ids`/`blocked_s_lot_ids`, explicit pipeline result uses `blocked_lot_ids`, capacity report uses lot-exception records, and issue candidates use `issue_type="blocked_lot"`.
8. **Week domains vary.** Some contexts use integer indexes, some use strings like `2027-W40`, and master samples use `YYYY-Www` strings. This request intentionally did not normalize them.
9. **`capacity_type` meaning varies by context.** Master and forward capacity use `P/S/I`; backward sample includes `capability_type=output`, which is ignored by the current backward builder except as a pass-through CSV column.
10. **No scenario package capacity master loading path was confirmed.** Scenario memos exist, but no runtime scenario-package loader for a canonical capacity master was identified in this inventory.

Suspicious duplicates to preserve but consolidate later:

- `pysi/capacity/capacity_master_loader.py` versus `pysi/planning/capacity_master.py`.
- `pysi/capacity.capacity_model.CapacityUsage/CapacityViolation` versus `pysi/planning.capacity_io.CapacityUsage/CapacityViolation` versus planner-local usage/violation dictionaries.
- `env.weekly_capability` versus `env.explicit_pipeline_backward_weekly_capability`.
- explicit forward capacity map shape versus weekly forward push list/index shape.
- multiple report/issue formats for blocked lots and capacity violations.

## 14. Recommended Next Implementation Step

Recommended next step: **implement one canonical `capacity_master.csv -> WeeklyCapacityRow` (or canonical capacity row) loader/adapter and then derive all runtime contexts from that canonical row set.**

More specifically:

1. Choose the canonical schema fields by reconciling `CapacityMasterRecord` and `WeeklyCapacityRow`.
2. Preserve the legacy `sku_P_month_data.csv` adapter by making it produce the same canonical weekly row set before building `env.weekly_capability`.
3. Add adapters from canonical weekly rows to:
   - `env.weekly_capability` for legacy backward planning;
   - `env.explicit_pipeline_backward_weekly_capability`;
   - `env.explicit_pipeline_forward_weekly_capacity` in the exact shape consumed by `weekly_forward_push_with_capacity(...)` or behind a deliberate adapter boundary.
4. Add capacity applicability status after the canonical row/adapters exist, so the diagnostic can distinguish absent, aligned, misaligned, applied, and blocking states without guessing across multiple shapes.

This recommendation is based on the inventory finding that loader/context fragmentation is the main current risk, not absence of capacity planning behavior.

## 15. No-Behavior-Change Confirmation

- Created only this inventory document: `docs/design/wom_capacity_master_schema_inventory.md`.
- No Python code was changed.
- No CSV/data files were changed.
- No tests were added or modified.
- No planner behavior was changed.
- No GUI behavior was changed.
- No week-key normalization or capacity-shape conversion was performed.
