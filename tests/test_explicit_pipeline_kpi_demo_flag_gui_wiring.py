from types import SimpleNamespace
import sys
import types


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


def test_maybe_apply_explicit_kpi_demo_flags_returns_none_when_checkbox_var_missing():
    fake = SimpleNamespace(env=SimpleNamespace())

    result = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert result is None


def test_maybe_apply_explicit_kpi_demo_flags_returns_none_when_checkbox_off():
    env = SimpleNamespace()
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: False),
    )

    result = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert result is None
    assert not hasattr(env, "enable_explicit_bridge_capacity_pipeline")


def test_maybe_apply_explicit_kpi_demo_flags_applies_phase1_flags_when_checkbox_on():
    env = SimpleNamespace()
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
    )

    applied = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert applied is not None
    assert applied["enable_explicit_bridge_capacity_pipeline"] is True
    assert applied["enable_explicit_bridge_capacity_report"] is True
    assert applied["enable_explicit_bridge_capacity_issue_candidates"] is True
    assert applied["enable_explicit_bridge_capacity_issue_candidate_cost_kpi"] is True
    assert applied["enable_explicit_bridge_capacity_report_export"] is False
    assert applied["enable_explicit_bridge_capacity_issue_candidate_export"] is False
    assert applied["enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export"] is False
    assert env.explicit_kpi_demo_flag_ctx_guard_skipped is True
    assert "explicit_pipeline_backward_weekly_capability" in env.explicit_kpi_demo_flag_missing_ctx_keys
    assert env.enable_explicit_bridge_capacity_pipeline is False
    assert env.enable_explicit_bridge_capacity_report is False
    assert env.enable_explicit_bridge_capacity_issue_candidates is False
    assert env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi is False
    assert env.enable_explicit_bridge_capacity_report_export is False
    assert env.enable_explicit_bridge_capacity_issue_candidate_export is False
    assert env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi_export is False


def test_maybe_apply_explicit_kpi_demo_flags_keeps_flags_enabled_when_ctx_present():
    env = SimpleNamespace(
        explicit_pipeline_backward_weekly_capability={"MOM": {"W01": 100}}
    )
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
    )

    applied = WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert applied is not None
    assert env.explicit_kpi_demo_flag_ctx_guard_skipped is False
    assert env.explicit_kpi_demo_flag_missing_ctx_keys == []
    assert env.enable_explicit_bridge_capacity_pipeline is True
    assert env.enable_explicit_bridge_capacity_report is True
    assert env.enable_explicit_bridge_capacity_issue_candidates is True
    assert env.enable_explicit_bridge_capacity_issue_candidate_cost_kpi is True


def test_run_full_plan_calls_preflight_hook_before_planning(monkeypatch):
    call_order = []

    fake = SimpleNamespace(current_mode="")

    def fake_apply():
        call_order.append("preflight")

    def fake_build_snapshot():
        call_order.append("build_snapshot")
        return {"baseline": True}

    def fake_run_planning_sequence(*, use_selected_decouples):
        call_order.append("planning")
        assert use_selected_decouples is True

    def fake_refresh_management_cockpit(**_kwargs):
        call_order.append("refresh_mgmt")

    def fake_refresh():
        call_order.append("refresh")

    fake._maybe_apply_explicit_kpi_demo_flags = fake_apply
    fake._build_management_snapshot = fake_build_snapshot
    fake._run_planning_sequence = fake_run_planning_sequence
    fake.refresh_management_cockpit = fake_refresh_management_cockpit
    fake.refresh = fake_refresh

    WOMCockpit.run_full_plan(fake)

    assert call_order[0] == "preflight"
    assert call_order.index("preflight") < call_order.index("planning")
