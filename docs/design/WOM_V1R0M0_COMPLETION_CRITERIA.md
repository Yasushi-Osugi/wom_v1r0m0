# WOM_V1R0M0_COMPLETION_CRITERIA

What must be true before WOM is called v1r0m0.

---

## The one-sentence test

> Run `python -m main`, load the Japanese Rice scenario,
> see demand change → PSI shift → profit impact on screen,
> and be able to explain why each number changed.

If a developer or business person can do this and say "I understand what happened",
v1r0m0 is complete.

---

## Required: the 7 gates

Every gate below must be green before tagging `v1r0m0`.

---

### Gate 1 — PSI pipeline runs end-to-end without error

**Command**
```
python -m main --backend mvp --scenario Baseline --ui cockpit
```

**Pass criteria**
- Launches without exception
- `WOMPipelineRunner.run()` completes
- `full_plan_result.json` is written to `outputs/`
- At least one product × node PSI series is non-zero

**Not required**
- Perfect numerical accuracy
- All scenarios working

---

### Gate 2 — Capacity gate is visible in the cockpit

**Pass criteria**
- DC-level capacity gate is displayed (accepted / blocked lot counts)
- `visual_capacity_gate_weekly.csv` is written
- Cockpit shows at least one week where blocked > 0 when capacity is constrained

**Rationale**
This is the first visible proof that Supply Side constraint works.
Without it, PSI is just a demand passthrough.

---

### Gate 3 — PPC simulator produces sales price output

**Command**
```
python -m pysi.ppc.ppc_simulator --scenario Baseline
```

**Pass criteria**
- `ppc_result.csv` is written with columns:
  `product_id, node_id, week, sales_price, unit_cost, margin_rate`
- At least one Leaf node shows a `sales_price > 0`
- Brand floor price constraint is applied (no price below `brand_floor_price`)

**Master data required**
- `data/product_price_policy.csv` exists and is loadable
- `data/node_cost_master.csv` exists and is loadable

---

### Gate 4 — Revenue = Ship_Qty × Sales_Price is computed and displayed

**Pass criteria**
- Cockpit Money panel shows Revenue, Cost, Profit per product or per node
- Numbers are derived from Gate 1 (ship_qty) × Gate 3 (sales_price)
- Gross margin % is shown

**Not required**
- Transfer pricing
- Multi-currency
- Tax calculation

---

### Gate 5 — Scenario comparison works for one named scenario pair

**Named pair**: `Baseline` vs `DemandSurge`

**Pass criteria**
- Both scenarios run without error
- Management Cockpit shows delta KPIs:
  - Revenue delta
  - Profit delta
  - Service rate delta
- At least one TrustEvent is generated in DemandSurge that does not appear in Baseline

---

### Gate 6 — At least one complete test suite passes

**Command**
```
python -m pytest tests/ -v
```

**Pass criteria**
- All existing tests pass (no regressions)
- At least one test covers PSI + PPC + Profit pipeline in sequence
- Test output is deterministic (same input = same output)

---

### Gate 7 — Repository is clean enough to hand to a new developer

**Pass criteria**
- `README.md` describes `python -m main` as the entry point
- `RUN.md` has working setup instructions (dependencies, data folder)
- No `.patch`, `.bat`, or temp files in repo root
  (move to `legacy/` or `archive/` if needed)
- `docs/design/WOM_DATA_MODEL_v1r0m0.md` is present (the revised data model)
- `docs/design/WOM_V1R0M0_COMPLETION_CRITERIA.md` is present (this file)
- `git log --oneline -1` shows a clean commit message, not a work-in-progress note

---

## Out of scope for v1r0m0

These are explicitly deferred to v1r1m0 or later:

| Feature                          | Reason for deferral                              |
|----------------------------------|--------------------------------------------------|
| Multi-currency support           | Adds complexity before core is stable            |
| Geopolitical / tariff layer      | Requires lane-level cost modelling               |
| LLM-assisted scenario narrative  | Depends on stable KPI contract first             |
| ERP / external data integration  | Integration layer is post-v1                     |
| Optimisation (OR-Tools)          | Plugin architecture must be stable first         |
| iPhone / Tesla scenario cases    | Japanese Rice is sufficient for v1 proof         |
| CO₂ / ESG KPI                   | Management Cockpit extension, not core           |

---

## Version naming convention

```
v{major}r{release}m{minor}

v1r0m0  = Version 1, Release 0, Minor 0 = first complete release
v1r0m1  = patch / hotfix on v1r0m0
v1r1m0  = next feature release on Version 1 branch
v2r0m0  = next major version (architecture change)
```

---

## Completion checklist (for gate review)

```
[ ] Gate 1  PSI pipeline end-to-end
[ ] Gate 2  Capacity gate visible in cockpit
[ ] Gate 3  PPC simulator output produced
[ ] Gate 4  Revenue = Ship_Qty × Sales_Price in cockpit
[ ] Gate 5  Baseline vs DemandSurge scenario comparison
[ ] Gate 6  pytest passes, no regressions
[ ] Gate 7  Repository clean, docs present
```

When all 7 boxes are checked:

```bash
git tag v1r0m0
git push origin v1r0m0
```

---

*End of WOM_V1R0M0_COMPLETION_CRITERIA*
