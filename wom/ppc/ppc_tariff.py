"""
wom/ppc/ppc_tariff.py
=====================
Step 3: Tariff & Landed Cost Calculation.

Applies import duty and logistics/insurance on cross-border edges.
Uses FIXED transfer_price from Step 2 (never recomputed here).

Landed cost formula:
    landed_cost = transfer_price + logistics + insurance + tariff

Tariff basis options (configured in ppc_tariff_rule.csv):
    transfer_price  - tariff on MOM's transfer price (most common)
    material_cost   - tariff on supplier cost only
    declared_value  - fixed declared value (future)

Edge processing order in Vertical Slice:
    1. MOM_China -> DAD_Japan   (CN→JP cross-border: tariff_rate=0.05)
    2. DAD_Japan -> US_Channel  (JP→US cross-border: tariff_rate=0.10)
    3. DAD_Japan -> JP_Channel  (domestic JP: no tariff)
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

from .ppc_models import LotCostAccumulator, PPCEvent
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet


def run_tariff_and_landed_cost(
    accumulators: List[LotCostAccumulator],
    rules: PPCRuleSet,
    fx: FXConverter,
    sc_paths: Dict[str, List[Tuple[str, str, str]]],
    mom_node: str = "MOM_China",
    dad_node: str = "DAD_Japan",
) -> List[PPCEvent]:
    """
    Step 3: Tariff, logistics (outbound), and landed cost events.

    Processes:
        a) MOM→DAD edge: tariff + logistics + insurance (inbound cross-border)
        b) DAD→Channel edge: logistics + tariff if JP→US (outbound)
        c) DAD node costs: warehouse, SGA

    Parameters
    ----------
    accumulators : mutable; updates tariff_in_base, logistics_out_base, etc.
    rules        : PPCRuleSet
    fx           : FXConverter
    sc_paths     : channel → [(node_id, edge_id, country), ...]
    mom_node     : MOM node id (transfer price origin)
    dad_node     : DAD (Distribution After Decoupling) node id

    Returns
    -------
    List of PPCEvent
    """
    events: List[PPCEvent] = []
    _ctr = itertools.count(1)

    for acc in accumulators:
        product = acc.product_id
        week = acc.week
        channel = acc.channel_node

        # ── a) MOM → DAD cross-border edge ────────────────────────────
        inbound_edge = f"{mom_node}->{dad_node}"

        # a-1) Tariff (CN→JP)
        tariff_row = rules.get_tariff(inbound_edge, product)
        if tariff_row is not None:
            tariff_rate = float(tariff_row["tariff_rate"])
            tariff_basis = str(tariff_row["tariff_basis"])

            if tariff_basis == "transfer_price":
                basis_local = acc.transfer_price_local
                # transfer_price is in CNY; tariff also in CNY
                tp_currency = "CNY"
            elif tariff_basis == "material_cost":
                # supplier cost in CNY
                mom_fx_rate, _ = fx.get_rate(week, "CNY")
                basis_local = acc.supplier_cost_base / mom_fx_rate if mom_fx_rate else 0.0
                tp_currency = "CNY"
            else:
                basis_local = acc.transfer_price_local
                tp_currency = "CNY"

            tariff_local = basis_local * tariff_rate
            t_fx_rate, tariff_base = fx.convert(tariff_local, tp_currency, week)
            acc.tariff_in_base += tariff_base

            events.append(PPCEvent(
                event_id=f"TAR-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=dad_node,
                edge_id=inbound_edge,
                product_id=product,
                qty=1,
                ppc_event_type="tariff_cost",
                amount_local=tariff_local,
                currency=tp_currency,
                fx_rate=t_fx_rate,
                amount_base=tariff_base,
                amount_per_unit_base=tariff_base,
                source_rule="ppc_tariff_rule.csv",
                direction="forward",
                profit_zone=rules.get_profit_zone(dad_node, product),
            ))

        # a-2) Edge logistics + insurance (MOM→DAD)
        for _, row in rules.get_edge_costs(inbound_edge, product).iterrows():
            ct = str(row["cost_type"])
            if ct not in ("logistics_cost", "insurance_cost"):
                continue

            e_currency = str(row["currency"])
            if ct == "insurance_cost":
                # basis = transfer_price in the same currency
                if e_currency == "CNY":
                    base_val = acc.transfer_price_local
                else:
                    base_val = acc.transfer_price_base
                e_local = float(row["rate"]) * base_val + float(row["fixed_amount"])
            else:
                e_local = float(row["rate"]) * 1 + float(row["fixed_amount"])

            if e_local == 0:
                continue

            e_fx_rate, e_base = fx.convert(e_local, e_currency, week)
            acc.logistics_in_base += e_base  # reuse field for CN→JP leg logistics

            events.append(PPCEvent(
                event_id=f"TAR-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=dad_node,
                edge_id=inbound_edge,
                product_id=product,
                qty=1,
                ppc_event_type=ct,
                amount_local=e_local,
                currency=e_currency,
                fx_rate=e_fx_rate,
                amount_base=e_base,
                amount_per_unit_base=e_base,
                source_rule="ppc_edge_cost_rule.csv",
                direction="forward",
                profit_zone=rules.get_profit_zone(dad_node, product),
            ))

        # ── a-3) Landed cost informational event ──────────────────────
        landed_base = (
            acc.transfer_price_base
            + acc.logistics_in_base
            + acc.insurance_in_base
            + acc.tariff_in_base
        )
        events.append(PPCEvent(
            event_id=f"TAR-{next(_ctr):06d}",
            week=week,
            lot_id=acc.lot_id,
            node_id=dad_node,
            edge_id=inbound_edge,
            product_id=product,
            qty=1,
            ppc_event_type="landed_cost_total",
            amount_local=landed_base,  # in base currency for simplicity
            currency=fx.base_currency,
            fx_rate=1.0,
            amount_base=landed_base,
            amount_per_unit_base=landed_base,
            source_rule="computed",
            direction="forward",
            profit_zone=rules.get_profit_zone(dad_node, product),
        ))

        # ── b) DAD node costs (warehouse, SGA) ────────────────────────
        dad_profit_zone = rules.get_profit_zone(dad_node, product)
        for _, row in rules.get_node_costs(dad_node, product).iterrows():
            ct = str(row["cost_type"])
            n_currency = str(row["currency"])
            n_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            n_fx_rate, n_base = fx.convert(n_local, n_currency, week)

            if ct == "warehouse_cost":
                acc.warehouse_base += n_base
            elif ct == "sga_cost":
                acc.dad_sga_base += n_base

            events.append(PPCEvent(
                event_id=f"DAD-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=dad_node,
                edge_id="",
                product_id=product,
                qty=1,
                ppc_event_type=ct,
                amount_local=n_local,
                currency=n_currency,
                fx_rate=n_fx_rate,
                amount_base=n_base,
                amount_per_unit_base=n_base,
                source_rule="ppc_node_cost_rule.csv",
                direction="forward",
                profit_zone=dad_profit_zone,
            ))

        # ── c) DAD → Channel edge ──────────────────────────────────────
        outbound_edge = f"{dad_node}->{channel}"
        out_profit_zone = rules.get_profit_zone(channel, product)

        # c-1) Outbound logistics
        for _, row in rules.get_edge_costs(outbound_edge, product).iterrows():
            ct = str(row["cost_type"])
            e_currency = str(row["currency"])
            e_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            e_fx_rate, e_base = fx.convert(e_local, e_currency, week)
            acc.logistics_out_base += e_base

            events.append(PPCEvent(
                event_id=f"OUT-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=channel,
                edge_id=outbound_edge,
                product_id=product,
                qty=1,
                ppc_event_type=ct,
                amount_local=e_local,
                currency=e_currency,
                fx_rate=e_fx_rate,
                amount_base=e_base,
                amount_per_unit_base=e_base,
                source_rule="ppc_edge_cost_rule.csv",
                direction="forward",
                profit_zone=out_profit_zone,
            ))

        # c-2) Outbound tariff (JP→US only)
        out_tariff_row = rules.get_tariff(outbound_edge, product)
        if out_tariff_row is not None:
            t_rate = float(out_tariff_row["tariff_rate"])
            t_basis = str(out_tariff_row["tariff_basis"])

            if t_basis == "transfer_price":
                basis_local = acc.transfer_price_local
                t_currency = "CNY"
            else:
                basis_local = acc.transfer_price_local
                t_currency = "CNY"

            t_local = basis_local * t_rate
            t_fx_rate, t_base = fx.convert(t_local, t_currency, week)
            acc.tariff_out_base += t_base

            events.append(PPCEvent(
                event_id=f"OUT-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=channel,
                edge_id=outbound_edge,
                product_id=product,
                qty=1,
                ppc_event_type="tariff_cost",
                amount_local=t_local,
                currency=t_currency,
                fx_rate=t_fx_rate,
                amount_base=t_base,
                amount_per_unit_base=t_base,
                source_rule="ppc_tariff_rule.csv",
                direction="forward",
                profit_zone=out_profit_zone,
            ))

    return events
