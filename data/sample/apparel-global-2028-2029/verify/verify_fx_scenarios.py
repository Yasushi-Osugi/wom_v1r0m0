#!/usr/bin/env python3
"""
FX scenario comparison for apparel-global-2028-2029: Base / StrongYen / WeakYen.

ppc_fx_rate.csv has NO scenario dimension (just week/currency/base_currency/
rate -- confirmed by reading wom/ppc/ppc_fx.py), unlike edge_cost_master.csv's
tariff scenarios. So a Base/StrongYen/WeakYen comparison for JP-market REVENUE
(which flows through ppc_market_price.csv's JPY-denominated rows -> FXConverter)
requires actually re-running the PPC engine with 3 different flat JPY/USD
assumptions, each on an isolated tmpdir copy of the model (never touches the
committed CSVs) -- same rigor as apparel-us-2026's exercises/ex1 and ex2.
"""
import os
import sys
import shutil
import tempfile
import csv as csv_mod
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)

MODEL_DIR = "data/sample/apparel-global-2028-2029"

from wom.engine.sc_tree_builder import build_sc_tree_from_master
from wom.model.lot_generator import assign_demand_lots_from_dict
from wom.engine.lane_assignment import LaneTable
from wom.engine.backward_planner import BackwardPlanner
from wom.engine.plan_copy import copy_demand_to_supply
from wom.engine.forward_planner import ForwardPlanner
from wom.engine.push_pull import PushProductionPlanner, PushConfig
from wom.ppc.ppc_runner import run_ppc_from_psi

sc_master = pd.read_csv(os.path.join(MODEL_DIR, "sc_tree_master.csv"))
demand_df = pd.read_csv(os.path.join(MODEL_DIR, "demand_forecast.csv"), dtype={"week": str})
cap_df = pd.read_csv(os.path.join(MODEL_DIR, "capacity_plan.csv"), dtype={"week": str})
weeks = sorted(demand_df["week"].unique())

SCENARIOS = {
    "Base":      150.0,   # JPY per USD
    "StrongYen": 130.0,   # yen strengthens -> JP revenue converts to MORE USD
    "WeakYen":   170.0,   # yen weakens -> JP revenue converts to FEWER USD
}

results = {}

for scen_name, jpy_per_usd in SCENARIOS.items():
    tmpdir = tempfile.mkdtemp(prefix=f"apparel_global_fx_{scen_name}_")
    try:
        for fname in os.listdir(MODEL_DIR):
            src = os.path.join(MODEL_DIR, fname)
            if os.path.isfile(src) and fname.endswith(".csv"):
                shutil.copy(src, os.path.join(tmpdir, fname))

        rate = round(1.0 / jpy_per_usd, 6)
        fx_path = os.path.join(tmpdir, "ppc_fx_rate.csv")
        with open(fx_path, "w") as f:
            f.write("week,currency,base_currency,rate\n")
            for wk in weeks:
                f.write(f"{wk},USD,USD,1.0\n")
                f.write(f"{wk},JPY,USD,{rate}\n")

        sc_tree = build_sc_tree_from_master(sc_master, weeks)
        products = sorted(sc_master["product_name"].unique())

        demand_dict = {}
        for _, row in demand_df.iterrows():
            demand_dict[(row["sku_id"], row["region"], row["week"])] = row["quantity"]
        assign_demand_lots_from_dict(sc_tree, demand_dict)

        lane_table = LaneTable.from_csv(os.path.join(MODEL_DIR, "lane_assignment.csv"))
        for _, row in cap_df.iterrows():
            for nd in sc_tree.iter_all_nodes(row["sku_id"]):
                if nd.node_name == row["node_name"] and row["week"] in nd.week_labels:
                    widx = nd.week_labels.index(row["week"])
                    nd.set_capacity(widx, cap_hard=float(row["max_supply"]),
                                     cap_soft=float(row["max_supply"]))

        push_path = os.path.join(tmpdir, "push_config.csv")
        push_cfgs_by_prod = {}
        if os.path.exists(push_path):
            with open(push_path, newline="", encoding="utf-8") as pf:
                for pr in csv_mod.DictReader(pf):
                    pn = pr.get("sku_id", "").strip()
                    if not pn:
                        continue
                    push_cfgs_by_prod.setdefault(pn, []).append(PushConfig(
                        node_id=pr.get("node_id", "").strip(),
                        push_qty_per_week=int(pr.get("push_qty_per_week") or 0),
                        buffer_lots=int(pr.get("buffer_lots") or 0),
                        sku_id=pn,
                        mode_only=pr.get("mode_only", "").strip().lower() == "true",
                        mom_ref_node_id=pr.get("mom_ref_node_id", "").strip(),
                        pre_build_qty_per_week=int(pr.get("pre_build_qty_per_week") or 0),
                        pre_build_end_week=pr.get("pre_build_end_week", "").strip(),
                        push_lead_time_weeks=int(pr.get("push_lead_time_weeks") or 0),
                        push_eol_week=pr.get("push_eol_week", "").strip(),
                    ))

        for prod in products:
            BackwardPlanner(sc_tree, lane_table).run(prod)
            copy_demand_to_supply(sc_tree, prod)
            for cfg in push_cfgs_by_prod.get(prod, []):
                PushProductionPlanner(sc_tree).setup(prod, cfg)
            ForwardPlanner(sc_tree).run(prod)

        OUT = os.path.join(tmpdir, "ppc_out")
        os.makedirs(OUT, exist_ok=True)
        run_ppc_from_psi(
            sc_tree, weeks,
            data_dir=tmpdir, output_dir=OUT,
            base_currency="USD", verbose=False, use_node_name=True,
        )
        rec = pd.read_csv(os.path.join(OUT, "ppc_lot_reconciliation.csv"))
        rec_jp = rec[rec["channel_node"].str.contains("_JP_")]
        rec_us = rec[rec["channel_node"].str.contains("_US_")]

        jp_revenue_total = (rec_jp["market_revenue_base"] * rec_jp["qty"]).sum()
        us_revenue_total = (rec_us["market_revenue_base"] * rec_us["qty"]).sum()
        jp_gm = (
            (rec_jp["gross_profit_base"] * rec_jp["qty"]).sum() / jp_revenue_total
            if jp_revenue_total else 0.0
        )
        results[scen_name] = {
            "jpy_per_usd": jpy_per_usd,
            "jp_revenue_usd": jp_revenue_total,
            "jp_gross_margin_pct": jp_gm * 100,
            "us_revenue_usd": us_revenue_total,
        }
        print(f"[{scen_name}] JPY/USD={jpy_per_usd}: "
              f"JP revenue=${jp_revenue_total:,.0f}  JP GM%={jp_gm*100:.1f}%  "
              f"US revenue=${us_revenue_total:,.0f} (unaffected, sanity check)")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

print("\n=== FX Scenario Comparison Summary ===")
base_jp_rev = results["Base"]["jp_revenue_usd"]
for scen_name, r in results.items():
    delta_pct = (r["jp_revenue_usd"] / base_jp_rev - 1.0) * 100 if base_jp_rev else 0.0
    print(f"{scen_name:12s} JPY/USD={r['jpy_per_usd']:6.1f}  "
          f"JP revenue(USD)=${r['jp_revenue_usd']:>12,.0f}  "
          f"Deltavs Base={delta_pct:+.1f}%  JP GM%={r['jp_gross_margin_pct']:.1f}%")

assert abs(results["Base"]["us_revenue_usd"] - results["StrongYen"]["us_revenue_usd"]) < 1.0, \
    "US revenue should be completely unaffected by JPY rate changes"
print("\n[OK] US revenue confirmed unaffected by FX scenario (as expected -- USD-denominated)")
print("=== FX VERIFICATION PASSED ===")
