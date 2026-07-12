"""
課題② 関税ショックの損益分岐点分析:
TariffShock2025シナリオ下でApparel_OutsourcedのLanded GM%をBase水準(35.9%)まで
戻すために必要な小売価格の引き上げ幅を実測する。

重要な発見の検証も兼ねる: Section 5 の Landed Cost テーブルの revenue は
sku_master.csv の selling_price から来ており(Management engineのevaluate_money経由)、
ppc_market_price.csv (PPCエンジン側の価格) を変更しても、このテーブルの
数値には一切影響しない -- という「二重スコープ」のもう一つの現れを実証する。
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
from wom.engine.landed_cost import (
    load_edge_cost_master, load_route_master, build_route_index, compare_lc_scenarios
)

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
print("Planning run complete.\n")

plan_df = sc_tree_to_planning_df(sc_tree, scenario_name=SCENARIO_PLANNING)

edge_path = os.path.join(MODEL_DIR, "edge_cost_master.csv")
route_path = os.path.join(MODEL_DIR, "route_master.csv")
lc_scens = load_edge_cost_master(edge_path)
route_idx = build_route_index(load_route_master(route_path)) if os.path.exists(route_path) else {}


def landed_gm_for_sku_master(sku_master_df, sku_id, lc_scenario_name):
    plan_df2 = plan_df.copy()
    apply_inv_value(plan_df2, sku_master_df)
    mgr = ScenarioManager()
    mgr.add(SCENARIO_PLANNING, plan_df2)
    combined = mgr.combined()
    weekly_money, summary_money = evaluate_money(combined, sku_master_df)
    filtered = summary_money[summary_money[Cols.SKU_ID] == sku_id]
    kpi = build_scenario_money_kpi(filtered)
    lc_df = compare_lc_scenarios(kpi, lc_scens, route_idx, sku_id=sku_id)
    row = lc_df[lc_df["lc_scenario"] == lc_scenario_name].iloc[0]
    return row


sku_master = pd.read_csv(os.path.join(MODEL_DIR, "sku_master.csv"))

print("=== STEP 1: baseline check (unmodified sku_master.csv) ===")
row_base = landed_gm_for_sku_master(sku_master, "Apparel_Outsourced_S4", "Base")
row_shock = landed_gm_for_sku_master(sku_master, "Apparel_Outsourced_S4", "TariffShock2025")
print(f"Base:  revenue={row_base['revenue']:,.0f}  landed_gm={row_base['landed_gross_margin']:.4%}")
print(f"Shock: revenue={row_shock['revenue']:,.0f}  landed_gm={row_shock['landed_gross_margin']:.4%}")

print("\n=== STEP 2: 'naive' attempt -- raise ppc_market_price.csv ONLY (+10%) ===")
mp_path = os.path.join(MODEL_DIR, "ppc_market_price.csv")
mp_df = pd.read_csv(mp_path)
mp_mod = mp_df.copy()
mask = mp_mod["product_id"].str.startswith("Apparel_Outsourced")
mp_mod.loc[mask, "market_price"] *= 1.10
tmp_mp = os.path.join(tempfile.mkdtemp(prefix="ex2_mp_"), "ppc_market_price.csv")
mp_mod.to_csv(tmp_mp, index=False)
# sku_master unchanged -> landed cost table should NOT move
row_shock_naive = landed_gm_for_sku_master(sku_master, "Apparel_Outsourced_S4", "TariffShock2025")
print(f"Shock (ppc_market_price.csv +10%, sku_master UNCHANGED): "
      f"revenue={row_shock_naive['revenue']:,.0f}  landed_gm={row_shock_naive['landed_gross_margin']:.4%}"
      f"  <-- should be IDENTICAL to Step1 Shock (proves ppc_market_price.csv has no effect on this table)")

print("\n=== STEP 3: correct fix -- raise sku_master.csv selling_price ===")
target_gm = row_base["landed_gross_margin"]
lo, hi = 1.00, 1.20
for _ in range(40):
    mid = (lo + hi) / 2
    sm_mod = sku_master.copy()
    m2 = sm_mod["sku_id"] == "Apparel_Outsourced_S4"
    sm_mod.loc[m2, "selling_price"] = sku_master.loc[sku_master["sku_id"] == "Apparel_Outsourced_S4", "selling_price"].iloc[0] * mid
    row = landed_gm_for_sku_master(sm_mod, "Apparel_Outsourced_S4", "TariffShock2025")
    if row["landed_gross_margin"] < target_gm:
        lo = mid
    else:
        hi = mid
required_increase_pct = (mid - 1) * 100
print(f"Required selling_price increase: +{required_increase_pct:.2f}%  "
      f"(binary search converged, target landed_gm={target_gm:.4%})")

sm_final = sku_master.copy()
m2 = sm_final["sku_id"] == "Apparel_Outsourced_S4"
orig_price = sku_master.loc[sku_master["sku_id"] == "Apparel_Outsourced_S4", "selling_price"].iloc[0]
sm_final.loc[m2, "selling_price"] = orig_price * (1 + required_increase_pct / 100)
row_final = landed_gm_for_sku_master(sm_final, "Apparel_Outsourced_S4", "TariffShock2025")
print(f"Verification: orig_price=${orig_price:.2f} -> new_price=${orig_price*(1+required_increase_pct/100):.2f}  "
      f"landed_gm={row_final['landed_gross_margin']:.4%}  (target was {target_gm:.4%})")

out = {
    "base_landed_gm": row_base["landed_gross_margin"],
    "shock_landed_gm": row_shock["landed_gross_margin"],
    "shock_naive_market_price_landed_gm": row_shock_naive["landed_gross_margin"],
    "required_price_increase_pct": required_increase_pct,
    "orig_price": orig_price,
    "new_price": orig_price * (1 + required_increase_pct / 100),
    "verified_landed_gm_after_fix": row_final["landed_gross_margin"],
}
pd.Series(out).to_csv("/tmp/docxbuild/ex2_breakeven_price.csv")
print("\nSaved: /tmp/docxbuild/ex2_breakeven_price.csv")
print(out)
