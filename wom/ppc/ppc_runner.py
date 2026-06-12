"""
wom/ppc/ppc_runner.py
=====================
High-level runner: PSI → PPC engine → CSV/JSON export.

Called from WOM GUI after Planning Engine completes (B2 integration).

Usage (from GUI thread via threading.Thread):
    from wom.ppc.ppc_runner import run_ppc_from_psi
    kpi = run_ppc_from_psi(sc_tree, weeks, data_dir="data/ppc",
                            output_dir="output/ppc")

Returns
-------
dict
    kpi_summary from PPCSimulationResult, or raises on error.
"""

from __future__ import annotations

import os
import warnings
from typing import Dict, List, Optional

import pandas as pd

from .ppc_psi_bridge import psi_to_sales_records, summarize_psi_records
from .ppc_rules import PPCRuleSet
from .ppc_engine import (PPCSimulationEngine,
                          build_iphone_vs_paths, build_rice_vs_paths,
                          detect_scenario)
from .ppc_export import export_results


def run_ppc_from_psi(
    sc_tree,
    weeks: List[str],
    data_dir: str = "data/ppc",
    output_dir: str = "output/ppc",
    channel_map: Optional[Dict[str, str]] = None,
    product_id_map: Optional[Dict[str, str]] = None,
    base_currency: str = "JPY",
    verbose: bool = False,
) -> dict:
    """
    Run the full PPC Simulation pipeline using PSI leaf-out quantities.

    Steps
    -----
    1. Load PPC rule masters from ``data_dir``.
    2. Convert sc_tree leaf_out supply → sales_records via ppc_psi_bridge.
    3. Filter records to products/channels that exist in the PPC rules.
    4. If no valid records remain, fall back to sample data covering ``weeks``.
    5. Run PPCSimulationEngine.
    6. Export results to ``output_dir``.
    7. Return kpi_summary dict.

    Parameters
    ----------
    sc_tree       : SCTree (post-ForwardPlanner)
    weeks         : ISO week labels matching the planning horizon
    data_dir      : Directory containing ppc_*.csv rule masters
    output_dir    : Directory for PPC output CSV/JSON files
    channel_map   : Optional region→channel_node overrides
    product_id_map: Optional sku_id→product_id overrides
    base_currency : Base currency for KPI amounts (default "JPY")
    verbose       : Print step-by-step progress

    Returns
    -------
    kpi_summary dict (keys: base_currency, total_lots, gross_margin_pct, ...)
    """
    warnings.filterwarnings("ignore")

    # ── Step 1: Load PPC rules ─────────────────────────────────────────────
    if verbose:
        print(f"[PPC Runner] Loading rules from: {data_dir}")
    rules = PPCRuleSet.load(data_dir)

    known_products = set(rules.supplier_cost["product_id"].unique())
    known_channels = set(rules.market_price["market_node"].unique())

    if verbose:
        print(f"[PPC Runner] Known products: {sorted(known_products)}")
        print(f"[PPC Runner] Known channels: {sorted(known_channels)}")

    # ── Step 2: PSI → sales_records ───────────────────────────────────────
    sales = psi_to_sales_records(
        sc_tree, weeks,
        channel_map=channel_map,
        product_id_map=product_id_map,
    )
    if verbose:
        print(f"[PPC Runner] PSI bridge: {summarize_psi_records(sales)}")

    # ── Step 3: Filter to PPC-known products & channels ───────────────────
    psi_mode = False
    if not sales.empty:
        valid = (
            sales["product_id"].isin(known_products) &
            sales["channel_node"].isin(known_channels)
        )
        sales_filtered = sales[valid].copy()
        if not sales_filtered.empty:
            psi_mode = True
            sales = sales_filtered
            if verbose:
                print(
                    f"[PPC Runner] After filter: {len(sales)} records "
                    f"({int(sales['qty'].sum()):,} total units)"
                )

    # ── Step 4: Fallback to sample data ───────────────────────────────────
    if not psi_mode:
        if verbose:
            print(
                "[PPC Runner] No PSI↔PPC-compatible records found.\n"
                "             Reason: product_id or channel_node not in PPC rules.\n"
                "             Falling back to sample data for the planning horizon."
            )
        from wom.ppc.__main__ import generate_sample_sales
        start_week = weeks[0] if weeks else "2026-W01"
        sales = generate_sample_sales(
            start_week=start_week,
            n_weeks=len(weeks),
        )
        if verbose:
            print(
                f"[PPC Runner] Sample data: {len(sales)} records "
                f"(weeks {sales['week'].min()}..{sales['week'].max()})"
            )

    # ── Step 5: Auto-detect scenario and run PPC engine ──────────────────
    scenario = detect_scenario(sales)
    if scenario == "rice":
        sc_paths     = build_rice_vs_paths()
        mom_node     = "JA_Seihaku"
        supplier_node = "Farm_JP"
        dad_node     = "DC_Rice"
    else:
        sc_paths     = build_iphone_vs_paths()
        mom_node     = "MOM_China"
        supplier_node = "Supplier_CN"
        dad_node     = "DAD_Japan"

    if verbose:
        print(f"[PPC Runner] Scenario: {scenario.upper()}  "
              f"mom={mom_node}  supplier={supplier_node}  dad={dad_node}")
        print(f"[PPC Runner] Running engine on {len(sales)} lot-records …")

    eng = PPCSimulationEngine(
        sales_records=sales,
        sc_paths=sc_paths,
        rules=rules,
        base_currency=base_currency,
        mom_node=mom_node,
        supplier_node=supplier_node,
        dad_node=dad_node,
        verbose=False,          # keep engine silent; runner controls logging
    )
    result = eng.run()

    if verbose:
        kpi = result.kpi_summary
        print(
            f"[PPC Runner] Done — lots={kpi['total_lots']:,}  "
            f"events={len(result.ppc_events):,}  "
            f"margin={kpi['gross_margin_pct']:.1%}  "
            f"trust_events={kpi['trust_event_count']}"
        )
        if not psi_mode:
            print("[PPC Runner] ⚠ Results based on SAMPLE data (PSI→PPC mapping missing)")

    # ── Step 6: Export ────────────────────────────────────────────────────
    export_results(result, output_dir)

    # Annotate kpi with source mode for GUI display
    result.kpi_summary["_psi_mode"] = psi_mode

    return result.kpi_summary
