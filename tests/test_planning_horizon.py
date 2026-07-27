from pathlib import Path
import pandas as pd
import pytest
from wom.config import WOMConfig
from wom.planning_horizon import (
    PlanningHorizon, autodetect_horizon, load_planning_horizon, ppc_horizons,
)
from wom.engine.scenario import ScenarioManager
from wom.data.schema import Cols
from wom.model.plan_node import NODE_TYPE_LEAF_OUT, S
from wom.ppc.ppc_psi_bridge import psi_to_sales_records

MODEL = Path("data/sample/soysauce-us-2027")


def test_iso_week_generation_crosses_2026_w53():
    config = WOMConfig(start_week="2026-W33", num_weeks=125,
                       reporting_start_week="2027-W01", reporting_weeks=104)
    assert len(config.weeks) == 125
    assert config.weeks[0] == "2026-W33"
    assert "2026-W53" in config.weeks
    assert config.weeks[-1] == "2028-W52"


def test_explicit_horizon_config():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    assert (horizon.planning_start_week, horizon.planning_weeks,
            horizon.reporting_start_week, horizon.reporting_weeks) == (
                "2026-W33", 125, "2027-W01", 104)


def test_legacy_autodetect_defaults_reporting_to_planning():
    horizon = autodetect_horizon(["2027-W02", "2027-W01", "2027-W02"])
    assert horizon.source == "demand-autodetect"
    assert horizon.planning_start_week == horizon.reporting_start_week == "2027-W01"
    assert horizon.planning_weeks == horizon.reporting_weeks == 2


def test_warmup_has_zero_demand_without_synthetic_rows():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    demand = pd.read_csv(MODEL / "demand_forecast.csv")
    by_week = demand.groupby("week")["quantity"].sum().to_dict()
    assert all(by_week.get(w, 0) == 0 for w in horizon.planning_week_labels[:21])
    assert by_week["2027-W01"] > 0


def test_warmup_capacity_is_explicit_and_finite():
    capacity = pd.read_csv(MODEL / "capacity_plan.csv")
    warmup = capacity[capacity["week"].between("2026-W33", "2026-W53")]
    assert warmup["week"].nunique() == 21
    expected = {"Bottling_Noda": 1500, "Brewing_Noda": 1500,
                "Materials_JP": 50000}
    for node, value in expected.items():
        rows = warmup[warmup["node_name"] == node]
        assert len(rows) == 21
        assert set(rows["max_supply"]) == {value}


@pytest.mark.parametrize("kwargs,message", [
    (dict(planning_start_week="bad", planning_weeks=1,
          reporting_start_week="2027-W01", reporting_weeks=1), "invalid ISO"),
    (dict(planning_start_week="2027-W01", planning_weeks=0,
          reporting_start_week="2027-W01", reporting_weeks=1), "> 0"),
    (dict(planning_start_week="2027-W01", planning_weeks=4,
          reporting_start_week="2027-W04", reporting_weeks=2), "inside"),
])
def test_invalid_horizon(kwargs, message):
    with pytest.raises(ValueError, match=message):
        PlanningHorizon(**kwargs)


def test_push_lead_time_and_holiday_data_unchanged():
    assert pd.read_csv(MODEL / "push_config.csv").loc[0, "push_lead_time_weeks"] == 7
    assert set(pd.read_csv(MODEL / "holiday_calendar.csv")["value"]) == {0}


def test_reporting_filter_preserves_full_internal_result():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    df = pd.DataFrame({
        Cols.SCENARIO: ["Planning"] * horizon.planning_weeks,
        Cols.SKU_ID: ["Soy_Sauce"] * horizon.planning_weeks,
        Cols.REGION: ["JP"] * horizon.planning_weeks,
        Cols.WEEK: horizon.planning_week_labels,
        Cols.DEMAND_FCST: [1] * horizon.planning_weeks,
        Cols.DEMAND_FULFILLED: [1] * horizon.planning_weeks,
        Cols.STOCKOUT_QTY: [0] * horizon.planning_weeks,
        Cols.FILL_RATE: [1] * horizon.planning_weeks,
        Cols.CLOSING_INV: [0] * horizon.planning_weeks,
        Cols.INV_COVER_WKS: [0] * horizon.planning_weeks,
        Cols.REORDER_QTY: [0] * horizon.planning_weeks,
    })
    manager = ScenarioManager(horizon.reporting_week_labels)
    manager.add("Planning", df)
    assert len(manager.get("Planning")) == 125
    assert manager.planning_combined()[Cols.WEEK].iloc[0] == "2026-W33"
    assert len(manager.combined()) == 104
    assert manager.combined()[Cols.WEEK].iloc[0] == "2027-W01"
    assert manager.combined()[Cols.WEEK].iloc[-1] == "2028-W52"


class _BridgeNode:
    node_type = NODE_TYPE_LEAF_OUT
    node_id = "OUT:leaf_out:US:Soy_Sauce"
    node_name = "US_Channel"

    def __init__(self, supply_by_index):
        self.supply_by_index = supply_by_index

    def qty_supply(self, week, bucket):
        assert bucket == S
        return self.supply_by_index.get(week, 0)


class _BridgeTree:
    products = ["Soy_Sauce"]

    def __init__(self, weeks, node):
        self.week_labels = weeks
        self.node = node

    def iter_all_nodes(self, product):
        assert product == "Soy_Sauce"
        return [self.node]


def test_ppc_bridge_resolves_reporting_subset_to_physical_week_indices():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    assert horizon.planning_week_labels.index("2027-W01") == 21
    tree = _BridgeTree(
        horizon.planning_week_labels,
        _BridgeNode({0: 900, 21: 101, 103: 151, 124: 252}),
    )

    records = psi_to_sales_records(
        tree, horizon.reporting_week_labels, use_node_name=True
    )
    by_week = records.set_index("week")["qty"].to_dict()

    assert by_week["2027-W01"] == 101
    assert "2026-W33" not in by_week
    assert by_week["2028-W31"] == 151
    assert by_week["2028-W52"] == 252
    assert records["week"].min() == "2027-W01"
    assert records["week"].max() == "2028-W52"


def test_ppc_bridge_full_horizon_retains_warmup_and_final_bucket():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    tree = _BridgeTree(
        horizon.planning_week_labels,
        _BridgeNode({0: 33, 21: 101, 124: 852}),
    )

    records = psi_to_sales_records(
        tree, horizon.planning_week_labels, use_node_name=True
    )
    by_week = records.set_index("week")["qty"].to_dict()

    assert by_week == {
        "2026-W33": 33,
        "2027-W01": 101,
        "2028-W52": 852,
    }


def test_gui_ppc_boundary_passes_full_planning_and_separate_reporting_horizon():
    horizon = load_planning_horizon(MODEL / "planning_horizon.csv")
    valuation_weeks, reporting_weeks = ppc_horizons(
        horizon.planning_week_labels,
        horizon.reporting_start_week,
        horizon.reporting_weeks,
    )

    assert (valuation_weeks[0], valuation_weeks[-1], len(valuation_weeks)) == (
        "2026-W33", "2028-W52", 125,
    )
    assert (reporting_weeks[0], reporting_weeks[-1], len(reporting_weeks)) == (
        "2027-W01", "2028-W52", 104,
    )
