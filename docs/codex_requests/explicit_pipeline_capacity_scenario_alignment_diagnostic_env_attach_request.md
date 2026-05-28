# Codex Request: Attach Explicit Pipeline Capacity Scenario Alignment Diagnostic to Env / KPI Messages

**Version:** v0r1  
**Date:** 2026-05-28  
**Status:** Codex implementation request  
**Target path:** `docs/codex_requests/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_request.md`  
**Related design memo:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md`  
**Related completion memo:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md`  
**Related implementation commit:** `fd7f92b Add explicit pipeline capacity scenario alignment diagnostic module and tests`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Request Summary

Please attach the existing capacity scenario alignment diagnostic to the Explicit Pipeline runtime environment and make the diagnostic visible to downstream KPI reporting / messages.

The diagnostic module already exists:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

with the following public function:

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

This request is the next step:

```text
pure diagnostic module
    ↓
env / ctx attach
    ↓
Explicit KPI View message visibility
```

This request must remain non-invasive.

Do not fix capacity behavior yet.

Do not normalize week keys.

Do not convert forward capacity shapes.

Do not change planning engine behavior.

The goal is to allow WOM to say:

```text
The capacity context exists, but it may not be aligned with the selected product / node / week domain / shape expectation.
```

---

## 2. Current State

The current branch already contains:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic.md
docs/codex_requests/explicit_pipeline_capacity_scenario_alignment_diagnostic_request.md
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_completion.md
```

The diagnostic module can detect:

```text
selected product mismatch
node mismatch
week-domain mismatch
forward capacity shape mismatch
backward capability shape
list-indexed forward capacity shape alignment
```

The current missing piece is runtime visibility.

The diagnostic should be computed during Explicit KPI / explicit pipeline preparation and attached to the environment so that the Management Cockpit can display or consume it.

---

## 3. Primary Implementation Scope

Please implement env/ctx attachment for the diagnostic.

Recommended implementation locations:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

However, keep the patch small.

If a clean integration can be done without changing all of these files, prefer the smaller approach.

Minimum acceptable implementation:

```text
1. Add helper to compute and attach diagnostic to env.
2. Wire helper into Explicit KPI preflight / run_full_plan path after capacity contexts are attached.
3. Expose diagnostic messages to the Explicit KPI View model messages.
4. Add focused tests.
```

---

## 4. Do Not Modify

Do not modify:

```text
pysi/plan/weekly_forward_push_with_capacity.py
pysi/plan/explicit_bridge_capacity_pipeline.py
pysi/plan/bridges/e2e_bridge_forward_capacity_smoke.py
data/explicit_pipeline_forward_weekly_capacity.csv
data/explicit_pipeline_backward_weekly_capability.csv
```

Do not change:

```text
capacity enforcement behavior
week key normalization
forward capacity dict-to-list conversion
scenario selection
sample CSV values
warning count semantics
Cost/KPI enrichment rules
graph calculations
```

This request should only attach and surface diagnostic information.

---

## 5. Required Env Attribute

Please attach the diagnostic result to:

```text
env.explicit_pipeline_capacity_scenario_alignment_diagnostic
```

The attached object should be the dictionary returned by:

```python
build_explicit_pipeline_capacity_scenario_alignment_diagnostic(...)
```

The helper should be safe when any required inputs are missing.

The diagnostic should still be attached with:

```python
{
    "available": False,
    ...
}
```

or a safe equivalent if insufficient information is available.

---

## 6. Recommended Helper Function

Add a small helper, preferably in:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

Recommended function name:

```python
attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(...)
```

Suggested signature:

```python
def attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(
    env,
    *,
    selected_product: str | None = None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    backward_weekly_capability: dict | None = None,
    forward_weekly_capacity: dict | None = None,
) -> dict:
    ...
```

Suggested behavior:

```python
selected_product = selected_product or getattr(env, "product_selected", None)
backward_weekly_capability = backward_weekly_capability or getattr(env, "explicit_pipeline_backward_weekly_capability", None)
forward_weekly_capacity = forward_weekly_capacity or getattr(env, "explicit_pipeline_forward_weekly_capacity", None)
```

Then call:

```python
diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
    selected_product=selected_product,
    backward_weekly_capability=backward_weekly_capability,
    forward_weekly_capacity=forward_weekly_capacity,
    outbound_root=outbound_root,
    inbound_root=inbound_root,
)
```

Then attach:

```python
env.explicit_pipeline_capacity_scenario_alignment_diagnostic = diagnostic
```

Return:

```python
diagnostic
```

This helper is the only acceptable mutation in the diagnostic flow.

The existing builder should remain pure.

---

## 7. Where to Call the Helper

Please inspect the current Explicit KPI preflight / run_full_plan integration before editing.

Likely location:

```text
pysi/gui/cockpit_tk.py
```

The call should happen after:

```text
backward capability context attach
forward weekly capacity context attach
```

and before or around:

```text
explicit pipeline ctx guard / explicit pipeline run
```

Recommended conceptual order:

```text
Explicit KPI ON
    ↓
apply demo flags
    ↓
attach backward capability from CSV
    ↓
attach forward weekly capacity from CSV
    ↓
attach capacity scenario alignment diagnostic
    ↓
ctx guard check
    ↓
run explicit bridge capacity pipeline if guard passes
    ↓
build KPI view model
```

If the actual code structure makes a slightly different placement safer, use that placement and document it in the summary.

---

## 8. KPI View / Messages Integration

Please surface diagnostic messages in the Explicit KPI View model if this can be done safely.

The diagnostic already contains:

```text
diagnostic["messages"]
```

Recommended behavior:

```text
Existing Explicit KPI View messages
    +
Capacity scenario alignment diagnostic messages
```

Do not replace existing messages.

Append diagnostic messages as warning/info messages.

Recommended message prefix:

```text
Capacity scenario alignment:
```

Example messages:

```text
Capacity scenario alignment: Selected product IPHONE_NM_2028_BASE is not present in forward capacity context product set [PACKAGED_RICE_STANDARD].
```

```text
Capacity scenario alignment: Forward capacity uses label week keys such as 2027-W40, while the current forward capacity consumer expects integer week indexes.
```

If the current view model message structure is plain strings, append plain strings.

If it uses dict messages, follow the existing structure.

Do not redesign the UI.

Do not add a new tab in this request.

---

## 9. Optional ctx Attachment

If the explicit pipeline ctx is assembled in a localized function and it is small and safe to do so, also include:

```python
ctx["explicit_pipeline_capacity_scenario_alignment_diagnostic"] = diagnostic
```

However, env attachment is required.

ctx attachment is optional.

Do not force a larger refactor just to attach to ctx.

---

## 10. Expected Behavior After This Patch

When Explicit KPI is ON and capacity contexts are attached, WOM should compute and retain a diagnostic like:

```python
env.explicit_pipeline_capacity_scenario_alignment_diagnostic
```

If current GUI product is:

```text
IPHONE_NM_2028_BASE
```

and capacity sample is:

```text
PACKAGED_RICE_STANDARD / MILL_EAST / 2027-W40
```

then diagnostic should report warning-level messages for likely mismatches:

```text
selected product mismatch
node mismatch
week-domain mismatch
shape mismatch
scenario/sample mismatch or uncertainty
```

The system should still run as before.

This patch should add visibility, not change execution.

---

## 11. Required Tests

Please add or update focused tests.

Preferred test files:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Keep tests small.

### 11.1 Env attach helper test

Add test to:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py
```

Test:

```text
helper attaches diagnostic to env
helper returns same diagnostic object
diagnostic includes product mismatch message
```

Example:

```python
env = SimpleNamespace(
    product_selected="IPHONE_NM_2028_BASE",
    explicit_pipeline_forward_weekly_capacity={
        "PACKAGED_RICE_STANDARD": {
            "MILL_EAST": {
                "P": {"2027-W40": 5}
            }
        }
    },
    explicit_pipeline_backward_weekly_capability={
        "MILL_EAST": {
            "PACKAGED_RICE_STANDARD": {
                "2027-W40": 5
            }
        }
    },
)
```

Assert:

```python
diagnostic is env.explicit_pipeline_capacity_scenario_alignment_diagnostic
diagnostic["alignment"]["product_alignment"] in {"mismatch", "partial_match"}
diagnostic["messages"]
```

### 11.2 Missing context attach safety test

Test:

```text
helper does not raise when env lacks capacity contexts
env still receives a diagnostic
```

### 11.3 GUI wiring test

If wiring is added in `cockpit_tk.py`, update an existing GUI wiring test or add a small focused test that confirms:

```text
Explicit KPI ON calls capacity scenario alignment diagnostic attach after capacity contexts are attached
```

Do not require a real Tk window if existing tests avoid it.

Use monkeypatch or fake helpers consistent with current test style.

### 11.4 KPI view messages test

If diagnostic messages are appended to the view model, test:

```text
given env or input bundle has diagnostic messages
view model messages include those diagnostic messages
existing messages are preserved
```

---

## 12. Required Test Commands

At minimum run:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Recommended regression:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_forward_capacity_context.py
python -m pytest tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py
python -m pytest tests/test_explicit_pipeline_capacity_context.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flags.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

---

## 13. Acceptance Criteria

The request is complete when:

```text
env.explicit_pipeline_capacity_scenario_alignment_diagnostic is attached in the Explicit KPI path
diagnostic messages can be surfaced to Explicit KPI View messages
capacity enforcement behavior is unchanged
planning behavior is unchanged
sample CSV files are unchanged
new/updated tests pass
```

The Codex summary should explicitly answer:

```text
Where is the diagnostic attached?
Is env.explicit_pipeline_capacity_scenario_alignment_diagnostic populated?
Are diagnostic messages visible to KPI view messages?
Were planning / capacity enforcement behaviors left unchanged?
Were week key normalization and shape conversion deferred?
Which tests passed?
```

---

## 14. Safety Reminder

This request is still part of the diagnostic phase.

Do not fix the capacity mismatch yet.

The intended development sequence is:

```text
diagnostic builder
    ↓
env / ctx attach
    ↓
message visibility
    ↓
manual GUI observation
    ↓
then decide week-key normalization / shape conversion
```

This patch should connect the stethoscope to the cockpit.

It should not perform surgery.

