# Codex Request: Japanese Rice Network Master Vertical Slice

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_network_master_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_network_master_vertical_slice.md
```

**Related design / completion docs:**

```text
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_demand_master_vertical_slice.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice.md
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice Case network master vertical slice.

This request should add the minimal WOM E2E hammock network master files and focused tests proving the following structure:

```text
Inbound:
  supply_side_root
    -> supply_point
      -> RICE_MILL_A
        -> FARM_REGION_A
          -> Procurement_Center

Outbound:
  demand_side_root
    -> supply_point
      -> DC_KANTO
        -> MARKET_TOKYO
          -> Global_Sales_Office
```

The implementation should add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
pysi/network/network_master_loader.py
pysi/network/__init__.py
tests/test_japanese_rice_network_master_vertical_slice.py
```

If a `pysi/network` package or equivalent loader already exists, reuse or extend it minimally.

Do not implement a full PSI run.

Do not modify planner behavior.

Do not modify GUI layout.

Do not remove NetworkX in this request.

Do not implement the full V0R8 master migration in this request.

---

## 2. Strategic Context

The Japanese Rice Case already has:

```text
Capacity:
  examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv

Demand:
  examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

The network vertical slice adds the missing structure:

```text
Network:
  node_master.csv
  network_master.csv
```

After this request, the Japanese Rice Case will have the three base elements required for a future PSI run:

```text
Demand
Capacity
Network
```

---

## 3. WOM E2E Hammock Model Requirement

This request must preserve WOM's E2E hammock model.

The network is not a generic edge list only.

It must encode:

```text
Inbound supply-side tree
Outbound demand-side tree
supply_point hinge
MOM / DAD node_character roles
MOM-DAD partner_key alignment
final demand market leaf
global procurement / sales endpoints
```

The intended structure is:

```text
Inbound:
  supply_side_root
    / supply_point
    / MOM role node
    / supplier leaf
    / Procurement_Center

Outbound:
  demand_side_root
    / supply_point
    / DAD role node
    / market leaf
    / Global_Sales_Office
```

For Japanese Rice Case:

```text
RICE_MILL_A = MOM
DC_KANTO = DAD
FARM_REGION_A = SUPPLIER_LEAF
MARKET_TOKYO = MARKET_LEAF
```

---

## 4. Critical Layout Semantics

Please follow these rules exactly.

### 4.1 tree parent-child mapping is primary

The canonical network structure is:

```text
network_master.csv parent_node / child_node relationships
```

Default layout should be derivable from this tree structure.

Do not make `position_group` or `e2e_stage` the primary network definition.

### 4.2 position_group is optional

`position_group` is only a layout hint.

It may help:

```text
cluster related nodes
stabilize sibling ordering
reduce visual edge crossing in dense graphs
```

But it must not replace:

```text
parent_node / child_node tree mapping
```

### 4.3 e2e_stage is optional

`e2e_stage` should be derived from tree depth by default.

It may be used only as an optional override / fixed-rank hint.

It is not:

```text
leadtime
week number
business priority
capacity rank
```

### 4.4 partner_key is an E2E alignment semantic

`partner_key` is more important than a layout hint.

It identifies the MOM-DAD correspondence across the E2E hammock.

For Japanese Rice Case:

```text
RICE_MILL_A:
  node_character = MOM
  partner_key = RICE_CORE

DC_KANTO:
  node_character = DAD
  partner_key = RICE_CORE
```

This is required because MOM/DAD can no longer be reliably paired by node_name prefix.

The test must verify:

```text
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
```

---

## 5. MOM / DAD Prefix Deprecation Policy

MOM and DAD remain canonical WOM roles.

However:

```text
node_name prefix MOM / DAD must not be required.
```

The implementation should detect MOM/DAD from:

```text
node_character
```

not from:

```text
node_name.startswith("MOM")
node_name.startswith("DAD")
```

Legacy prefix fallback may be documented, but this Japanese Rice slice must prove arbitrary names work:

```text
RICE_MILL_A is MOM because node_character = MOM
DC_KANTO is DAD because node_character = DAD
```

---

## 6. NetworkX Non-Scope

Do not remove or refactor NetworkX in this request.

Reason:

```text
This request is about network master data and focused loader tests.
NetworkX dependency retirement is a future GUI / layout-engine task.
```

Future possible design:

```text
docs/design/wom_networkx_dependency_retirement.md
docs/design/wom_e2e_network_layout_engine_without_networkx.md
```

This request must not touch GUI network drawing code.

---

## 7. Files to Add

### 7.1 Required scenario master files

Add:

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

### 7.2 Required implementation files

Add if not existing:

```text
pysi/network/__init__.py
pysi/network/network_master_loader.py
```

### 7.3 Required test file

Add:

```text
tests/test_japanese_rice_network_master_vertical_slice.py
```

---

## 8. node_master.csv Schema

Use this schema:

```csv
scenario_id,node_name,display_name,node_character,node_role,tree_side,product_name,is_root,is_supply_point,is_mom,is_dad,is_leaf,is_supplier_leaf,is_market_leaf,is_procurement_center,is_global_sales_office,position_group,partner_key,e2e_stage,priority,comment
```

Column notes:

```text
node_character:
  canonical WOM role. Use this for MOM/DAD detection.

position_group:
  optional layout hint.

partner_key:
  E2E alignment semantic. Required for the RICE_MILL_A / DC_KANTO MOM-DAD pair.

e2e_stage:
  optional layout override. It may be blank when stage should be derived from tree depth.
```

Boolean values may be parsed from:

```text
true / false
1 / 0
yes / no
```

Use a simple deterministic parser.

---

## 9. node_master.csv Rows

Add exactly these rows unless loader constraints require minor formatting changes:

```csv
scenario_id,node_name,display_name,node_character,node_role,tree_side,product_name,is_root,is_supply_point,is_mom,is_dad,is_leaf,is_supplier_leaf,is_market_leaf,is_procurement_center,is_global_sales_office,position_group,partner_key,e2e_stage,priority,comment
JAPANESE_RICE_VSLICE_001,supply_side_root,Supply side root,SUPPLY_SIDE_ROOT,root,inbound,JAPANESE_RICE_STANDARD,true,false,false,false,false,false,false,false,false,GLOBAL_CONTROL,,0,1,Inbound root
JAPANESE_RICE_VSLICE_001,demand_side_root,Demand side root,DEMAND_SIDE_ROOT,root,outbound,JAPANESE_RICE_STANDARD,true,false,false,false,false,false,false,false,false,GLOBAL_CONTROL,,0,1,Outbound root
JAPANESE_RICE_VSLICE_001,supply_point,Supply point,SUPPLY_POINT,hinge,both,JAPANESE_RICE_STANDARD,false,true,false,false,false,false,false,false,false,RICE_CORE,RICE_CORE,0,1,E2E hammock hinge
JAPANESE_RICE_VSLICE_001,RICE_MILL_A,Rice mill A,MOM,processing,inbound,JAPANESE_RICE_STANDARD,false,false,true,false,false,false,false,false,false,RICE_CORE,RICE_CORE,,1,Rice milling MOM role node
JAPANESE_RICE_VSLICE_001,FARM_REGION_A,Farm region A,SUPPLIER_LEAF,supply_source,inbound,JAPANESE_RICE_STANDARD,false,false,false,false,true,true,false,false,false,RICE_SUPPLY,RICE_CORE,,1,Rice producing region
JAPANESE_RICE_VSLICE_001,Procurement_Center,Procurement Center,PROCUREMENT_CENTER,control,inbound,JAPANESE_RICE_STANDARD,false,false,false,false,true,false,false,true,false,GLOBAL_CONTROL,,,1,Global procurement endpoint
JAPANESE_RICE_VSLICE_001,DC_KANTO,Kanto DC,DAD,distribution,outbound,JAPANESE_RICE_STANDARD,false,false,false,true,false,false,false,false,false,RICE_CORE,RICE_CORE,,1,Distribution DAD role node
JAPANESE_RICE_VSLICE_001,MARKET_TOKYO,Tokyo market,MARKET_LEAF,final_demand,outbound,JAPANESE_RICE_STANDARD,false,false,false,false,true,false,true,false,false,KANTO_MARKET,RICE_CORE,,1,Tokyo final demand leaf
JAPANESE_RICE_VSLICE_001,Global_Sales_Office,Global Sales Office,GLOBAL_SALES_OFFICE,control,outbound,JAPANESE_RICE_STANDARD,false,false,false,false,true,false,false,false,true,GLOBAL_CONTROL,,,1,Global sales endpoint
```

Expected node count:

```text
9
```

---

## 10. network_master.csv Schema

Use this schema:

```csv
scenario_id,product_name,tree_side,parent_node,child_node,edge_type,edge_role,leadtime,process_capa,transport_capacity_qty,unit,priority,calendar_id,comment
```

Column notes:

```text
parent_node / child_node:
  canonical tree structure and primary layout source

tree_side:
  inbound / outbound

leadtime:
  integer weeks for this slice

process_capa:
  optional legacy-compatible planning parameter

transport_capacity_qty:
  optional lane capacity

unit:
  lot
```

---

## 11. network_master.csv Rows

Add exactly these rows unless loader constraints require minor formatting changes:

```csv
scenario_id,product_name,tree_side,parent_node,child_node,edge_type,edge_role,leadtime,process_capa,transport_capacity_qty,unit,priority,calendar_id,comment
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,inbound,supply_side_root,supply_point,root_to_supply_point,hammock_structure,0,,,lot,1,CAL_JP_STD,Inbound root to supply point
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,inbound,supply_point,RICE_MILL_A,supply_point_to_mom,hammock_structure,1,100,,lot,1,CAL_JP_STD,Supply point to rice mill MOM
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,inbound,RICE_MILL_A,FARM_REGION_A,mom_to_supplier_leaf,hammock_structure,1,120,,lot,1,CAL_JP_STD,Rice mill to farm region supplier leaf
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,inbound,FARM_REGION_A,Procurement_Center,supplier_leaf_to_procurement_center,control_endpoint,1,,,lot,1,CAL_JP_STD,Farm region to procurement endpoint
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,outbound,demand_side_root,supply_point,root_to_supply_point,hammock_structure,0,,,lot,1,CAL_JP_STD,Outbound root to supply point
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,outbound,supply_point,DC_KANTO,supply_point_to_dad,hammock_structure,1,90,,lot,1,CAL_JP_STD,Supply point to Kanto DC DAD
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,outbound,DC_KANTO,MARKET_TOKYO,dad_to_market_leaf,hammock_structure,1,90,,lot,1,CAL_JP_STD,Kanto DC to Tokyo market leaf
JAPANESE_RICE_VSLICE_001,JAPANESE_RICE_STANDARD,outbound,MARKET_TOKYO,Global_Sales_Office,market_leaf_to_global_sales,control_endpoint,1,,,lot,1,CAL_JP_STD,Tokyo market to global sales endpoint
```

Expected edge count:

```text
8
```

Expected inbound path:

```text
supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center
```

Expected outbound path:

```text
demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office
```

---

## 12. Implementation Contracts

### 12.1 NetworkNodeRow

If no equivalent exists, implement:

```python
@dataclass(frozen=True)
class NetworkNodeRow:
    scenario_id: str
    node_name: str
    display_name: str
    node_character: str
    node_role: str
    tree_side: str
    product_id: str
    is_root: bool = False
    is_supply_point: bool = False
    is_mom: bool = False
    is_dad: bool = False
    is_leaf: bool = False
    is_supplier_leaf: bool = False
    is_market_leaf: bool = False
    is_procurement_center: bool = False
    is_global_sales_office: bool = False
    position_group: str | None = None
    partner_key: str | None = None
    e2e_stage: int | None = None
    priority: int | None = None
    comment: str | None = None
```

It may expose `product_name` as a compatibility alias for `product_id`.

### 12.2 NetworkEdgeRow

If no equivalent exists, implement:

```python
@dataclass(frozen=True)
class NetworkEdgeRow:
    scenario_id: str
    product_id: str
    tree_side: str
    parent_node: str
    child_node: str
    edge_type: str
    edge_role: str
    leadtime: int
    process_capa: int | float | None = None
    transport_capacity_qty: int | float | None = None
    unit: str = "lot"
    priority: int | None = None
    calendar_id: str | None = None
    comment: str | None = None
```

It may expose `product_name` as a compatibility alias for `product_id`.

---

## 13. Loader Functions

Implement or reuse:

```python
load_network_node_master_csv(path) -> list[NetworkNodeRow]
load_network_edge_master_csv(path) -> list[NetworkEdgeRow]
load_network_master_package(scenario_root) -> dict
```

The package loader may return:

```python
{
    "nodes": list[NetworkNodeRow],
    "edges": list[NetworkEdgeRow],
    "summary": {...},
}
```

Keep this pure.

Do not mutate planner state.

Do not build a full PySI tree in this slice.

Do not call GUI code.

Do not use NetworkX.

---

## 14. Helper Functions

Add small pure helpers if useful:

```python
find_node(nodes, node_name) -> NetworkNodeRow | None
edges_by_tree_side(edges, tree_side) -> list[NetworkEdgeRow]
has_path(edges, path: list[str], tree_side: str) -> bool
derive_tree_depths(edges, root_node, tree_side) -> dict[str, int]
```

`derive_tree_depths(...)` should prove that a default layout stage can be derived from tree structure.

It should not use NetworkX.

A simple adjacency dict / BFS is enough.

---

## 15. V0R8 Attribute Preservation

Do not implement the full V0R8 master migration in this request.

However, preserve these fields in the design / loader where present:

```text
leadtime
process_capa
```

and keep naming compatible with old product tree concepts:

```text
product_name
parent_node
child_node
```

The request must not lose sight of future fields documented in the design:

```text
lot_size
long_vacation_weeks
LT_boat
LT_air
LT_qourier
weeks_year
SS_days
TAX_currency_condition
HS_code
customs_tariff_rate
price_elasticity
cost_standard_flag
AR_lead_time
AP_lead_time
PSI_graph_flag
buffering_stock_flag
```

Do not implement all of them now.

Just do not design the loader in a way that blocks them later.

---

## 16. Required Tests

Add:

```text
tests/test_japanese_rice_network_master_vertical_slice.py
```

### 16.1 Master files exist and load

Assert:

```text
node_master.csv exists
network_master.csv exists
node loader returns 9 nodes
edge loader returns 8 edges
```

### 16.2 Node characters are correct

Assert:

```text
supply_point.node_character == SUPPLY_POINT
RICE_MILL_A.node_character == MOM
DC_KANTO.node_character == DAD
FARM_REGION_A.node_character == SUPPLIER_LEAF
MARKET_TOKYO.node_character == MARKET_LEAF
Procurement_Center exists
Global_Sales_Office exists
```

### 16.3 MOM / DAD are detected from node_character

Assert:

```text
RICE_MILL_A.is_mom is True
DC_KANTO.is_dad is True
```

Do not infer these from node_name prefixes.

The names intentionally do not start with MOM / DAD.

### 16.4 partner_key aligns MOM and DAD

Assert:

```text
RICE_MILL_A.partner_key == "RICE_CORE"
DC_KANTO.partner_key == "RICE_CORE"
```

Also assert:

```text
MOM/DAD partner_key alignment exists for RICE_CORE
```

### 16.5 Inbound hammock path exists

Assert path:

```text
supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center
```

for:

```text
tree_side = inbound
```

### 16.6 Outbound hammock path exists

Assert path:

```text
demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office
```

for:

```text
tree_side = outbound
```

### 16.7 MARKET_TOKYO is outbound final demand leaf

Assert:

```text
MARKET_TOKYO.is_leaf is True
MARKET_TOKYO.is_market_leaf is True
MARKET_TOKYO.tree_side == "outbound"
```

### 16.8 Capacity and demand nodes align with network

From existing scenario semantics, assert network includes:

```text
capacity nodes:
  FARM_REGION_A
  RICE_MILL_A
  DC_KANTO

demand node:
  MARKET_TOKYO
```

Do not reload capacity/demand files unless simple.

It is sufficient to assert the node names exist in node master.

### 16.9 Default layout depth can be derived from tree

Using pure helper:

```python
derive_tree_depths(edges, root_node="supply_side_root", tree_side="inbound")
derive_tree_depths(edges, root_node="demand_side_root", tree_side="outbound")
```

Assert representative depths:

```text
inbound:
  supply_side_root = 0
  supply_point = 1
  RICE_MILL_A = 2
  FARM_REGION_A = 3
  Procurement_Center = 4

outbound:
  demand_side_root = 0
  supply_point = 1
  DC_KANTO = 2
  MARKET_TOKYO = 3
  Global_Sales_Office = 4
```

This proves:

```text
tree parent-child mapping is sufficient for default layout stage derivation.
```

### 16.10 position_group and e2e_stage are optional

Assert:

```text
RICE_MILL_A.e2e_stage is None
DC_KANTO.e2e_stage is None
```

or equivalent blank parsing.

Assert that tree depth derivation still works.

This proves:

```text
e2e_stage is optional override, not required for the tree.
```

---

## 17. Test Commands

Run focused network vertical slice test:

```bat
python -m pytest tests/test_japanese_rice_network_master_vertical_slice.py
```

Run Japanese Rice capacity and demand vertical slice tests:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
python -m pytest tests/test_japanese_rice_demand_master_vertical_slice.py
```

Run related capacity diagnostic tests:

```bat
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

## 18. Safety Boundaries

Expected changed / added files:

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
pysi/network/__init__.py
pysi/network/network_master_loader.py
tests/test_japanese_rice_network_master_vertical_slice.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Do not remove NetworkX.

Do not wire into GUI.

Do not run full PSI.

Do not implement monthly demand compatibility.

Do not implement cost / tariff / price loaders in this request.

---

## 19. Acceptance Criteria

This request is complete when:

```text
Japanese Rice node_master.csv is added
Japanese Rice network_master.csv is added
minimal network loader is added or reused
node loader returns 9 nodes
edge loader returns 8 edges
node_character roles are loaded
MOM/DAD are detected from node_character, not node_name prefix
supply_point is represented as SUPPLY_POINT
MARKET_TOKYO is represented as outbound MARKET_LEAF
RICE_MILL_A is represented as MOM
DC_KANTO is represented as DAD
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
inbound hammock path exists
outbound hammock path exists
default layout depth can be derived from tree parent-child structure
position_group remains optional
e2e_stage remains optional / override only
capacity nodes exist in network
demand node exists as outbound leaf
focused tests pass
Japanese Rice capacity and demand tests still pass
capacity diagnostic / regression tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX dependency untouched
full PSI run not required
```

---

## 20. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where were node_master.csv and network_master.csv added?
How many nodes and edges do they contain?
Where are NetworkNodeRow and NetworkEdgeRow implemented or reused?
What loader functions were added or reused?
Does RICE_MILL_A use node_character=MOM without MOM prefix?
Does DC_KANTO use node_character=DAD without DAD prefix?
Do RICE_MILL_A and DC_KANTO share partner_key=RICE_CORE?
Does supply_point exist as SUPPLY_POINT?
Does the inbound hammock path exist?
Does the outbound hammock path exist?
Can default layout depth be derived from parent-child tree structure?
Are position_group and e2e_stage optional?
Did you change planner behavior?
Did you change GUI layout?
Did you remove or modify NetworkX dependency?
Did you run a full PSI plan?
Which tests passed?
```

---

## 21. Development Meaning

This request gives Japanese Rice Case its WOM E2E network skeleton.

After completion:

```text
Capacity:
  what supply can do

Demand:
  what final market wants

Network:
  how WOM connects the two through an E2E hammock
```

This is not yet a PSI run.

It is the structural bridge that makes the first PSI run possible.

The key design victory is:

```text
WOM node semantics are no longer locked into node_name prefixes.
MOM/DAD roles are carried by node_character.
MOM-DAD alignment is carried by partner_key.
Tree layout is derived from parent-child structure.
```

This prepares the next milestone:

```text
Japanese Rice first PSI run vertical slice
