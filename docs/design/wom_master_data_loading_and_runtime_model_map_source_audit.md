# WOM Master Data Loading and Runtime Model Map Source Audit

**Version:** v0r1 source audit  
**Date:** 2026-06-03  
**Status:** implementation-grounded documentation appendix  
**Companion design memo:** `docs/design/wom_master_data_loading_and_runtime_model_map.md`  
**Preceding design memo:** `docs/design/wom_top_routine_and_pipeline_core_design.md`

## 1. Executive Summary

The current implementation has a clear, tested Japanese Rice vertical-slice path for network, demand, demand-lot seeding, capacity row loading, capacity runtime attachment diagnostics, isolated capacity-gate evaluation, runner output, and GUI/chart datasets.

Clearly implemented categories:

- **Network / node / edge master**: `examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv` and `network_master.csv` are loaded by `pysi.network.network_master_loader`, validated, converted to `NetworkNodeRow` / `NetworkEdgeRow`, and instantiated into `ProductPlanNode` inbound/outbound trees by `pysi.plan.plan_node_tree_instantiation`.
- **Demand master**: `demand_master.csv` is loaded by `pysi.demand.demand_master_loader.load_weekly_demand_master_csv`, converted to `WeeklyDemandRow`, expanded to deterministic `DemandAnchoredLot` records, and attached to `MARKET_TOKYO.psi4demand[week][0]` in the actual `ProductPlanNode` tree.
- **Capacity master**: `capacity_master.csv` is loaded by `pysi.capacity.capacity_master_loader.load_capacity_master_csv` into `WeeklyCapacityRow`, attached to `env.capacity_weekly_rows` by `pysi.capacity.capacity_weekly_rows_source.load_capacity_weekly_rows_to_env`, then converted into diagnostic runtime capacity contexts by `pysi.reporting.explicit_pipeline_capacity_scenario_alignment.apply_capacity_runtime_attachment_preflight`.
- **Visualization dataset adapters for Japanese Rice**: `pysi.gui.japanese_rice_first_runner_view` contains stable adapter-like helpers that transform runner output into a GUI model, chart dataset, chart series, and scenario comparison dataset.

Partial / legacy / not-yet-connected categories:

- **Cost / money / cash-flow**: multiple mature but separate paths exist. `pysi.cost.load_cost_masters` loads cost-master directories into `CostMasterBundle`; `pysi.master_data.money_master_loader` loads node/product money masters; `pysi.evaluate.money_evaluator` computes node/product money rows and can attach them to `env.money_result`. These are not wired into the Japanese Rice runner or a unified Run Full Plan contract.
- **Price / offering price**: price appears in cost masters (`sales_price_master.csv`), SQL tables (`price_tag`, `scenario_price_tag`), `pysi.evaluate.offering_price`, legacy exported `offering_price_ASIS_TOBE.csv`, and `pysi.wom_main.export_offering_prices`. It is not scenario-package master data for Japanese Rice.
- **Tariff**: tariff-like fields exist as lane-cost `tariff_rate`, money edge `duty_cost_per_lot`, legacy `tariff_table.csv`, `customs_tariff_rate`, `tax_tariff_cost_per_lot`, and experimental propagation code. There is no current canonical tariff loader or tariff evaluator connected to Japanese Rice or Run Full Plan.
- **Product / SKU, calendar / week, lane / logistics**: present in legacy, modeling, and cost/reporting paths, but not in the Japanese Rice scenario package as separate product/SKU/calendar/lane master files. `calendar_id` is preserved as a string in Japanese Rice network/demand/capacity rows but not resolved through a calendar master.

Important Run Full Plan graph-adapter findings:

1. The most stable source for Japanese Rice GUI graph/table/chart work is the runner output contract from `run_japanese_rice_first_psi_vslice`, not raw planner internals.
2. `ProductPlanNode` is the current vertical-slice runtime node class; legacy `Node` still exists with different bucket shape and `nx_capacity`, so graph adapters must avoid assuming one universal runtime object.
3. Capacity has several representations: raw `WeeklyCapacityRow`, `env.capacity_weekly_rows`, forward/backward diagnostic contexts, legacy `weekly_capability`, isolated DC capacity gate rows, and legacy `Node.nx_capacity`. A FullPlanResult should name exactly which representation it exposes.
4. There is no unified `MasterLoadResult`, `WomRuntimeModel`, or `FullPlanResult` object yet; current code uses dict contracts and env attributes.

## 2. Master File Inventory

| Category | File path / pattern | Example scenario | Status | Notes |
|---|---|---:|---|---|
| scenario config | `scenario_config["masters"]["capacity_master"]` accepted only by `capacity_weekly_rows_source`; no checked-in Japanese Rice scenario config file found | Japanese Rice uses root path directly | partial | Capacity source resolution supports config, but network/demand loaders directly use `scenario_root / "masters" / ...`. |
| network / node / edge | `examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv`, `network_master.csv` | `japanese_rice_vslice_001` | implemented | `load_network_master_package` loads both files and reports counts/paths/tree sides. |
| demand | `examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv` | `japanese_rice_vslice_001` | implemented | Weekly demand rows are expanded one lot per quantity by default. |
| capacity | `examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv`; `pysi/master_data/capacity_master_sample.csv` | `japanese_rice_vslice_001` | implemented | Canonical loader creates `WeeklyCapacityRow`; env loader attaches rows and summary. |
| cost | `data/cost_masters/*.csv`; inbound templates under `data/cost_masters/wom_inbound_costing_templates/*.csv`; `pysi/master_data/node_product_money_master.csv` | global sample data, not Japanese Rice scenario package | partial | Loaders exist, but no Japanese Rice runner wiring or unified Full Plan cost result. |
| price / offering price | `data/cost_masters/sales_price_master.csv`; `data/offering_price_ASIS_TOBE.csv`; SQL `price_tag` / `scenario_price_tag`; `pysi/master_data/node_product_money_master.csv` `ship_price_per_lot` | global / legacy | partial | Several sources and evaluators exist; no Japanese Rice scenario-specific price master. |
| tariff | `data/tariff_table.csv`, `pysi/optimise/tariff_table.csv`, lane-cost `tariff_rate`, money `duty_cost_per_lot` | global / legacy | legacy | No canonical tariff master loader or current tariff simulation connection found. |
| product / SKU | `examples/scenarios/edu_csv/products.csv`; `pysi/optimise/sku_*_month_data.csv`; `data/cost_masters/product_cost_master.csv`; legacy SKU settings | not in Japanese Rice scenario package | legacy / partial | Japanese Rice product is carried as `product_name` columns, not a standalone product/SKU master. |
| calendar / week | `calendar_id` columns in Japanese Rice CSVs; `pysi.adapters.calendar_445`; week strings such as `2027-W40` | Japanese Rice | partial | Week keys are preserved; no scenario calendar master is loaded for Japanese Rice. |
| lane / logistics | `data/cost_masters/lane_cost_master.csv`; `pysi.reporting.e2e_lane_route_*`; network edge rows include parent/child/leadtime/capacity | global / reporting | partial | Logistics costs are reporting/cost-master data; Japanese Rice network edges are structural but not full lane-cost masters. |

## 3. Loader Function Inventory

| Category | Module | Function / class | Input | Output | Status | Notes |
|---|---|---|---|---|---|---|
| network node | `pysi/network/network_master_loader.py` | `load_network_node_master_csv`, `NetworkNodeRow` | `node_master.csv` | `list[NetworkNodeRow]` | implemented | Validates required columns; derives MOM/DAD flags from `node_character` too. |
| network edge | `pysi/network/network_master_loader.py` | `load_network_edge_master_csv`, `NetworkEdgeRow` | `network_master.csv` | `list[NetworkEdgeRow]` | implemented | Validates parent/child/leadtime/process/transport fields. |
| network package | `pysi/network/network_master_loader.py` | `load_network_master_package` | `scenario_root` | dict with `nodes`, `edges`, `summary` | implemented | Hard-codes `masters/node_master.csv` and `masters/network_master.csv`. |
| tree instantiation | `pysi/plan/plan_node_tree_instantiation.py` | `ProductPlanNode`, `instantiate_product_plan_node_trees` | node/edge rows | inbound/outbound tree dict | implemented | Sets `parent`, `children`, role flags, `partner_key`, `node_character`, empty PSI dicts. |
| Japanese Rice tree + demand | `pysi/plan/plan_node_tree_instantiation.py` | `instantiate_japanese_rice_plan_node_tree_and_attach_demand` | `scenario_root` | trees, lots, `market_tokyo`, summary | implemented | Loads network + demand and mutates `MARKET_TOKYO.psi4demand`. |
| demand | `pysi/demand/demand_master_loader.py` | `load_weekly_demand_master_csv`, `WeeklyDemandRow` | `demand_master.csv` | `list[WeeklyDemandRow]` | implemented | Preserves week strings; does not run planner. |
| demand lots | `pysi/demand/demand_lot_generator.py` | `generate_demand_anchored_lots`, `DemandAnchoredLot` | demand rows | deterministic lot list | implemented | `lot_id = scenario|node|product|week|sequence`. |
| demand compatibility attach | `pysi/demand/demand_lot_generator.py` | `attach_demand_lots_to_leaf_plan_node_psi4demand` | lots and optional actual nodes | nested dict and optional node mutation | implemented | Supports symbolic `"S"` bucket and legacy index 0 mutation. |
| capacity canonical CSV | `pysi/capacity/capacity_master_loader.py` | `load_capacity_master_csv` | `capacity_master.csv` | `list[WeeklyCapacityRow]` | implemented | Stops at canonical row boundary. |
| capacity source/env | `pysi/capacity/capacity_weekly_rows_source.py` | `load_capacity_weekly_rows_to_env` | explicit path or scenario root/config | env attributes + summary | implemented | Resolution order: explicit path, config, `masters/capacity_master.csv`, direct root file. |
| capacity runtime context | `pysi/plan/explicit_pipeline_capacity_context.py` | `attach_capacity_runtime_contexts_to_env_from_weekly_rows` | `list[WeeklyCapacityRow]` | `env.explicit_pipeline_forward_weekly_capacity`, `env.explicit_pipeline_backward_weekly_capability_from_weekly_rows`, summary | diagnostic-only | Planner-neutral switchyard; does not replace consumer-facing backward capability. |
| capacity preflight | `pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py` | `apply_capacity_runtime_attachment_preflight` | env with `capacity_weekly_rows` | preflight result + diagnostic contexts | diagnostic-only | Used by Japanese Rice runner for `runtime_attachment_applied`. |
| capacity gate | `pysi/plan/capacity_constrained_first_flow.py` | `run_japanese_rice_capacity_constrained_first_flow`, `compute_capacity_gate_flow_by_week` | scenario root / lots / capacity | accepted/blocked gate result | implemented vertical slice | Isolated DC_KANTO S capacity gate, not full PSI planner. |
| legacy/planning capacity | `pysi/planning/capacity_master.py` | `load_capacity_master_csv`, `build_capacity_lookup`, `get_capacity_record` | capacity CSV | `CapacityMasterRecord` lookup | partial / parallel | Separate int-only capacity path used by `capacity_io`. |
| explicit legacy capability CSV | `pysi/plan/explicit_pipeline_capacity_context.py` | `load_explicit_pipeline_backward_weekly_capability_csv`, `load_explicit_pipeline_forward_weekly_capacity_csv` | explicit pipeline capability/capacity CSVs | context dicts | partial | Uses legacy columns such as `node`, `product`, `capability_lots` / `capacity_lots`. |
| cost masters | `pysi/cost/load_cost_masters.py` | `load_cost_masters`, `CostMasterBundle`, `load_inbound_cost_masters` | cost-master directory | bundle or legacy payload | partial | Loads many CSVs; not Japanese Rice runner input. |
| money masters | `pysi/master_data/money_master_loader.py` | `load_money_master_bundle` and component loaders | node/money CSVs | `MoneyMasterBundle` | partial | Rich money master bundle used by money evaluator / legacy WOM. |
| money evaluation | `pysi/evaluate/money_evaluator.py` | `evaluate_money_by_node` | env with PSI/tree/money bundle | node money rows and env attachments | partial | Computes revenue/cost/tax/profit rows; not invoked by Japanese Rice runner. |
| offering price | `pysi/evaluate/offering_price.py` | `build_offering_price_frame`, `plot_offering_price_grid` | SQLite DB / SQL tables | pandas frame / matplotlib figure | legacy / partial | Supports scenario-specific SQL `scenario_price_tag`; not scenario CSV loader. |
| price chart | `pysi/reporting/price_propagation_chart.py` | `load_node_price_waterfall`, `load_price_propagation_trace`, `generate_price_waterfall_stacked_bar` | exported CSVs | chart files | reporting-only | Reads flat report outputs, not masters. |
| Japanese Rice GUI | `pysi/gui/japanese_rice_first_runner_view.py` | `extract_japanese_rice_first_runner_gui_model`, chart dataset/series helpers | runner result | GUI/chart model dicts | implemented | Best current adapter pattern for Run Full Plan graph-panel design. |

## 4. Runtime Setting Map

| Source | Loader output | Runtime object | Attribute / index | Set by | Used by | Notes |
|---|---|---|---|---|---|---|
| `node_master.csv` | `NetworkNodeRow` | `ProductPlanNode` | `node_character`, `node_role`, flags, `partner_key`, `position_group` | `_make_product_plan_node` | tests, runner network validation, GUI summaries | Role flags are copied and also inferred from `node_character` in loader. |
| `network_master.csv` | `NetworkEdgeRow` | `ProductPlanNode` | `parent`, `children`, `depth` | `_instantiate_tree_side` | path tests, tree summaries, demand attach | One inbound and one outbound `supply_point` runtime object exist. |
| `demand_master.csv` | `WeeklyDemandRow` | `DemandAnchoredLot` | `lot_id`, `demand_week`, `anchor_node`, `target_psi_slot` | `generate_demand_anchored_lots` | demand attach, capacity gate | Lot IDs are deterministic and source-row-linked. |
| demand lots | `DemandAnchoredLot` | `ProductPlanNode` | `psi4demand[week][0]` | `attach_demand_lots_to_actual_plan_node_psi4demand` | `run_japanese_rice_capacity_constrained_first_flow` | Actual Japanese Rice path reads `MARKET_TOKYO.psi4demand[week][0]`. |
| demand lots | `DemandAnchoredLot` | compatibility dict | `product -> demand_node -> psi4demand[week]["S"]` | `attach_demand_lots_to_leaf_plan_node_psi4demand` | first runner compatibility checks | Runner validates compatibility counts separately from actual tree diagnostic. |
| `ProductPlanNode` class | dataclass defaults | `ProductPlanNode` | `psi4demand`, `psi4supply` empty dicts | dataclass construction | demand seeding and future planning | `psi4supply` exists but Japanese Rice first runner does not seed it. |
| `capacity_master.csv` | `WeeklyCapacityRow` | env | `capacity_weekly_rows`, source metadata, load summary | `load_capacity_weekly_rows_to_env` | runner, diagnostics, preflight | Canonical capacity rows are not stored on `ProductPlanNode`. |
| `env.capacity_weekly_rows` | `WeeklyCapacityRow` list | env | `explicit_pipeline_forward_weekly_capacity[product][node][type][week]` | `attach_capacity_runtime_contexts_to_env_from_weekly_rows` via preflight | diagnostics / KPI preflight | Product-first shape; duplicate keys summed. |
| `env.capacity_weekly_rows` | `WeeklyCapacityRow` list | env | `explicit_pipeline_backward_weekly_capability_from_weekly_rows[product][node][type][week]` | same | diagnostics | Canonical side attribute; does not replace `env.explicit_pipeline_backward_weekly_capability`. |
| legacy explicit CSV | records | env | `explicit_pipeline_backward_weekly_capability[node][product][week]` | `attach_explicit_pipeline_backward_weekly_capability_to_env` | explicit pipeline legacy consumers | Different shape from canonical weekly-row backward context. |
| `capacity_master.csv` | filtered DC rows | capacity gate result | `weekly[week].accepted_lot_ids`, `blocked_lot_ids` | `compute_capacity_gate_flow_by_week` | runner demo summary and GUI chart | Uses only `DC_KANTO` / `S` over target weeks. |
| capacity rows / legacy adapter | `WeeklyCapacityRow` list | dict | `weekly_capability[product][mom_name][week_index]` | `weekly_capacity_rows_to_weekly_capability` | capacity adapter tests / older pipeline | Normalizes `DAD*` to `MOM*` by default; not Japanese Rice first runner runtime. |
| legacy `Node` | constructor defaults | `Node` | `nx_capacity` | `pysi/network/node_base.py` `Node.__init__` | legacy NetworkX/planner paths | Default is 1; not set by Japanese Rice capacity loader. |
| cost CSV directory | `CostMasterBundle` | bundle / payload | `node_cost_rates`, `lane_cost_rates`, `market_cost_rates`, lookups | `load_cost_masters` | reporting MVP, cost engine | Parallel cost path; not attached in Japanese Rice runner. |
| money master CSVs | `MoneyMasterBundle` | env | `money_master_bundle` | `pysi.wom_main._load_money_master_bundle_once` and callers | `evaluate_money_by_node` | Money evaluator reads bundle and attaches `env.money_result`. |
| money evaluator | node money rows | env | `money_unit_price_rows`, `money_weekly_rows`, `node_money_rows`, `money_result` | `evaluate_money_by_node` | reporting/exporters | Not wired into Japanese Rice first runner. |
| price SQL/CSV | price rows / frames | pandas / node attrs | `offering_price_ASIS`, `offering_price_TOBE`, `ship_price_per_lot` | `offering_price.py`, `evaluate_cost_models_v2.py`, `wom_main.export_offering_prices` | price charts, legacy eval | Multiple sources; no single current price master contract. |
| tariff-like rows | lane cost / legacy tariff tables / node attrs | bundle / node / rows | `tariff_rate`, `duty_cost_per_lot`, `customs_tariff_rate`, `tax_tariff_cost_per_lot` | cost/money/legacy loaders | legacy cost/price/reporting | No canonical tariff index or evaluator. |
| runner result | result dict | GUI model | `weekly_rows`, `totals`, `management_message` | `extract_japanese_rice_first_runner_gui_model` | Tk view and chart dataset | Current best adapter boundary. |

## 5. Japanese Rice Current Path

Actual current path from source code:

1. **Scenario root**: caller passes `examples/scenarios/japanese_rice_vslice_001` to `pysi.runners.run_japanese_rice_first_psi_vslice.run_japanese_rice_first_psi_vslice`; GUI default is `pysi.gui.japanese_rice_first_runner_view.DEFAULT_SCENARIO_ROOT`.
2. **Network master load**: `load_network_master_package(root)` loads `masters/node_master.csv` and `masters/network_master.csv` into `NetworkNodeRow` / `NetworkEdgeRow` and a summary.
3. **ProductPlanNode tree**: `instantiate_japanese_rice_plan_node_tree_and_attach_demand` calls `instantiate_product_plan_node_trees` to build inbound/outbound `ProductPlanNode` trees and set parent/children links.
4. **Demand master load**: `load_weekly_demand_master_csv(root / "masters" / "demand_master.csv")` loads `WeeklyDemandRow` records.
5. **Demand lot generation**: `generate_demand_anchored_lots(demand_rows)` creates `DemandAnchoredLot` values.
6. **MARKET_TOKYO PSI demand attach**: `_find_market_leaf(..., "MARKET_TOKYO")` selects the outbound leaf and `attach_demand_lots_to_actual_plan_node_psi4demand` appends lot IDs into `MARKET_TOKYO.psi4demand[week][0]`.
7. **Capacity master load**: `load_capacity_weekly_rows_to_env(env, scenario_root=root, required=True)` finds `masters/capacity_master.csv`, parses `WeeklyCapacityRow`, and sets `env.capacity_weekly_rows`.
8. **Capacity runtime attachment**: `apply_capacity_runtime_attachment_preflight(env)` builds diagnostic forward/backward runtime contexts and summaries from `env.capacity_weekly_rows`.
9. **DC_KANTO capacity gate**: `run_japanese_rice_capacity_constrained_first_flow` reuses the actual plan-node demand lot source, filters capacity rows for `DC_KANTO` / `S`, and `compute_capacity_gate_flow_by_week` calculates accepted/blocked lots.
10. **Runner output contract**: `run_japanese_rice_first_psi_vslice` returns a dict with `contract_version`, master counts, demand/network/capacity summaries, actual plan-node diagnostics, capacity-constrained first flow, balance, `demo_summary`, and CLI lines.
11. **GUI model**: `extract_japanese_rice_first_runner_gui_model` consumes only the public demo summary and CLI lines to produce GUI fields.
12. **Chart dataset**: `build_japanese_rice_capacity_gate_chart_dataset` converts GUI weekly rows into presentation-neutral chart rows, totals, and series names.
13. **Chart view**: `build_japanese_rice_capacity_gate_chart_series` converts dataset rows to x-values and numeric series; `add_capacity_gate_chart_to_window` renders them in Tk.
14. **Scenario variation**: `build_capacity_override_chart_dataset` and `build_capacity_gate_scenario_comparison` create a non-mutating capacity-up comparison from the base chart dataset.

## 6. Capacity Master Audit

### 6.1 CSV loading and expected columns

`pysi.capacity.capacity_master_loader.load_capacity_master_csv` expects:

```text
scenario_id, tree_side, node_name, product_name, week, capacity_type,
capacity_qty, cap_mode, unit
```

Optional columns preserved by the loader are `comment`, `priority`, `calendar_id`, and `source_file` metadata. It trims strings, parses `capacity_qty` as int-or-float, and emits `WeeklyCapacityRow` with:

- `product_id = product_name`
- `capacity_owner_type = "node"`
- `capacity_owner_id = node_name`
- `source_granularity = "weekly"`
- `source_id = "capacity_master.csv:<row_num>"`
- `tree_side`, `priority`, `calendar_id`, and `source_file` preserved.

A parallel loader exists at `pysi.planning.capacity_master.load_capacity_master_csv`; it creates `CapacityMasterRecord`, requires valid `capacity_type in {P,S,I}`, valid `cap_mode in {soft,hard}`, and integer `capacity_qty`. This is a separate planning-capacity path, not the one used by the Japanese Rice first runner.

### 6.2 Source resolution and env attachment

`pysi.capacity.capacity_weekly_rows_source.load_capacity_weekly_rows_to_env` resolves capacity in this order:

1. explicit `capacity_master_path`
2. `scenario_config["masters"]["capacity_master"]` relative to `scenario_root`
3. `scenario_root / "masters" / "capacity_master.csv"`
4. `scenario_root / "capacity_master.csv"`

When found, it sets:

- `env.capacity_weekly_rows`
- `env.capacity_weekly_rows_source_kind`
- `env.capacity_weekly_rows_source_path`
- `env.capacity_weekly_rows_load_summary`

When not found, it sets a missing summary and raises only if `required=True`.

### 6.3 Runtime attachment and context shapes

`pysi.reporting.explicit_pipeline_capacity_scenario_alignment.apply_capacity_runtime_attachment_preflight` checks for `env.capacity_weekly_rows`. If present, it delegates to `pysi.plan.explicit_pipeline_capacity_context.attach_capacity_runtime_contexts_to_env_from_weekly_rows` and returns:

- `applied: True`
- `row_source: "env.capacity_weekly_rows"`
- `input_row_count`
- `attachment_summary`
- `runtime_attachment`

The attachment helper builds:

```text
env.explicit_pipeline_forward_weekly_capacity[product][node][capacity_type][week] = capacity_qty
env.explicit_pipeline_backward_weekly_capability_from_weekly_rows[product][node][capacity_type][week] = capacity_qty
env.capacity_runtime_attachment_summary
```

It does **not** replace legacy `env.explicit_pipeline_backward_weekly_capability`, whose older shape is:

```text
env.explicit_pipeline_backward_weekly_capability[node][product][week] = capability_lots
```

### 6.4 ProductPlanNode and legacy Node storage

- `ProductPlanNode` does not currently store capacity directly. Capacity is held in row lists, env contexts, and isolated gate result dicts.
- Legacy `pysi.network.node_base.Node` initializes `nx_capacity = 1` for NetworkX/legacy paths, but the Japanese Rice capacity master loader does not write to `Node.nx_capacity`.
- `weekly_capacity_rows_to_weekly_capability` in `pysi.adapters.capacity_input_granularity` can build `weekly_capability[product][owner][week_index]` with optional `DAD* -> MOM*` owner normalization and a capacity type filter. This is a separate adapter path and is not the Japanese Rice first runner's DC gate source.

### 6.5 Precedence rules found

- Capacity source path precedence is explicit path > scenario config > scenario package master > direct root CSV.
- Runtime canonical weekly-row attachment does not overwrite legacy consumer-facing backward capability.
- Planning `build_capacity_lookup` uses sorted priority and first-row-wins per `(scenario, tree_side, node, product, week, capacity_type)`, with wildcard product fallback in `get_capacity_record`.
- Japanese Rice DC gate sums all matching `WeeklyCapacityRow.capacity_qty` for `DC_KANTO` / `S` / target week, and treats zero as missing.

### 6.6 Known concept audit

| Concept | Found? | Location / status | Notes |
|---|---:|---|---|
| `load_capacity_weekly_rows_to_env` | yes | `pysi/capacity/capacity_weekly_rows_source.py` | Central Japanese Rice capacity env loader. |
| `runtime_attachment_applied` | yes | `_extract_capacity_context_summary` in runner | Derived from preflight `applied is True`. |
| `input_row_count` | yes | preflight result and tests | Japanese Rice tests assert 9. |
| `weekly_capability[product][mom_name]` | yes | `weekly_capacity_rows_to_weekly_capability` | Adapter path, not first runner gate. |
| `weekly_capability[mom_name]` | not as current canonical shape | explicit legacy contexts use `node -> product -> week`; older docs/tests mention variants | Ambiguous legacy shape; avoid exposing without version. |
| `mom.nx_capacity` | not in Japanese Rice current path | legacy `Node.nx_capacity` only | No capacity-master attachment to ProductPlanNode or Node found for Japanese Rice. |
| capacity gate accepted / blocked | yes | `pysi/plan/capacity_constrained_first_flow.py` | FIFO split by capacity for DC_KANTO S. |

## 7. Cost / Money / Cash-Flow Audit

### 7.1 Cost master files and loaders

Cost-master files exist under `data/cost_masters`, including:

- `product_cost_master.csv`
- `node_cost_master.csv`
- `lane_cost_master.csv`
- `sales_price_master.csv`
- `allocation_rule_master.csv`
- `market_master.csv`
- `cs_node_to_market_map.csv`
- `sga_marketing_tax_master.csv`
- `fixed_asset_cost_master.csv`

Inbound templates exist under `data/cost_masters/wom_inbound_costing_templates`, including `inbound_item_master.csv`, `inbound_bom_usage_master.csv`, `inbound_price_decision_master.csv`, and `inbound_adjustment_master.csv`.

`pysi.cost.load_cost_masters.load_cost_masters` reads these files into `CostMasterBundle` rows and lookups. Current direct lookups include `node_cost_rates`, `lane_cost_rates`, `market_cost_rates`, and `allocation_rules`. Additional future-facing lookups include product, node, lane, sales price, market, SGA, fixed asset, and inbound lookups.

### 7.2 Money master files and loaders

Money-master files exist under `pysi/master_data`, especially:

- `node_master.csv`
- `node_character_money_master.csv`
- `node_product_money_master.csv`

`pysi.master_data.money_master_loader.load_money_master_bundle` loads these into `MoneyMasterBundle`, which exposes node, node-character policy, node-product money, edge-product money, and valuation-policy lookups. The node-product money master includes purchase cost, ship price, inventory value, variable cost, fixed cost, tax, currency, and effective-week fields.

### 7.3 Money / cash-flow calculation and reporting

`pysi.evaluate.money_evaluator.evaluate_money_by_node` builds unit price records, weekly money rows, node money rows, KPI summary rows, and product money summary rows. It attaches results back to env as `money_unit_price_rows`, `money_weekly_rows`, `node_money_rows`, `money_node_rows`, and `money_result`.

`pysi.evaluate.money_output_exporter.export_money_outputs` exports `node_money_eval.csv`, `kpi_summary.csv`, `product_money_summary.csv`, `node_price_waterfall.csv`, and `price_propagation_trace.csv`. `pysi.reporting.price_propagation_chart` then reads waterfall/trace/route CSVs for charts. `pysi.reporting.business_report_builder.build_business_report` aggregates generic cost lines into product, market, monthly, cost-waterfall, and management-facing report rows.

### 7.4 Connection status

- Connected to Japanese Rice first runner: **no**. No call to cost/money loaders or money evaluator occurs in `run_japanese_rice_first_psi_vslice`.
- Connected to current Run Full Plan: **partial / unclear**. Pipeline code references money evaluation, and explicit pipeline cost-KPI enrichment can consume `explicit_bridge_capacity_cost_kpi_context`, but no unified Run Full Plan cost result contract exists.
- Overall status: **partial / experimental / parallel**. Useful components exist, but they need a formal adapter contract before graph panel, cockpit, and Full Plan use.

## 8. Price / Offering Price Audit

Price appears in several places:

1. `data/cost_masters/sales_price_master.csv` is loaded by `pysi.cost.load_cost_masters` into `sales_price_rows`, `sales_price_lookup`, and market-cost rates.
2. `pysi.master_data.node_product_money_master.csv` carries `ship_price_per_lot`, exposed as `NodeProductMoneyMasterRecord.revenue_unit_value`.
3. `pysi.evaluate.offering_price.build_offering_price_frame` reads SQLite tables `price_tag`, optionally `scenario_price_tag`, `node_product`, and `product_edge`, then builds `offering_price_ASIS` / `offering_price_TOBE` frames. Scenario-specific price is supported in SQL when `scenario_id` is provided.
4. Legacy `data/offering_price_ASIS_TOBE.csv` and `pysi.wom_main.export_offering_prices` export or consume node-level ASIS/TOBE offering prices.
5. `pysi.evaluate.evaluate_cost_models_v2` contains legacy helpers `load_tobe_prices`, `assign_tobe_prices_to_leaf_nodes`, `load_asis_prices`, and `assign_asis_prices_to_root_nodes`.

Connection status:

- Japanese Rice first runner: **not connected**.
- Current GUI/reporting: **connected in legacy/reporting paths**, especially offering price grid/plots and price propagation charts.
- Scenario-specific CSV price master: **not found** for Japanese Rice. Scenario-specific price currently appears SQL-based (`scenario_price_tag`) or cost-master-directory based (`sales_price_master.csv`).

## 9. Tariff Audit

Tariff-like data exists, but no canonical tariff simulation path is connected.

Found data / fields:

- `data/tariff_table.csv` and `pysi/optimise/tariff_table.csv` are legacy tariff tables.
- `data/cost_masters/lane_cost_master.csv` has `tariff_rate` and `customs_cost_per_unit`, loaded by `pysi.cost.load_cost_masters` into `lane_cost_rates["tariff"]` and `lane_cost_rates["customs"]`.
- `pysi.master_data.money_master_loader.EdgeProductMoneyRecord` has `duty_cost_per_lot`.
- `pysi.network.node_base.Node` has `customs_tariff_rate`, `tariff_on_price`, and related cost/tax attributes.
- `pysi.evaluate.evaluate_cost_models_v2` uses tariff rates in experimental ASIS/TOBE price propagation and writes `tariff_cost` on nodes.
- Reporting and tests mention `tax_tariff_cost_per_lot` as a price waterfall component.

Status:

- Tariff master file exists: **legacy yes**.
- Tariff loader exists: **legacy/embedded yes**, but no canonical `tariff_master_loader.py` found.
- Tariff used in current Japanese Rice calculation: **no**.
- Tariff used in Run Full Plan: **not found / unclear**.
- Tariff tests: found tariff-related assertions around money evaluator / price waterfall fields, but no end-to-end tariff simulation test.

Missing for future tariff simulation:

- canonical tariff master schema and loader,
- product/HS-code/origin/destination/week index,
- explicit tariff evaluator that consumes FullPlanResult or flat flow/lane rows,
- clear relationship to lane cost `tariff_rate` and money `duty_cost_per_lot`,
- reporting/GUI adapter contract for tariff deltas.

## 10. Visualization Dataset Audit

### 10.1 Japanese Rice adapters

`pysi.gui.japanese_rice_first_runner_view` is the strongest current adapter-like pattern:

- `extract_japanese_rice_first_runner_gui_model(result)` consumes stable runner output and builds a GUI model.
- `build_japanese_rice_weekly_capacity_gate_rows(result)` builds table rows from `demo_summary.capacity_gate_summary.weekly`.
- `build_japanese_rice_capacity_gate_chart_dataset(model_or_result)` converts GUI rows into chart-ready rows with derived shortage, unused capacity, usage percentage, and blocked percentage.
- `build_japanese_rice_capacity_gate_chart_series(dataset)` converts chart dataset rows into x-values and numeric series.
- `build_capacity_override_chart_dataset(base_dataset, capacity_value=...)` builds a deterministic capacity-up variant without mutating master data or planner state.
- `build_capacity_gate_scenario_comparison(base_dataset, variant_dataset)` builds week-by-week and total deltas.
- `add_capacity_gate_chart_to_window` and `_launch_model_window` render the dataset directly in Tk.

### 10.2 Reporting / cockpit adapter patterns

- `pysi.reporting.explicit_pipeline_capacity_report` and `pysi.reporting.explicit_pipeline_capacity_report_exporter` build/export flat explicit pipeline capacity reports.
- `pysi.reporting.explicit_pipeline_issue_candidates` and cost-KPI modules build issue candidate bundles and optional cost-KPI enrichment from env/reporting inputs.
- `pysi.reporting.e2e_lane_route_runtime` and `e2e_lane_route_exporter` build lane route rows from env/product trees.
- `pysi.reporting.e2e_lane_price_chart_runtime.generate_e2e_lane_price_chart_from_env` is a safe wrapper that exports route rows and invokes price waterfall chart generation from flat CSVs.
- `pysi.reporting.price_propagation_chart` reads flat CSV datasets and creates chart files.
- `pysi.gui.explicit_pipeline_management_cockpit_view` builds management cockpit view models from diagnostics/KPI data; it is adapter-like but broader than the Japanese Rice runner path.
- `pysi.gui.cockpit_tk` still contains GUI methods that read env/runner-specific attributes directly, so not all GUI paths are adapter-isolated.

## 11. Test Coverage Map

| Area | Test file | What it verifies | Gaps |
|---|---|---|---|
| Japanese Rice network master | `tests/test_japanese_rice_network_master_vertical_slice.py` | master row loading, node/edge counts, roles, paths | No unified master package object beyond network dict. |
| Japanese Rice demand master | `tests/test_japanese_rice_demand_master_vertical_slice.py` | weekly demand loader and lot generation | No monthly allocation in this vertical slice. |
| Japanese Rice capacity master | `tests/test_japanese_rice_capacity_master_vertical_slice.py` | scenario-root capacity loading, row domains, runtime preflight contexts | Does not attach capacity to `ProductPlanNode`; no tariff/cost link. |
| ProductPlanNode tree | `tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py` | parent/children links, role preservation, demand attach to `psi4demand[week][0]` | No `psi4supply` planning behavior. |
| First PSI runner | `tests/test_japanese_rice_first_psi_run_vertical_slice.py` | master counts, demand attachment, runtime capacity attachment, balance, messages | Diagnostic-first only; no Full PSI plan. |
| Runner output / CLI | `tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py` | output contract and CLI summary | Contract is runner-specific, not unified FullPlanResult. |
| Capacity-constrained first flow | `tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py` and `tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py` | actual `MARKET_TOKYO.psi4demand[week][0]` source and DC_KANTO accepted/blocked lots | Single gate only, not multi-node plan. |
| Chart dataset/view/scenario variation | `tests/test_japanese_rice_first_runner_chart_dataset_vertical_slice.py`, `tests/test_japanese_rice_first_runner_chart_view_vertical_slice.py`, `tests/test_japanese_rice_first_runner_scenario_variation_vertical_slice.py`, `tests/test_japanese_rice_first_runner_gui_wrapper_vertical_slice.py` | GUI model, chart dataset/series, Tk helper, capacity-up comparison | Japanese Rice-specific adapter; no generic graph panel adapter. |
| Capacity runtime attachment | `tests/test_wom_capacity_weekly_rows_runtime_env_attach.py`, `tests/test_wom_capacity_runtime_attachment_diagnostic_integration.py`, `tests/test_wom_capacity_runtime_attachment_preflight_wiring.py`, `tests/test_wom_capacity_runtime_attachment_explicit_kpi_preflight_wiring.py` | env attachment, diagnostics, preflight wiring | Multiple shapes remain; no single capacity model. |
| Capacity weekly rows source | `tests/test_wom_capacity_master_to_env_capacity_weekly_rows_source.py`, `tests/test_wom_capacity_weekly_rows_source_diagnostic.py` | source resolution and diagnostics | Mainly capacity-only diagnostics. |
| Explicit forward/backward contexts | `tests/test_wom_capacity_weekly_rows_to_explicit_backward_context.py`, `tests/test_wom_capacity_weekly_rows_to_explicit_forward_context.py`, `tests/test_explicit_pipeline_capacity_context.py` | context conversion shapes and validation | Legacy and canonical shapes coexist. |
| Cost master | `tests/test_cost_master_data.py` | loads `data/cost_masters` | Very thin test; no Japanese Rice integration. |
| Money evaluator | `tests/evaluate_test_money_evaluator_*.py`, `tests/master_data_test_node_product_money_master_pro_placeholder.py` | money rows, price waterfall trace/export, purchase cost propagation, placeholder fields | Not connected to Japanese Rice runner / Full Plan. |
| Reporting price/cost | `tests/reporting_test_price_propagation_chart.py`, `tests/reporting_test_e2e_lane_price_chart_runtime.py`, `tests/reporting_test_e2e_lane_route_*` | flat reporting/chart exports | Reads exported CSV/runtime env, not unified FullPlanResult. |
| Tariff-related | money/price waterfall tests mention `tax_tariff_cost_per_lot`; legacy tariff files exist | field presence / price model references | No canonical tariff loader/evaluator test found. |

## 12. Gaps and Risks

1. **No unified `MasterLoadResult`**: network/demand/capacity loaders return separate row lists/dicts and env attributes.
2. **No unified `WomRuntimeModel`**: `ProductPlanNode`, legacy `Node`, env contexts, and result dicts coexist.
3. **No unified `FullPlanResult`**: current Japanese Rice runner returns a runner-specific contract; reporting/cost paths expect env, CSV, or cost lines.
4. **Multiple capacity representations**: `WeeklyCapacityRow`, `CapacityMasterRecord`, `env.capacity_weekly_rows`, explicit forward context, canonical backward context, legacy backward capability, `weekly_capability`, DC gate result, and legacy `Node.nx_capacity` all exist.
5. **Legacy `Node` vs `ProductPlanNode` ambiguity**: legacy `Node` has list-based PSI arrays and `nx_capacity`; `ProductPlanNode` has dict week buckets and no direct capacity field.
6. **GUI modules sometimes read runner/env internals**: Japanese Rice chart helpers are clean, but cockpit code still reads env attributes directly.
7. **Cost master is not fully mapped to runtime planning**: cost loaders and evaluators exist, but Japanese Rice and Run Full Plan do not expose a cost-evaluation result contract.
8. **Price / offering price has multiple sources**: SQL tags, exported CSVs, money masters, sales price masters, and legacy node attributes are not unified.
9. **Tariff is not connected**: tariff-like fields exist but no tariff master loader/index/evaluator is active in the Japanese Rice path.
10. **Calendar is preserved but not resolved**: `calendar_id` is loaded, but week/calendar master behavior is not central in the current Japanese Rice runtime path.
11. **Lane/logistics are split between network structure and cost reporting**: network edges define topology/leadtime, while lane costs live in cost masters/reporting paths.

## 13. Recommended Next Design Actions

1. **`docs/design/wom_entrypoint_and_run_full_plan_contract.md`**  
   Define the official Run Full Plan entrypoint, scenario-root resolution, explicit master-load stages, and side-effect boundaries. This should come first because source audit shows loaders are currently called ad hoc.

2. **`docs/design/wom_full_plan_result_contract.md`**  
   Define a `FullPlanResult` that separates `master_load`, `runtime_model`, `planning_result`, `capacity_result`, `money_result`, `tariff_result`, `visualization_datasets`, and diagnostics. This is needed before GUI and reporting can consume one stable object.

3. **`docs/design/wom_run_full_plan_graph_panel_adapter_vertical_slice.md`**  
   Use the Japanese Rice GUI helpers as the adapter pattern: runner/full-plan result -> GUI model -> chart/graph dataset -> renderer. Include explicit handling for `ProductPlanNode` vs legacy `Node`.

4. **`docs/design/wom_capacity_representation_consolidation.md`**  
   Decide which capacity shape is canonical for Full Plan (`WeeklyCapacityRow` plus product/node/type/week context is the strongest candidate) and how to label legacy `weekly_capability` and `Node.nx_capacity`.

5. **`docs/design/wom_tariff_cost_simulation_model_vertical_slice.md`**  
   Design tariff as post-plan evaluation first. Define tariff master schema, loader, index, route/lane matching, result rows, and chart/report adapters without mutating PSI planning.

6. **Cost / money adapter request**  
   Add a design memo that connects `MoneyMasterBundle`, `CostMasterBundle`, and `evaluate_money_by_node` to `FullPlanResult.money_result`, rather than directly to env/CSV outputs.

## 14. Evidence Index

- `pysi/network/network_master_loader.py`
  - `NetworkNodeRow`, `NetworkEdgeRow`
  - `load_network_node_master_csv(...)`, `load_network_edge_master_csv(...)`, `load_network_master_package(...)`
  - status: implemented for Japanese Rice network rows.
- `pysi/plan/plan_node_tree_instantiation.py`
  - `ProductPlanNode`
  - `instantiate_product_plan_node_trees(...)`
  - `attach_demand_lots_to_actual_plan_node_psi4demand(...)`
  - `instantiate_japanese_rice_plan_node_tree_and_attach_demand(...)`
  - status: implemented for Japanese Rice runtime plan-node tree and demand S-slot seeding.
- `pysi/demand/demand_master_loader.py`
  - `WeeklyDemandRow`
  - `load_weekly_demand_master_csv(...)`
  - status: implemented weekly demand loader.
- `pysi/demand/demand_lot_generator.py`
  - `DemandAnchoredLot`
  - `generate_demand_anchored_lots(...)`
  - `attach_demand_lots_to_leaf_plan_node_psi4demand(...)`
  - status: implemented lot generation and compatibility attachment.
- `pysi/capacity/capacity_master_loader.py`
  - `load_capacity_master_csv(...)`
  - status: implemented canonical capacity CSV loader to `WeeklyCapacityRow`.
- `pysi/capacity/capacity_weekly_rows_source.py`
  - `load_capacity_weekly_rows_to_env(...)`
  - status: implemented capacity source resolution and env attachment.
- `pysi/plan/explicit_pipeline_capacity_context.py`
  - `attach_capacity_runtime_contexts_to_env_from_weekly_rows(...)`
  - `weekly_capacity_rows_to_explicit_forward_capacity(...)`
  - `weekly_capacity_rows_to_explicit_backward_capability(...)`
  - status: diagnostic/runtime context adapter, planner-neutral.
- `pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py`
  - `apply_capacity_runtime_attachment_preflight(...)`
  - `build_capacity_runtime_attachment_diagnostic(...)`
  - status: capacity preflight and diagnostics.
- `pysi/plan/capacity_constrained_first_flow.py`
  - `run_japanese_rice_capacity_constrained_first_flow(...)`
  - `compute_capacity_gate_flow_by_week(...)`
  - status: implemented isolated DC_KANTO accepted/blocked capacity gate.
- `pysi/runners/run_japanese_rice_first_psi_vslice.py`
  - `run_japanese_rice_first_psi_vslice(...)`
  - `build_japanese_rice_first_runner_demo_summary(...)`
  - status: diagnostic-first runner output contract.
- `pysi/gui/japanese_rice_first_runner_view.py`
  - `extract_japanese_rice_first_runner_gui_model(...)`
  - `build_japanese_rice_capacity_gate_chart_dataset(...)`
  - `build_japanese_rice_capacity_gate_chart_series(...)`
  - `build_capacity_override_chart_dataset(...)`
  - `build_capacity_gate_scenario_comparison(...)`
  - status: implemented GUI/chart adapter helpers.
- `pysi/cost/load_cost_masters.py`
  - `CostMasterBundle`, `load_cost_masters(...)`, `load_inbound_cost_masters(...)`
  - status: cost master loader, not Japanese Rice-connected.
- `pysi/master_data/money_master_loader.py`
  - `MoneyMasterBundle`, `load_money_master_bundle(...)`
  - status: money master loader, separate from Japanese Rice current path.
- `pysi/evaluate/money_evaluator.py`
  - `evaluate_money_by_node(...)`
  - status: money evaluation and env attachment, not Japanese Rice-connected.
- `pysi/evaluate/offering_price.py`
  - `build_offering_price_frame(...)`
  - status: SQL/pandas offering-price path, not scenario CSV Japanese Rice path.
- `pysi/network/node_base.py`
  - `Node`
  - status: legacy runtime node with list PSI arrays and `nx_capacity`.
