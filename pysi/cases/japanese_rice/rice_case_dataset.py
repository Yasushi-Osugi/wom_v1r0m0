from __future__ import annotations

from dataclasses import dataclass


SCENARIO_ID = "RICE_AS_IS"
PRODUCT_ID = "PACKAGED_RICE_STANDARD"


@dataclass(frozen=True)
class RiceSupplyPlanRow:
    scenario_id: str
    node_id: str
    product_id: str
    week: str
    supply_qty: float
    supply_type: str
    source_type: str
    comment: str = ""


@dataclass(frozen=True)
class RiceDemandPlanRow:
    scenario_id: str
    demand_node_id: str
    region: str
    product_id: str
    week: str
    demand_qty: float
    demand_type: str
    priority: int = 100
    comment: str = ""


@dataclass(frozen=True)
class RiceCostPrice:
    cost_price_type: str
    unit_value: float


@dataclass(frozen=True)
class RiceCaseDataset:
    scenario_id: str
    weeks: list[str]
    supply_plan: list[RiceSupplyPlanRow]
    demand_plan: list[RiceDemandPlanRow]
    cost_price: dict[str, float]
    storage_capacity: float
    milling_capacity: float
    transport_capacity: float


def build_weeks(year: int = 2026) -> list[str]:
    return [f"{year}-W{i:02d}" for i in range(1, 53)]


def build_default_rice_case_dataset() -> RiceCaseDataset:
    weeks = build_weeks(2026)

    harvest_supply = {
        "2026-W40": 20.0,
        "2026-W41": 30.0,
        "2026-W42": 30.0,
        "2026-W43": 15.0,
        "2026-W44": 5.0,
    }
    supply_plan = [
        RiceSupplyPlanRow(
            scenario_id=SCENARIO_ID,
            node_id="PRODUCER_NIIGATA",
            product_id=PRODUCT_ID,
            week=week,
            supply_qty=qty,
            supply_type="HARVEST",
            source_type="DOMESTIC",
            comment="MVP fixed harvest supply pattern",
        )
        for week, qty in harvest_supply.items()
    ]

    demand_plan: list[RiceDemandPlanRow] = []
    for week in weeks:
        demand_plan.append(
            RiceDemandPlanRow(
                scenario_id=SCENARIO_ID,
                demand_node_id="DEMAND_HOUSEHOLD_TOKYO",
                region="TOKYO",
                product_id=PRODUCT_ID,
                week=week,
                demand_qty=1.0,
                demand_type="HOUSEHOLD",
                comment="MVP household demand",
            )
        )
        demand_plan.append(
            RiceDemandPlanRow(
                scenario_id=SCENARIO_ID,
                demand_node_id="DEMAND_FOOD_SERVICE_TOKYO",
                region="TOKYO",
                product_id=PRODUCT_ID,
                week=week,
                demand_qty=0.6,
                demand_type="FOOD_SERVICE",
                comment="MVP food service demand",
            )
        )

    # Modeling assumptions for MVP smoke only (not real market values)
    cost_price = {
        "purchase_cost_per_lot": 250_000.0,
        "storage_cost_per_lot_week": 5_000.0,
        "milling_cost_per_lot": 30_000.0,
        "transport_cost_per_lot": 20_000.0,
        "selling_price_per_lot": 500_000.0,
    }

    return RiceCaseDataset(
        scenario_id=SCENARIO_ID,
        weeks=weeks,
        supply_plan=supply_plan,
        demand_plan=demand_plan,
        cost_price=cost_price,
        storage_capacity=100.0,
        milling_capacity=5.0,
        transport_capacity=5.0,
    )
