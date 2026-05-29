from __future__ import annotations

from types import SimpleNamespace
import sys
import types

from pysi.adapters.capacity_input_granularity import WeeklyCapacityRow


def _ensure_matplotlib_stub():
    if "matplotlib" in sys.modules and "matplotlib.pyplot" in sys.modules:
        return
    matplotlib_stub = types.ModuleType("matplotlib")
    pyplot_stub = types.ModuleType("matplotlib.pyplot")
    backends_stub = types.ModuleType("matplotlib.backends")
    backend_tkagg_stub = types.ModuleType("matplotlib.backends.backend_tkagg")
    backend_tkagg_stub.FigureCanvasTkAgg = object
    animation_stub = types.ModuleType("matplotlib.animation")
    animation_stub.FuncAnimation = object
    figure_stub = types.ModuleType("matplotlib.figure")
    figure_stub.Figure = object
    matplotlib_stub.pyplot = pyplot_stub
    matplotlib_stub.use = lambda *_args, **_kwargs: None
    sys.modules.setdefault("matplotlib", matplotlib_stub)
    sys.modules.setdefault("matplotlib.pyplot", pyplot_stub)
    sys.modules.setdefault("matplotlib.backends", backends_stub)
    sys.modules.setdefault("matplotlib.backends.backend_tkagg", backend_tkagg_stub)
    sys.modules.setdefault("matplotlib.figure", figure_stub)
    sys.modules.setdefault("matplotlib.animation", animation_stub)


_ensure_matplotlib_stub()
sys.modules.setdefault("networkx", types.ModuleType("networkx"))

from pysi.gui.cockpit_tk import WOMCockpit


def _weekly_capacity_row(
    product_id: str = "PACKAGED_RICE_STANDARD",
    node_id: str = "MILL_EAST",
    capacity_type: str = "P",
    week: str = "2027-W40",
    qty: int = 5,
) -> WeeklyCapacityRow:
    return WeeklyCapacityRow(
        scenario_id="RICE_AS_IS",
        product_id=product_id,
        capacity_owner_type="node",
        capacity_owner_id=node_id,
        week=week,
        capacity_type=capacity_type,
        capacity_qty=qty,
        cap_mode="hard",
        unit="lot",
        source_granularity="weekly",
    )


def _fake_cockpit(env: SimpleNamespace) -> SimpleNamespace:
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
    )
    fake._maybe_attach_explicit_pipeline_backward_weekly_capability = lambda: None
    fake._maybe_attach_explicit_pipeline_forward_weekly_capacity = lambda: None
    fake._maybe_apply_capacity_runtime_attachment_preflight = (
        WOMCockpit._maybe_apply_capacity_runtime_attachment_preflight.__get__(fake)
    )
    fake._maybe_attach_explicit_pipeline_capacity_scenario_alignment_diagnostic = (
        WOMCockpit._maybe_attach_explicit_pipeline_capacity_scenario_alignment_diagnostic.__get__(fake)
    )
    return fake


def test_explicit_kpi_preflight_applies_runtime_attachment_when_weekly_rows_exist():
    env = SimpleNamespace(
        product_selected="PACKAGED_RICE_STANDARD",
        capacity_weekly_rows=[_weekly_capacity_row()],
    )
    fake = _fake_cockpit(env)

    applied = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert applied is not None
    result = env.capacity_runtime_attachment_preflight_result
    assert result["applied"] is True
    assert result["row_source"] == "env.capacity_weekly_rows"
    assert env.capacity_runtime_attachment_summary["input_row_count"] == 1
    assert env.explicit_pipeline_forward_weekly_capacity == {
        "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}}
    }
    assert env.explicit_pipeline_backward_weekly_capability_from_weekly_rows == {
        "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}}
    }
    assert not hasattr(env, "explicit_pipeline_backward_weekly_capability")


def test_explicit_kpi_preflight_skips_safely_when_weekly_rows_are_missing():
    env = SimpleNamespace(product_selected="PACKAGED_RICE_STANDARD")
    fake = _fake_cockpit(env)

    applied = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert applied is not None
    result = env.capacity_runtime_attachment_preflight_result
    assert result["applied"] is False
    assert result["reason"] == "capacity_weekly_rows_missing"
    assert result["row_source"] == "missing"


def test_runtime_attachment_diagnostic_and_messages_are_available_after_explicit_kpi_preflight():
    env = SimpleNamespace(
        product_selected="PACKAGED_RICE_STANDARD",
        capacity_weekly_rows=[_weekly_capacity_row()],
    )
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    diagnostic = env.explicit_pipeline_capacity_scenario_alignment_diagnostic
    assert "runtime_attachment" in diagnostic
    assert diagnostic["runtime_attachment"]["available"] is True
    assert "Capacity runtime attachment: summary available." in diagnostic["messages"]
    assert (
        "Capacity runtime attachment: summary available."
        in env.capacity_runtime_attachment_preflight_result["messages"]
    )


def test_runtime_attachment_preflight_runs_before_alignment_diagnostic():
    env = SimpleNamespace(capacity_weekly_rows=[_weekly_capacity_row()])
    call_order: list[str] = []
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
    )
    fake._maybe_attach_explicit_pipeline_backward_weekly_capability = lambda: call_order.append(
        "backward"
    )
    fake._maybe_attach_explicit_pipeline_forward_weekly_capacity = lambda: call_order.append(
        "forward"
    )

    def fake_runtime_preflight(*, messages=None):
        call_order.append("runtime_preflight")
        assert messages == []
        env.capacity_runtime_attachment_preflight_result = {"applied": True}
        env.explicit_pipeline_forward_weekly_capacity = {
            "PACKAGED_RICE_STANDARD": {"MILL_EAST": {"P": {"2027-W40": 5}}}
        }
        return env.capacity_runtime_attachment_preflight_result

    def fake_alignment():
        call_order.append("alignment")
        assert env.capacity_runtime_attachment_preflight_result["applied"] is True
        env.explicit_pipeline_capacity_scenario_alignment_diagnostic = {
            "runtime_attachment": {"available": True},
            "messages": [],
        }

    fake._maybe_apply_capacity_runtime_attachment_preflight = fake_runtime_preflight
    fake._maybe_attach_explicit_pipeline_capacity_scenario_alignment_diagnostic = fake_alignment

    applied = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert applied is not None
    assert call_order == ["backward", "forward", "runtime_preflight", "alignment"]


def test_explicit_kpi_preflight_repeated_invocation_is_deterministic():
    env = SimpleNamespace(
        product_selected="PACKAGED_RICE_STANDARD",
        capacity_weekly_rows=[_weekly_capacity_row()],
    )
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
    first = dict(env.capacity_runtime_attachment_preflight_result)
    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
    second = env.capacity_runtime_attachment_preflight_result

    assert second["applied"] is True
    assert second["row_source"] == first["row_source"]
    assert second["input_row_count"] == first["input_row_count"] == 1
    assert second["messages"] == first["messages"]
