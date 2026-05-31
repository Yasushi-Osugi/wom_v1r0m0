# Japanese Rice Network Master Vertical Slice — Revised for WOM E2E Hammock Model

**Version:** v0r3 revised  
**Date:** 2026-05-31  
**Status:** Revised design memo  
**Target path:** `docs/design/japanese_rice_network_master_vertical_slice.md`

**Strategic role:** WOM modeling entrance design for E2E network / node / route master data  
**Primary case:** Japanese Rice Case  
**Initial master focus:** WOM E2E network master, node character master, tree edge master, and legacy PySI V0R8 attribute preservation  
**Initial execution target:** connect capacity rows and demand anchored lots through a WOM-compatible inbound/outbound hammock model

---

## 1. Purpose

This revised memo updates the Japanese Rice network master vertical slice to reflect the original WOM / PySI V0R8 E2E network concept more accurately.

The simple physical chain:

```text
FARM_REGION_A -> RICE_MILL_A -> DC_KANTO -> MARKET_TOKYO
```

is useful as business intuition, but it is not sufficient as a generic WOM model master definition.

WOM's E2E network is a hammock-shaped planning model with:

```text
Inbound / supply side
Outbound / demand side
supply_point as the central hinge
```

This memo separates:

```text
physical business nodes
product-specific planning nodes
tree-side structure
parent-child network master
node_character / node_role semantics
E2E graph layout semantics
legacy PySI V0R8 compatibility attributes
```

The design goal is to use Japanese Rice Case as the first visible network vertical slice while preserving the general WOM E2E network model.

---

## 2. Correct WOM E2E Network Basic Structure

The intended WOM hammock structure is:

```text
Inbound:
  supply_side_root
    / supply_point
    / MOM role node
    / ...
    / supplier_leaf_nodes
    / Procurement_Center

Outbound:
  demand_side_root
    / supply_point
    / DAD role node
    / ...
    / market leaf
    / Global_Sales_Office
```

Important points:

```text
1. This is a WOM planning-tree / E2E graph hierarchy.
2. It is not always identical to physical material-flow direction.
3. supply_point is the central hinge connecting inbound and outbound views.
4. MOM and DAD are WOM node_character roles, not mandatory node_name prefixes.
5. Procurement_Center and Global_Sales_Office are global management endpoints.
```

The Japanese Rice network master must encode this structure.

---

## 3. Physical Layer vs Planning Layer

### 3.1 Physical layer

Physical nodes are real or representative business locations:

```text
FARM_REGION_A
RICE_MILL_A
DC_KANTO
MARKET_TOKYO
Procurement_Center
Global_Sales_Office
```

### 3.2 Planning layer

Planning nodes are product-specific and tree-side-specific.

For example:

```text
product_name = JAPANESE_RICE_STANDARD
tree_side = outbound
physical node = MARKET_TOKYO
```

represents:

```text
JAPANESE_RICE_STANDARD outbound leaf plan_node MARKET_TOKYO
```

This is where demand lots attach:

```python
plan_node.psi4demand[week]["S"] = list[lot_ID]
```

### 3.3 Why this separation matters

A physical node may appear in multiple product-specific planning trees.

A node name should not carry all planning semantics by itself.

Planning semantics should come from explicit fields:

```text
product_name
tree_side
node_character
node_role
is_leaf
is_mom
is_dad
is_supply_point
```

rather than from hard-coded node_name prefixes.

---

## 4. MOM / DAD Role Policy

### 4.1 Legacy behavior

In original PySI V0R8, node names often used prefixes:

```text
MOMxxx
DADxxx
```

Role could therefore be inferred as:

```text
node_name startswith("MOM") -> MOM node
node_name startswith("DAD") -> DAD node
```

### 4.2 Revised WOM policy

The revised WOM master definition should not require these prefixes.

Correct policy:

```text
MOM / DAD are canonical WOM node_character roles.
MOM / DAD should not be mandatory node_name prefixes.
```

Recommended detection order:

```text
1. Read node_character.
2. If missing, read node_role / node_type.
3. If still missing, use legacy node_name prefix as fallback.
4. If fallback is used, report a diagnostic warning.
```

Preferred definitions:

```text
node_name = RICE_MILL_A
node_character = MOM

node_name = DC_KANTO
node_character = DAD
```

---

## 5. supply_point Policy

`supply_point` is the central hinge of the WOM hammock model.

For compatibility and clarity:

```text
node_name = supply_point
node_character = SUPPLY_POINT
```

should be used in the first vertical slice.

Future extension may allow a different display name, but the canonical structural role must remain explicit:

```text
canonical_node_key = supply_point
node_character = SUPPLY_POINT
```

---

## 6. Primary Layout Principle: Tree Mapping First

This section is the key correction.

The default E2E graph layout should be computed from the actual tree structure.

Primary layout source:

```text
parent_node / child_node relationships in network_master.csv
```

This means:

```text
depth
sibling order
subtree width
leaf distribution
```

should be derived from the inbound and outbound planning trees.

The default layout should follow the tree naturally and minimize edge crossing by spacing child subtrees.

This preserves the original PySI V0R8 spirit:

```text
Map the tree parent-child structure directly,
then adjust vertical spacing between nodes at the same depth.
```

Therefore:

```text
tree parent-child mapping is canonical.
position_group is not the primary source of layout.
e2e_stage is not the primary source of layout.
```

---

## 7. E2E Graph Positioning Metadata

The network master may still include layout metadata, but it must be interpreted carefully.

### 7.1 tree_side

Meaning:

```text
Which WOM planning-tree view the node or edge belongs to.
```

Recommended values:

```text
inbound
outbound
both
control
```

Usage:

```text
inbound:
  supply-side tree / procurement-to-MOM-side planning view

outbound:
  demand-side tree / DAD-to-market-side planning view

both:
  shared structural node or connector, especially supply_point

control:
  global management endpoint such as Procurement_Center or Global_Sales_Office
```

`tree_side` is a core semantic field.

It is not merely a layout hint.

### 7.2 e2e_stage

Meaning:

```text
E2E graph rank / stage for layout.
```

Important rule:

```text
e2e_stage should be derived from tree depth by default.
```

It may be stored as an optional override only when stable visual alignment is required.

It is not:

```text
lead time
week number
capacity rank
business priority
```

Recommended interpretation:

```text
derived_e2e_stage:
  computed from parent-child tree depth

e2e_stage:
  optional override / fixed rank for graph layout
```

### 7.3 position_group

Meaning:

```text
Optional layout hint for grouping nodes within the same derived or overridden stage.
```

Critical rule:

```text
position_group must not replace parent-child tree mapping.
```

Use it only to:

```text
stabilize sibling ordering
cluster related nodes
reduce visual edge crossing in dense graphs
keep product-family or region-family nodes visually close
```

It is not a business role.

It is not a substitute for node_character.

It is not the primary graph structure.

Recommended interpretation:

```text
position_group = optional sibling ordering / clustering hint
```

### 7.4 partner_key

Meaning:

```text
E2E alignment semantic that links related MOM-side and DAD-side nodes.
```

This is more important than a mere layout hint.

`partner_key` identifies the correspondence across the hammock.

Example:

```text
RICE_MILL_A:
  node_character = MOM
  partner_key = RICE_CORE

DC_KANTO:
  node_character = DAD
  partner_key = RICE_CORE
```

This means:

```text
RICE_MILL_A and DC_KANTO are an E2E aligned MOM-DAD pair.
```

Why it matters:

```text
1. MOM and DAD cannot be reliably paired by name if node_name prefixes are removed.
2. The E2E graph needs this pairing to place corresponding nodes horizontally.
3. Future logic may use this alignment to compare MOM-side demand/supply pressure and DAD-side distribution behavior.
```

Therefore:

```text
partner_key is an E2E alignment semantic.
It is stronger than position_group.
```

Recommended usage:

```text
partner_key:
  required for MOM/DAD pair alignment when such pairing exists

position_group:
  optional visual clustering hint

e2e_stage:
  derived by default, optional override
```

---

## 8. Recommended Layout Calculation Order

Recommended E2E layout algorithm:

```text
1. Build inbound and outbound trees from parent_node / child_node.
2. Identify supply_point.
3. Compute depth from supply_point or each tree root.
4. Compute subtree width and sibling order from tree structure.
5. Place nodes by tree_side and derived depth.
6. Use partner_key to align MOM/DAD counterpart nodes.
7. Use position_group only to stabilize ordering within the same stage.
8. Use e2e_stage only as optional override.
9. Use node_geo only for map view, not default hammock layout.
```

This preserves PySI V0R8's direct tree mapping behavior while giving the new WOM master enough metadata for stable generalization.

---

## 9. NetworkX Dependency Policy

Current GUI code appears to use NetworkX mainly as:

```text
graph container
draw_networkx_* helper
simple in_degree / out_edges utility
```

The layout itself is already supplied by WOM logic:

```text
pos_E2E = make_E2E_positions(...)
```

Therefore, NetworkX can be removed in the future.

However, NetworkX removal should not be part of this Japanese Rice network master vertical slice.

Recommended policy:

```text
WOM network master and layout model should not depend on NetworkX.
NetworkX may remain as an optional rendering adapter during migration.
```

Future design topic:

```text
docs/design/wom_networkx_dependency_retirement.md
```

or:

```text
docs/design/wom_e2e_network_layout_engine_without_networkx.md
```

Recommended migration:

```text
1. Define WOM network master and canonical rows.
2. Implement pure tree-based E2E layout engine.
3. Render with matplotlib directly using pos dict and edge list.
4. Keep optional to_networkx(...) adapter only if needed.
5. Remove direct NetworkX dependency from GUI when stable.
```

This memo does not request NetworkX removal.

---

## 10. Japanese Rice Node Character Mapping

The first Japanese Rice network should define:

```text
supply_side_root:
  node_character = SUPPLY_SIDE_ROOT
  tree_side = inbound

demand_side_root:
  node_character = DEMAND_SIDE_ROOT
  tree_side = outbound

supply_point:
  node_character = SUPPLY_POINT
  tree_side = both

RICE_MILL_A:
  node_character = MOM
  tree_side = inbound
  partner_key = RICE_CORE

DC_KANTO:
  node_character = DAD
  tree_side = outbound
  partner_key = RICE_CORE

FARM_REGION_A:
  node_character = SUPPLIER_LEAF
  tree_side = inbound

Procurement_Center:
  node_character = PROCUREMENT_CENTER
  tree_side = inbound or control

MARKET_TOKYO:
  node_character = MARKET_LEAF
  tree_side = outbound

Global_Sales_Office:
  node_character = GLOBAL_SALES_OFFICE
  tree_side = outbound or control
```

The business flow remains intuitive:

```text
FARM_REGION_A -> RICE_MILL_A -> DC_KANTO -> MARKET_TOKYO
```

But the WOM master must also encode the E2E hammock roles.

---

## 11. Revised Japanese Rice Hammock Structure

Recommended inbound tree view:

```text
supply_side_root
    -> supply_point
        -> RICE_MILL_A          [node_character = MOM]
            -> FARM_REGION_A    [node_character = SUPPLIER_LEAF]
                -> Procurement_Center
```

Recommended outbound tree view:

```text
demand_side_root
    -> supply_point
        -> DC_KANTO             [node_character = DAD]
            -> MARKET_TOKYO     [node_character = MARKET_LEAF]
                -> Global_Sales_Office
```

This structure supports:

```text
inbound bottleneck / procurement view
outbound allocation / final demand view
E2E graph hammock positioning
product-specific plan_node generation
demand leaf anchoring
future MOM-DAD balance visualization
```

---

## 12. Legacy PySI V0R8 Master Attributes to Preserve

The original PySI V0R8 master files contain more information than a simple network edge list.

The new WOM master family must preserve those attributes.

### 12.1 product_tree_inbound / product_tree_outbound attributes

Observed columns:

```text
Product_name
Parent_node
Child_node
child_node_name
lot_size
leadtime
process_capa
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

These attributes should not be lost.

### 12.2 sku_S_month_data / sku_P_month_data attributes

Observed columns:

```text
product_name
node_name
year
m1 ... m12
```

These are legacy-compatible monthly demand / supply source data.

### 12.3 sku_cost_table_inbound / sku_cost_table_outbound attributes

Observed columns:

```text
product_name
node_name
price_sales_shipped
cost_total
profit
marketing_promotion
sales_admin_cost
SGA_total
logistics_costs
warehouse_cost
direct_materials_costs
tariff_cost
purchase_total_cost
prod_indirect_labor
prod_indirect_others
direct_labor_costs
depreciation_others
manufacturing_overhead
```

These should map to cost / price / KPI masters.

### 12.4 tariff_table attributes

Observed columns:

```text
product_name
from_node
to_node
tariff_rate
```

These should map to lane tariff master or edge tariff attributes.

### 12.5 offering_price_ASIS_TOBE attributes

Observed columns:

```text
product_name
node_name
offering_price_ASIS
offering_price_TOBE
```

These should map to scenario offering price master.

### 12.6 node_geo attributes

Observed columns:

```text
node_name
lat
lon
```

These should map to node_geo master.

---

## 13. Proposed New WOM Master Family

The new WOM master definition should be a master family.

Recommended family:

```text
node_master.csv
network_master.csv
node_plan_parameter_master.csv
node_geo.csv
capacity_master.csv
demand_master.csv
cost_profile_master.csv
tariff_master.csv
offering_price_master.csv
monthly_demand_supply_master.csv
```

### 13.1 node_master.csv

Purpose:

```text
Define physical / logical node identity and WOM node_character.
```

Core columns:

```csv
scenario_id,node_name,display_name,node_character,node_role,tree_side,product_name,is_root,is_supply_point,is_mom,is_dad,is_leaf,is_supplier_leaf,is_market_leaf,is_procurement_center,is_global_sales_office,position_group,partner_key,e2e_stage,priority,comment
```

Clarification:

```text
position_group and e2e_stage are optional layout hints.
partner_key is an E2E alignment semantic.
```

### 13.2 network_master.csv

Purpose:

```text
Define parent-child tree relationships and E2E graph structure.
```

Core columns:

```csv
scenario_id,product_name,tree_side,parent_node,child_node,edge_type,edge_role,leadtime,process_capa,transport_capacity_qty,unit,priority,calendar_id,comment
```

This master is the canonical source for tree mapping and default layout.

### 13.3 node_plan_parameter_master.csv

Purpose:

```text
Preserve V0R8 planning parameters from product_tree files.
```

Core columns:

```csv
scenario_id,product_name,node_name,tree_side,lot_size,leadtime,process_capa,long_vacation_weeks,LT_boat,LT_air,LT_qourier,weeks_year,SS_days,TAX_currency_condition,HS_code,customs_tariff_rate,price_elasticity,cost_standard_flag,AR_lead_time,AP_lead_time,PSI_graph_flag,buffering_stock_flag
```

### 13.4 node_geo.csv

Purpose:

```text
Preserve node coordinates for map / geographic view.
```

Core columns:

```csv
node_name,lat,lon
```

### 13.5 capacity_master.csv

Already started for Japanese Rice Case.

### 13.6 demand_master.csv

Already started for Japanese Rice Case.

### 13.7 cost_profile_master.csv

Purpose:

```text
Preserve cost structure by product and node.
```

### 13.8 tariff_master.csv

Purpose:

```text
Define product / lane tariff rate.
```

Core columns:

```csv
scenario_id,product_name,from_node,to_node,tariff_rate,comment
```

### 13.9 offering_price_master.csv

Purpose:

```text
Define ASIS / TOBE offering prices.
```

Core columns:

```csv
scenario_id,product_name,node_name,offering_price_ASIS,offering_price_TOBE,comment
```

### 13.10 monthly_demand_supply_master.csv

Purpose:

```text
Preserve legacy monthly demand / supply data source.
```

Core columns:

```csv
scenario_id,product_name,node_name,signal_type,year,m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12
```

Where:

```text
signal_type = S or P
```

This can unify:

```text
sku_S_month_data.csv
sku_P_month_data.csv
```

without losing legacy compatibility.

---

## 14. Immediate Japanese Rice Network Slice Scope

For the immediate Japanese Rice network vertical slice, do not implement the full master family.

Immediate scope should be:

```text
node_master.csv
network_master.csv
pysi/network/network_master_loader.py
tests/test_japanese_rice_network_master_vertical_slice.py
```

The full V0R8 attribute mapping should remain documented and protected for future implementation.

This avoids turning the network slice into a large master migration project.

---

## 15. Recommended node_master.csv for Japanese Rice

Recommended file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
```

Recommended rows:

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

Note:

```text
e2e_stage may be blank for nodes whose stage should be derived from the tree.
```

---

## 16. Recommended network_master.csv for Japanese Rice

Recommended file:

```text
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

Recommended rows:

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

Important structural facts:

```text
supply_point appears in both inbound and outbound.
RICE_MILL_A is the MOM node.
DC_KANTO is the DAD node.
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE.
MARKET_TOKYO is the outbound market leaf.
Procurement_Center and Global_Sales_Office are global endpoints.
```

---

## 17. Legacy PySI V0R8 Compatibility Rules

Future loaders should support compatibility with legacy columns:

```text
Product_name -> product_name
Parent_node -> parent_node
Child_node -> child_node
child_node_name -> child_node_display_name
process_capa -> process_capacity_qty
LT_qourier -> LT_courier alias, while preserving original typo compatibility
```

The legacy spelling:

```text
LT_qourier
```

should not be silently lost.

It can be preserved and optionally normalized as:

```text
LT_courier
```

with alias support.

---

## 18. Test Strategy

Recommended focused test file:

```text
tests/test_japanese_rice_network_master_vertical_slice.py
```

Tests should cover:

```text
node_master.csv exists
network_master.csv exists
node loader returns expected nodes
network loader returns expected edges
RICE_MILL_A has node_character = MOM
DC_KANTO has node_character = DAD
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
supply_point has node_character = SUPPLY_POINT
MARKET_TOKYO has node_character = MARKET_LEAF and is_leaf = true
FARM_REGION_A has node_character = SUPPLIER_LEAF
Procurement_Center exists
Global_Sales_Office exists
inbound path supply_side_root -> supply_point -> RICE_MILL_A -> FARM_REGION_A -> Procurement_Center exists
outbound path demand_side_root -> supply_point -> DC_KANTO -> MARKET_TOKYO -> Global_Sales_Office exists
default layout can be derived from parent-child tree structure
position_group is optional and not required to build the tree
e2e_stage is optional and not required to build the tree
capacity nodes exist in network
demand node exists as outbound leaf
V0R8 product_tree attributes are represented in the revised master family design
```

Do not require full PSI planning execution.

Do not require GUI rendering.

Do not require NetworkX.

---

## 19. Acceptance Criteria for Future Codex Request

The future implementation is acceptable when:

```text
Japanese Rice node_master.csv is added
Japanese Rice network_master.csv is added
minimal network loader is added or reused
node_character roles are loaded
MOM/DAD are detected from node_character, not node_name prefix
legacy prefix fallback policy is documented
supply_point is represented as SUPPLY_POINT
MARKET_TOKYO is represented as outbound MARKET_LEAF
RICE_MILL_A is represented as MOM
DC_KANTO is represented as DAD
RICE_MILL_A and DC_KANTO share partner_key = RICE_CORE
inbound hammock path exists
outbound hammock path exists
default layout can be derived from tree parent-child structure
position_group remains optional
e2e_stage remains optional / override only
V0R8 attributes are not lost in design mapping
focused tests pass
planner behavior unchanged
GUI layout unchanged
full PSI run not required
NetworkX dependency is not touched in this slice
```

---

## 20. Non-Goals

This design does not yet implement:

```text
full PSI run
MOM balance graph
optimization
GUI wiring
scenario runner wiring
monthly S_month_data compatibility
cost profile loader
tariff loader
offering price loader
node_geo map rendering
NetworkX dependency retirement
```

It only defines the network / node master entrance with WOM hammock semantics.

---

## 21. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_network_master_vertical_slice_request.md
```

Scope:

```text
add node_master.csv
add network_master.csv
add minimal network loader
add focused tests
preserve WOM hammock semantics
detect MOM/DAD from node_character
verify partner_key MOM/DAD alignment
derive layout stage from tree by default
treat position_group as optional
treat e2e_stage as optional override
do not modify planner
do not modify GUI
do not remove NetworkX
do not run full PSI
```

---

## 22. Summary

The Japanese Rice Case now has:

```text
capacity_master.csv:
  supply capability entrance

demand_master.csv:
  final demand lot source
```

The next required piece is:

```text
node_master.csv / network_master.csv:
  WOM E2E hammock structure
```

This revised design clarifies that WOM network master definition must include:

```text
inbound / outbound hammock structure
supply_point hinge
MOM / DAD as node_character roles
MOM-DAD partner_key alignment
tree parent-child mapping as primary layout source
position_group as optional layout hint
e2e_stage as optional override
legacy PySI V0R8 attribute preservation
```

Once this network vertical slice is complete, the Japanese Rice Case will have the three base elements for a first meaningful PSI run:

```text
Demand
Capacity
Network
```
