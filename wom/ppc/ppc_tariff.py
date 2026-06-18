"""
wom/ppc/ppc_tariff.py
=====================
Step 3: Tariff & Landed Cost Calculation.

Applies import duty and logistics/insurance on cross-border edges.
Uses FIXED transfer_price from Step 2 (never recomputed here).

Landed cost formula:
    landed_cost = transfer_price + logistics + insurance + tariff

Edge processing order in Vertical Slice:
    1. MOM → DAD   (cross-border: tariff_rate from ppc_tariff_rule.csv)
    2. DAD → Channel (outbound: tariff if cross-border)
    3. DAD node costs: warehouse, SGA

mom_node and dad_node accept either str or dict[product_id -> node_id].
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple, Union

from .ppc_models import LotCostAccumulator, PPCEvent
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet


def _resolve_node(node: Union[str, Dict[str, str]], product_id: str) -> str:
    if isinstance(node, dict):
        return node.get(product_id, next(iter(node.values()), ""))
    return node


def run_tariff_and_landed_cost(
    accumulators: List[LotCostAccumulator],
    rules: PPCRuleSet,
    fx: FXConverter,
    sc_paths: Dict[str, List[Tuple[str, str, str]]],
    mom_node: Union[str, Dict[str, str]] = "MOM_China",
    dad_node: Union[str, Dict[str, str]] = "DAD_Japan",
) -> List[PPCEvent]:
    """
    Step 3: Tariff, logistics (outbound), and landed cost events.

    mom_node / dad_node accept str OR dict[product_id -> node_id].
    """
    events: List[PPCEvent] = []
    _ctr = itertools.count(1)

    for acc in accumulators:
        product = acc.product_id
        week = acc.week
        channel = acc.channel_node

        m_node = _resolve_node(mom_node, product)
        d_node = _resolve_node(dad_node, product)

        # ── a) MOM → DAD cross-border edge ────────────────────────────
        inbound_edge = f"{m_node}->{d_node}"

        # a-1) Tariff (MOM→DAD)
        tariff_row = rules.get_tariff(inbound_edge, product)
        if tariff_row is not None:
            tariff_rate = float(tariff_row["tariff_rate"])
            tariff_basis = str(tariff_row["tariff_basis"])

            # Determine the actual TP currency from transfer price rule (e.g. CNY for China)
            tp_rule = rules.get_transfer_price_rule(m_node, product)
            actual_tp_currency = str(tp_rule["currency"]) if tp_rule is not None else "JPY"

            if tariff_basis == "transfer_price":
                basis_local = acc.transfer_price_local
                tp_currency = actual_tp_currency
            elif tariff_basis == "material_cost":
                mom_fx_rate, _ = fx.get_rate(week, actual_tp_currency)
                basis_local = acc.supplier_cost_base / mom_fx_rate if mom_fx_rate else 0.0
                tp_currency = actual_tp_currency
            else:
                basis_local = acc.transfer_price_local
                tp_currency = actual_tp_currency

            tariff_local = basis_local * tariff_rate
            t_fx_rate, tariff_base = fx.convert(tariff_local, tp_currency, week)
            acc.tariff_in_base += tariff_base

            events.append(PPCEvent(
                event_id=f"TAR-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=d_node,
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
                profit_zone=rules.get_profit_zone(d_node, product),
            ))

        # a-2) Edge logistics + insurance (MOM→DAD)
        for _, row in rules.get_edge_costs(inbound_edge, product).iterrows():
            ct = str(row["cost_type"])
            if ct not in ("logistics_cost", "insurance_cost"):
                continue

            e_currency = str(row["currency"])
            if ct == "insurance_cost":
                if e_currency == "USD":
                    base_val = acc.transfer_price_local
                else:
                    base_val = acc.transfer_price_base
                e_local = float(row["rate"]) * base_val + float(row["fixed_amount"])
            else:
                e_local = float(row["rate"]) * 1 + float(row["fixed_amount"])

            if e_local == 0:
                continue

            e_fx_rate, e_base = fx.convert(e_local, e_currency, week)
            acc.logistics_in_base += e_base

            events.append(PPCEvent(
                event_id=f"TAR-{next(_ctr):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=d_node,
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
                profit_zone=rules.get_profit_zone(d_node, product),
            ))

        # a-3) Landed cost informational event
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
            node_id=d_node,
            edge_id=inbound_edge,
            product_id=product,
            qty=1,
            ppc_event_type="landed_cost_total",
            amount_local=landed_base,
            currency=fx.base_currency,
            fx_rate=1.0,
            amount_base=landed_base,
            amount_per_unit_base=landed_base,
            source_rule="computed",
            direction="forward",
            profit_zone=rules.get_profit_zone(d_node, product),
        ))

        # ── b) DAD node costs (warehouse, SGA) ────────────────────────
        dad_profit_zone = rules.get_profit_zone(d_node, product)
        for _, row in rules.get_node_costs(d_node, product).iterrows():
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
                node_id=d_node,
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
        outbound_edge = f"{d_node}->{channel}"
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

        # c-2) Outbound tariff (DAD→Channel cross-border)
        out_tariff_row = rules.get_tariff(outbound_edge, product)
        if out_tariff_row is not None:
            t_rate = float(out_tariff_row["tariff_rate"])
            t_basis = str(out_tariff_row["tariff_basis"])

            if t_basis == "transfer_price":
                basis_local = acc.transfer_price_local
                t_currency = "USD"
            else:
                basis_local = acc.transfer_price_local
                t_currency = "USD"

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
