from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pysi.capacity.capacity_weekly_rows_source import load_capacity_weekly_rows_to_env
from pysi.reporting.explicit_pipeline_capacity_scenario_alignment import (
    apply_capacity_runtime_attachment_preflight,
    build_explicit_pipeline_capacity_scenario_alignment_diagnostic,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "examples" / "scenarios" / "japanese_rice_vslice_001"
CAPACITY_MASTER_PATH = SCENARIO_ROOT / "masters" / "capacity_master.csv"
EXPECTED_PRODUCT = "JAPANESE_RICE_STANDARD"
EXPECTED_NODES = {"FARM_REGION_A", "RICE_MILL_A", "DC_KANTO"}
EXPECTED_WEEKS = {"2027-W40", "2027-W41", "2027-W42"}
EXPECTED_CAPACITY_TYPES = {"P", "S"}


def _loaded_env() -> SimpleNamespace:
    env = SimpleNamespace(product_selected=EXPECTED_PRODUCT)
    load_capacity_weekly_rows_to_env(env, scenario_root=SCENARIO_ROOT)
    return env


def test_japanese_rice_capacity_master_sample_loads_through_scenario_root() -> None:
    assert CAPACITY_MASTER_PATH.exists()
    env = _loaded_env()

    assert hasattr(env, "capacity_weekly_rows")
    assert len(env.capacity_weekly_rows) == 9
    assert env.capacity_weekly_rows_load_summary["available"] is True
    assert env.capacity_weekly_rows_load_summary["row_count"] == 9
    assert env.capacity_weekly_rows_source_kind == "scenario_package_capacity_master"
    assert env.capacity_weekly_rows_source_path == str(CAPACITY_MASTER_PATH)


def test_loaded_rows_preserve_japanese_rice_product_node_week_and_type_domains() -> None:
    env = _loaded_env()
    rows = env.capacity_weekly_rows

    assert {row.product_id for row in rows} == {EXPECTED_PRODUCT}
    assert {row.product_name for row in rows} == {EXPECTED_PRODUCT}
    assert {row.capacity_owner_id for row in rows} == EXPECTED_NODES
    assert {row.node_name for row in rows} == EXPECTED_NODES
    assert {row.week for row in rows} == EXPECTED_WEEKS
    assert {row.capacity_type for row in rows} == EXPECTED_CAPACITY_TYPES


def test_source_diagnostic_reports_japanese_rice_capacity_master_sample() -> None:
    env = _loaded_env()

    diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product=EXPECTED_PRODUCT,
        backward_weekly_capability=None,
        forward_weekly_capacity=None,
        env=env,
    )
    source = diagnostic["capacity_weekly_rows_source"]

    assert source["available"] is True
    assert source["summary_available"] is True
    assert source["row_count"] == 9
    assert source["env_rows_present"] is True
    assert source["env_row_count"] == 9
    assert source["row_count_matches_env"] is True


def test_runtime_attachment_preflight_consumes_japanese_rice_capacity_rows() -> None:
    env = _loaded_env()

    result = apply_capacity_runtime_attachment_preflight(env)
    env.capacity_runtime_attachment_preflight_result = result

    assert env.capacity_runtime_attachment_preflight_result["applied"] is True
    assert env.capacity_runtime_attachment_preflight_result["input_row_count"] == 9
    assert hasattr(env, "capacity_runtime_attachment_summary")
    assert env.capacity_runtime_attachment_summary["input_row_count"] == 9

    diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
        selected_product=EXPECTED_PRODUCT,
        backward_weekly_capability=getattr(
            env, "explicit_pipeline_backward_weekly_capability_from_weekly_rows"
        ),
        forward_weekly_capacity=env.explicit_pipeline_forward_weekly_capacity,
        env=env,
    )
    runtime_attachment = diagnostic["runtime_attachment"]

    assert runtime_attachment["summary_available"] is True
    assert runtime_attachment["summary"]["input_row_count"] == 9
    assert runtime_attachment["shape"]["forward_shape_from_summary"] == (
        "product_node_type_week_qty_v1"
    )
    assert runtime_attachment["shape"]["backward_shape_from_summary"] == (
        "product_node_type_week_qty_v1"
    )


def test_runtime_context_shape_includes_expected_japanese_rice_domain() -> None:
    env = _loaded_env()

    apply_capacity_runtime_attachment_preflight(env)

    forward_context = env.explicit_pipeline_forward_weekly_capacity
    assert set(forward_context) == {EXPECTED_PRODUCT}
    assert set(forward_context[EXPECTED_PRODUCT]) == EXPECTED_NODES
    assert set(forward_context[EXPECTED_PRODUCT]["FARM_REGION_A"]) == {"P"}
    assert set(forward_context[EXPECTED_PRODUCT]["RICE_MILL_A"]) == {"P"}
    assert set(forward_context[EXPECTED_PRODUCT]["DC_KANTO"]) == {"S"}
    assert set(forward_context[EXPECTED_PRODUCT]["FARM_REGION_A"]["P"]) == EXPECTED_WEEKS
    assert set(forward_context[EXPECTED_PRODUCT]["RICE_MILL_A"]["P"]) == EXPECTED_WEEKS
    assert set(forward_context[EXPECTED_PRODUCT]["DC_KANTO"]["S"]) == EXPECTED_WEEKS
    assert forward_context[EXPECTED_PRODUCT]["FARM_REGION_A"]["P"]["2027-W40"] == 120
    assert forward_context[EXPECTED_PRODUCT]["RICE_MILL_A"]["P"]["2027-W40"] == 100
    assert forward_context[EXPECTED_PRODUCT]["DC_KANTO"]["S"]["2027-W40"] == 90
