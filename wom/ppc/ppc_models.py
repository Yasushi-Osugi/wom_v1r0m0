"""
wom/ppc/ppc_models.py
=====================
Data classes for PPC (Profit / Price / Cost) Simulation Engine.

Design:
    - PPCEvent: single financial event on the supply chain (immutable record)
    - PPCTrustEvent: reconciliation alert for a lot
    - LotCostAccumulator: mutable per-lot cost state during computation
    - PPCSimulationResult: final output bundle

PPC Event types:
    Forward:
        supplier_cost          - material purchase at Supplier node
        conversion_cost        - production cost at MOM node
        transfer_price_set     - transfer price determined at MOM (informational)
        logistics_cost         - freight cost on an edge
        insurance_cost         - insurance on an edge
        tariff_cost            - import duty on cross-border edge
        landed_cost_total      - sum of transfer + logistics + insurance + tariff (informational)
        warehouse_cost         - storage cost at DAD/Operation node
        sga_cost               - selling/general/admin cost at a node
        marketing_cost         - marketing cost at a node
        hq_royalty             - global HQ brand royalty (future)
    Revenue:
        market_revenue         - sale revenue at leaf_out (market channel)
    Backward:
        backward_allowable     - allowable cost computed backward from market price

Trust Event types (reconciliation):
    NEGATIVE_MARGIN                - forward cost > backward allowable at leaf_out
    TARIFF_SHOCK                   - tariff cost > 20% of transfer price
    LANDED_COST_EXCEEDS_MARKET     - landed cost at DAD > market price
    MOM_PROFIT_TOO_LOW             - MOM gross profit < 0
    CHANNEL_MARGIN_TOO_LOW         - channel gross margin < 5%
    HQ_ROYALTY_BURDEN_TOO_HIGH     - royalty > 10% of market price
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# PPCEvent
# ---------------------------------------------------------------------------
@dataclass
class PPCEvent:
    """
    A single financial event in the PPC Simulation Engine.

    All amounts are in both local currency and base currency (JPY by default).
    """
    event_id:            str
    week:                str         # ISO week, e.g. "2026-W01"
    lot_id:              str
    node_id:             str
    edge_id:             str         # "" if pure node event
    product_id:          str
    qty:                 int         # always 1 per lot in WOM
    ppc_event_type:      str         # see module docstring
    amount_local:        float       # amount in local (transaction) currency
    currency:            str         # local currency code
    fx_rate:             float       # local → base_currency conversion rate
    amount_base:         float       # amount in base currency
    amount_per_unit_base: float      # amount_base / qty
    source_rule:         str         # which master rule triggered this event
    direction:           str         # "forward" | "backward" | "revenue"
    profit_zone:         str         # OUTBOUND_CHANNEL_PROFIT / MOM_PLANT_PROFIT / etc.


# ---------------------------------------------------------------------------
# PPCTrustEvent  (Reconciliation alert)
# ---------------------------------------------------------------------------
@dataclass
class PPCTrustEvent:
    """
    Generated when reconciliation detects an unresolvable gap.
    Named after WOM's general Trust-Event concept.
    """
    lot_id:                     str
    week:                       str
    channel_node:               str
    product_id:                 str
    trust_event_type:           str    # see module docstring
    forward_cost_base:          float  # total forward cost in base currency
    backward_allowable_base:    float  # backward allowable cost in base currency
    gap_base:                   float  # forward_cost - backward_allowable (>0 = deficit)
    message:                    str


# ---------------------------------------------------------------------------
# LotCostAccumulator  (mutable, internal use during computation)
# ---------------------------------------------------------------------------
@dataclass
class LotCostAccumulator:
    """
    Mutable per-lot state accumulated during forward propagation.
    Converted to PPCEvents when each cost item is finalized.
    """
    lot_id:             str
    week:               str
    product_id:         str
    channel_node:       str         # leaf_out node_id (destination channel)

    # Forward costs (in base currency)
    supplier_cost_base:     float = 0.0
    conversion_cost_base:   float = 0.0
    logistics_in_base:      float = 0.0   # inbound logistics (Supplier→MOM edge)
    tariff_in_base:         float = 0.0   # import duty CN→JP
    insurance_in_base:      float = 0.0   # insurance on CN→JP edge
    logistics_out_base:     float = 0.0   # outbound logistics (DAD→Channel edge)
    tariff_out_base:        float = 0.0   # import duty JP→US (if applicable)
    warehouse_base:         float = 0.0   # DAD warehouse cost
    dad_sga_base:           float = 0.0   # DAD SGA
    channel_sga_base:       float = 0.0   # Channel SGA
    channel_marketing_base: float = 0.0   # Channel marketing

    # Transfer price (in base currency, for reference)
    transfer_price_local:   float = 0.0   # CNY
    transfer_price_base:    float = 0.0   # JPY

    # Revenue (in base currency)
    market_revenue_base:    float = 0.0

    # Backward allowable (in base currency)
    backward_allowable_base: float = 0.0

    def total_forward_cost_base(self) -> float:
        return (
            self.supplier_cost_base
            + self.conversion_cost_base
            + self.logistics_in_base
            + self.tariff_in_base
            + self.insurance_in_base
            + self.logistics_out_base
            + self.tariff_out_base
            + self.warehouse_base
            + self.dad_sga_base
            + self.channel_sga_base
            + self.channel_marketing_base
        )

    def gross_profit_base(self) -> float:
        return self.market_revenue_base - self.total_forward_cost_base()

    def gross_margin_pct(self) -> float:
        if self.market_revenue_base <= 0:
            return 0.0
        return self.gross_profit_base() / self.market_revenue_base


# ---------------------------------------------------------------------------
# PPCSimulationResult
# ---------------------------------------------------------------------------
@dataclass
class PPCSimulationResult:
    """
    Complete output of one PPC simulation run.
    """
    base_currency:          str
    lot_accumulators:       List[LotCostAccumulator]
    ppc_events:             List[PPCEvent]
    trust_events:           List[PPCTrustEvent]
    node_week_summary:      "pd.DataFrame"   # type: ignore
    profit_zone_summary:    "pd.DataFrame"   # type: ignore
    lot_reconciliation:     "pd.DataFrame"   # type: ignore
    kpi_summary:            Dict
