# Explicit Pipeline Capacity Scenario Alignment Diagnostic Env Attach Completion Memo

**Version:** v0r1  
**Date:** 2026-05-28  
**Status:** Completed  
**Target path:** `docs/design/explicit_pipeline_capacity_scenario_alignment_diagnostic_env_attach_completion.md`  
**Branch:** `feature/explicit-kpi-demo-flag-preset-v0r1`

---

## 1. Purpose

This completion memo records the completion of the env / KPI View integration for the Explicit Pipeline Capacity Scenario Alignment Diagnostic.

The previous phase implemented the pure diagnostic builder:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

This phase connected that diagnostic to the WOM runtime and the Explicit KPI View so that WOM can visibly report capacity scenario alignment issues in the Management Cockpit.

The purpose of this phase was not to fix capacity enforcement.

The purpose was to make the current semantic mismatch visible to the user.

---

## 2. Key Commit

Implementation commit:

```text
93f12ac Attach capacity scenario alignment diagnostic to explicit KPI flow
```

Related preceding commits:

```text
fd7f92b Add explicit pipeline capacity scenario alignment diagnostic module and tests
f57fb25 Add explicit pipeline capacity scenario alignment diagnostic completion memo
f9342ad Add explicit pipeline capacity scenario alignment diagnostic env attach request
```

---

## 3. Files Changed

The implementation modified the following files:

```text
pysi/gui/cockpit_tk.py
pysi/gui/explicit_pipeline_management_cockpit_view.py
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_capacity_scenario_alignment.py
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

---

## 4. Implementation Summary

### 4.1 Env attach helper

Added:

```python
attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(...)
```

to:

```text
pysi/reporting/explicit_pipeline_capacity_scenario_alignment.py
```

This helper:

```text
computes the existing pure diagnostic
attaches it to env.explicit_pipeline_capacity_scenario_alignment_diagnostic
returns the same diagnostic object
tolerates missing inputs
attaches a safe unavailable warning diagnostic if evaluation raises
```

The pure diagnostic builder remains side-effect free.

The env attach helper is the only intentional mutation point.

---

### 4.2 Explicit KPI preflight wiring

The diagnostic attach was wired into the Explicit KPI preflight path in:

```text
pysi/gui/cockpit_tk.py
```

The conceptual order is now:

```text
Explicit KPI ON
    ↓
apply demo flags
    ↓
attach backward capability context
    ↓
attach forward weekly capacity context
    ↓
attach capacity scenario alignment diagnostic
    ↓
ctx guard evaluation
    ↓
explicit pipeline execution / skip behavior
    ↓
KPI view model
```

This placement is important because the diagnostic needs the backward and forward capacity contexts before evaluating alignment.

It is also intentionally placed before ctx guard evaluation so the diagnostic can describe capacity-context alignment while the Explicit KPI path is being prepared.

---

### 4.3 KPI View message surfacing

The diagnostic messages are surfaced in:

```text
pysi/gui/explicit_pipeline_management_cockpit_view.py
```

Messages are appended to the existing KPI View messages with the required prefix:

```text
Capacity scenario alignment:
```

Existing messages are preserved.

The diagnostic payload is also exposed through the view model so future UI or report surfaces can consume it.

---

## 5. Tests Executed

The following focused tests passed:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py
python -m pytest tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py
python -m pytest tests/test_explicit_pipeline_management_cockpit_kpi_view.py
```

Observed results:

```text
tests/test_explicit_pipeline_capacity_scenario_alignment.py       11 passed
tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py           9 passed
tests/test_explicit_pipeline_management_cockpit_kpi_view.py       11 passed
```

The following related regression set also passed:

```bat
python -m pytest tests/test_explicit_pipeline_capacity_scenario_alignment.py tests/test_explicit_pipeline_capacity_pipeline_shape_and_scenario_alignment.py tests/test_explicit_pipeline_forward_capacity_context.py tests/test_explicit_pipeline_forward_weekly_capacity_sample_csv.py tests/test_explicit_pipeline_capacity_context.py tests/test_explicit_pipeline_kpi_demo_flags.py tests/test_explicit_pipeline_kpi_demo_flag_gui_wiring.py tests/test_explicit_pipeline_management_cockpit_kpi_view.py tests/test_explicit_pipeline_management_cockpit_kpi_graph_view.py
```

Observed result:

```text
82 passed
```

---

## 6. Manual GUI Validation

Manual GUI validation was performed with:

```bat
python -m main
```

Observed GUI behavior:

```text
Explicit KPI ON
    ↓
Run Full Plan
    ↓
Explicit Pipeline Management Cockpit KPI View
    ↓
Messages tab
    ↓
Capacity scenario alignment messages displayed
```

The Messages tab successfully displayed capacity scenario alignment diagnostics.

Observed message categories included:

```text
selected product mismatch
backward capability product mismatch
week-domain mismatch
forward capacity shape mismatch
capacity node mismatch
```

Representative displayed messages:

```text
Capacity scenario alignment: Selected product IPHONE_NM_2028_BASE is not present in forward capacity context product ...
Capacity scenario alignment: Selected product IPHONE_NM_2028_BASE is not present in backward capability context ...
Capacity scenario alignment: Forward capacity uses week-key domain label_week, while consumer expects integer_index.
Capacity scenario alignment: Forward capacity producer shape appears to be product_node_type_week_map_v1, while ...
Capacity scenario alignment: Capacity nodes do not match runtime tree nodes. Unmatched capacity nodes: ['MILL_EAST'].
```

This confirms that WOM can now visibly report that the current capacity context exists but is semantically misaligned with the active GUI runtime scenario.

---

## 7. Meaning of the Manual GUI Result

The manual GUI result should be interpreted as a success.

The diagnostic messages do not mean the new implementation failed.

They mean the diagnostic is correctly detecting the known current mismatch:

```text
active GUI product:
    IPHONE_NM_2028_BASE

sample capacity product:
    PACKAGED_RICE_STANDARD

sample capacity node:
    MILL_EAST

capacity week domain:
    label_week, such as 2027-W40

current forward consumer expectation:
    integer_index

forward capacity producer shape:
    product_node_type_week_map_v1

current forward consumer expectation:
    product_node_type_week_list_v0
```

Before this phase, these mismatches were implicit and could only be inferred by reading code and logs.

After this phase, WOM reports them in the cockpit.

---

## 8. Safety Boundaries Honored

This phase did not change:

```text
capacity enforcement behavior
weekly_forward_push_with_capacity behavior
explicit_bridge_capacity_pipeline behavior
Bridge A / Bridge B behavior
week key normalization
forward capacity dict-to-list conversion
sample CSV values
scenario selection
cost / KPI enrichment logic
warning count semantics
graph calculation behavior
```

The phase only added:

```text
diagnostic env attachment
KPI View message surfacing
focused tests
```

---

## 9. Current Development State

The Explicit Pipeline Capacity Scenario Alignment work now has the following completed sequence:

```text
design memo
    ↓
Codex request
    ↓
pure diagnostic module + tests
    ↓
completion memo
    ↓
env attach Codex request
    ↓
env attach + KPI messages integration
    ↓
manual GUI confirmation
```

Important commits:

```text
f55b9a4 Add explicit pipeline capacity scenario alignment diagnostic design
92340a2 Add explicit pipeline capacity scenario alignment diagnostic Codex request
fd7f92b Add explicit pipeline capacity scenario alignment diagnostic module and tests
f57fb25 Add explicit pipeline capacity scenario alignment diagnostic completion memo
f9342ad Add explicit pipeline capacity scenario alignment diagnostic env attach request
93f12ac Attach capacity scenario alignment diagnostic to explicit KPI flow
```

---

## 10. Development Meaning

Before this phase, WOM could say:

```text
Explicit KPI artifacts are available.
```

After this phase, WOM can say:

```text
Explicit KPI artifacts are available, but the capacity context appears misaligned with the active scenario.
```

This is an important step toward WOM as a context-aware planning cockpit.

WOM is no longer merely running calculations.

WOM is beginning to explain the semantic validity of its own runtime context.

---

## 11. Deferred Work

The following items remain intentionally deferred.

### 11.1 Scenario-aligned sample data

The current sample capacity context is suitable for detecting mismatch and validating diagnostics.

It is not yet a meaningful iPhone GUI capacity sample.

A later phase may add:

```text
iPhone-specific forward capacity sample
iPhone-specific backward capability sample
or a GUI path for Japanese Rice Case scenario execution
```

### 11.2 Week-key normalization

A later phase may decide whether to convert:

```text
2027-W40
```

to:

```text
integer week index
```

or whether to revise the consumer contract to accept labeled week keys.

### 11.3 Forward capacity shape conversion

A later phase may convert:

```text
product -> node -> capacity_type -> week_label -> capacity_lots
```

into:

```text
product -> node -> capacity_type -> list[index] -> capacity_lots
```

if the current forward consumer contract is kept.

### 11.4 Capacity applicability status

A later phase may add explicit semantics for:

```text
capacity present but not applied
capacity absent and treated as unlimited
capacity applied and blocking
capacity unavailable due to context mismatch
```

---

## 12. Recommended Next Step

Recommended next topic:

```text
docs/design/explicit_pipeline_capacity_scenario_alignment_next_action.md
```

or more concretely one of the following:

```text
docs/design/explicit_pipeline_capacity_week_key_normalization.md
docs/design/explicit_pipeline_forward_capacity_shape_conversion.md
docs/design/explicit_pipeline_iphone_capacity_sample_alignment.md
docs/design/explicit_pipeline_capacity_applicability_status.md
```

The recommended decision point is:

```text
Should the next step be sample alignment, week-key normalization, or forward capacity shape conversion?
```

A safe recommended order is:

```text
1. Record this env attach completion memo.
2. Decide whether to create iPhone-aligned capacity sample data or normalize the Rice Case path.
3. Only then decide week-key normalization / shape conversion behavior.
```

---

## 13. Summary

This phase successfully connected the capacity scenario alignment diagnostic to the WOM cockpit.

The diagnostic is now:

```text
computed during Explicit KPI ON preflight
attached to env
surfaced in Explicit KPI View messages
confirmed manually through python -m main
```

The displayed messages correctly identify the known mismatch between the active iPhone GUI scenario and the Japanese Rice Case capacity sample context.

In short:

```text
WOM can now speak about its capacity context alignment.
```

The next development question is no longer whether WOM can detect the mismatch.

The next question is how WOM should resolve it.
