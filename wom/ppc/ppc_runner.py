"""
wom/ppc/ppc_runner.py
=====================
High-level runner: PSI → PPC engine → CSV/JSON export.
"""

from __future__ import annotations

import os
import warnings
from typing import Dict, List, Optional

import pandas as pd

from .ppc_psi_bridge import psi_to_sales_records, summarize_psi_records
from .ppc_rules import PPCRuleSet
from .ppc_engine import (PPCSimulationEngine,
                          build_iphone_vs_paths,
                          build_iphone_global_vs_paths,
                          build_rice_vs_paths,
                          build_biscuit_vs_paths,
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
    use_node_name: bool = False,
) -> dict:
    """
    Run the full PPC Simulation pipeline using PSI leaf-out quantities.
    """
    warnings.filterwarnings("ignore")

    # ── Step 1: Load PPC rules ─────────────────────────────────────────────
    if verbose:
        print(f"[PPC Runner] Loading rules from: {data_dir}")
    rules = PPCRuleSet.load(data_dir)

    known_products = {p for p in rules.supplier_cost["product_id"].unique() if isinstance(p, str)}
    known_channels = {c for c in rules.market_price["market_node"].unique() if isinstance(c, str)}

    if verbose:
        print(f"[PPC Runner] Known products: {sorted(known_products)}")
        print(f"[PPC Runner] Known channels: {sorted(known_channels)}")

    # ── Step 2: PSI → sales_records ───────────────────────────────────────
    sales = psi_to_sales_records(
        sc_tree, weeks,
        channel_map=channel_map,
        product_id_map=product_id_map,
        use_node_name=use_node_name,
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
                "[PPC Runner] No PSI<->PPC-compatible records found.\n"
                "             Falling back to sample data."
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

    # ── Step 5: Auto-detect scenario and build engine parameters ─────────
    scenario = detect_scenario(sales)

    # dad_nodes_chain: ordered list of all DAD nodes per product (MOM-side first).
    # None for rice / iphone_global (single-DAD chains).
    dad_nodes_chain = None

    if scenario == "rice":
        sc_paths      = build_rice_vs_paths()
        mom_node      = "JA_Seihaku"
        supplier_node = "Farm_JP"
        dad_node      = "DC_Rice"

    elif scenario == "biscuit":
        sc_paths      = build_biscuit_vs_paths()
        mom_node      = {"OREO_JP": "Factory_OREO_CN",  "LUVAN_JP": "Factory_LUVAN_JP"}
        supplier_node = {"OREO_JP": "Ingredients_CN",   "LUVAN_JP": "Ingredients_JP"}
        dad_node      = {"OREO_JP": "DC_JP_BONDED",     "LUVAN_JP": "DC_LUVAN_JP"}
        dad_nodes_chain = {
            "OREO_JP":  ["DC_JP_BONDED", "DC_JP_MAIN"],
            "LUVAN_JP": ["DC_LUVAN_JP"],
        }
        if verbose:
            print("[PPC Runner] Scenario: BISCUIT_JP  "
                  "(Factory_OREO_CN/LUVAN_JP -> DC_JP_BONDED/DC_JP_MAIN/DC_LUVAN_JP -> Retail_JP_*)")

    elif scenario == "iphone_global":
        sc_paths      = build_iphone_global_vs_paths()
        mom_node = {
            "iPhone16": "Foxconn_CN",
            "iPhone15": "Foxconn_CN_i15",
            "iPhone17": "Foxconn_CN_i17",
        }
        supplier_node = mom_node
        dad_node = {
            "iPhone16": "SP_iPhone16",
            "iPhone15": "SP_iPhone15",
            "iPhone17": "SP_iPhone17",
        }
        if verbose:
            print("[PPC Runner] Scenario: IPHONE_GLOBAL  "
                  "(Foxconn_CN/i15/i17 -> SP_iPhone16/15/17 -> Retail_*)")

    else:
        # Generic: auto-detect mom/supplier/dad from SCTree structure.
        # Collects ALL DAD nodes per product in OT preorder for multi-tier support.
        sc_paths = {}
        _mom_map: dict = {}
        _sup_map: dict = {}
        _dad_map: dict = {}       # first DAD per product (for tariff)
        _dad_list_map: dict = {}  # all DADs per product in OT preorder

        if sc_tree is not None:
            from wom.model.plan_node import (
                NODE_TYPE_MOM, NODE_TYPE_LEAF_IN, NODE_TYPE_DAD
            )
            for _prod in sc_tree.products:
                if _prod not in known_products:
                    continue
                _dad_list_map[_prod] = []
                for _nd in sc_tree.iter_all_nodes(_prod):
                    _nt = getattr(_nd, "node_type", "")
                    _nm = getattr(_nd, "node_name",
                                  getattr(_nd, "node_id", ""))
                    if _nt == NODE_TYPE_DAD:
                        _dad_list_map[_prod].append(_nm)  # ordered OT preorder
                        if _prod not in _dad_map:
                            _dad_map[_prod] = _nm  # first DAD (for tariff compat)
                    elif _nt == NODE_TYPE_MOM and _prod not in _mom_map:
                        _mom_map[_prod] = _nm
                    elif _nt == NODE_TYPE_LEAF_IN and _prod not in _sup_map:
                        _sup_map[_prod] = _nm

        # Build dad_nodes_chain for multi-tier DAD backward propagation
        dad_nodes_chain = _dad_list_map if _dad_list_map else None

        if _mom_map:
            # Collapse to str when only one product
            mom_node = (
                _mom_map if len(_mom_map) != 1
                else next(iter(_mom_map.values()))
            )
            supplier_node = (
                _sup_map if len(_sup_map) != 1
                else next(iter(_sup_map.values()))
            )
            dad_node = (
                _dad_map if len(_dad_map) != 1
                else next(iter(_dad_map.values()), "")
            )
            if verbose:
                print(f"[PPC Runner] Scenario: GENERIC  "
                      f"mom={mom_node}  "
                      f"supplier={supplier_node}  "
                      f"dad={dad_node}  "
                      f"dad_chain={dad_nodes_chain}")
        else:
            # Final fallback: legacy iphone (JP_Channel / US_Channel)
            sc_paths      = build_iphone_vs_paths()
            mom_node      = "MOM_China"
            supplier_node = "Supplier_CN"
            dad_node      = "DAD_Japan"
            dad_nodes_chain = None
            if verbose:
                print("[PPC Runner] Scenario: IPHONE (legacy)  "
                      f"mom={mom_node}  "
                      f"supplier={supplier_node}  "
                      f"dad={dad_node}")

    if verbose and scenario != "iphone_global":
        print(f"[PPC Runner] Scenario: {scenario.upper()}  "
              f"mom={mom_node}  supplier={supplier_node}  dad={dad_node}")

    if verbose:
        print(f"[PPC Runner] Running engine on {len(sales)} lot-records ...")

    eng = PPCSimulationEngine(
        sales_records=sales,
        sc_paths=sc_paths,
        rules=rules,
        base_currency=base_currency,
        mom_node=mom_node,
        supplier_node=supplier_node,
        dad_node=dad_node,
        dad_nodes_chain=dad_nodes_chain,
        verbose=False,
    )
    result = eng.run()

    if verbose:
        kpi = result.kpi_summary
        print(
            f"[PPC Runner] Done -- lots={kpi['total_lots']:,}  "
            f"events={len(result.ppc_events):,}  "
            f"margin={kpi['gross_margin_pct']:.1%}  "
            f"trust_events={kpi['trust_event_count']}"
        )
        if not psi_mode:
            print("[PPC Runner] WARNING: Results based on SAMPLE data (PSI->PPC mapping missing)")

    # ── Step 6: Export ────────────────────────────────────────────────────
    export_results(result, output_dir)

    return result.kpi_summary
