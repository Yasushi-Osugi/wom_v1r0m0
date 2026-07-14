#!/usr/bin/env python3
"""
Headless verification for data/sample/apparel-global-2028-2029/.

Runs the full WOM pipeline exactly as the GUI would:
  sc_tree_master.csv -> build_sc_tree_from_master
  -> assign_demand_lots_from_dict -> capacity (LaneTable)
  -> BackwardPlanner -> copy_demand_to_supply -> [PushEngine, Step 8, if
     push_config.csv present] -> ForwardPlanner   (PSI, per product)
  -> run_ppc_from_psi (PPC engine, use_node_name=True, base_currency=USD)

Run from repo root: python3 /path/to/verify_apparel_global.py
"""
import os
import sys
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
print(f"Weeks: {weeks[0]} .. {weeks[-1]} ({len(weeks)} weeks)")

sc_tree = build_sc_tree_from_master(sc_master, weeks)
products = sorted(sc_master["product_name"].unique())
print(f"Products: {products}")

demand_dict = {}
for _, row in demand_df.iterrows():
    key = (row["sku_id"], row["region"], row["week"])
    demand_dict[key] = row["quantity"]
assign_demand_lots_from_dict(sc_tree, demand_dict)

lane_table = LaneTable.from_csv(os.path.join(MODEL_DIR, "lane_assignment.csv"))
cap_set = 0
for _, row in cap_df.iterrows():
    prod = row["sku_id"]
    node_name = row["node_name"]
    week = row["week"]
    cap = float(row["max_supply"])
    for nd in sc_tree.iter_all_nodes(prod):
        if nd.node_name == node_name:
            if week in nd.week_labels:
                widx = nd.week_labels.index(week)
                nd.set_capacity(widx, cap_hard=cap, cap_soft=cap)
                cap_set += 1
print(f"Capacity cells set: {cap_set}")

# push_config.csv (Step 8, PushProductionPlanner) -- same auto-detect + wiring
# logic as wom/gui/app.py's Planning-run path (search "PushEngine" in app.py).
# If present, this designates an InBound node as a PUSH decoupling point:
# everything below it becomes a pass-through pipeline feeding a buffer, and
# the decoupling node itself computes its OWN production/shortfall signal
# instead of accumulating a cascading Carry-Over. See the CO investigation
# notes in this directory's README.md for the full rationale.
push_path = os.path.join(MODEL_DIR, "push_config.csv")
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
    print(f"[PushPull] Loaded push_config.csv: {sum(len(v) for v in push_cfgs_by_prod.values())} row(s)")
else:
    print("[PushPull] push_config.csv not found -- skipping Step 8 (pure PULL)")

errors = []
for prod in products:
    try:
        BackwardPlanner(sc_tree, lane_table).run(prod)
        copy_demand_to_supply(sc_tree, prod)
        for cfg in push_cfgs_by_prod.get(prod, []):
            res = PushProductionPlanner(sc_tree).setup(prod, cfg)
            print(f"[PushPull] {prod}: {res}")
        ForwardPlanner(sc_tree).run(prod)
        print(f"[OK] Planning ran for {prod}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append((prod, str(e)))
        print(f"[FAIL] Planning error for {prod}: {e}")

if errors:
    print("=== PLANNING ERRORS ===")
    for prod, msg in errors:
        print(f"{prod}: {msg}")
    sys.exit(1)

from wom.model.plan_node import S, CO, I, P
for prod in products:
    for nd in sc_tree.iter_all_nodes(prod):
        if nd.node_name.startswith("FG_WH"):
            max_inv = max(len(nd.psi4supply[w][I]) for w in range(len(weeks)))
            print(f"{prod} / {nd.node_name}: max on-hand lots = {max_inv}")

OUT = "/tmp/apparel_global_ppc_out"
os.makedirs(OUT, exist_ok=True)
try:
    result = run_ppc_from_psi(
        sc_tree, weeks,
        data_dir=MODEL_DIR, output_dir=OUT,
        base_currency="USD", verbose=True, use_node_name=True,
    )
    print("[OK] PPC engine ran successfully")
    kpi = result.get("kpi_summary")
    if kpi is not None:
        print("KPI summary keys:", list(kpi.keys()) if isinstance(kpi, dict) else type(kpi))
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"[FAIL] PPC engine error: {e}")
    sys.exit(1)

print("=== ALL CHECKS PASSED ===")

# ── Management engine (narrow GM) ───────────────────────────────────────
from wom.engine.sc_tree_to_df import sc_tree_to_planning_df, apply_inv_value
from wom.engine.money import evaluate_money, build_scenario_money_kpi

planning_df = sc_tree_to_planning_df(sc_tree, scenario_name="apparel-global-2028-2029")
sku_master_df = pd.read_csv(os.path.join(MODEL_DIR, "sku_master.csv"))
planning_df = apply_inv_value(planning_df, sku_master_df)
weekly_money, summary_money = evaluate_money(planning_df, sku_master_df)
print("\n=== Management engine (narrow GM), per SKU/region ===")
print(summary_money[["sku_id", "region", "revenue", "cogs", "gross_profit", "gross_margin"]].to_string(index=False))

sku_kpi_by_sku = {}
for sku in products:
    sub = summary_money[summary_money["sku_id"] == sku]
    sku_kpi_by_sku[sku] = build_scenario_money_kpi(sub)

# ── Landed Cost / Tariff & FX scenario comparison ────────────────────────
from wom.engine.landed_cost import (load_edge_cost_master, load_route_master,
                                     build_route_index, compare_lc_scenarios,
                                     filter_scenario_by_sku)

lc_scens = load_edge_cost_master(os.path.join(MODEL_DIR, "edge_cost_master.csv"))
routes = load_route_master(os.path.join(MODEL_DIR, "route_master.csv"))
route_idx = build_route_index(routes)
print("\n=== Landed Cost / Tariff scenario comparison ===")
for sku in products:
    sku_kpi = sku_kpi_by_sku.get(sku)
    if sku_kpi is None or sku_kpi.empty:
        continue
    cmp_df = compare_lc_scenarios(sku_kpi, lc_scens, route_idx, sku_id=sku)
    print(f"\n--- {sku} ---")
    print(cmp_df[["wom_scenario", "lc_scenario", "revenue", "landed_cogs",
                   "landed_gross_margin", "tariff_burden_pct"]].to_string(index=False))

print("\n=== MANAGEMENT + LANDED COST CHECKS PASSED ===")
