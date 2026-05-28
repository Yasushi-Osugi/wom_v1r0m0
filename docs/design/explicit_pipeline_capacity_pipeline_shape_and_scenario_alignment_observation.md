# Explicit Pipeline Capacity Pipeline Shape and Scenario Alignment Observation

## 1. Purpose
This memo records observed runtime behavior of the Explicit Pipeline Capacity Pipeline as a WOM Knowledge Increment. It characterizes current operational semantics without changing business logic.

## 2. Files inspected
- `pysi/plan/explicit_bridge_capacity_pipeline.py`
- `pysi/plan/explicit_pipeline_capacity_context.py`
- `pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py`
- `pysi/plan/weekly_forward_push_with_capacity.py`
- `pysi/reporting/explicit_pipeline_capacity_report.py`
- `pysi/reporting/explicit_pipeline_issue_candidates.py`
- `pysi/reporting/explicit_pipeline_reporting_flags.py`
- `pysi/reporting/explicit_pipeline_kpi_demo_flags.py`
- `pysi/gui/cockpit_tk.py`
- `pysi/gui/explicit_pipeline_management_cockpit_view.py`
- `tests/test_explicit_pipeline_forward_capacity_context.py`
- `tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py`
- `tests/test_explicit_pipeline_management_cockpit_kpi_view.py`
- `tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py`
- `tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py`

## 3. Pipeline entry points
Entry points were identified as:
- `maybe_run_explicit_bridge_capacity_pipeline_from_env(...)`
- `maybe_run_explicit_bridge_capacity_pipeline(ctx)`
- `run_explicit_bridge_capacity_pipeline(...)`

Required ctx keys are enforced in `maybe_run_explicit_bridge_capacity_pipeline`:
- `explicit_pipeline_outbound_root`
- `explicit_pipeline_inbound_root`
- `explicit_pipeline_product`
- `explicit_pipeline_mom_policy`
- `explicit_pipeline_backward_weekly_capability`
- `explicit_pipeline_forward_weekly_capacity`

`maybe_run_explicit_bridge_capacity_pipeline_from_env` reads feature flag and optional mode/config attrs from `env`, assembles a ctx dict, runs pipeline, and attaches `env.explicit_bridge_capacity_pipeline_result`.

## 4. Required ctx keys
Observed as runtime-required for pipeline execution:
- `explicit_pipeline_backward_weekly_capability`
- `explicit_pipeline_forward_weekly_capacity`

Observed as required for KPI reporting stack (when respective flags are ON):
- `explicit_bridge_capacity_pipeline_result` (for capacity report)
- `explicit_bridge_capacity_pipeline_report` (for issue candidates)
- `explicit_bridge_capacity_issue_candidates` (for cost/KPI enrichment)

## 5. Backward capability shape actually consumed
Current context builder emits:
- `node -> product -> week -> capability_lots`

Smoke flow passes this into `capacity_aware_inbound_backward_planning(...)` as `weekly_capability`. No contradiction was found in inspected code paths for backward shape.

## 6. Forward capacity shape actually consumed
There is a shape mismatch between producer and consumer:
- Context builder emits: `product -> node -> capacity_type -> week -> capacity_lots` (week keys may be strings such as `2027-W40`).
- Forward execution consumer (`weekly_forward_push_with_capacity`) expects: `weekly_capacity[product][node][capacity_type]` to be a **list indexed by integer week position**.

Operational effect:
- The function calls `_cap_for_week(cap_values, week_int)`.
- If `cap_values` is not a list (e.g., dict of week strings), `_cap_for_week` returns `None`.
- `None` means unlimited capacity fallback (MVP behavior).

Therefore current forward capacity context is accepted syntactically by pipeline wiring but semantically ignored by forward capacity enforcement.

## 7. Product selection and filtering behavior
The pipeline uses `explicit_pipeline_product` from ctx and passes it to smoke/forward functions. In forward execution:
- Product filtering is strict at top-level map lookup: `capacity_by_product = (weekly_capacity or {}).get(product, {})`.
- If selected product key is absent, product capacity map is empty.

No env.product_selected direct read occurs in pipeline file; product is consumed from function argument/ctx.

## 8. Missing selected product behavior
When selected product is absent from forward capacity context:
- No unavailability marker is raised.
- No explicit diagnostic is emitted in this layer.
- Capacity caps resolve to `None` and are treated as unlimited in forward push.

So current behavior aligns most with: pipeline continues and effectively ignores missing product capacity (not zero-capacity blocking).

## 9. Week-key handling
Observed behavior:
- No week-key normalization between string week labels and integer week indexes in forward execution.
- String keys and integer indices are effectively different domains.
- If context uses string week keys (e.g., `2027-W40`) and consumer expects list index 0..N-1, capacity is not applied.

## 10. Node matching behavior
Forward execution looks up node capacity by exact node name under selected product map:
- `node_caps = capacity_by_product.get(node_name, {})`

No MOM/DAD semantic mapping layer is present here; any node key can work if exact names match runtime nodes.

## 11. Capacity type handling
At context build time:
- Capacity type aliases normalize to `P/S/I`.

At forward execution:
- `P/S/I` are queried directly by keys from `node_caps`.

In issue rows for lot exceptions (e.g., `blocked_lot`), `capacity_type` is not populated by design in issue candidate builder. Hence UI `capacity_type` can appear blank for blocked lot records.

## 12. blocked_lot issue generation
Lineage:
1. Forward push produces blocked lot IDs (`blocked_p_lot_ids`, `blocked_s_lot_ids`).
2. Pipeline result stores union in `blocked_lot_ids`.
3. Capacity report emits one `lot_exception` record per blocked lot with `exception_type="blocked"`.
4. Issue candidate builder maps each blocked lot exception to:
   - one planning issue (`issue_type="blocked_lot"`)
   - one management issue (`issue_type="service_risk"`)

Estimated impact appears `0.00` because top impact table is sourced from **cost/KPI enriched** candidates; when impact fields are absent or defaulted, `_to_float` returns 0.0.

## 13. Issue count lineage
Observed count behavior is structurally consistent with code:
- Each blocked lot exception becomes one planning issue.
- Each blocked lot exception (elevated) also becomes one management issue.
- Warning severity count is aggregated across planning + management candidate buckets.

Therefore warnings ~= planning warnings + management warnings, which naturally doubles when both layers are warning-level and one-to-one.

## 14. Graph data requirements
Graph model derives from KPI view model:
- `weekly_issue_counts` is built only from `top_impact_issues` rows with non-empty `week`.
- `top_impact_issues` comes from enriched management + planning issue candidates.

If enriched rows have empty/None week fields, weekly graph shows “No week-level issue data is available.”

## 15. Cost / KPI composition requirements
Impact composition bars always read numeric totals from `executive_kpi_summary`:
- `estimated_lost_sales_value_total`
- `estimated_margin_impact_total`
- `estimated_inventory_cost_impact_total`
- `estimated_capacity_cost_impact_total`
- `estimated_service_penalty_total`

If all are zero (or missing -> coerced to 0.0), chart renderer shows “No Cost / KPI impact composition is available.” because max bar value <= 0.

## 16. Current interpretation of 92,422 / 184,844
Most likely interpretation:
- 92,422 lot exceptions (blocked-driven) flowed into 92,422 planning issues.
- Same 92,422 exceptions elevated into 92,422 management issues.
- Warning count = planning warnings + management warnings = 184,844.

This appears to be expected current counting semantics, not accidental arithmetic duplication in UI.

## 17. WOM Knowledge Increment

### 17.1 Case Observation
- Case name: Explicit Pipeline Capacity Context Scenario Alignment Observation (F3+).
- Active GUI product observed: `IPHONE_NM_2028_BASE`.
- Attached context keys include backward and forward capacity contexts.
- Sample forward CSV product/node/weeks: `PACKAGED_RICE_STANDARD` / `MILL_EAST` / `2027-W40, 2027-W41`.
- Observed cockpit: available pipeline artifacts with high blocked/service risk volume and zero impact composition.

### 17.2 Context Dictionary Update
1) `explicit_pipeline_backward_weekly_capability`
- Owner/producer: capacity context CSV loader.
- Consumer: backward planning stage.
- Shape: `node -> product -> week -> capability_lots`.
- Semantic meaning: backward planning capability ceiling per node/product/week.
- Missing behavior: no explicit diagnostic schema in this module.
- Observed issue: none in this investigation.
- Future rule candidate: add metadata on week domain format.

2) `explicit_pipeline_forward_weekly_capacity`
- Owner/producer: forward capacity context CSV loader.
- Consumer: `weekly_forward_push_with_capacity` via smoke flow.
- Produced shape: `product -> node -> capacity_type -> week -> capacity_lots`.
- Consumed semantic expectation: `product -> node -> capacity_type -> list[indexed_week]`.
- Missing behavior: no mismatch diagnostic when dict week map supplied.
- Observed issue: semantic no-op of capacity caps due to shape mismatch.
- Future rule candidate: explicit shape validation and conversion to consumer format.

### 17.3 Operational Semantics Rule Candidate
- If selected product is absent from forward capacity context, emit explicit scenario alignment diagnostic with product set and selected product.
- If forward capacity week domain is not index-list compatible, emit context-shape diagnostic or normalize before execution.
- Distinguish “capacity missing” from “capacity unlimited fallback” in report semantics.

### 17.4 Diagnostic Pattern
Pattern A: Product mismatch / scenario mismatch.
- Symptoms: many blocked/service-risk issues under active product, while sample capacity context belongs to different product scenario.
- Interpretation: scenario alignment uncertainty.

Pattern B: Forward capacity shape mismatch.
- Symptoms: capacity report available, yet caps may not constrain runtime.
- Interpretation: context present but operationally not applied.

Pattern C: Warning doubling.
- Symptoms: warnings exactly 2x management issues when planning and management warnings are one-to-one.
- Interpretation: layered issue candidate counting semantics.

Pattern D: Graph no-data states.
- Symptoms: empty weekly chart and impact composition.
- Interpretation: missing/non-positive enriched fields rather than graph failure.

### 17.5 Characterization Test Candidate
- Product mismatch behavior preserves current fallback (no hard failure).
- Forward capacity dict week map currently yields unlimited-cap fallback.
- Issue lineage preserves one planning + one management warning per blocked lot exception.
- Graph no-data behavior when week fields absent and impact totals zero.

### 17.6 Grammar / Context Delta Proposal
Potential future context grammar additions:
- `explicit_pipeline_scenario_alignment_diagnostic`
- `explicit_pipeline_selected_product_capacity_presence`
- `explicit_pipeline_capacity_context_product_set`
- `explicit_pipeline_capacity_week_key_format`
- `explicit_pipeline_capacity_node_level`
- `explicit_pipeline_forward_capacity_shape_version`

## 18. Recommended next sample data strategy
For next validation phase (not in this patch):
- Provide forward capacity sample aligned to active scenario product and node names.
- Provide week domain matching forward execution week index semantics or add normalization layer.

## 19. Recommended next behavior changes (not implemented here)
- Add shape guard for forward capacity consumer contract.
- Add scenario alignment diagnostics to KPI view model messages.
- Add explicit warning semantics split: planning-layer vs management-layer counts.

## 20. Safety boundaries
This patch intentionally does **not** change:
- explicit bridge capacity pipeline behavior
- planning engine behavior
- GUI behavior
- sample CSV data
- cost/KPI calculations
- scenario selectors or scenario wiring

## 21. Summary
The pipeline is available and producing diagnostics, but the forward capacity context producer/consumer semantics are currently misaligned (dict week map vs list-indexed weeks), and issue/warning proliferation is explained by current two-layer issue candidate generation semantics.
