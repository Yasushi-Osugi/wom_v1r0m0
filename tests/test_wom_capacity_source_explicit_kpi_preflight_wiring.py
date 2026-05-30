from __future__ import annotations

from pathlib import Path
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

CAPACITY_MASTER_HEADER = (
    "scenario_id,tree_side,node_name,product_name,week,capacity_type,capacity_qty,"
    "cap_mode,unit,priority,calendar_id,comment"
)


def _write_capacity_master_csv(path: Path, rows: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [CAPACITY_MASTER_HEADER]
    if rows is None:
        rows = [
            (
                "RICE_AS_IS,inbound,MILL_EAST,PACKAGED_RICE_STANDARD,2027-W40,"
                "P,10,hard,lot,1,CAL_STD,test row"
            )
        ]
    lines.extend(rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    return path


def _fake_cockpit(env: SimpleNamespace) -> SimpleNamespace:
    fake = SimpleNamespace(
        env=env,
        var_enable_explicit_kpi_reporting=SimpleNamespace(get=lambda: True),
    )
    fake._maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight = (
        WOMCockpit._maybe_load_capacity_weekly_rows_source_for_explicit_kpi_preflight.__get__(fake)
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


def test_capacity_master_path_loads_rows_before_runtime_preflight(tmp_path: Path) -> None:
    path = _write_capacity_master_csv(tmp_path / "capacity_master.csv")
    env = SimpleNamespace(
        product_selected="PACKAGED_RICE_STANDARD",
        capacity_master_path=path,
    )
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert hasattr(env, "capacity_weekly_rows")
    assert env.capacity_weekly_rows_load_summary["available"] is True
    assert env.capacity_weekly_rows_load_summary["row_count"] == 1
    assert env.capacity_runtime_attachment_preflight_result["applied"] is True
    assert hasattr(env, "explicit_pipeline_forward_weekly_capacity")
    assert hasattr(env, "explicit_pipeline_backward_weekly_capability_from_weekly_rows")


def test_no_source_hint_preserves_runtime_preflight_safe_skip() -> None:
    env = SimpleNamespace(product_selected="PACKAGED_RICE_STANDARD")
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    result = env.capacity_runtime_attachment_preflight_result
    assert result["applied"] is False
    assert result["reason"] == "capacity_weekly_rows_missing"
    assert not hasattr(env, "capacity_weekly_rows_load_summary")


def test_scenario_root_default_masters_capacity_master_loads_rows(
    tmp_path: Path,
) -> None:
    scenario_root = tmp_path / "scenario"
    path = _write_capacity_master_csv(scenario_root / "masters" / "capacity_master.csv")
    env = SimpleNamespace(
        product_selected="PACKAGED_RICE_STANDARD",
        scenario_root=scenario_root,
    )
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert env.capacity_weekly_rows_load_summary["available"] is True
    assert env.capacity_weekly_rows_load_summary["source_path"] == str(path)
    assert env.capacity_runtime_attachment_preflight_result["applied"] is True


def test_source_messages_are_preserved_in_load_summary_and_preflight_messages(
    tmp_path: Path,
) -> None:
    path = _write_capacity_master_csv(tmp_path / "capacity_master.csv")
    env = SimpleNamespace(capacity_master_path=path)
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    source_messages = env.capacity_weekly_rows_load_summary["messages"]
    assert any("Capacity weekly rows source: loaded" in m for m in source_messages)
    assert any(
        "Capacity weekly rows source: loaded" in m
        for m in env.capacity_runtime_attachment_preflight_result["messages"]
    )


def test_empty_valid_source_file_attaches_empty_rows_and_runtime_applies(
    tmp_path: Path,
) -> None:
    path = _write_capacity_master_csv(tmp_path / "capacity_master.csv", rows=[])
    env = SimpleNamespace(capacity_master_path=path)
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert env.capacity_weekly_rows == []
    assert env.capacity_weekly_rows_load_summary["row_count"] == 0
    assert env.capacity_runtime_attachment_preflight_result["applied"] is True


def test_repeated_explicit_kpi_preflight_source_loading_is_deterministic(
    tmp_path: Path,
) -> None:
    path = _write_capacity_master_csv(tmp_path / "capacity_master.csv")
    env = SimpleNamespace(capacity_master_path=path)
    fake = _fake_cockpit(env)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)
    first_rows = list(env.capacity_weekly_rows)
    first_load_summary = dict(env.capacity_weekly_rows_load_summary)
    first_preflight = dict(env.capacity_runtime_attachment_preflight_result)

    WOMCockpit._maybe_apply_explicit_kpi_demo_flags(fake)

    assert env.capacity_weekly_rows == first_rows
    assert env.capacity_weekly_rows_load_summary == first_load_summary
    assert env.capacity_runtime_attachment_preflight_result["applied"] is True
    assert env.capacity_runtime_attachment_preflight_result["input_row_count"] == first_preflight[
        "input_row_count"
    ]
    assert env.capacity_runtime_attachment_preflight_result["messages"] == first_preflight[
        "messages"
    ]
