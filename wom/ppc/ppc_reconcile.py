"""
wom/ppc/ppc_reconcile.py
========================
Step 6: Lot-based PPC Reconciliation.

Compares forward cost (total_forward_cost_base) vs
backward allowable cost (backward_allowable_base) for each lot.

A gap > 0 means: forward cost exceeds what the market "allows".
That lot is unprofitable at current prices/costs/tariffs.

PPC_TRUST_EVENT types generated:
    NEGATIVE_MARGIN          - gross profit < 0  (forward > market revenue)
    CHANNEL_MARGIN_TOO_LOW   - gross margin < 5%
    MOM_PROFIT_TOO_LOW       - MOM profit (transfer_price - supply_cost) < 0
    TARIFF_SHOCK             - tariff cost > 20% of transfer price
    LANDED_COST_EXCEEDS_MARKET - landed cost at DAD > market price

Multiple trust events can fire for the same lot.

Output:
    - List[PPCTrustEvent]
    - lot_reconciliation DataFrame (one row per lot)
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from .ppc_models import LotCostAccumulator, PPCTrustEvent


# Thresholds (could be made configurable in future)
CHANNEL_MARGIN_FLOOR = 0.05   # 5% gross margin minimum
TARIFF_SHOCK_RATIO   = 0.20   # tariff > 20% of transfer price → shock
MOM_PROFIT_FLOOR     = 0.0    # MOM profit >= 0


def run_reconciliation(
    accumulators: List[LotCostAccumulator],
) -> Tuple[List[PPCTrustEvent], pd.DataFrame]:
    """
    Step 6: Generate PPCTrustEvents and lot_reconciliation DataFrame.

    Parameters
    ----------
    accumulators : list of LotCostAccumulator (all forward + backward complete)

    Returns
    -------
    (trust_events, lot_reconciliation_df)
        lot_reconciliation_df columns:
            lot_id, week, channel_node, product_id,
            forward_cost_base, backward_allowable_base,
            gap_base, market_revenue_base, gross_profit_base,
            gross_margin_pct, trust_events_fired
    """
    trust_events: List[PPCTrustEvent] = []
    rows = []

    for acc in accumulators:
        forward_cost = acc.total_forward_cost_base()
        backward_allow = acc.backward_allowable_base
        gap = forward_cost - backward_allow
        gross_profit = acc.gross_profit_base()
        gross_margin = acc.gross_margin_pct()

        fired: List[str] = []

        # ── Check 1: Negative margin ───────────────────────────────────
        if gross_profit < 0:
            msg = (
                f"NEGATIVE_MARGIN: lot={acc.lot_id} week={acc.week} "
                f"channel={acc.channel_node} "
                f"gross_profit={gross_profit:,.0f} {''}"
            )
            trust_events.append(PPCTrustEvent(
                lot_id=acc.lot_id,
                week=acc.week,
                channel_node=acc.channel_node,
                product_id=acc.product_id,
                trust_event_type="NEGATIVE_MARGIN",
                forward_cost_base=forward_cost,
                backward_allowable_base=backward_allow,
                gap_base=gap,
                message=msg,
            ))
            fired.append("NEGATIVE_MARGIN")

        # ── Check 2: Channel margin too low ───────────────────────────
        elif gross_margin < CHANNEL_MARGIN_FLOOR:
            msg = (
                f"CHANNEL_MARGIN_TOO_LOW: lot={acc.lot_id} week={acc.week} "
                f"channel={acc.channel_node} margin={gross_margin:.1%} "
                f"< floor={CHANNEL_MARGIN_FLOOR:.0%}"
            )
            trust_events.append(PPCTrustEvent(
                lot_id=acc.lot_id,
                week=acc.week,
                channel_node=acc.channel_node,
                product_id=acc.product_id,
                trust_event_type="CHANNEL_MARGIN_TOO_LOW",
                forward_cost_base=forward_cost,
                backward_allowable_base=backward_allow,
                gap_base=gap,
                message=msg,
            ))
            fired.append("CHANNEL_MARGIN_TOO_LOW")

        # ── Check 3: MOM profit too low ────────────────────────────────
        mom_supply_cost = (
            acc.supplier_cost_base
            + acc.conversion_cost_base
            + acc.logistics_in_base
        )
        mom_profit = acc.transfer_price_base - mom_supply_cost
        if mom_profit < MOM_PROFIT_FLOOR:
            msg = (
                f"MOM_PROFIT_TOO_LOW: lot={acc.lot_id} week={acc.week} "
                f"mom_profit={mom_profit:,.0f}"
            )
            trust_events.append(PPCTrustEvent(
                lot_id=acc.lot_id,
                week=acc.week,
                channel_node=acc.channel_node,
                product_id=acc.product_id,
                trust_event_type="MOM_PROFIT_TOO_LOW",
                forward_cost_base=forward_cost,
                backward_allowable_base=backward_allow,
                gap_base=gap,
                message=msg,
            ))
            fired.append("MOM_PROFIT_TOO_LOW")

        # ── Check 4: Tariff shock ──────────────────────────────────────
        total_tariff = acc.tariff_in_base + acc.tariff_out_base
        if acc.transfer_price_base > 0:
            tariff_ratio = total_tariff / acc.transfer_price_base
            if tariff_ratio > TARIFF_SHOCK_RATIO:
                msg = (
                    f"TARIFF_SHOCK: lot={acc.lot_id} week={acc.week} "
                    f"tariff_ratio={tariff_ratio:.1%} > {TARIFF_SHOCK_RATIO:.0%}"
                )
                trust_events.append(PPCTrustEvent(
                    lot_id=acc.lot_id,
                    week=acc.week,
                    channel_node=acc.channel_node,
                    product_id=acc.product_id,
                    trust_event_type="TARIFF_SHOCK",
                    forward_cost_base=forward_cost,
                    backward_allowable_base=backward_allow,
                    gap_base=gap,
                    message=msg,
                ))
                fired.append("TARIFF_SHOCK")

        # ── Check 5: Landed cost exceeds market price ──────────────────
        landed_cost = (
            acc.transfer_price_base
            + acc.logistics_in_base
            + acc.insurance_in_base
            + acc.tariff_in_base
        )
        if landed_cost > acc.market_revenue_base:
            msg = (
                f"LANDED_COST_EXCEEDS_MARKET: lot={acc.lot_id} "
                f"landed={landed_cost:,.0f} > market={acc.market_revenue_base:,.0f}"
            )
            trust_events.append(PPCTrustEvent(
                lot_id=acc.lot_id,
                week=acc.week,
                channel_node=acc.channel_node,
                product_id=acc.product_id,
                trust_event_type="LANDED_COST_EXCEEDS_MARKET",
                forward_cost_base=forward_cost,
                backward_allowable_base=backward_allow,
                gap_base=gap,
                message=msg,
            ))
            fired.append("LANDED_COST_EXCEEDS_MARKET")

        rows.append({
            "lot_id":                   acc.lot_id,
            "week":                     acc.week,
            "channel_node":             acc.channel_node,
            "product_id":               acc.product_id,
            "forward_cost_base":        forward_cost,
            "backward_allowable_base":  backward_allow,
            "gap_base":                 gap,
            "market_revenue_base":      acc.market_revenue_base,
            "gross_profit_base":        gross_profit,
            "gross_margin_pct":         gross_margin,
            "transfer_price_base":      acc.transfer_price_base,
            "tariff_in_base":           acc.tariff_in_base,
            "tariff_out_base":          acc.tariff_out_base,
            "trust_events_fired":       "|".join(fired) if fired else "",
        })

    lot_df = pd.DataFrame(rows)
    return trust_events, lot_df
