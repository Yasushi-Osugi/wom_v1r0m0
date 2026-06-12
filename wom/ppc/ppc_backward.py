"""
wom/ppc/ppc_backward.py
=======================
Step 5: Market Requesting Price Backward Propagation (Lot-based).

Design Decision D3 (Rev.2):
    - Each lot computes its OWN backward allowable cost independently.
    - Lots going to JP_Channel start from JPY market price.
    - Lots going to US_Channel start from USD market price (different allowable).
    - Aggregation to Node/Week level is done later in ppc_kpi.py (display only).

Algorithm (per lot):
    1. Start from market_price (at channel node)
    2. Subtract channel SGA + marketing costs
       → allowable_cost_at_channel_entry
    3. Subtract outbound logistics + tariff (DAD→channel edge)
       → allowable_cost_at_DAD_exit
    4. Subtract DAD node costs (warehouse, SGA)
       → allowable_cost_at_MOM_arrival
    5. Subtract inbound tariff + logistics + insurance (MOM→DAD edge)
       → backward_requesting_price_at_MOM

The backward_requesting_price_at_MOM is compared with transfer_price
in Step 6 (reconciliation). If transfer_price > requesting_price → deficit.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

from .ppc_models import LotCostAccumulator, PPCEvent
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet


def run_backward_propagation(
    accumulators: List[LotCostAccumulator],
    rules: PPCRuleSet,
    fx: FXConverter,
    sc_paths: Dict[str, List[Tuple[str, str, str]]],
    mom_node: str = "MOM_China",
    dad_node: str = "DAD_Japan",
) -> List[PPCEvent]:
    """
    Step 5: Lot-based backward requesting price propagation.

    For each lot, compute what the market "allows" the MOM to charge,
    i.e. market_price minus all downstream costs.

    Parameters
    ----------
    accumulators : mutable; sets backward_allowable_base per lot
    rules        : PPCRuleSet
    fx           : FXConverter
    sc_paths     : channel → topology path (unused here; kept for API symmetry)
    mom_node     : MOM node id
    dad_node     : DAD node id

    Returns
    -------
    List of PPCEvent (direction="backward")
    """
    events: List[PPCEvent] = []
    _ctr = itertools.count(1)

    for acc in accumulators:
        product = acc.product_id
        week = acc.week
        channel = acc.channel_node

        # ── Start: market price in base currency ──────────────────────
        market_price_local, market_currency = rules.get_market_price(
            channel, product, week
        )
        _, market_base = fx.convert(market_price_local, market_currency, week)
        allowable = market_base

        # ── Subtract channel costs (SGA, marketing) ───────────────────
        for _, row in rules.get_node_costs(channel, product).iterrows():
            basis = str(row["basis"])
            rate = float(row["rate"])
            fixed = float(row["fixed_amount"])
            c_currency = str(row["currency"])

            if basis == "revenue":
                c_local = rate * market_price_local + fixed
            elif basis == "qty":
                c_local = rate * 1 + fixed
            else:
                c_local = fixed

            _, c_base = fx.convert(c_local, c_currency, week)
            allowable -= c_base

        # ── Subtract DAD→Channel edge costs ───────────────────────────
        outbound_edge = f"{dad_node}->{channel}"
        for _, row in rules.get_edge_costs(outbound_edge, product).iterrows():
            e_currency = str(row["currency"])
            e_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            _, e_base = fx.convert(e_local, e_currency, week)
            allowable -= e_base

        # Subtract outbound tariff (JP→US)
        out_tariff = rules.get_tariff(outbound_edge, product)
        if out_tariff is not None:
            # Backward: tariff was based on transfer_price, but in backward
            # we don't know transfer_price yet from this side — use the
            # FORWARD transfer_price (already fixed in Step 2).
            t_rate = float(out_tariff["tariff_rate"])
            t_local = acc.transfer_price_local * t_rate
            _, t_base = fx.convert(t_local, "CNY", week)
            allowable -= t_base

        # ── Subtract DAD node costs ────────────────────────────────────
        for _, row in rules.get_node_costs(dad_node, product).iterrows():
            n_currency = str(row["currency"])
            n_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            _, n_base = fx.convert(n_local, n_currency, week)
            allowable -= n_base

        # ── Subtract MOM→DAD inbound edge costs ───────────────────────
        inbound_edge = f"{mom_node}->{dad_node}"
        for _, row in rules.get_edge_costs(inbound_edge, product).iterrows():
            ct = str(row["cost_type"])
            e_currency = str(row["currency"])
            if ct == "insurance_cost":
                # Uses transfer_price as basis
                if e_currency == "CNY":
                    base_val = acc.transfer_price_local
                else:
                    base_val = acc.transfer_price_base
                e_local = float(row["rate"]) * base_val + float(row["fixed_amount"])
            else:
                e_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            _, e_base = fx.convert(e_local, e_currency, week)
            allowable -= e_base

        # Subtract inbound tariff (CN→JP)
        in_tariff = rules.get_tariff(inbound_edge, product)
        if in_tariff is not None:
            t_rate = float(in_tariff["tariff_rate"])
            t_local = acc.transfer_price_local * t_rate
            _, t_base = fx.convert(t_local, "CNY", week)
            allowable -= t_base

        # ── Store result ───────────────────────────────────────────────
        acc.backward_allowable_base = allowable

        backward_zone = rules.get_profit_zone(mom_node, product)
        events.append(PPCEvent(
            event_id=f"BWD-{next(_ctr):06d}",
            week=week,
            lot_id=acc.lot_id,
            node_id=mom_node,
            edge_id="",
            product_id=product,
            qty=1,
            ppc_event_type="backward_allowable",
            amount_local=allowable,
            currency=fx.base_currency,
            fx_rate=1.0,
            amount_base=allowable,
            amount_per_unit_base=allowable,
            source_rule="computed:market_price - downstream_costs",
            direction="backward",
            profit_zone=backward_zone,
        ))

    return events
