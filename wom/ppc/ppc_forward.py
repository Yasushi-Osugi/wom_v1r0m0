"""
wom/ppc/ppc_forward.py
=======================
Step 1: Supplier Offering Cost Forward Propagation.

Walks the supply chain path from Supplier -> MOM, accumulating costs
per lot. Generates PPCEvents for each cost item.

Design:
    - Input: LotCostAccumulator list (lot_id, week, channel)
    - Output: PPCEvent list (supplier_cost, conversion_cost events)
    - transfer_price is NOT set here (see ppc_transfer.py, Step 2)
    - Inbound edge logistics/insurance added here (before tariff)

Node parameters (supplier_node, mom_node) accept either str or
dict[product_id -> node_id] for multi-product models.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple, Union

from .ppc_models import LotCostAccumulator, PPCEvent
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet


def _resolve_node(node: Union[str, Dict[str, str]], product_id: str) -> str:
    """Resolve node name: accepts str or dict[product_id -> node_id]."""
    if isinstance(node, dict):
        return node.get(product_id, next(iter(node.values()), ""))
    return node


def _resolve_node_list(
    node: Union[str, List[str], Dict[str, str], Dict[str, List[str]]],
    product_id: str,
) -> List[str]:
    """Resolve supplier_node to an ordered list of node_ids for a product.

    Accepts (in order of precedence):
      dict[str, list]  -> node[product_id]                (multi-supplier, per product)
      dict[str, str]   -> [node[product_id]]               (single-supplier, per product; legacy)
      list[str]        -> node                              (multi-supplier, same for all products)
      str              -> [node]                             (single-supplier; legacy default)
    Falls back to the first available product's value if product_id is missing,
    matching the legacy _resolve_node behavior.
    """
    if isinstance(node, dict):
        val = node.get(product_id, next(iter(node.values()), []))
        if isinstance(val, list):
            return val
        return [val] if val else []
    if isinstance(node, list):
        return node
    return [node] if node else []


def run_forward_propagation(
    accumulators: List[LotCostAccumulator],
    rules: PPCRuleSet,
    fx: FXConverter,
    sc_paths: Dict[str, List[Tuple[str, str, str]]],
    mom_node: Union[str, Dict[str, str]] = "MOM_China",
    supplier_node: Union[str, List[str], Dict[str, str], Dict[str, List[str]]] = "Supplier_CN",
) -> List[PPCEvent]:
    """
    Step 1: Forward cost accumulation from Supplier(s) -> MOM.

    Parameters
    ----------
    accumulators  : mutable list; updates supplier_cost_base, conversion_cost_base, etc.
    rules         : PPCRuleSet
    fx            : FXConverter
    sc_paths      : channel_node -> [(node_id, edge_id, country), ...]
                    in supply-chain order (Supplier first, market channel last)
    mom_node      : MOM node_id string OR dict[product_id -> node_id]
    supplier_node : leaf_in (Supplier) node_id(s). Accepts a single string,
                    a list[str] (multiple Tier-1 suppliers feeding one MOM,
                    e.g. Battery/Motor/ECU), dict[product_id -> node_id], or
                    dict[product_id -> list[str]]. Every resolved supplier
                    node contributes its own supplier_cost event (so per-node
                    P&L can attribute cost to each Tier-1 supplier correctly)
                    and all of them are summed into acc.supplier_cost_base.

    Returns
    -------
    List of PPCEvent (forward direction)
    """
    events: List[PPCEvent] = []
    _event_counter = itertools.count(1)

    for acc in accumulators:
        channel = acc.channel_node
        product = acc.product_id
        week = acc.week

        s_nodes = _resolve_node_list(supplier_node, product)
        m_node = _resolve_node(mom_node, product)

        # ── Step 1a: Supplier purchase cost (one or more Tier-1 suppliers) ──
        for s_node in s_nodes:
            price_local, currency = rules.get_supplier_cost(s_node, product, week)
            fx_rate, price_base = fx.convert(price_local, currency, week)

            acc.supplier_cost_base += price_base
            profit_zone = rules.get_profit_zone(s_node, product)

            events.append(PPCEvent(
                event_id=f"FWD-{next(_event_counter):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=s_node,
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
                cost_phase="EXW",
            ))

            # ── Step 1b: Inbound edge (this Supplier -> MOM) logistics ──
            inbound_edge = f"{s_node}->{m_node}"
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
                        node_id=m_node,
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
                        profit_zone=rules.get_profit_zone(m_node, product),
                        cost_phase="FOB",
                    ))

        # ── Step 1c: MOM node costs (conversion + logistics) ─────────
        mom_profit_zone = rules.get_profit_zone(m_node, product)
        for _, row in rules.get_node_costs(m_node, product).iterrows():
            cost_type = row["cost_type"]
            if cost_type not in ("conversion_cost", "logistics_cost"):
                continue
            c_local = float(row["rate"]) * 1 + float(row["fixed_amount"])
            c_currency = str(row["currency"])
            if c_local == 0:
                continue
            c_fx_rate, c_base = fx.convert(c_local, c_currency, week)
            if cost_type == "conversion_cost":
                acc.conversion_cost_base += c_base
                ev_type   = "conversion_cost"
                ev_phase  = "MOM"
            else:
                # logistics_cost at MOM node = domestic transport to export port (FOB)
                acc.logistics_in_base += c_base
                ev_type   = "logistics_cost"
                ev_phase  = "FOB"
            events.append(PPCEvent(
                event_id=f"FWD-{next(_event_counter):06d}",
                week=week,
                lot_id=acc.lot_id,
                node_id=m_node,
                edge_id="",
                product_id=product,
                qty=1,
                ppc_event_type=ev_type,
                amount_local=c_local,
                currency=c_currency,
                fx_rate=c_fx_rate,
                amount_base=c_base,
                amount_per_unit_base=c_base,
                source_rule="ppc_node_cost_rule.csv",
                direction="forward",
                profit_zone=mom_profit_zone,
                cost_phase=ev_phase,
            ))

    return events
