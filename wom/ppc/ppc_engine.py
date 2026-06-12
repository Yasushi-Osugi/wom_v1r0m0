"""
wom/ppc/ppc_engine.py
=====================
PPCSimulationEngine — Top-level orchestrator.

Processing Flow (per Request Letter Rev.2):
    Step 0. Load sales records (read-only quantity input)
    Step 1. Supplier Offering Cost Forward Propagation
    Step 2. Transfer Price Determination (D2: cost_plus, no circular ref)
    Step 3. Tariff & Landed Cost Calculation (on fixed transfer price)
    Step 4. Profit Zone Allocation + Market Revenue
    Step 5. Market Requesting Price Backward Propagation (lot-based, D3)
    Step 6. PPC Reconciliation (lot-based trust events)
    Step 7. KPI Summary (base currency, D1)

Interface:
    sales_records : pd.DataFrame
        Columns: lot_id, week, channel_node, product_id, qty
        One row per lot sold at a leaf_out (market channel).
        Source: extracted from WOM SCTree psi4supply[w][S] at leaf_out nodes,
                or created synthetically for testing.

    sc_paths : dict[channel_node → list[(node_id, edge_id, country)]]
        Topology of the supply chain path for each channel.
        Example:
            {"JP_Channel": [
                ("Supplier_CN",  "",                        "CN"),
                ("MOM_China",    "Supplier_CN->MOM_China",  "CN"),
                ("DAD_Japan",    "MOM_China->DAD_Japan",    "JP"),
                ("JP_Channel",   "DAD_Japan->JP_Channel",   "JP"),
            ]}

    rules : PPCRuleSet  (loaded from data/ppc/ CSV masters)
    base_currency : str  (default "JPY")
    mom_node : str       (default "MOM_China")
    supplier_node : str  (default "Supplier_CN")
    dad_node : str       (default "DAD_Japan")
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from .ppc_models import LotCostAccumulator, PPCSimulationResult
from .ppc_fx import FXConverter
from .ppc_rules import PPCRuleSet
from .ppc_forward import run_forward_propagation
from .ppc_transfer import run_transfer_price_determination
from .ppc_tariff import run_tariff_and_landed_cost
from .ppc_profit_zone import run_profit_zone_allocation
from .ppc_backward import run_backward_propagation
from .ppc_reconcile import run_reconciliation
from .ppc_kpi import build_node_week_summary, build_profit_zone_summary, build_kpi_summary


class PPCSimulationEngine:
    """
    PPC Simulation Engine — evaluates price, cost, profit on a fixed
    quantity flow result from the WOM PSI Planning Engine.

    Parameters
    ----------
    sales_records   : DataFrame with lot sales at market channels
    sc_paths        : supply chain topology per channel
    rules           : loaded PPCRuleSet
    base_currency   : base currency for all summaries (default "JPY")
    mom_node        : MOM node id
    supplier_node   : leaf_in (supplier) node id
    dad_node        : DAD node id
    verbose         : print step progress
    """

    def __init__(
        self,
        sales_records: pd.DataFrame,
        sc_paths: Dict[str, List[Tuple[str, str, str]]],
        rules: PPCRuleSet,
        base_currency: str = "JPY",
        mom_node: str = "MOM_China",
        supplier_node: str = "Supplier_CN",
        dad_node: str = "DAD_Japan",
        verbose: bool = False,
    ):
        self.sales_records  = sales_records
        self.sc_paths       = sc_paths
        self.rules          = rules
        self.base_currency  = base_currency
        self.mom_node       = mom_node
        self.supplier_node  = supplier_node
        self.dad_node       = dad_node
        self.verbose        = verbose

        self._fx = FXConverter(rules.fx_rate, base_currency)
        self._result: Optional[PPCSimulationResult] = None

    # ------------------------------------------------------------------
    def run(self) -> PPCSimulationResult:
        """
        Execute all 7 steps and return PPCSimulationResult.

        Transfer price is computed exactly ONCE (Step 2).
        Backward pass (Step 5) uses the fixed transfer_price set in Step 2.
        """
        # ── Step 0: Build LotCostAccumulators from sales records ───────
        accumulators = self._build_accumulators()
        if self.verbose:
            print(f"[PPC Step 0] {len(accumulators)} lot-records loaded")

        all_events = []

        # ── Step 1: Supplier Offering Cost Forward Propagation ─────────
        fwd_events = run_forward_propagation(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, supplier_node=self.supplier_node,
        )
        all_events.extend(fwd_events)
        if self.verbose:
            print(f"[PPC Step 1] Forward propagation: {len(fwd_events)} events")

        # ── Step 2: Transfer Price Determination ───────────────────────
        tp_events = run_transfer_price_determination(
            accumulators, self.rules, self._fx, mom_node=self.mom_node,
        )
        all_events.extend(tp_events)
        if self.verbose:
            sample = accumulators[0] if accumulators else None
            if sample:
                print(f"[PPC Step 2] Transfer price set. "
                      f"Example: lot={sample.lot_id} "
                      f"tp_local={sample.transfer_price_local:.0f} CNY "
                      f"tp_base={sample.transfer_price_base:.0f} {self.base_currency}")

        # ── Step 3: Tariff & Landed Cost ───────────────────────────────
        tariff_events = run_tariff_and_landed_cost(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, dad_node=self.dad_node,
        )
        all_events.extend(tariff_events)
        if self.verbose:
            print(f"[PPC Step 3] Tariff/landed cost: {len(tariff_events)} events")

        # ── Step 4: Profit Zone Allocation + Market Revenue ────────────
        pz_events = run_profit_zone_allocation(
            accumulators, self.rules, self._fx,
        )
        all_events.extend(pz_events)
        if self.verbose:
            print(f"[PPC Step 4] Revenue + channel costs: {len(pz_events)} events")

        # ── Step 5: Backward Propagation ──────────────────────────────
        bwd_events = run_backward_propagation(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, dad_node=self.dad_node,
        )
        all_events.extend(bwd_events)
        if self.verbose:
            print(f"[PPC Step 5] Backward propagation: {len(bwd_events)} events")

        # ── Step 6: Reconciliation ─────────────────────────────────────
        trust_events, lot_reconciliation = run_reconciliation(accumulators)
        if self.verbose:
            print(f"[PPC Step 6] Reconciliation: "
                  f"{len(trust_events)} trust events fired")

        # ── Step 7: KPI Summary ────────────────────────────────────────
        node_week_summary   = build_node_week_summary(all_events)
        profit_zone_summary = build_profit_zone_summary(all_events)
        kpi_summary         = build_kpi_summary(
            accumulators, trust_events, self.base_currency
        )
        if self.verbose:
            kpi = kpi_summary
            print(
                f"[PPC Step 7] KPI Summary ({self.base_currency}): "
                f"Revenue={kpi['total_revenue_base']:,.0f}  "
                f"Cost={kpi['total_cost_base']:,.0f}  "
                f"GrossProfit={kpi['gross_profit_base']:,.0f}  "
                f"Margin={kpi['gross_margin_pct']:.1%}  "
                f"Tariff={kpi['total_tariff_base']:,.0f}"
            )

        self._result = PPCSimulationResult(
            base_currency=self.base_currency,
            lot_accumulators=accumulators,
            ppc_events=all_events,
            trust_events=trust_events,
            node_week_summary=node_week_summary,
            profit_zone_summary=profit_zone_summary,
            lot_reconciliation=lot_reconciliation,
            kpi_summary=kpi_summary,
        )
        return self._result

    # ------------------------------------------------------------------
    def _build_accumulators(self) -> List[LotCostAccumulator]:
        """Create one LotCostAccumulator per row in sales_records."""
        accs = []
        for _, row in self.sales_records.iterrows():
            accs.append(LotCostAccumulator(
                lot_id=str(row["lot_id"]),
                week=str(row["week"]),
                product_id=str(row["product_id"]),
                channel_node=str(row["channel_node"]),
            ))
        return accs


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------
def build_iphone_vs_paths() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Return sc_paths for the iphone Vertical Slice scenario.

    topology: Supplier_CN → MOM_China → DAD_Japan → JP_Channel / US_Channel
    """
    return {
        "JP_Channel": [
            ("Supplier_CN", "",                          "CN"),
            ("MOM_China",   "Supplier_CN->MOM_China",   "CN"),
            ("DAD_Japan",   "MOM_China->DAD_Japan",      "JP"),
            ("JP_Channel",  "DAD_Japan->JP_Channel",     "JP"),
        ],
        "US_Channel": [
            ("Supplier_CN", "",                          "CN"),
            ("MOM_China",   "Supplier_CN->MOM_China",   "CN"),
            ("DAD_Japan",   "MOM_China->DAD_Japan",      "JP"),
            ("US_Channel",  "DAD_Japan->US_Channel",     "US"),
        ],
    }


def build_rice_vs_paths() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Return sc_paths for the Japanese Rice Vertical Slice scenario.

    Topology (domestic Japan, no FX conversion):
        Farm_JP -> JA_Seihaku -> DC_Rice -> JP_Channel

    All nodes are domestic JP - no tariff on any edge.
    All amounts in JPY (base_currency = "JPY"; FX rate = 1.0).
    """
    return {
        "JP_Channel": [
            ("Farm_JP",    "",                          "JP"),
            ("JA_Seihaku", "Farm_JP->JA_Seihaku",      "JP"),
            ("DC_Rice",    "JA_Seihaku->DC_Rice",       "JP"),
            ("JP_Channel", "DC_Rice->JP_Channel",       "JP"),
        ],
    }


# Products that map to the Rice scenario
_RICE_PRODUCTS = {"Koshihikari", "Yumepirika", "KOSHIHIKARI", "YUMEPIRIKA"}


def detect_scenario(sales_records) -> str:
    """
    Detect which PPC scenario to use based on product_ids in sales_records.

    Returns
    -------
    "rice"   - if any product is a known rice variety
    "iphone" - otherwise (default)
    """
    if sales_records is None or len(sales_records) == 0:
        return "iphone"
    products = set(sales_records["product_id"].unique())
    if products & _RICE_PRODUCTS:
        return "rice"
    return "iphone"
