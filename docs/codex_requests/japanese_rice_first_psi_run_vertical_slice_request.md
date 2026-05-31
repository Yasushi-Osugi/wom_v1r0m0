# Codex Request: Japanese Rice First PSI Run Vertical Slice

**Version:** v0r1  
**Date:** 2026-05-31  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/japanese_rice_first_psi_run_vertical_slice_request.md`

**Parent design doc:**

```text
docs/design/japanese_rice_first_psi_run_vertical_slice.md
```

**Related design / completion docs:**

```text
docs/design/japanese_rice_network_master_vertical_slice_completion.md
docs/design/japanese_rice_network_master_vertical_slice.md
docs/design/japanese_rice_demand_master_vertical_slice_completion.md
docs/design/japanese_rice_capacity_master_vertical_slice_completion.md
```

**Related existing tests:**

```text
tests/test_japanese_rice_network_master_vertical_slice.py
tests/test_japanese_rice_demand_master_vertical_slice.py
tests/test_japanese_rice_capacity_master_vertical_slice.py
```

**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please implement the Japanese Rice first PSI run vertical slice.

This request should add a small, deterministic, diagnostic-first PSI smoke runner that integrates the already completed Japanese Rice vertical slices:

```text
Capacity
Demand
Network
```

The first run should prove:

```text
capacity_master.csv loads
demand_master.csv loads
node_master.csv / network_master.csv load
285 DemandAnchoredLots are generated
demand lots attach to MARKET_TOKYO leaf plan_node compatibility shape
capacity runtime context attaches
inbound / outbound WOM hammock paths exist
simple weekly balance summary is computed
```

This is not a full canonical PSI planner implementation.

This is not a GUI feature.

This is not a NetworkX refactor.

This is a deterministic integration smoke run.

---

## 2. Strategic Context

The Japanese Rice Case now has the three foundational model entrances.

### Capacity

```text
examples/scenarios/japanese_rice_vslice_001/masters/capacity_master.csv
```

Completed behavior:

```text
capacity_master.csv
    ↓
WeeklyCapacityRow
    ↓
env.capacity_weekly_rows
    ↓
capacity runtime attachment
    ↓
capacity diagnostics
```

### Demand

```text
examples/scenarios/japanese_rice_vslice_001/masters/demand_master.csv
```

Completed behavior:

```text
demand_master.csv
    ↓
WeeklyDemandRow
    ↓
DemandAnchoredLot
    ↓
MARKET_TOKYO outbound leaf plan_node compatibility shape
    ↓
psi4demand[week]["S"]
```

### Network

```text
examples/scenarios/japanese_rice_vslice_001/masters/node_master.csv
examples/scenarios/japanese_rice_vslice_001/masters/network_master.csv
```

Completed behavior:

```text
node_master.csv / network_master.csv
    ↓
WOM E2E hammock structure
    ↓
inbound / outbound paths
    ↓
MOM-DAD partner_key alignment
```

This request connects these three completed slices into a first deterministic PSI smoke result.

---

## 3. Scope Control

### In scope

Implement a pure runner and focused test:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

The runner should:

```text
load Japanese Rice network masters
load Japanese Rice demand master
generate DemandAnchoredLots
attach lots to MARKET_TOKYO leaf psi4demand compatibility shape
load Japanese Rice capacity master to env
apply capacity runtime attachment preflight
verify network alignment
verify demand/network alignment
verify capacity/network alignment
compute simple weekly balance summary
return deterministic diagnostic dict
```

### Out of scope

Do not implement:

```text
full WOM planner
full original PySI V0R8 monthly demand compatibility
leadtime-shifted full PSI propagation
inventory carry-over
backlog / CO calculation
optimization
cost / price / profit simulation
GUI wiring
NetworkX dependency retirement
MOM balance chart rendering
scenario runner integration beyond isolated helper
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

---

## 4. Implementation Target

Add:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

If `pysi/runners/__init__.py` exists and project style requires export, update it minimally.

If `pysi/runners` does not exist, create it with an empty or minimal `__init__.py`.

Keep the runner callable from tests.

Do not require CLI execution.

---

## 5. Proposed API

Implement:

```python
run_japanese_rice_first_psi_vslice(
    scenario_root: str | Path,
) -> dict
```

Recommended default scenario root in tests:

```text
examples/scenarios/japanese_rice_vslice_001
```

The runner should not depend on current working directory except through the supplied `scenario_root`.

---

## 6. Existing Functions to Reuse

Reuse existing loaders/helpers wherever possible.

### Capacity

Expected existing functions:

```python
load_capacity_weekly_rows_to_env(...)
apply_capacity_runtime_attachment_preflight(...)
build_capacity_runtime_attachment_diagnostic(...)
build_capacity_weekly_rows_source_diagnostic(...)
```

Use the already implemented capacity loader and runtime attachment helpers.

Do not duplicate capacity CSV parsing.

### Demand

Expected existing functions:

```python
load_weekly_demand_master_csv(...)
generate_demand_anchored_lots(...)
attach_demand_lots_to_leaf_plan_node_psi4demand(...)
```

Use the already implemented demand loader and lot generator.

Do not duplicate demand CSV parsing.

### Network

Expected existing functions:

```python
load_network_node_master_csv(...)
load_network_edge_master_csv(...)
load_network_master_package(...)
find_node(...)
edges_by_tree_side(...)
has_path(...)
derive_tree_depths(...)
```

Use the already implemented network loader and helpers.

Do not use NetworkX.

---

## 7. Expected Scenario Constants

Use:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
scenario_root = examples/scenarios/japanese_rice_vslice_001
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

Expected demand node:

```text
MARKET_TOKYO
```

Expected MOM node:

```text
RICE_MILL_A
```

Expected DAD node:

```text
DC_KANTO
```

Expected supply source node:

```text
FARM_REGION_A
```

Expected partner key:

```text
RICE_CORE
```

---

## 8. Required Loading Sequence

The runner should follow this sequence:

```text
1. Load network master package.
2. Load demand master.
3. Generate demand anchored lots.
4. Attach demand lots to MARKET_TOKYO leaf plan_node compatibility shape.
5. Load capacity rows into env.capacity_weekly_rows.
6. Apply capacity runtime attachment preflight.
7. Validate cross-master alignment.
8. Compute simple weekly balance summary.
9. Return deterministic diagnostic dict.
```

A simple `types.SimpleNamespace()` env is acceptable for capacity source/preflight helpers if that matches existing tests.

---

## 9. Demand Requirements

Expected demand rows:

```text
3
```

Expected demand lots:

```text
285
```

Expected weekly demand lot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

The runner should confirm that the demand attachment represents:

```text
JAPANESE_RICE_STANDARD
  MARKET_TOKYO
    psi4demand
      week
        S = list[lot_ID]
```

The target remains the compatibility meaning:

```python
MARKET_TOKYO.plan_node.psi4demand[week]["S"] = list[lot_ID]
```

Do not create or require full PlanNode objects unless already trivial.

---

## 10. Capacity Requirements

Expected capacity rows:

```text
9
```

Expected capacity facts:

```text
FARM_REGION_A P capacity = 120 lots/week
RICE_MILL_A P capacity = 100 lots/week
DC_KANTO S capacity = 90 lots/week
```

Expected weeks:

```text
2027-W40
2027-W41
2027-W42
```

The runner should apply:

```python
apply_capacity_runtime_attachment_preflight(env)
```

Expected:

```text
runtime_attachment_applied = True
input_row_count = 9
```

or equivalent fields available from the preflight result.

Do not change capacity enforcement behavior.

---

## 11. Network Requirements

Expected node count:

```text
9
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

Expected role checks:

```text
supply_point.node_character = SUPPLY_POINT
RICE_MILL_A.node_character = MOM
DC_KANTO.node_character = DAD
MARKET_TOKYO.node_character = MARKET_LEAF
FARM_REGION_A.node_character = SUPPLIER_LEAF
```

Expected MOM/DAD alignment:

```text
RICE_MILL_A.partner_key = RICE_CORE
DC_KANTO.partner_key = RICE_CORE
```

The runner should verify these and return the result in the diagnostic.

---

## 12. Cross-Master Alignment Requirements

The runner should verify:

```text
demand node MARKET_TOKYO exists in node_master
capacity nodes FARM_REGION_A, RICE_MILL_A, DC_KANTO exist in node_master
all loaded rows use product_name = JAPANESE_RICE_STANDARD
all loaded rows use scenario_id = JAPANESE_RICE_VSLICE_001
```

If mismatch handling is implemented, it should be deterministic and non-crashing for this happy path.

For this slice, happy-path tests are enough.

---

## 13. Simple Weekly Balance Summary

Compute a deterministic same-week smoke balance.

This is not final PSI.

It does not apply leadtime, inventory, backlog, or optimization.

### 13.1 Demand pressure series

Use demand lot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

### 13.2 DC_KANTO balance

Use:

```text
DC_KANTO S capacity = 90
```

Expected:

```text
2027-W40:
  demand = 80
  capacity = 90
  balance = +10
  shortage = 0

2027-W41:
  demand = 95
  capacity = 90
  balance = -5
  shortage = 5

2027-W42:
  demand = 110
  capacity = 90
  balance = -20
  shortage = 20
```

### 13.3 RICE_MILL_A balance

Use:

```text
RICE_MILL_A P capacity = 100
```

Expected:

```text
2027-W40:
  demand = 80
  capacity = 100
  balance = +20
  shortage = 0

2027-W41:
  demand = 95
  capacity = 100
  balance = +5
  shortage = 0

2027-W42:
  demand = 110
  capacity = 100
  balance = -10
  shortage = 10
```

### 13.4 FARM_REGION_A balance

Use:

```text
FARM_REGION_A P capacity = 120
```

Expected:

```text
2027-W40:
  demand = 80
  capacity = 120
  balance = +40
  shortage = 0

2027-W41:
  demand = 95
  capacity = 120
  balance = +25
  shortage = 0

2027-W42:
  demand = 110
  capacity = 120
  balance = +10
  shortage = 0
```

### 13.5 Bottleneck interpretation

The diagnostic may include:

```text
first_shortage_node = DC_KANTO
```

or:

```text
most_restrictive_node = DC_KANTO
```

This is optional but useful.

If included, tests should verify that DC_KANTO has shortages in W41 and W42.

---

## 14. Expected Return Shape

Return a deterministic dictionary.

Recommended shape:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "available": True,
    "masters": {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    },
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],
    "demand": {
        "node": "MARKET_TOKYO",
        "weekly_lot_counts": {
            "2027-W40": 80,
            "2027-W41": 95,
            "2027-W42": 110,
        },
        "total_lots": 285,
    },
    "network": {
        "inbound_path_exists": True,
        "outbound_path_exists": True,
        "mom_node": "RICE_MILL_A",
        "dad_node": "DC_KANTO",
        "partner_key": "RICE_CORE",
        "market_leaf": "MARKET_TOKYO",
        "supply_point": "supply_point",
    },
    "capacity": {
        "runtime_attachment_applied": True,
        "input_row_count": 9,
    },
    "balance": {
        "DC_KANTO": {
            "2027-W40": {"demand": 80, "capacity": 90, "balance": 10, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 90, "balance": -5, "shortage": 5},
            "2027-W42": {"demand": 110, "capacity": 90, "balance": -20, "shortage": 20},
        },
        "RICE_MILL_A": {
            "2027-W40": {"demand": 80, "capacity": 100, "balance": 20, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 100, "balance": 5, "shortage": 0},
            "2027-W42": {"demand": 110, "capacity": 100, "balance": -10, "shortage": 10},
        },
        "FARM_REGION_A": {
            "2027-W40": {"demand": 80, "capacity": 120, "balance": 40, "shortage": 0},
            "2027-W41": {"demand": 95, "capacity": 120, "balance": 25, "shortage": 0},
            "2027-W42": {"demand": 110, "capacity": 120, "balance": 10, "shortage": 0},
        },
    },
    "messages": [
        "Japanese Rice first PSI vertical slice: masters loaded.",
        "Japanese Rice first PSI vertical slice: demand lots attached to MARKET_TOKYO leaf.",
        "Japanese Rice first PSI vertical slice: capacity runtime context attached.",
        "Japanese Rice first PSI vertical slice: network hammock paths verified.",
        "Japanese Rice first PSI vertical slice: simple weekly balance computed.",
    ],
}
```

The exact field names may differ slightly, but tests must verify the same facts.

---

## 15. Required Tests

Add:

```text
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

### 15.1 Runner loads all masters

Assert:

```text
result["available"] is True
capacity_rows == 9
demand_rows == 3
demand_lots == 285
network_nodes == 9
network_edges == 8
```

### 15.2 Demand lots attach to MARKET_TOKYO

Assert:

```text
result["demand"]["node"] == "MARKET_TOKYO"
weekly lot counts are 80 / 95 / 110
total_lots == 285
```

If the runner returns the leaf compatibility structure, assert that:

```text
psi4demand[week]["S"] contains the expected number of lot IDs
```

### 15.3 Capacity runtime attachment applied

Assert:

```text
runtime_attachment_applied is True
input_row_count == 9
```

### 15.4 Network paths verified

Assert:

```text
inbound_path_exists is True
outbound_path_exists is True
mom_node == RICE_MILL_A
dad_node == DC_KANTO
partner_key == RICE_CORE
market_leaf == MARKET_TOKYO
supply_point == supply_point
```

### 15.5 Simple balance for DC_KANTO

Assert:

```text
2027-W40 balance = 10, shortage = 0
2027-W41 balance = -5, shortage = 5
2027-W42 balance = -20, shortage = 20
```

### 15.6 Simple balance for RICE_MILL_A

Assert:

```text
2027-W40 balance = 20, shortage = 0
2027-W41 balance = 5, shortage = 0
2027-W42 balance = -10, shortage = 10
```

### 15.7 Simple balance for FARM_REGION_A

Assert:

```text
2027-W40 balance = 40, shortage = 0
2027-W41 balance = 25, shortage = 0
2027-W42 balance = 10, shortage = 0
```

### 15.8 Messages are deterministic

Assert messages include:

```text
masters loaded
demand lots attached
capacity runtime context attached
network hammock paths verified
simple weekly balance computed
```

### 15.9 Not a full PSI run

Assert that the result includes wording or a flag such as:

```text
run_mode = diagnostic_first_psi_smoke
```

or:

```text
full_psi_plan = False
```

This prevents future confusion.

---

## 16. Test Commands

Run focused first PSI smoke test:

```bat
python -m pytest tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Run Japanese Rice vertical slice tests:

```bat
python -m pytest tests/test_japanese_rice_capacity_master_vertical_slice.py
python -m pytest tests/test_japanese_rice_demand_master_vertical_slice.py
python -m pytest tests/test_japanese_rice_network_master_vertical_slice.py
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

Run compile check:

```bat
python -m compileall pysi/runners tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

If `pysi/runners` already has many files, compile only the new runner file if preferable.

---

## 17. Safety Boundaries

Expected changed / added files:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
tests/test_japanese_rice_first_psi_run_vertical_slice.py
```

Optional:

```text
pysi/runners/__init__.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/capacity_aware_inbound_backward.py
pysi/plan/explicit_bridge_capacity_pipeline.py
```

Do not modify existing scenario master CSVs unless a clear typo is found and tests require it.

Do not remove NetworkX.

Do not wire into GUI.

Do not claim full PSI planning.

---

## 18. Acceptance Criteria

This request is complete when:

```text
Japanese Rice first PSI smoke runner is added
focused first PSI smoke test is added
runner loads capacity / demand / network masters
runner generates 285 demand lots
runner attaches demand lots to MARKET_TOKYO leaf compatibility shape
runner attaches capacity runtime context
runner verifies inbound / outbound hammock paths
runner verifies MOM/DAD partner_key alignment
runner computes deterministic simple weekly balance summary
DC_KANTO balance is +10 / -5 / -20
RICE_MILL_A balance is +20 / +5 / -10
FARM_REGION_A balance is +40 / +25 / +10
result explicitly marks this as diagnostic-first PSI smoke, not full PSI
focused tests pass
Japanese Rice capacity / demand / network tests still pass
capacity diagnostic / regression tests still pass
planner behavior unchanged
GUI layout unchanged
NetworkX untouched
full PSI run not claimed
```

---

## 19. Codex Summary Requirements

In the final summary, please explicitly answer:

```text
Where was the runner implemented?
What test file was added?
Does it load capacity / demand / network masters?
Does it generate 285 demand lots?
Does it attach demand lots to MARKET_TOKYO leaf compatibility shape?
Does it apply capacity runtime attachment preflight?
Does it verify inbound and outbound hammock paths?
Does it verify RICE_MILL_A / DC_KANTO partner_key alignment?
What are the DC_KANTO balance values?
What are the RICE_MILL_A balance values?
What are the FARM_REGION_A balance values?
Does the result clearly mark diagnostic-first PSI smoke rather than full PSI?
Did you change planner behavior?
Did you change GUI layout?
Did you remove or modify NetworkX?
Which tests passed?
```

---

## 20. Development Meaning

This request starts the Japanese Rice Case engine for the first time.

The goal is not full planning sophistication.

The goal is to prove that the scenario is now integrated:

```text
Demand:
  Tokyo market wants rice.

Capacity:
  farm, mill, and DC capacities exist.

Network:
  WOM E2E hammock path connects them.

First PSI smoke:
  demand and capacity can be compared by week.
```

This is the first visible step from static master definitions toward a runnable WOM scenario.

In simple terms:

```text
The rice bags, the demand, and the road network are ready.
This request turns the key for the first smoke test.
```
