# Japanese Rice First Runner Output Contract and CLI Smoke

**Version:** v0r1 draft  
**Date:** 2026-06-01  
**Status:** Design memo  
**Target path:** `docs/design/japanese_rice_first_runner_output_contract_and_cli_smoke.md`

**Strategic role:** Stabilize the visible output contract of `run_japanese_rice_first_psi_vslice(...)` before GUI wiring  
**Primary case:** Japanese Rice Case  
**Current north star:** Management-visible simulation before recommendation AI  
**Immediate goal:** Make the Japanese Rice first runner output compact, stable, testable, and CLI-friendly

---

## 1. Purpose

This memo defines the output contract and CLI smoke direction for the Japanese Rice first PSI runner.

The current runner has already been upgraded to show:

```text
masters loaded
actual ProductPlanNode tree
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO capacity gate
accepted / blocked lots
```

The next step is not yet full GUI wiring.

The next step is to stabilize what the runner returns and how it can be shown from CLI.

The purpose is:

```text
Make the runner output stable enough to become a demo summary and GUI input contract.
```

This memo is the bridge from:

```text
diagnostic runner
```

to:

```text
visible management cockpit / demo output
```

---

## 2. Design Inputs from Prior WOM Specifications

This design is based on the following WOM internal design principles.

### 2.1 V0R8 lot_ID list model

The V0R8 core model keeps PSI buckets as lot_ID lists.

Quantity is derived from list length.

```text
quantity = len(lot_ID list)
```

The runner output should respect this principle and avoid replacing lot behavior with simple aggregate-only counts too early.

### 2.2 Physical node world and ProductPlanNode world

WOM has two node worlds.

```text
Physical / GUI node world:
  product-independent
  used for map, NetworkX, E2E layout, visual selection

Planning / ProductPlanNode world:
  product-specific
  holds psi4demand / psi4supply
  source of lot movement, dump rows, event generation, and runner output
```

For the Japanese Rice first runner, output must come from the actual ProductPlanNode world, not only the physical GUI node world.

### 2.3 psi_state save format direction

The psi_state save format separates:

```text
tree_physical_outbound.json
tree_physical_inbound.json
plan_tree_outbound.json
plan_tree_inbound.json
psi_events.parquet
parameters.json
metadata.json
state_hash.txt
```

This output contract should not implement full psi_state persistence yet.

However, it should be consistent with that direction by separating:

```text
physical/network summary
plan_node summary
psi quantity summary
event-ready / future event summary
metadata
```

### 2.4 Canonical Event Layer

Canonical event design is based on:

```text
P_TO_I
I_TO_S
S_TO_NEXT_P
```

Node Character interprets these canonical transitions into business and financial meanings.

This CLI smoke output should not generate full canonical events yet.

However, it should prepare event-ready fields such as:

```text
lot_id counts
node_id
week
from / to concept
capacity gate
accepted / blocked
```

### 2.5 KPI and Costing direction

KPI and Costing are downstream evaluation layers.

They should not be mixed into the runner prematurely.

The output should leave clear extension points for:

```text
service KPI
inventory KPI
capacity KPI
revenue / profit KPI
cost structure impact
pain point report
```

The immediate target is quantity visibility.

Money visibility comes after the runner output is stable.

---

## 3. Current Runner State

Current runner:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

Current expected diagnostic sections:

```text
scenario_id
product_name
run_mode
full_psi_plan
masters
demand
network
capacity
balance
actual_plan_node_tree
capacity_constrained_first_flow
messages
```

Current important values:

```text
scenario_id = JAPANESE_RICE_VSLICE_001
product_name = JAPANESE_RICE_STANDARD
run_mode = diagnostic_first_psi_smoke
full_psi_plan = False
```

Current master counts:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

Current actual plan_node evidence:

```text
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
demand_lot_source = MARKET_TOKYO.psi4demand[week][0]
```

Current S-slot counts:

```text
2027-W40 = 80
2027-W41 = 95
2027-W42 = 110
```

Current first capacity gate result:

```text
capacity_node = DC_KANTO
capacity_type = S

2027-W40:
  accepted = 80
  blocked = 0

2027-W41:
  accepted = 90
  blocked = 5

2027-W42:
  accepted = 90
  blocked = 20

Total:
  accepted = 260
  blocked = 25
```

---

## 4. What This Output Contract Should Achieve

The runner output should satisfy five needs.

### 4.1 Machine-readable

The output should be stable enough for tests and future GUI wrapper.

### 4.2 Human-readable

The output should be easy to summarize from CLI.

### 4.3 Demo-ready

The output should show the value of WOM without requiring users to inspect internal code.

### 4.4 Trace-ready

The output should not yet be full event trace, but it should keep fields that can later connect to event / LotCAP / canonical event layers.

### 4.5 Management-visible

The output should show enough to support the first management discussion:

```text
Demand exists.
Capacity is limited.
Some lots pass.
Some lots wait.
This can later be converted into revenue / lost-sales / profit impact.
```

---

## 5. LPI Note

The uploaded design materials strongly define PSI state, ProductPlanNode, canonical event, KPI, and cost/reporting layers.

The acronym `LPI` should not be fixed in this memo unless a canonical definition is later added.

For this memo, the relevant visible output concept is:

```text
Lot / PSI / Impact visibility
```

or, more cautiously:

```text
LPI-like runner summary:
  Lot counts
  PSI-position evidence
  Impact from capacity gate
```

This memo does not define LPI as a formal WOM term.

It only defines the first runner output contract that can later support such a layer.

---

## 6. Recommended Output Contract v0r1

The returned object should keep the current sections and add a stable compact summary section.

Recommended top-level shape:

```python
{
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "run_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    "available": True,

    "contract_version": "japanese_rice_first_runner_output_v0r1",

    "masters": {...},
    "actual_plan_node_tree": {...},
    "capacity_constrained_first_flow": {...},

    "demo_summary": {...},
    "cli_summary_lines": [...],
    "messages": [...],
}
```

The key addition is:

```text
contract_version
demo_summary
cli_summary_lines
```

These should be stable.

---

## 7. demo_summary Contract

Recommended `demo_summary`:

```python
"demo_summary": {
    "title": "Japanese Rice first PSI smoke",
    "scenario_id": "JAPANESE_RICE_VSLICE_001",
    "product_name": "JAPANESE_RICE_STANDARD",
    "runner_mode": "diagnostic_first_psi_smoke",
    "full_psi_plan": False,
    "weeks": ["2027-W40", "2027-W41", "2027-W42"],

    "master_counts": {
        "capacity_rows": 9,
        "demand_rows": 3,
        "demand_lots": 285,
        "network_nodes": 9,
        "network_edges": 8,
    },

    "plan_node_summary": {
        "inbound_node_count": 5,
        "outbound_node_count": 5,
        "demand_node": "MARKET_TOKYO",
        "demand_lot_source": "MARKET_TOKYO.psi4demand[week][0]",
        "weekly_s_slot_counts": {
            "2027-W40": 80,
            "2027-W41": 95,
            "2027-W42": 110,
        },
    },

    "capacity_gate_summary": {
        "capacity_node": "DC_KANTO",
        "capacity_type": "S",
        "unit": "lot",
        "weekly": {
            "2027-W40": {
                "requested": 80,
                "capacity": 90,
                "accepted": 80,
                "blocked": 0,
            },
            "2027-W41": {
                "requested": 95,
                "capacity": 90,
                "accepted": 90,
                "blocked": 5,
            },
            "2027-W42": {
                "requested": 110,
                "capacity": 90,
                "accepted": 90,
                "blocked": 20,
            },
        },
        "totals": {
            "requested": 285,
            "capacity": 270,
            "accepted": 260,
            "blocked": 25,
        },
    },

    "management_message": "DC_KANTO accepts 260 lots and blocks 25 lots over the three-week smoke horizon."
}
```

---

## 8. CLI Summary Lines Contract

Recommended `cli_summary_lines` should be a list of plain strings.

Example:

```text
WOM Japanese Rice first PSI smoke
Scenario: JAPANESE_RICE_VSLICE_001
Product: JAPANESE_RICE_STANDARD
Mode: diagnostic_first_psi_smoke
Full PSI plan: False

Masters:
  capacity_rows=9, demand_rows=3, demand_lots=285, network_nodes=9, network_edges=8

Actual ProductPlanNode:
  inbound_nodes=5, outbound_nodes=5
  demand_node=MARKET_TOKYO
  demand_lot_source=MARKET_TOKYO.psi4demand[week][0]

Weekly demand S-slot:
  2027-W40: 80
  2027-W41: 95
  2027-W42: 110

DC_KANTO S capacity gate:
  2027-W40: requested=80, capacity=90, accepted=80, blocked=0
  2027-W41: requested=95, capacity=90, accepted=90, blocked=5
  2027-W42: requested=110, capacity=90, accepted=90, blocked=20

Totals:
  requested=285, capacity=270, accepted=260, blocked=25
```

This should be easy to print.

It should also be easy to show in a GUI text panel.

---

## 9. CLI Smoke Command Design

Recommended future CLI command:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format summary
```

Alternative:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format json
```

Optional output file:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice --scenario-root examples/scenarios/japanese_rice_vslice_001 --format json --out outputs/japanese_rice_first_psi_smoke.json
```

Supported formats should initially be:

```text
summary
json
```

Do not add CSV yet unless needed.

---

## 10. CLI Behavior

### 10.1 summary format

The CLI should print only the compact summary lines.

It should not dump the whole nested diagnostic dictionary by default.

### 10.2 json format

The CLI should print the full JSON diagnostic object.

Use stable key ordering if convenient.

### 10.3 exit status

Expected:

```text
0 = runner available and completed
1 = runner unavailable or validation failed
```

This is useful for CI and future demo scripts.

### 10.4 no GUI dependency

The CLI smoke must not require GUI.

It must not import Tkinter or cockpit modules.

---

## 11. GUI Readiness

This output contract prepares GUI wiring.

Future GUI wrapper can show:

```text
demo_summary.title
demo_summary.master_counts
demo_summary.plan_node_summary
demo_summary.capacity_gate_summary.weekly
demo_summary.capacity_gate_summary.totals
```

A minimal GUI cockpit panel can display:

```text
weekly requested
weekly capacity
weekly accepted
weekly blocked
total accepted
total blocked
```

The GUI should consume the stable output contract rather than reaching into internal helper details.

---

## 12. Relationship to Event / LotCAP Layer

This CLI smoke output should not yet be full event trace.

However, it should be compatible with future event extraction.

Future event-ready fields:

```text
scenario_id
product_name
week
node_id
capacity_node
demand_node
accepted_lot_count
blocked_lot_count
accepted_lot_ids
blocked_lot_ids
```

In future, accepted / blocked lots can become events such as:

```text
capacity_gate_accepted
capacity_gate_blocked
```

At that point, these can map toward canonical event / event analyzer / LotCAP concepts.

For now, the CLI smoke should remain a compact diagnostic output.

---

## 13. Relationship to KPI / Cost Layer

This CLI smoke output should not compute money yet.

But it should prepare the next step.

Future extensions can add:

```text
lost_sales_proxy
revenue_accepted_proxy
revenue_blocked_proxy
profit_impact_proxy
inventory_value_proxy
```

The current output already provides:

```text
accepted lots
blocked lots
capacity shortage
```

These are sufficient to calculate first-order management impact later.

---

## 14. What Not to Do in This Slice

Do not implement:

```text
full GUI cockpit
full canonical event generation
full psi_state persistence
full cost / profit simulation
multi-gate flow
leadtime-aware propagation
inventory carry-over
recommendation AI
```

This slice is only:

```text
stable output contract
compact CLI smoke
testable summary
```

---

## 15. Recommended Implementation Files

Expected modified file:

```text
pysi/runners/run_japanese_rice_first_psi_vslice.py
```

Possible new helper file:

```text
pysi/runners/japanese_rice_first_psi_output_contract.py
```

Recommended test file:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Optional, only if project style supports it:

```text
pysi/runners/__init__.py
```

Do not modify GUI files.

---

## 16. Recommended Functions

Add helper:

```python
build_japanese_rice_first_runner_demo_summary(result: dict) -> dict
```

Add helper:

```python
format_japanese_rice_first_runner_cli_summary(result: dict) -> list[str]
```

Optionally add:

```python
main(argv: list[str] | None = None) -> int
```

to support:

```bat
python -m pysi.runners.run_japanese_rice_first_psi_vslice
```

The runner function itself should remain:

```python
run_japanese_rice_first_psi_vslice(scenario_root)
```

Do not rename it.

---

## 17. Test Requirements

Add:

```text
tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

### 17.1 Contract version

Assert:

```text
contract_version = japanese_rice_first_runner_output_v0r1
```

### 17.2 demo_summary exists

Assert:

```text
demo_summary exists
demo_summary.scenario_id = JAPANESE_RICE_VSLICE_001
demo_summary.product_name = JAPANESE_RICE_STANDARD
demo_summary.full_psi_plan = False
```

### 17.3 Master counts

Assert:

```text
capacity_rows = 9
demand_rows = 3
demand_lots = 285
network_nodes = 9
network_edges = 8
```

### 17.4 Plan node summary

Assert:

```text
inbound_node_count = 5
outbound_node_count = 5
demand_node = MARKET_TOKYO
weekly_s_slot_counts = 80 / 95 / 110
```

### 17.5 Capacity gate summary

Assert:

```text
2027-W40 accepted / blocked = 80 / 0
2027-W41 accepted / blocked = 90 / 5
2027-W42 accepted / blocked = 90 / 20
total accepted / blocked = 260 / 25
```

### 17.6 CLI summary lines

Assert `cli_summary_lines` includes strings containing:

```text
WOM Japanese Rice first PSI smoke
MARKET_TOKYO.psi4demand[week][0]
DC_KANTO S capacity gate
accepted=260
blocked=25
```

### 17.7 CLI summary command

If a `main(...)` entrypoint is added, test:

```text
--format summary
```

and optionally:

```text
--format json
```

without requiring GUI.

---

## 18. Test Commands

Focused test:

```bat
python -m pytest tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

Existing related tests:

```bat
python -m pytest tests/test_japanese_rice_first_psi_runner_actual_plan_node_upgrade.py tests/test_japanese_rice_first_psi_run_vertical_slice.py tests/test_japanese_rice_capacity_constrained_first_flow_vertical_slice.py tests/test_japanese_rice_plan_node_tree_instantiation_vertical_slice.py tests/test_japanese_rice_network_master_vertical_slice.py tests/test_japanese_rice_demand_master_vertical_slice.py tests/test_japanese_rice_capacity_master_vertical_slice.py
```

Compile check:

```bat
python -m compileall -q pysi/runners/run_japanese_rice_first_psi_vslice.py tests/test_japanese_rice_first_runner_output_contract_and_cli_smoke.py
```

If a helper file is added:

```bat
python -m compileall -q pysi/runners/japanese_rice_first_psi_output_contract.py
```

---

## 19. Acceptance Criteria

This slice is complete when:

```text
run_japanese_rice_first_psi_vslice(...) returns contract_version
run_japanese_rice_first_psi_vslice(...) returns demo_summary
run_japanese_rice_first_psi_vslice(...) returns cli_summary_lines
demo_summary includes master counts
demo_summary includes actual plan_node summary
demo_summary includes DC_KANTO capacity gate summary
cli_summary_lines are compact and human-readable
the runner remains diagnostic_first_psi_smoke
full_psi_plan remains False
no GUI dependency is introduced
existing Japanese Rice runner tests still pass
focused output contract test passes
compileall passes
```

---

## 20. Recommended Next Codex Request

Recommended next request:

```text
docs/codex_requests/japanese_rice_first_runner_output_contract_and_cli_smoke_request.md
```

Scope:

```text
add stable output contract fields
add demo_summary
add cli_summary_lines
optionally add CLI main with --format summary/json
add focused tests
do not modify GUI
do not modify planner behavior
do not claim full PSI planning
```

---

## 21. Development Meaning

This slice is important because it makes the current runner output showable.

Before this slice:

```text
The runner has rich diagnostic data.
```

After this slice:

```text
The runner has a stable demo summary and CLI smoke output.
```

This is a small technical step but a large demo-readiness step.

It moves WOM toward:

```text
management-visible simulation
```

without prematurely jumping into recommendation AI or full GUI.

In simple terms:

```text
The rice bags are on the WOM vehicle.
DC_KANTO has accepted 260 and blocked 25.
Now the dashboard needs a stable line that says so.
```
