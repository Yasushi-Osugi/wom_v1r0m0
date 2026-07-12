"""
課題① margin_rate感応度分析:
ppc_transfer_price_rule.csv の Apparel_Integrated 行の margin_rate を
複数値に差し替えて PPC エンジンを再実行し、
  (a) PPC (広義) Gross Margin% の変化
  (b) Management (狭義) Gross Margin% が margin_rate に依存しないこと
を実測する。
"""
import os
import sys
import re
import shutil
import datetime
import tempfile
import pandas as pd

ROOT = "/sessions/gracious-clever-bell/mnt/WOM_V0R2M1_new_cockpit/wom-v1r1m8"
sys.path.insert(0, ROOT)
MODEL_DIR = os.path.join(ROOT, "data", "sample", "apparel-us-2026")

from wom.engine.sc_tree_builder import build_sc_tree_from_master
from wom.model.lot_generator import assign_demand_lots_from_dict
from wom.engine.lane_assignment import LaneTable
from wom.engine.backward_planner import BackwardPlanner
from wom.engine.plan_copy import copy_demand_to_supply
from wom.engine.forward_planner import ForwardPlanner
from wom.engine.sc_tree_to_df import sc_tree_to_planning_df, apply_inv_value, SCENARIO_PLANNING
from wom.engine.money import evaluate_money, build_scenario_money_kpi
from wom.engine.scenario import ScenarioManager
from wom.data.schema import Cols
from wom.ppc.ppc_runner import run_ppc_from_psi

# ── Build week labels ───────────────────────────────────────────────────
n_weeks = 105
start = "2026-W01"
m = re.match(r"(\d{4})-W(\d+)", start)
yr, wk = int(m.group(1)), int(m.group(2))
weeks = []
d = datetime.date.fromisocalendar(yr, wk, 1)
for _ in range(n_weeks):
    yr2, wk2, _ = d.isocalendar()
    weeks.append(f"{yr2}-W{wk2:02d}")
    d += datetime.timedelta(weeks=1)

# ── SC Tree + planning run (shared across all margin_rate trials) ───────
sc_tree_df = pd.read_csv(os.path.join(MODEL_DIR, "sc_tree_master.csv"))
sc_tree = build_sc_tree_from_master(sc_tree_df, weeks)

dem_df = pd.read_csv(os.path.join(MODEL_DIR, "demand_forecast.csv"))
demand_dict = {}
for _, row in dem_df.iterrows():
    key = (str(row["sku_id"]), str(row["region"]), str(row["week"]))
    demand_dict[key] = demand_dict.get(key, 0) + int(row["quantity"])
assign_demand_lots_from_dict(sc_tree, demand_dict, cpu_size=1)

cap_df = pd.read_csv(os.path.join(MODEL_DIR, "capacity_plan.csv"))
week_idx_map = {w: i for i, w in enumerate(weeks)}
node_lookup = {}
for pn in sc_tree.products:
    for nd in sc_tree.iter_all_nodes(pn):
        node_lookup[(pn, nd.node_name)] = nd
for _, row in cap_df.iterrows():
    nd = node_lookup.get((str(row["sku_id"]), str(row["node_name"])))
    if nd is None:
        continue
    w_idx = week_idx_map.get(str(row["week"]))
    if w_idx is not None:
        nd.set_capacity(w_idx, cap_hard=float(row["max_supply"]))

lane_path = os.path.join(MODEL_DIR, "lane_assignment.csv")
lane_table = LaneTable.from_csv(lane_path) if os.path.exists(lane_path) else LaneTable.empty()
cfg = {"n_weeks": n_weeks, "start_week": start, "cap_path": "", "holiday_cal_path": ""}

for prod_nm in sc_tree.products:
    BackwardPlanner(sc_tree, lane_table=lane_table, config=cfg).run(prod_nm)
    copy_demand_to_supply(sc_tree, prod_nm)
    ForwardPlanner(sc_tree, opening_inv={}).run(prod_nm)
print("Planning run complete (shared across all margin_rate trials).\n")

# ── Management (narrow) Gross Margin -- computed once, independent of ────
# ── ppc_transfer_price_rule.csv (verifies it truly doesn't move) ─────────
sku_master = pd.read_csv(os.path.join(MODEL_DIR, "sku_master.csv"))
plan_df = sc_tree_to_planning_df(sc_tree, scenario_name=SCENARIO_PLANNING)
apply_inv_value(plan_df, sku_master)
mgr = ScenarioManager()
mgr.add(SCENARIO_PLANNING, plan_df)
combined = mgr.combined()
weekly_money, summary_money = evaluate_money(combined, sku_master)

mgmt_gm = {}
for brand, sku_prefix in [("Apparel_Outsourced", "Apparel_Outsourced"), ("Apparel_Integrated", "Apparel_Integrated")]:
    filtered = summary_money[summary_money[Cols.SKU_ID].str.startswith(sku_prefix)]
    kpi = build_scenario_money_kpi(filtered)
    gm = float(kpi.iloc[0]["gross_margin"])
    mgmt_gm[brand] = gm
    print(f"Management (narrow) Gross Margin — {brand} (all 8 seasons): {gm:.4%}")

# ── PPC (broad) Gross Margin sensitivity to margin_rate ──────────────────
# Work on an isolated tmp copy of the whole model dir -- never touch the
# real repo files under data/sample/apparel-us-2026/.
margin_rates_to_test = [0.0, 0.05, 0.10, 0.20, 0.30, 0.40]
results = []

tmp_model_dir = tempfile.mkdtemp(prefix="ppc_ex1_model_")
for fname in os.listdir(MODEL_DIR):
    if fname.endswith(".csv"):
        shutil.copy(os.path.join(MODEL_DIR, fname), os.path.join(tmp_model_dir, fname))
trial_rule_path = os.path.join(tmp_model_dir, "ppc_transfer_price_rule.csv")
orig_rule_df = pd.read_csv(trial_rule_path)

for mr in margin_rates_to_test:
    trial_df = orig_rule_df.copy()
    mask = trial_df["mom_node"] == "Factory_Local_ES"
    trial_df.loc[mask, "margin_rate"] = mr
    trial_df.to_csv(trial_rule_path, index=False)

    out_dir = tempfile.mkdtemp(prefix=f"ppc_ex1_out_mr{mr}_")
    kpi = run_ppc_from_psi(
        sc_tree, weeks,
        data_dir=tmp_model_dir, output_dir=out_dir,
        base_currency="USD", verbose=False, use_node_name=True,
    )
    ledger_path = os.path.join(out_dir, "ppc_event_ledger.csv")
    ev = pd.read_csv(ledger_path)
    ev_int = ev[ev["product_id"].astype(str).str.startswith("Apparel_Integrated")]

    revenue = ev_int[ev_int["ppc_event_type"] == "market_revenue"]["amount_base"].sum()
    cost_types = ["supplier_cost", "tariff_cost", "sga_cost", "marketing_cost"]
    has_phase = "cost_phase" in ev_int.columns
    if has_phase:
        cost_by_type = ev_int[ev_int["ppc_event_type"].isin(cost_types)]["amount_base"].sum()
        cost_by_phase = ev_int[ev_int["cost_phase"].isin(["FOB", "MOM", "CIF", "DAD"])]["amount_base"].sum()
        total_cost = cost_by_type + cost_by_phase
    else:
        total_cost = ev_int[ev_int["ppc_event_type"] != "market_revenue"]["amount_base"].sum()
    gp = revenue - total_cost
    ppc_gm = gp / revenue if revenue else 0.0

    results.append({
        "margin_rate": mr,
        "revenue": revenue,
        "total_cost": total_cost,
        "gross_profit": gp,
        "ppc_gross_margin": ppc_gm,
    })
    print(f"margin_rate={mr:>4.2f}  PPC(広義)GM%={ppc_gm:.4%}  revenue={revenue:,.0f}  cost={total_cost:,.0f}")
    shutil.rmtree(out_dir, ignore_errors=True)

shutil.rmtree(tmp_model_dir, ignore_errors=True)
print("\n(worked entirely on a tmp copy -- real repo files untouched)")

res_df = pd.DataFrame(results)
res_df["management_gm_constant"] = mgmt_gm["Apparel_Integrated"]
out_csv = "/tmp/docxbuild/ex1_margin_sensitivity.csv"
res_df.to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")
print(res_df.to_string())
