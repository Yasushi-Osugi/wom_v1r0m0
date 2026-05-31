from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from dataclasses import dataclass
from typing import Any

from pysi.demand.demand_master_loader import WeeklyDemandRow

PSI_DEMAND_S_SLOT = "S"
LEGACY_PSI_DEMAND_S_INDEX = 0


@dataclass(frozen=True)
class DemandAnchoredLot:
    """A lot born from final-market demand at an outbound leaf plan_node."""

    lot_id: str
    scenario_id: str
    demand_node: str
    product_id: str
    demand_week: str
    quantity: int | float = 1
    anchor_tree_side: str = "outbound"
    anchor_node: str | None = None
    target_psi_layer: str = "demand"
    target_psi_slot: str = PSI_DEMAND_S_SLOT
    source_row_id: str | None = None
    source_granularity: str = "weekly"

    @property
    def product_name(self) -> str:
        return self.product_id

    @property
    def week(self) -> str:
        return self.demand_week


def _integer_lot_count(row: WeeklyDemandRow, lot_size: int | float) -> int:
    if lot_size <= 0:
        raise ValueError(f"lot_size must be positive, got {lot_size!r}")

    raw_count = row.demand_qty / lot_size
    if isinstance(raw_count, float) and not raw_count.is_integer():
        raise ValueError(
            "weekly demand lot generation requires integer lots for this slice "
            f"(row={row.source_id!r}, demand_qty={row.demand_qty!r}, lot_size={lot_size!r})"
        )
    return int(raw_count)


def generate_demand_anchored_lots(
    rows: Iterable[WeeklyDemandRow],
    *,
    lot_size: int | float = 1,
) -> list[DemandAnchoredLot]:
    """Generate deterministic demand lots anchored at outbound leaf nodes.

    Lot IDs are deterministic per input row and sequence number. The generated
    lots keep the final target contract explicit: outbound leaf plan_node,
    demand PSI layer, S slot.
    """

    lots: list[DemandAnchoredLot] = []
    for row in rows:
        lot_count = _integer_lot_count(row, lot_size)
        for sequence in range(1, lot_count + 1):
            lot_id = (
                f"{row.scenario_id}|{row.demand_node}|{row.product_id}|"
                f"{row.week}|{sequence:06d}"
            )
            lots.append(
                DemandAnchoredLot(
                    lot_id=lot_id,
                    scenario_id=row.scenario_id,
                    demand_node=row.demand_node,
                    product_id=row.product_id,
                    demand_week=row.week,
                    quantity=lot_size,
                    anchor_node=row.demand_node,
                    source_row_id=row.source_id,
                    source_granularity=row.source_granularity,
                )
            )
    return lots


def _ensure_symbolic_s_slot(node: Any, week: str) -> list[str]:
    psi4demand = getattr(node, "psi4demand", None)
    if psi4demand is None:
        psi4demand = {}
        setattr(node, "psi4demand", psi4demand)

    week_bucket = psi4demand.setdefault(week, {})
    if isinstance(week_bucket, MutableMapping):
        return week_bucket.setdefault(PSI_DEMAND_S_SLOT, [])
    if isinstance(week_bucket, list):
        while len(week_bucket) <= LEGACY_PSI_DEMAND_S_INDEX:
            week_bucket.append([])
        if not isinstance(week_bucket[LEGACY_PSI_DEMAND_S_INDEX], list):
            week_bucket[LEGACY_PSI_DEMAND_S_INDEX] = []
        return week_bucket[LEGACY_PSI_DEMAND_S_INDEX]
    raise TypeError(f"unsupported psi4demand week bucket for {week!r}: {type(week_bucket)!r}")


def attach_demand_lots_to_leaf_plan_node_psi4demand(
    lots: Iterable[DemandAnchoredLot],
    *,
    outbound_leaf_plan_nodes: dict[tuple[str, str], Any] | None = None,
) -> dict[str, dict[str, dict[str, dict[str, list[str]]]]]:
    """Attach/represent lots in product-specific outbound leaf plan_node PSI S slots.

    Returned shape documents the legacy-compatible target explicitly::

        product-specific outbound_tree
          -> leaf plan_node = demand_node
          -> psi4demand[week]["S"] = list[lot_id]

    When ``outbound_leaf_plan_nodes`` is supplied, matching actual nodes are also
    mutated at ``plan_node.psi4demand[week]["S"]`` or legacy index ``[0]``.
    """

    by_product_leaf: dict[str, dict[str, dict[str, dict[str, list[str]]]]] = {}
    for lot in lots:
        product = by_product_leaf.setdefault(lot.product_id, {})
        leaf = product.setdefault(lot.demand_node, {"psi4demand": {}})
        psi4demand = leaf["psi4demand"]
        week_bucket = psi4demand.setdefault(lot.demand_week, {PSI_DEMAND_S_SLOT: []})
        week_bucket.setdefault(PSI_DEMAND_S_SLOT, []).append(lot.lot_id)

        if outbound_leaf_plan_nodes is not None:
            plan_node = outbound_leaf_plan_nodes.get((lot.product_id, lot.demand_node))
            if plan_node is not None:
                _ensure_symbolic_s_slot(plan_node, lot.demand_week).append(lot.lot_id)

    return by_product_leaf
