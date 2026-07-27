# Codex Request: Planning Warm-up and Reporting Horizon

- **Request file**: `docs/codex_requests/planning_warmup_reporting_horizon_request.md`
- **Target repository**: `Yasushi-Osugi/wom_v1r0m0`
- **Target branch**: `wom-v1r2m1`
- **Implementation baseline commit**: `670c983` (`Implement explicit holiday closure semantics`)
- **Dependency status**: `holiday_explicit_closure_engine_request.md` completed, accepted, committed, and pushed in `670c983`
- **Verified baseline**: `python -m pytest -q` → `90 passed`; soy sauce GUI scenario verified with formal `supply_closure,value=0`
- **Request status**: Ready for implementation
- **Owner policy**: Do not commit, push, merge, create a pull request, or create a release tag unless the repository owner explicitly instructs you to do so.

Before editing, verify:

```text
branch = wom-v1r2m1
git status = clean
commit 670c983 is an ancestor of HEAD
```

Recommended commands:

```bat
git branch --show-current
git status
git merge-base --is-ancestor 670c983 HEAD
```

Expected:

```text
branch = wom-v1r2m1
working tree = clean
git merge-base exit code = 0
```

Exit code `0` from `git merge-base --is-ancestor 670c983 HEAD` means that the accepted Holiday Explicit Closure implementation is contained in the current `HEAD` history.

Codex must stop before implementation and report the mismatch if:

- the branch is not `wom-v1r2m1`;
- the working tree is not clean at implementation start;
- commit `670c983` is not an ancestor of `HEAD`.

---

## 1. Request Summary

Implement an explicit Planning Horizon and Reporting Horizon for the WOM model-folder workflow.

The current soy sauce model starts final demand at:

```text
2027-W01
```

The current AutoDetect behavior also starts the Planning Engine at the first week found in `demand_forecast.csv`.

This cuts off the pre-demand weeks needed for:

```text
raw-material preparation
brewing
bottling
FG warehouse pre-positioning
ocean transport
DC safety-stock formation
```

The solution is not to shorten:

```text
push_lead_time_weeks=7
```

The solution is to calculate from an earlier Planning Start while keeping the business demand and standard reporting start at `2027-W01`.

`Final Demand Start` is an observed property of `demand_forecast.csv`; do not add a redundant independently editable `final_demand_start_week` setting unless source inspection proves it is required.

Formal target for the soy sauce scenario:

```text
Planning Start          = 2026-W33
Planning Weeks          = 125
Planning Warm-up Period = 2026-W33 .. 2026-W53
Final Demand Start      = 2027-W01
Reporting Start         = 2027-W01
Reporting Weeks         = 104
push_lead_time_weeks    = 7
```

---

## 2. Read Before Coding

Read and follow:

```text
AGENTS.md
README.md
docs/development/README.md
docs/architecture/README.md
docs/architecture/planning_engine.md
docs/design/README.md
docs/design/holiday_calendar_push_lead_time_and_planning_horizon.md
docs/design/push_production_lead_time.md
docs/design/planning_warmup_and_reporting_horizon.md
docs/design/scenario_modeling_principles.md
data/sample/soysauce-us-2027/README.md
```

Inspect the current implementation paths that:

```text
load a model folder
detect the first demand week
count unique demand weeks
build WOMConfig / PlanningContext
generate week labels
initialize PlanNode PSI arrays
load demand and capacity
run BackwardPlanner and ForwardPlanner
convert SCTree results to DataFrame
render standard and diagnostic charts
bridge PSI to PPC
write management/PPC outputs
```

Likely relevant files include:

```text
wom/gui/app.py
wom/config.py
wom/data/loader.py
wom/data/schema.py
wom/engine/sc_tree_builder.py
wom/engine/backward_planner.py
wom/engine/forward_planner.py
wom/engine/sc_tree_to_df.py
wom/engine/scenario.py
wom/ppc/*
wom/reports/*
data/sample/soysauce-us-2027/demand_forecast.csv
data/sample/soysauce-us-2027/capacity_plan.csv
data/sample/soysauce-us-2027/push_config.csv
```

Do not assume all of these require changes. Identify the smallest coherent set.

---

## 3. Core Design Decisions

### Decision A: Planning, demand, and reporting boundaries are different concepts

The following must remain distinguishable:

```text
Planning Start
    first week calculated by the engine

Final Demand Start
    first week with actual market demand, derived from demand data

Reporting Start
    first week included in standard business reporting
```

Only Planning and Reporting boundaries require explicit horizon configuration in this request. Final Demand Start remains data-derived.

For the soy sauce model:

```text
Planning Start    = 2026-W33
Final Demand Start = 2027-W01
Reporting Start   = 2027-W01
```

### Decision B: Keep Push Lead Time unchanged

Do not change:

```text
push_lead_time_weeks=7
```

The current seven-week value remains the supply-side operating assumption.

### Decision C: Warm-up weeks are real planning weeks

Warm-up weeks must exist in:

```text
week labels
PlanNode PSI arrays
Backward Planning
Forward Planning
inventory state
capacity lookup
diagnostic output
```

They must not be removed before planning.

### Decision D: Reporting filtering occurs at output boundaries

Do not truncate the engine state to the reporting period.

Apply reporting-window selection only when producing:

```text
standard charts
management tables
standard PPC summaries/exports
```

Diagnostic views must be able to show the full Planning Horizon.

### Decision E: Preserve legacy AutoDetect

Models without explicit horizon configuration must continue to use the current behavior:

```text
first demand week
× unique demand week count
```

No existing model should be forced to add a new file.

### Decision F: ISO weeks must be correct

Do not implement week arithmetic as:

```text
always 52 weeks per year
```

The interval crosses:

```text
2026-W53
```

The current `WOMConfig.weeks` path already uses ISO-calendar date arithmetic. Reuse or safely extend that canonical path; do not create a second week-arithmetic implementation.

### Decision G: Preserve current WOMConfig compatibility

The current public planning fields are:

```text
WOMConfig.start_week
WOMConfig.num_weeks
```

Preserve them for existing callers and tests. They may remain the canonical Planning Horizon fields.

Acceptable approaches include:

```text
start_week / num_weeks remain canonical
+ reporting_start_week / reporting_weeks are added
+ optional read-only aliases planning_start_week / planning_weeks
```

Do not broadly rename `start_week` or `num_weeks` across the repository merely to match request terminology.

---

## 4. Configuration Interface

First inspect whether the repository already has a canonical model-level configuration file that can safely hold horizon settings.

Current repository facts to preserve:

```text
WOMConfig already owns start_week and num_weeks
WOMConfig already generates ISO week labels
WOMConfig supports dictionary/JSON serialisation
```

This does not by itself prove that a model-folder JSON file is the canonical scenario interface. Inspect the actual model-folder loading path before choosing the storage format.

### Preferred rule

If an existing model-level config mechanism exists:

```text
extend it
```

Do not create a second competing configuration format.

### Fallback rule

If no suitable model-level configuration exists, add an optional one-row CSV:

```text
planning_horizon.csv
```

Recommended schema:

```csv
planning_start_week,planning_weeks,reporting_start_week,reporting_weeks
2026-W33,125,2027-W01,104
```

Optional fields may be added only if clearly justified:

```text
warmup_weeks
diagnostic_show_warmup
```

Avoid storing redundant conflicting values unless validation defines precedence.

### Loading precedence

Use this precedence for Planning Start/Weeks:

```text
1. Current GUI entry values at Run time
2. Model-folder explicit horizon configuration loaded into the GUI
3. Legacy demand AutoDetect fallback
```

Use this precedence for Reporting Start/Weeks:

```text
1. Dedicated GUI values, only if deliberately added
2. Model-folder explicit horizon configuration
3. Planning Start/Weeks as the legacy-compatible default
```

Practical GUI behavior:

1. Loading a model folder populates Start Week and Weeks from explicit horizon config when present.
2. The user may edit the GUI values before Run Planning.
3. Run Planning uses the current GUI values.
4. Reporting Start/Weeks come from explicit config unless corresponding GUI controls are deliberately added.
5. Do not add unnecessary controls if the existing UI can remain simple.

If the current GUI architecture makes this precedence unsafe, document the minimal alternative and implement it consistently.

---

## 5. Required Engine Behavior

### 5.1 Week-label generation

Generate the full Planning Horizon from:

```text
planning_start_week
planning_weeks
```

For soy sauce, expected boundaries are:

```text
first week = 2026-W33
includes   = 2026-W53
last week  = 2028-W52
count      = 125
```

Add a direct automated assertion for all four facts.

### 5.2 Demand loading

Demand remains zero before `2027-W01`.

The engine must be able to use explicit Planning Start without requiring artificial zero-demand rows in `demand_forecast.csv`.

Required behavior:

```text
week exists in Planning Horizon
no demand row exists
→ zero demand
```

Do not modify the original 2027-W01 final-demand timing.

### 5.3 Capacity loading

Warm-up weeks must not accidentally become unlimited because no capacity row exists.

For the soy sauce scenario, update `capacity_plan.csv` for:

```text
2026-W33 .. 2026-W53
```

using the same normal capacities as the corresponding 2027 normal operating weeks.

At minimum include:

```text
Bottling_Noda = 1500
Brewing_Noda  = 1500
Materials_JP  = 50000
```

Preserve the current capacity schema exactly.

Do not introduce automatic backward capacity carry unless it is already the repository's standard rule. Explicit scenario rows are preferred for this request.

### 5.4 Planning context

Make both ranges available in the active planning context/config.

The existing names may remain canonical:

```text
start_week
num_weeks
reporting_start_week
reporting_weeks
```

Optional semantic aliases are acceptable:

```text
planning_start_week -> start_week
planning_weeks      -> num_weeks
```

A derived helper is acceptable:

```text
reporting_end_week
is_reporting_week(week)
reporting_slice
```

Use one canonical representation and avoid duplicate independent calculations in GUI, engine, PPC, and reports.

### 5.5 Internal data retention

The complete Planning Horizon must remain available in:

```text
SCTree
PlanNode
planning DataFrame
ScenarioManager or equivalent internal result
```

Do not permanently discard warm-up rows during conversion.

---

## 6. Reporting and Diagnostic Behavior

### 6.1 Engineering and diagnostic views

The following should be able to show all 125 weeks:

```text
Network node PSI chart
PSI List
Debug output
capacity diagnostics
holiday diagnostics
```

Keep the Network node PSI chart and PSI List on the full Planning Horizon by default. These are engineering views, even though they are displayed inside the GUI.

### 6.2 Standard business views

The following should default to the Reporting Horizon:

```text
Charts-tab business charts sourced from ScenarioManager/standard result data
KPI Table
Management views
Scenario Delta
standard PPC summary
standard report/export totals
```

Do not apply reporting filtering by destructively replacing the canonical full-horizon planning DataFrame. Prefer a shared reporting-window selector or filtered view at each business-output boundary.

The reporting window for soy sauce is:

```text
2027-W01 .. 2028-W52
104 weeks
```

### 6.3 PPC boundary rule

Do not change PPC price, cost, profit, tariff, or Lot-ID propagation logic.

Only prevent warm-up weeks from being counted as ordinary business-period reporting totals where the current output is intended to represent the 104-week business period.

If PPC requires warm-up event history to value later inventory correctly:

```text
retain the events internally
filter only presentation/summary rows
```

Do not delete warm-up events before valuation.

### 6.4 Traceability

Where practical, include or preserve enough metadata to distinguish:

```text
planning_week
reporting_included
```

A central helper such as `is_reporting_week()` or `reporting_slice()` is preferred over repeating boundary arithmetic in GUI, Management, PPC, and exports.

Do not require a broad event-ledger redesign in this request.

---

## 7. Soy Sauce Scenario Changes

### 7.1 Add explicit horizon configuration

Use the existing model config if available.

Otherwise add:

```text
data/sample/soysauce-us-2027/planning_horizon.csv
```

with:

```csv
planning_start_week,planning_weeks,reporting_start_week,reporting_weeks
2026-W33,125,2027-W01,104
```

### 7.2 Keep demand timing unchanged

Do not move 2027 demand into 2026.

Do not change demand quantities merely to create the planning horizon.

If temporary zero-demand rows already exist locally, the formal implementation should not require them.

### 7.3 Extend capacity data

Add normal capacity rows for all warm-up weeks:

```text
2026-W33 .. 2026-W53
```

Use the exact current column order and comments/style in `capacity_plan.csv`.

### 7.4 Keep push and holiday configuration unchanged

Verify:

```csv
push_lead_time_weeks=7
```

remains unchanged.

Also preserve the accepted Holiday Explicit Closure behavior from commit `670c983`:

```text
supply_closure is explicit event state
holiday_calendar.csv uses value=0
cap_hard <= 0 remains unconstrained when no explicit closure exists
```

### 7.5 Update scenario documentation

Update:

```text
data/sample/soysauce-us-2027/README.md
```

Document:

```text
Planning Warm-up Period = 2026-W33..W53
Business/Reporting Period = 2027-W01..2028-W52
why warm-up exists
how AutoDetect/config precedence works
which charts include warm-up
```

Do not turn the scenario README into a duplicate of the canonical design docs.

---

## 7.6 Required implementation sequence

Implement and validate in this order:

```text
Phase A
  horizon configuration + validation
  full Planning Horizon week labels
  zero-demand warm-up loading
  finite warm-up capacity
  full internal PSI retention

Phase B
  shared Reporting Horizon selector
  standard business-view filtering
  Management/PPC/export filtering
  diagnostic full-horizon preservation
```

After Phase A, run the focused planning/capacity/push/holiday tests before changing reporting boundaries. This keeps engine-horizon faults separate from output-filtering faults.

Do not commit between phases unless the repository owner explicitly requests it.

---

## 8. Validation and Error Handling

Validate explicit horizon configuration.

Reject with a clear message:

```text
invalid ISO week
planning_weeks <= 0
reporting_weeks <= 0
reporting_start before planning_start
reporting end outside planning horizon
duplicate conflicting config rows
```

Allow:

```text
reporting_start == planning_start
```

for models without warm-up.

When no horizon config exists, log the legacy fallback source.

Recommended logs:

```text
[PlanningHorizon] source=model-config planning=2026-W33 x125 reporting=2027-W01 x104
```

or:

```text
[PlanningHorizon] source=demand-autodetect planning=2027-W01 x104 reporting=2027-W01 x104
```

Do not log a successful explicit horizon and then silently replace it with demand AutoDetect.

---

## 9. Test Requirements

A dedicated test file is recommended:

```text
tests/test_planning_horizon.py
```

Add reporting-filter tests near the relevant reporting/PPC tests if that is clearer.

### Test 1: ISO week generation across W53

Input:

```text
start = 2026-W33
weeks = 125
```

Expected:

```text
len = 125
first = 2026-W33
contains = 2026-W53
last = 2028-W52
```

### Test 2: Explicit config parsing

Load the preferred model config or fallback `planning_horizon.csv`.

Expected:

```text
planning_start_week = 2026-W33
planning_weeks = 125
reporting_start_week = 2027-W01
reporting_weeks = 104
```

### Test 3: Legacy AutoDetect fallback

Model with no explicit horizon config.

Expected:

- current first-demand-week behavior remains;
- current unique-week-count behavior remains;
- reporting range defaults to the same range as planning.

### Test 4: Missing warm-up demand becomes zero

Planning includes 2026 weeks, while demand CSV begins in 2027.

Expected:

```text
2026 demand = 0
2027-W01 demand unchanged
```

### Test 5: Warm-up capacity is finite

Load soy sauce capacity data.

Expected for representative 2026 warm-up weeks:

```text
Bottling_Noda = 1500
Brewing_Noda = 1500
Materials_JP = 50000
```

No warm-up week should be unlimited merely because the row was omitted.

### Test 6: Internal planning result retains warm-up rows

Expected:

```text
planning DataFrame first week = 2026-W33
planning DataFrame length/range includes all 125 weeks
```

Use the correct dimensional assertion for the current DataFrame structure.

### Test 7: Reporting filter

Given a planning result containing 2026-W33..2028-W52:

Expected standard reporting range:

```text
2027-W01..2028-W52
```

Verify that:

```text
warm-up rows remain internally
warm-up rows are excluded from standard totals
```

### Test 8: Diagnostic full horizon

Verify the data source used by the diagnostic PSI view still contains 2026 warm-up weeks.

A headless data-level test is sufficient; do not require screenshot automation.

### Test 9: Manual GUI override

If GUI tests are feasible, verify that a user-edited Planning Start/Weeks value is used at Run.

If GUI automation is impractical, isolate the precedence logic in a pure helper and test it.

### Test 10: Invalid configuration

Cover at least:

```text
bad week label
zero planning weeks
reporting range outside planning range
```

### Test 11: Push lead time regression

Verify soy sauce still loads:

```text
push_lead_time_weeks=7
```

### Test 12: No-horizon scenario regression

Run at least one existing sample model without explicit horizon config and confirm its period remains unchanged.

### Test 13: Holiday closure regression

Run:

```text
tests/test_holiday_explicit_closure.py
```

Expected:

```text
all accepted Holiday Explicit Closure tests continue to pass
soy sauce holiday_calendar.csv remains value=0
```

---

## 10. Manual Verification

Run:

```text
python -m main
Load Model Folder:
data/sample/soysauce-us-2027
Run Planning
```

Expected log:

```text
[PlanningHorizon] source=model-config planning=2026-W33 x125 reporting=2027-W01 x104
```

Verify:

### Diagnostic PSI

At:

```text
Materials_JP
Brewing_Noda
Bottling_Noda
FG_WH_Noda
DC_US_SF
DC_US_NY
```

the PSI data includes 2026 warm-up weeks.

Expected qualitative behavior:

```text
upstream P begins before 2027-W01
inventory is positioned before final demand
2027-W01 DC inventory is greater than zero where the model requires it
initial DC CO is eliminated or materially reduced
```

### Final demand

Verify:

```text
Rest_JP / Rest_US_West / Rest_US_East
actual demand still begins at 2027-W01
```

### Standard business outputs

Verify that standard Management/PPC totals use:

```text
2027-W01..2028-W52
```

and do not count 2026 warm-up weeks as ordinary sales weeks.

### Diagnostic output

Verify that an engineering view can still display:

```text
2026-W33..2028-W52
```

---

## 11. Required Test Commands

Run focused tests appropriate to the final file locations.

At minimum:

```bat
python -m pytest tests/test_planning_horizon.py -q
python -m pytest tests/test_step8_push_pull.py -q
python -m pytest tests/test_step7_capacity.py -q
python -m pytest tests/test_holiday_explicit_closure.py -q
```

Run relevant reporting/PPC tests selected after source inspection.

Then run:

```bat
python -m pytest -q
```

Report exact results.

If full-suite failures pre-exist, distinguish them from new failures.

---

## 12. Non-goals

Do not implement the following in this request:

```text
change push_lead_time_weeks from 7 to 4
Push Config production_node_id redesign
rework or replace the accepted Holiday Explicit Closure implementation
capacity mode enum redesign
automatic capacity backfill for every scenario
automatic optimal warm-up calculation from network LT
PPC price/cost/tariff formula redesign
opening-inventory accounting redesign
major GUI layout redesign
broad rename of WOMConfig.start_week / num_weeks
```

The automatic formula:

```text
inbound lead time
+ outbound cumulative LT
+ safety-stock weeks
```

may be documented as a future enhancement, but do not implement it here.

---

## 13. Definition of Done

- [ ] Planning Start is independent from Final Demand Start.
- [ ] Reporting Start is independent from Planning Start.
- [ ] Soy sauce planning runs from 2026-W33 for 125 weeks.
- [ ] Soy sauce final demand still starts at 2027-W01.
- [ ] Soy sauce standard reporting covers 104 weeks from 2027-W01.
- [ ] ISO 2026-W53 is handled correctly.
- [ ] Warm-up demand defaults to zero without synthetic demand rows.
- [ ] Warm-up capacity is explicitly finite in scenario data.
- [ ] Full PSI state retains warm-up weeks.
- [ ] Diagnostic views can use the full horizon.
- [ ] Standard Management/PPC outputs apply the reporting window.
- [ ] `push_lead_time_weeks=7` remains unchanged.
- [ ] Holiday Explicit Closure behavior from `670c983` remains unchanged and its focused tests pass.
- [ ] Models without horizon config preserve legacy AutoDetect.
- [ ] Invalid horizon config gives a clear error.
- [ ] Focused tests pass.
- [ ] Full-suite results are reported.
- [ ] Manual soy sauce verification is summarized.

---

## 14. Required Completion Report

Return:

```text
1. Starting branch/HEAD verification
2. Configuration interface chosen and why
3. Files changed
4. Loading/precedence behavior
5. Planning vs reporting data flow
6. Tests added
7. Exact test commands and results
8. Manual soy sauce results
9. Legacy model regression result
10. Holiday closure regression result
11. Remaining limitations
12. git diff --stat
13. Recommended commit message
```

Recommended commit message:

```text
Add planning warm-up and reporting horizons
```

Suggested body:

```text
Add optional model-level planning/reporting horizon configuration, preserve
legacy demand AutoDetect, calculate the soy sauce model from 2026-W33, retain
full warm-up PSI internally, and filter standard business reporting from
2027-W01 without changing push lead time.
```
