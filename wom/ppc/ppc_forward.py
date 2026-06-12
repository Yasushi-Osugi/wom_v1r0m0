"""
wom/ppc/ppc_forward.py
=======================
Step 1: Supplier Offering Cost Forward Propagation.

Walks the supply chain path from Supplier → MOM, accumulating costs
per lot. Generates PPCEvents for each cost item.

Design:
    - Input: LotCostAccumulator list (lot_id, week, channel)
    - Output: PPCEvent list (supplier_cost, conversion_cost events)
    - transfer_price is NOT set here (see ppc_transfer.py, Step 2)
    - Inbound edge logistics/insurance added here (before tariff)
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

from .ppc_models import LotCostAccumulator, PPCEvent
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet


def run_forward_propagation(
    accumulators: List[LotCostAccumulator],
    rules: PPCRuleSet,
    fx: FXConverter,
    sc_paths: Dict[str, List[Tuple[str, str, str]]],
    mom_node: str = "MOM_China",
    supplier_node: str = "Supplier_CN",
) -> List[PPCEvent]:
    """
    Step 1: Forward cost accumulation from Supplier → MOM.

    Parameters
    ----------
    accumulators  : mutable list; updates supplier_cost_base, conversion_cost_base, etc.
    rules         : PPCRuleSet
    fx            : FXConverter
    sc_paths      : channel_node → [(node_id, edge_id, country), ...]
                    in supply-chain order (Supplier first, market channel last)
    mom_node      : MOM node_id string
    supplier_node : leaf_in (Supplier) node_id string

    Returns
    -------
    List of PPCEvent (forward direction)
    """
    events: List[PPCEvent] = []
    _event_counter = itertools.count(1)

    for acc in accumulators:
        channel = acc.channel_node
        path = sc_paths.get(channel, [])
        product = acc.product_id
        week = acc.week

        # ── Step 1a: Supplier purchase cost ───────────────────────────
        price_local, currency = rules.get_supplier_cost(supplier_node, product, week)
        fx_rate, price_base = fx.convert(price_local, currency, week)

        acc.supplier_cost_base += price_base
        profit_zone = rules.get_profit_zone(supplier_node, product)

        events.append(PPCEvent(
            event_id=f"FWD-{next(_event_counter):06d}",
            week=week,
            lot_id=acc.lot_id,
            node_id=supplier_node,
            edge_id="",
            product_id=product,
            qty=1,
            ppc_event_type="supplier_cost",
            amount_local=price_local,
            currency=currency,
            fx_rate=fx_rate,
            amount_base=price_base,
            amount_per_unit_base=price_base,
            source_rule="ppc_supplier_cost.csv",
            direction="forward",
            profit_zone=profit_zone,
        ))

        # ── Step 1b: Inbound edge (Supplier → MOM) logistics ──────────
        inbound_edge = f"{supplier_node}->{mom_node}"
        for _, row in rules.get_edge_costs(inbound_edge, product).iterrows():
            if row["cost_type"] == "logistics_cost":
                e_amount_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
                e_currency = str(row["currency"])
                if e_amount_local == 0:
                    continue
                e_fx_rate, e_amount_base = fx.convert(e_amount_local, e_currency, week)
                acc.logistics_in_base += e_amount_base
                events.append(PPCEvent(
                    event_id=f"FWD-{next(_event_counter):06d}",
                    week=week,
                    lot_id=acc.lot_id,
                    node_id=mom_node,
                    edge_id=inbound_edge,
                    product_id=product,
                    qty=1,
                    ppc_event_type="logistics_cost",
                    amount_local=e_amount_local,
                    currency=e_currency,
                    fx_rate=e_fx_rate,
                    amount_base=e_amount_base,
                    amount_per_unit_base=e_amount_base,
                    source_rule="ppc_edge_cost_rule.csv",
                    direction="forward",
                    profit_zone=rules.get_profit_zone(mom_node, product),
                ))

        # ── Step 1c: MOM conversion cost ──────────────────────────────
        mom_profit_zone = rules.get_profit_zone(mom_node, product)
        for _, row in rules.get_node_costs(mom_node, product).iterrows():
            if row["cost_type"] != "conversion_cost":
                continue
            c_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            c_currency = str(row["currency"])
            c_fx_rate, c_base = fx.convert(c_local, c_currency, week)
            acc.conversion_cost_base += c_base
            events.append(PPCEvent(
                event_id=f"FWD-{next(_event_counter):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=mom_node,
                edge_id="",
                product_id=product,
                qty=1,
                ppc_event_type="conversion_cost",
                amount_local=c_local,
                currency=c_currency,
                fx_rate=c_fx_rate,
                amount_base=c_base,
                amount_per_unit_base=c_base,
                source_rule="ppc_node_cost_rule.csv",
                direction="forward",
                profit_zone=mom_profit_zone,
            ))

    return events
