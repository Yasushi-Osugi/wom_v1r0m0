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
    sc_paths : dict[channel_node → list[(node_id, edge_id, country)]]
    rules : PPCRuleSet
    base_currency : str  (default "JPY")
    mom_node : str OR dict[product_id -> node_id]
    supplier_node : str OR dict[product_id -> node_id]
    dad_node : str OR dict[product_id -> node_id]
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

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
    PPC Simulation Engine.

    mom_node / supplier_node / dad_node accept str OR dict[product_id -> node_id].
    """

    def __init__(
        self,
        sales_records: pd.DataFrame,
        sc_paths: Dict[str, List[Tuple[str, str, str]]],
        rules: PPCRuleSet,
        base_currency: str = "JPY",
        mom_node: Union[str, Dict[str, str]] = "MOM_China",
        supplier_node: Union[str, Dict[str, str]] = "Supplier_CN",
        dad_node: Union[str, Dict[str, str]] = "DAD_Japan",
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
        """Execute all 7 steps and return PPCSimulationResult."""
        accumulators = self._build_accumulators()
        if self.verbose:
            print(f"[PPC Step 0] {len(accumulators)} lot-records loaded")

        all_events = []

        # Step 1: Supplier Offering Cost Forward Propagation
        fwd_events = run_forward_propagation(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, supplier_node=self.supplier_node,
        )
        all_events.extend(fwd_events)
        if self.verbose:
            print(f"[PPC Step 1] Forward propagation: {len(fwd_events)} events")

        # Step 2: Transfer Price Determination
        tp_events = run_transfer_price_determination(
            accumulators, self.rules, self._fx,
            mom_node=self.mom_node,
        )
        all_events.extend(tp_events)
        if self.verbose:
            print(f"[PPC Step 2] Transfer price: {len(tp_events)} events")

        # Step 3: Tariff & Landed Cost
        tar_events = run_tariff_and_landed_cost(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, dad_node=self.dad_node,
        )
        all_events.extend(tar_events)
        if self.verbose:
            print(f"[PPC Step 3] Tariff/landed: {len(tar_events)} events")

        # Step 4: Profit Zone Allocation + Market Revenue
        pz_events = run_profit_zone_allocation(
            accumulators, self.rules, self._fx,
        )
        all_events.extend(pz_events)
        if self.verbose:
            print(f"[PPC Step 4] Profit zone: {len(pz_events)} events")

        # Step 5: Market Requesting Price Backward Propagation
        bwd_events = run_backward_propagation(
            accumulators, self.rules, self._fx, self.sc_paths,
            mom_node=self.mom_node, dad_node=self.dad_node,
        )
        all_events.extend(bwd_events)
        if self.verbose:
            print(f"[PPC Step 5] Backward: {len(bwd_events)} events")

        # Step 6: Reconciliation
        trust_events, lot_df = run_reconciliation(accumulators)
        if self.verbose:
            print(f"[PPC Step 6] Reconciliation: {len(trust_events)} trust events")

        # Step 7: KPI Summary
        node_week_df = build_node_week_summary(all_events)
        profit_zone_df = build_profit_zone_summary(all_events)
        kpi = build_kpi_summary(accumulators, trust_events, self.base_currency)

        self._result = PPCSimulationResult(
            base_currency=self.base_currency,
            lot_accumulators=accumulators,
            ppc_events=all_events,
            trust_events=trust_events,
            node_week_summary=node_week_df,
            profit_zone_summary=profit_zone_df,
            lot_reconciliation=lot_df,
            kpi_summary=kpi,
        )
        return self._result

    # ------------------------------------------------------------------
    def _build_accumulators(self) -> List[LotCostAccumulator]:
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
# Convenience factory functions
# ---------------------------------------------------------------------------

def build_iphone_vs_paths() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Legacy iphone Vertical Slice paths (old node names).
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


def build_iphone_global_vs_paths() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    iPhone Global Supply Chain sc_paths.

    Topology per product:
        iPhone16:  Foxconn_CN → SP_iPhone16 → Retail_AMER/EMEA/APAC
        iPhone15:  Foxconn_CN_i15 → SP_iPhone15 → Retail_AMER_i15/EMEA_i15/APAC_i15
        iPhone17:  Foxconn_CN_i17 → SP_iPhone17 → Retail_AMER_i17/EMEA_i17/APAC_i17

    DAD node per product = SP_iPhone16 / SP_iPhone15 / SP_iPhone17
    Tariff is looked up on edge  SP_iPhoneXX -> Retail_YYY
    """
    return {
        # ── iPhone 16 ──────────────────────────────────────────────────
        "Retail_AMER": [
            ("Foxconn_CN",   "",                              "CN"),
            ("SP_iPhone16",  "Foxconn_CN->SP_iPhone16",       "CN"),
            ("Retail_AMER",  "SP_iPhone16->Retail_AMER",      "US"),
        ],
        "Retail_EMEA": [
            ("Foxconn_CN",   "",                              "CN"),
            ("SP_iPhone16",  "Foxconn_CN->SP_iPhone16",       "CN"),
            ("Retail_EMEA",  "SP_iPhone16->Retail_EMEA",      "EU"),
        ],
        "Retail_APAC": [
            ("Foxconn_CN",   "",                              "CN"),
            ("SP_iPhone16",  "Foxconn_CN->SP_iPhone16",       "CN"),
            ("Retail_APAC",  "SP_iPhone16->Retail_APAC",      "SG"),
        ],
        # ── iPhone 15 ──────────────────────────────────────────────────
        "Retail_AMER_i15": [
            ("Foxconn_CN_i15",  "",                                    "CN"),
            ("SP_iPhone15",     "Foxconn_CN_i15->SP_iPhone15",         "CN"),
            ("Retail_AMER_i15", "SP_iPhone15->Retail_AMER_i15",        "US"),
        ],
        "Retail_EMEA_i15": [
            ("Foxconn_CN_i15",  "",                                    "CN"),
            ("SP_iPhone15",     "Foxconn_CN_i15->SP_iPhone15",         "CN"),
            ("Retail_EMEA_i15", "SP_iPhone15->Retail_EMEA_i15",        "EU"),
        ],
        "Retail_APAC_i15": [
            ("Foxconn_CN_i15",  "",                                    "CN"),
            ("SP_iPhone15",     "Foxconn_CN_i15->SP_iPhone15",         "CN"),
            ("Retail_APAC_i15", "SP_iPhone15->Retail_APAC_i15",        "SG"),
        ],
        # ── iPhone 17 ──────────────────────────────────────────────────
        "Retail_AMER_i17": [
            ("Foxconn_CN_i17",  "",                                    "CN"),
            ("SP_iPhone17",     "Foxconn_CN_i17->SP_iPhone17",         "CN"),
            ("Retail_AMER_i17", "SP_iPhone17->Retail_AMER_i17",        "US"),
        ],
        "Retail_EMEA_i17": [
            ("Foxconn_CN_i17",  "",                                    "CN"),
            ("SP_iPhone17",     "Foxconn_CN_i17->SP_iPhone17",         "CN"),
            ("Retail_EMEA_i17", "SP_iPhone17->Retail_EMEA_i17",        "EU"),
        ],
        "Retail_APAC_i17": [
            ("Foxconn_CN_i17",  "",                                    "CN"),
            ("SP_iPhone17",     "Foxconn_CN_i17->SP_iPhone17",         "CN"),
            ("Retail_APAC_i17", "SP_iPhone17->Retail_APAC_i17",        "SG"),
        ],
    }


def build_rice_vs_paths() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Japanese Rice Vertical Slice: Farm_JP -> JA_Seihaku -> DC_Rice -> JP_Channel
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
# Channels that identify iPhone Global model
_IPHONE_GLOBAL_CHANNELS = {
    "Retail_AMER", "Retail_EMEA", "Retail_APAC",
    "Retail_AMER_i15", "Retail_EMEA_i15", "Retail_APAC_i15",
    "Retail_AMER_i17", "Retail_EMEA_i17", "Retail_APAC_i17",
}


def detect_scenario(sales_records) -> str:
    """
    Detect which PPC scenario to use.

    Returns
    -------
    "rice"          - if any product is a known rice variety
    "iphone_global" - if channels match iPhone Global SC node names
    "iphone"        - legacy iphone (default)
    """
    if sales_records is None or len(sales_records) == 0:
        return "iphone"
    products = set(sales_records["product_id"].unique())
    if products & _RICE_PRODUCTS:
        return "rice"
    channels = set(sales_records["channel_node"].unique())
    if channels & _IPHONE_GLOBAL_CHANNELS:
        return "iphone_global"
    return "iphone"
