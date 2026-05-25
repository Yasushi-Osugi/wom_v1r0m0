# Explicit Pipeline Management Cockpit KPI Demo Flag Preset Design Memo

**Version:** v0r1 draft  
**Date:** 2026-05-25  
**Status:** Design memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset.md`  
**Branch context:** `main` after PR merge / `feature/with-capacity-psi-engine-v0r2` retained locally for confirmation

---

## 1. Purpose

This memo defines the design for an **Explicit Pipeline Management Cockpit KPI Demo Flag Preset**.

The Explicit KPI View UI MVP has already been implemented and merged to `main`.

The UI now includes:

```text
Explicit KPI View
    ├─ Summary
    │   └─ KPI Cards
    ├─ Graphs
    │   └─ Canvas Charts
    ├─ Top Issues
    ├─ Replan Candidates
    ├─ Health
    ├─ Assumptions / Exports
    └─ Messages
```

However, during normal `python -m main` execution, the Explicit KPI View currently opens with empty data:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

This is expected because the explicit pipeline reporting stack is protected by default-off feature flags.

The goal of this design is to define a safe, minimal way to turn on the explicit KPI reporting signal path for demo and verification use.

---

## 2. Current Confirmed State

From local GUI verification:

```text
[OK] WOM GUI starts with python -m main
[OK] Mgmt Cockpit button exists and opens
[OK] Explicit KPI View button exists and opens
[OK] Summary tab exists
[OK] KPI Cards are visible
[OK] Graphs tab exists
[OK] Canvas chart panels are visible
[OK] Top Issues / Replan Candidates / Health / Assumptions / Messages tabs exist
[OK] Empty-state messages are displayed safely
```

But the Explicit KPI View shows:

```text
Available: No
Explicit Pipeline Result: No
Capacity Report: No
Issue Candidates: No
Cost / KPI Bundle: No
```

This means:

```text
UI layer is mounted.
Data signal path is not yet enabled in normal GUI operation.
```

This is not a UI failure.

It is a default-off safety behavior.

---

## 3. Problem Statement

The management cockpit UI is now available, but the normal user path does not yet provide an obvious way to generate the data needed by the Explicit KPI View.

Current user path:

```text
python -m main
    ↓
Run Full Plan
    ↓
Explicit KPI View
    ↓
empty KPI Cards / empty Graphs
```

Expected demo path:

```text
python -m main
    ↓
enable explicit KPI reporting flags
    ↓
Run Full Plan
    ↓
Explicit KPI View
    ↓
KPI Cards / Graphs / Issues populated
```

The missing piece is:

```text
safe demo flag preset
```

---

## 4. Design Goal

The design goal is to add a small, safe mechanism to enable the existing explicit pipeline reporting stack for demo and verification.

The first implementation should be minimal.

It should answer:

```text
How can a user run the existing plan and see the Explicit KPI View populated?
```

It should not introduce automatic execution from the view.

The cockpit should remain read-only.

---

## 5. Non-Goals

This phase must not implement:

```text
new planning engine logic
new capacity allocation logic
new issue candidate logic
new Cost / KPI enrichment logic
new exporter logic
automatic replan execution
ReplanCommand execution
OR optimization
database persistence
Knowledge Continuity persistence
large GUI redesign
complex settings panel
```

This phase is only for enabling the existing explicit pipeline reporting stack through a safe preset.

---

## 6. Core Safety Rule

The existing safety rule remains:

```text
Show the instruments.
Do not start the engine.
```

The demo preset may:

```text
set explicit pipeline / reporting flags before Run Full Plan
allow Run Full Plan to produce cockpit artifacts
allow Explicit KPI View to display those artifacts
```

It must not:

```text
run planning automatically when opening Explicit KPI View
run exports automatically from the view
execute ReplanCommand
mutate planning results after view rendering
hide that demo flags are enabled
```

---

## 7. Target User Experience

Recommended MVP user path:

```text
1. Start WOM:
   python -m main

2. Enable Explicit KPI Demo / Reporting preset.

3. Run Full Plan.

4. Open Explicit KPI View.

5. Confirm:
   Summary KPI Cards show values.
   Graphs tab shows bars.
   Top Issues / Replan Candidates / Health tabs show records if generated.
```

The simplest immediate target is not a polished final UX.

The immediate target is:

```text
make the cockpit light up in a reproducible demo path
```

---

## 8. Candidate Implementation Options

There are three candidate approaches.

---

### 8.1 Option A: Startup Demo Preset Helper

Add a helper function that can be called during GUI initialization or before planning.

Example:

```python
def enable_explicit_pipeline_kpi_demo_preset(env: Any) -> None:
    ...
```

This helper sets the required flags on `env`.

Advantages:

```text
minimal code
easy to test
easy to call from GUI or runner
keeps flag settings centralized
```

Disadvantages:

```text
requires a call site
may still be hidden unless surfaced in GUI or startup config
```

---

### 8.2 Option B: GUI Checkbox / Toggle

Add a visible checkbox in the main GUI:

```text
Enable Explicit KPI Reporting
```

When checked, it applies the flags before `Run Full Plan`.

Advantages:

```text
clear user control
safe default-off behavior preserved
good demo UX
```

Disadvantages:

```text
requires cockpit_tk.py UI modification
adds layout consideration
may require user education
```

---

### 8.3 Option C: Dedicated Demo Button / Preset Button

Add a button:

```text
Enable KPI Demo Flags
```

or:

```text
KPI Demo ON
```

Advantages:

```text
clear for developer/demo use
simple one-time action
```

Disadvantages:

```text
another button in an already crowded header
less clean than checkbox
```

---

## 9. Recommended Approach

Recommended staged approach:

```text
Phase 1: Add a pure preset helper and tests.
Phase 2: Wire it to GUI through a small checkbox or toggle.
Phase 3: Add optional startup config / CLI preset if needed.
```

For immediate next implementation, choose:

```text
Phase 1: pure preset helper
```

Then verify with a minimal call path.

After that, choose the best GUI exposure.

---

## 10. Phase 1 MVP Scope

### 10.1 Add helper module

Recommended new module:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Alternative location:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Recommended:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

because the flags control reporting stack behavior, not rendering.

---

### 10.2 Add helper function

Recommended function:

```python
def apply_explicit_pipeline_kpi_demo_flags(env: Any, *, include_exports: bool = False) -> dict[str, bool]:
    ...
```

The function should:

```text
set required env flags to True
optionally set export flags
return a dict of flag names and values applied
```

It should be safe for any object supporting `setattr`.

It should not run planning.

It should not write files.

It should not call reporting helpers.

---

## 11. Required Flags

For display-only cockpit data, recommended required flags:

```text
enable_explicit_bridge_capacity_pipeline
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
```

These should be set to:

```python
True
```

Reason:

```text
pipeline result creates explicit_result
capacity report creates report data
issue candidates create issue data
Cost / KPI enrichment creates card / graph data
```

---

## 12. Optional Export Flags

Export flags should remain optional.

When `include_exports=False`, do not enable export flags.

When `include_exports=True`, enable:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

Reason:

```text
GUI display does not require file exports.
Export generation may create files and should remain explicit.
```

Recommended default:

```python
include_exports=False
```

---

## 13. Optional Output Root

If export flags are enabled, optionally set:

```text
explicit_bridge_capacity_reporting_output_root
```

Recommended default:

```text
outputs/explicit_pipeline
```

But for Phase 1, avoid setting output root unless needed.

Keep helper minimal.

---

## 14. Cost / KPI Context

The existing reporting stack supports:

```text
explicit_bridge_capacity_cost_kpi_context
```

For Phase 1, the helper may optionally attach a minimal demo context.

Recommended default:

```python
cost_kpi_context: dict | None = None
```

Signature option:

```python
def apply_explicit_pipeline_kpi_demo_flags(
    env: Any,
    *,
    include_exports: bool = False,
    cost_kpi_context: dict[str, Any] | None = None,
) -> dict[str, bool]:
    ...
```

If `cost_kpi_context` is provided:

```python
env.explicit_bridge_capacity_cost_kpi_context = cost_kpi_context
```

If not provided:

```text
do not overwrite existing context
```

---

## 15. Helper Return Value

Return a stable dictionary:

```python
{
    "enable_explicit_bridge_capacity_pipeline": True,
    "enable_explicit_bridge_capacity_report": True,
    "enable_explicit_bridge_capacity_issue_candidates": True,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi": True,
    "enable_explicit_bridge_capacity_report_export": False,
    "enable_explicit_bridge_capacity_issue_candidate_export": False,
    "enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export": False,
}
```

If `include_exports=True`, export values are True.

This return value supports test assertions and future UI messages.

---

## 16. Phase 1 Tests

Recommended test file:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

Test cases:

```text
1. required flags are enabled
2. export flags remain False by default or are not set
3. export flags are enabled when include_exports=True
4. existing cost_kpi_context is not overwritten by default
5. provided cost_kpi_context is attached
6. function returns deterministic applied flag map
```

Use:

```python
from types import SimpleNamespace
```

No Tk needed.

---

## 17. Phase 2 GUI Wiring Design

After Phase 1, add GUI exposure.

Recommended UI:

```text
checkbox: Enable Explicit KPI Reporting
```

Placement:

```text
near Explicit KPI View button
or near Run Full Plan button
```

Behavior:

```text
unchecked by default
when checked, apply demo flags before Run Full Plan
```

The checkbox should not run planning by itself.

It should only influence the next planning run.

---

## 18. Phase 2 GUI Behavior

When `Run Full Plan` is executed:

```python
if self.var_enable_explicit_kpi_reporting.get():
    apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

Then existing `Run Full Plan` flow runs.

After planning:

```text
Explicit KPI View should be populated if reporting stack produced artifacts.
```

The view itself remains read-only.

---

## 19. Alternative Phase 2: Internal Dev Preset

If the header row is too crowded, add no visible checkbox initially.

Instead use a developer-level attribute:

```python
self.env.enable_explicit_kpi_demo_preset = True
```

or a startup config.

However, for practical usability, a visible checkbox is better.

---

## 20. Suggested GUI Label

Recommended label:

```text
Explicit KPI ON
```

or:

```text
Enable Explicit KPI
```

Avoid long text in the already crowded header.

Tooltip support is optional.

---

## 21. Recommended First Codex Request Scope

First request should implement only Phase 1:

```text
pure demo flag preset helper + tests
```

Files:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
pysi/reporting/__init__.py
```

Do not modify:

```text
pysi/gui/cockpit_tk.py
```

in Phase 1.

Phase 2 can then wire the helper into GUI.

---

## 22. Phase 1 Completion Criteria

Phase 1 is complete when:

```text
[OK] apply_explicit_pipeline_kpi_demo_flags(env) exists
[OK] required display flags are enabled
[OK] export flags are not enabled by default
[OK] export flags can be enabled with include_exports=True
[OK] existing cost_kpi_context is preserved by default
[OK] provided cost_kpi_context is attached
[OK] deterministic return map is provided
[OK] tests pass
[OK] no planning execution is added
[OK] no export execution is added
[OK] no GUI modification is made
```

---

## 23. Phase 2 Completion Criteria

Phase 2 is complete when:

```text
[OK] GUI has a visible or documented way to enable Explicit KPI Reporting
[OK] enabling the preset does not run planning by itself
[OK] Run Full Plan applies the preset before planning
[OK] Explicit KPI View can show populated data after Run Full Plan
[OK] view remains read-only
[OK] tests cover GUI integration
```

---

## 24. Operational Validation Scenario

After Phase 2, validation should be:

```text
1. python -m main
2. Enable Explicit KPI ON
3. Click Run Full Plan
4. Click Explicit KPI View
5. Confirm Summary:
   Available = Yes
   Explicit Pipeline Result = Yes
   Capacity Report = Yes
   Issue Candidates = Yes
   Cost / KPI Bundle = Yes
6. Confirm Graphs tab has at least some populated bars or clear no-issue messages.
```

If there are no issues by scenario design, `Issue Candidates` may be zero, but the reporting stack should still be available.

---

## 25. Important Distinction: Empty vs Unavailable

The UI should distinguish:

```text
Unavailable:
  reporting stack did not run
  Explicit Pipeline Result = No
  Capacity Report = No
  Issue Candidates = No

Empty:
  reporting stack ran
  Explicit Pipeline Result = Yes
  Capacity Report = Yes
  Issue Candidates = 0
  no issues were found
```

The current problem is `Unavailable`.

The demo flag preset should help reach `Available`.

---

## 26. Relation to Existing Mgmt Cockpit

The older `Mgmt Cockpit` button appears to show scenario comparison / management issue view.

The `Explicit KPI View` is a newer explicit-pipeline evidence view.

They are related but not identical.

The demo flag preset is specifically for:

```text
Explicit KPI View
```

not necessarily for the older `Mgmt Cockpit`.

---

## 27. Recommended Future UI Message

If the view is unavailable, improve the message from:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

to something more actionable:

```text
No explicit pipeline reporting data is available.
Enable Explicit KPI Reporting, run Full Plan, then reopen this view.
```

This can be a later small UI improvement.

---

## 28. Summary

The Explicit KPI View UI is correctly installed, but it currently opens empty under normal startup because the reporting stack flags are default-off.

This is a safe design, but it needs an explicit demo / reporting preset.

Recommended next implementation:

```text
Phase 1:
    pysi/reporting/explicit_pipeline_kpi_demo_flags.py
    apply_explicit_pipeline_kpi_demo_flags(env, include_exports=False)
    tests/test_explicit_pipeline_kpi_demo_flags.py

Phase 2:
    GUI checkbox or toggle near Run Full Plan / Explicit KPI View
    apply preset before Run Full Plan
```

The cockpit is installed.

The next step is to add the safe ignition switch.
