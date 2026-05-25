# Explicit Pipeline Management Cockpit KPI Demo Flag Preset Completion Memo

**Version:** v0r1 completion  
**Date:** 2026-05-25  
**Status:** Completion memo  
**Target path:** `docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_preset_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This memo summarizes the completion status of **Explicit Pipeline Management Cockpit KPI Demo Flag Preset Helper Phase 1**.

The purpose of this milestone was to implement a pure, execution-free helper that applies the explicit pipeline KPI reporting flags to an `env` object.

This helper is the first step toward making the already-mounted Explicit KPI View show populated data after `Run Full Plan`.

The completed Phase 1 scope is:

```text
Design memo
    ↓
Codex request
    ↓
Pure demo flag preset helper
    ↓
Focused tests
    ↓
Commit / push
```

This phase does not modify the GUI.

It does not add a checkbox.

It does not run planning.

It does not run exports.

It does not execute ReplanCommand.

---

## 2. Background

The Explicit Pipeline Management Cockpit KPI UI MVP has already been implemented.

The UI currently includes:

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

The UI opens correctly from the WOM GUI.

However, normal `python -m main` execution currently shows the Explicit KPI View with unavailable reporting data:

```text
No explicit pipeline reporting data is available.
Run planning with explicit pipeline enabled.
```

This happens because the explicit pipeline reporting stack is intentionally protected by default-off feature flags.

Phase 1 provides a small helper that can turn on the necessary flags safely.

---

## 3. Implemented Files

This milestone modified or added:

```text
pysi/reporting/__init__.py
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
tests/test_explicit_pipeline_kpi_demo_flags.py
```

The implementation was committed as:

```text
030872c Add explicit pipeline KPI demo flag preset helper
```

---

## 4. Main Implementation

A new helper module was added:

```text
pysi/reporting/explicit_pipeline_kpi_demo_flags.py
```

Main function:

```python
apply_explicit_pipeline_kpi_demo_flags(
    env,
    *,
    include_exports=False,
    cost_kpi_context=None,
)
```

The helper applies explicit pipeline KPI reporting flags to a generic `env` object.

It uses `setattr`.

It works with simple objects such as:

```python
types.SimpleNamespace
```

It returns a deterministic map of applied flag values.

---

## 5. Helper Function Signature

Implemented signature:

```python
def apply_explicit_pipeline_kpi_demo_flags(
    env: Any,
    *,
    include_exports: bool = False,
    cost_kpi_context: dict[str, Any] | None = None,
) -> dict[str, bool]:
    ...
```

This signature matches the design and Codex request.

The helper is intentionally small and explicit.

---

## 6. Display Flags Enabled

The helper always enables these display flags:

```text
enable_explicit_bridge_capacity_pipeline
enable_explicit_bridge_capacity_report
enable_explicit_bridge_capacity_issue_candidates
enable_explicit_bridge_capacity_issue_candidate_cost_kpi
```

Each is set to:

```python
True
```

These flags are required so that a later `Run Full Plan` can generate and attach explicit pipeline reporting artifacts for the Explicit KPI View.

The helper itself does not run `Run Full Plan`.

---

## 7. Export Flag Behavior

The helper manages these export flags:

```text
enable_explicit_bridge_capacity_report_export
enable_explicit_bridge_capacity_issue_candidate_export
enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export
```

Default behavior:

```python
include_exports=False
```

sets all export flags to:

```python
False
```

When called with:

```python
include_exports=True
```

all export flags are set to:

```python
True
```

This keeps file export behavior explicit and controlled.

GUI display does not require exports.

---

## 8. Cost / KPI Context Behavior

The helper supports an optional `cost_kpi_context`.

If:

```python
cost_kpi_context is not None
```

then it attaches:

```python
env.explicit_bridge_capacity_cost_kpi_context = cost_kpi_context
```

If:

```python
cost_kpi_context is None
```

the helper does not overwrite an existing context.

This preserves existing scenario context by default.

---

## 9. Return Map Behavior

The helper returns a deterministic dictionary.

With default `include_exports=False`, the return map is:

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

With `include_exports=True`, the export flags become:

```python
True
```

The return map supports future GUI status messages and test assertions.

---

## 10. Package Export

`pysi/reporting/__init__.py` was updated so the helper can be imported from:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags
```

This was verified through a direct import check.

---

## 11. Tests Added

Focused tests were added:

```text
tests/test_explicit_pipeline_kpi_demo_flags.py
```

The tests cover:

```text
1. required display flags enabled
2. export flags disabled by default
3. export flags enabled when include_exports=True
4. existing cost_kpi_context preserved by default
5. provided cost_kpi_context attached
```

The tests use:

```python
types.SimpleNamespace
```

No Tk is required.

No planning execution is required.

---

## 12. Validation Commands

The direct import check succeeded:

```bat
python -c "from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags; from types import SimpleNamespace; env=SimpleNamespace(); print(apply_explicit_pipeline_kpi_demo_flags(env))"
```

Observed output:

```text
{
  'enable_explicit_bridge_capacity_pipeline': True,
  'enable_explicit_bridge_capacity_report': True,
  'enable_explicit_bridge_capacity_issue_candidates': True,
  'enable_explicit_bridge_capacity_issue_candidate_cost_kpi': True,
  'enable_explicit_bridge_capacity_report_export': False,
  'enable_explicit_bridge_capacity_issue_candidate_export': False,
  'enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export': False
}
```

Focused test:

```bat
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
```

Observed result:

```text
4 passed
```

Related tests also passed:

```bat
python -m pytest tests/test_explicit_pipeline_reporting_flags.py
python -m pytest tests/test_explicit_pipeline_reporting_stack_insertion.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_cards.py
```

Observed results:

```text
tests/test_explicit_pipeline_reporting_flags.py                 10 passed
tests/test_explicit_pipeline_reporting_stack_insertion.py        7 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py      8 passed
tests/test_explicit_pipeline_management_cockpit_kpi_cards.py     3 passed
```

Total observed focused / related result:

```text
32 passed
```

---

## 13. Safety Boundaries Preserved

This phase preserved the intended safety boundaries.

It did not modify:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/plan/*
pysi/core/*
```

It did not add:

```text
GUI checkbox
GUI button
menu entry
Run Full Plan integration
planning execution
explicit pipeline execution
reporting stack execution
export execution
ReplanCommand execution
automatic replanning
OR optimization
database persistence
Knowledge Continuity persistence
matplotlib dependency
```

The helper only sets flags and optional context.

The rule remains:

```text
Prepare the ignition switch.
Do not start the engine.
```

---

## 14. Completion Criteria

This milestone satisfies the Phase 1 completion criteria.

```text
[OK] pysi/reporting/explicit_pipeline_kpi_demo_flags.py exists
[OK] apply_explicit_pipeline_kpi_demo_flags(env) exists
[OK] required display flags are enabled
[OK] export flags are False by default
[OK] export flags are True when include_exports=True
[OK] existing cost_kpi_context is preserved by default
[OK] provided cost_kpi_context is attached
[OK] deterministic return map is provided
[OK] tests/test_explicit_pipeline_kpi_demo_flags.py exists
[OK] focused tests pass
[OK] related cockpit / reporting tests pass
[OK] no GUI modification is made
[OK] no planning execution is added
[OK] no export execution is added
[OK] no ReplanCommand execution is added
```

---

## 15. Meaning of This Milestone

Before this milestone:

```text
Explicit KPI View was installed, but there was no centralized helper to enable the reporting signal path.
```

After this milestone:

```text
A pure helper exists to apply the explicit KPI reporting flags safely.
```

This means Phase 2 can now wire this helper into the GUI without duplicating flag logic.

The cockpit still does not light up automatically, but the ignition switch body now exists.

---

## 16. Current Pipeline Position

The staged integration now stands here:

```text
Explicit KPI View UI MVP                         ✅ completed
    ↓
Graph View Model                                 ✅ completed
    ↓
Graphs tab with Tk Canvas charts                 ✅ completed
    ↓
Summary KPI Cards                                ✅ completed
    ↓
Demo flag preset design                          ✅ completed
    ↓
Demo flag preset Codex request                   ✅ completed
    ↓
Demo flag preset helper Phase 1                  ✅ completed
    ↓
GUI checkbox / toggle wiring Phase 2             next
```

---

## 17. Current Operational Meaning

The helper can be used in future code like:

```python
from pysi.reporting import apply_explicit_pipeline_kpi_demo_flags

apply_explicit_pipeline_kpi_demo_flags(self.env, include_exports=False)
```

After Phase 2, the expected user flow will be:

```text
python -m main
    ↓
Enable Explicit KPI ON
    ↓
Run Full Plan
    ↓
Explicit KPI View
    ↓
Summary KPI Cards / Graphs / Issues populated
```

Phase 1 alone does not change the visible GUI workflow.

---

## 18. Known Limitations

This phase intentionally does not provide GUI access.

It does not yet:

```text
add a checkbox
apply flags before Run Full Plan
change unavailable-view messages
verify populated cockpit via GUI
add startup config
add CLI option
```

These belong to Phase 2 and later.

---

## 19. Recommended Next Step

The next design document should be:

```text
docs/design/explicit_pipeline_management_cockpit_kpi_demo_flag_gui_wiring.md
```

Recommended Phase 2 scope:

```text
add a visible checkbox or small toggle near Run Full Plan / Explicit KPI View
apply demo flags before Run Full Plan when enabled
keep checkbox default OFF
do not run planning by toggling
do not run exports by default
verify Explicit KPI View becomes Available after Run Full Plan
```

Recommended implementation target:

```text
pysi/gui/cockpit_tk.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
```

---

## 20. Summary

The Explicit Pipeline Management Cockpit KPI Demo Flag Preset Helper Phase 1 is complete.

The key achievement is:

```text
apply_explicit_pipeline_kpi_demo_flags(env, include_exports=False)
```

The helper safely enables display-related explicit KPI reporting flags and preserves export safety by default.

This phase remains non-invasive:

```text
no GUI modification
no planning execution
no export execution
no ReplanCommand execution
```

The ignition switch body is now built.

The next phase is to mount it onto the WOM GUI.
