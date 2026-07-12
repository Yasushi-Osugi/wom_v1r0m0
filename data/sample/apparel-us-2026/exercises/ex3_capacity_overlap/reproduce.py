"""
課題③ 季節重複時のキャパシティ競合検証:
S4とS5の需要期を意図的に完全一致させ、8倍に需要を増幅した上で、
Factory_Import_CN の cap_hard=15,000 lots/週 が S4/S5 で合算判定されるか、
SKU単位で独立判定されるかを実測する。

注意: capacity_plan.csv は「需要が発生する週」しかカバーしておらず、実際の
「生産が発生する週」(需要週からリードタイム分だけ手前)には capacity_plan.csv
の行が存在しない。cap_hard=0 は「無制約」を意味するため、capacity_plan.csv の
週レンジをそのまま使うと生産週でキャパシティ制約が一切効かない。この検証では
Factory_Import_CN の cap_hard=15,000 を全105週に明示的に設定して、この
カバレッジ・ギャップを回避している。実運用では capacity_plan.csv 自体を
「生産週」までカバーするよう拡張するのが正しい対処。
"""
import os
import sys
import re
import datetime
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
from wom.model.plan_node import S, CO, I, P

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
week_idx_map = {w: i for i, w in enumerate(weeks)}

sc_tree_df = pd.read_csv(os.path.join(MODEL_DIR, "sc_tree_master.csv"))
sc_tree = build_sc_tree_from_master(sc_tree_df, weeks)

dem_df = pd.read_csv(os.path.join(MODEL_DIR, "demand_forecast.csv"))
s4_weeks = sorted(dem_df[dem_df.sku_id == "Apparel_Outsourced_S4"]["week"].unique())

dem_mod = dem_df.copy()
# 需要を8倍に増幅(単独でもcap_hard=15,000に迫るように)
amp_mask = dem_mod["sku_id"].isin(["Apparel_Outsourced_S4", "Apparel_Outsourced_S5"])
dem_mod.loc[amp_mask, "quantity"] = (dem_mod.loc[amp_mask, "quantity"] * 8).astype(int)
# S5の需要週をS4と完全に重ねる
s5_mask = dem_mod["sku_id"] == "Apparel_Outsourced_S5"
s5_idx = dem_mod[s5_mask].index.tolist()
for i, idx in enumerate(s5_idx):
    dem_mod.at[idx, "week"] = s4_weeks[i % len(s4_weeks)]

demand_dict = {}
for _, row in dem_mod.iterrows():
    key = (str(row["sku_id"]), str(row["region"]), str(row["week"]))
    demand_dict[key] = demand_dict.get(key, 0) + int(row["quantity"])
assign_demand_lots_from_dict(sc_tree, demand_dict, cpu_size=1)

# Factory_Import_CN の cap_hard=15,000 を全週に明示設定(S4/S5それぞれのPlanNodeへ)
for sku in ["Apparel_Outsourced_S4", "Apparel_Outsourced_S5"]:
    for nd in sc_tree.iter_all_nodes(sku):
        if nd.node_name == "Factory_Import_CN":
            for w_idx in range(n_weeks):
                nd.set_capacity(w_idx, cap_hard=15000.0)

lane_path = os.path.join(MODEL_DIR, "lane_assignment.csv")
lane_table = LaneTable.from_csv(lane_path) if os.path.exists(lane_path) else LaneTable.empty()
cfg = {"n_weeks": n_weeks, "start_week": start, "cap_path": "", "holiday_cal_path": ""}

for prod_nm in sc_tree.products:
    BackwardPlanner(sc_tree, lane_table=lane_table, config=cfg).run(prod_nm)
    copy_demand_to_supply(sc_tree, prod_nm)
    ForwardPlanner(sc_tree, opening_inv={}).run(prod_nm)
print("Planning run complete (S4/S5 forced overlap, 8x demand, cap_hard=15000 explicit).\n")

rows = []
for w_idx, w_label in enumerate(weeks):
    per_sku = {}
    for sku in ["Apparel_Outsourced_S4", "Apparel_Outsourced_S5"]:
        for nd in sc_tree.iter_all_nodes(sku):
            if nd.node_name == "Factory_Import_CN":
                p_count = len(nd.psi4supply[w_idx][P]) if w_idx < len(nd.psi4supply) else 0
                per_sku[sku] = p_count
    tot = per_sku.get("Apparel_Outsourced_S4", 0) + per_sku.get("Apparel_Outsourced_S5", 0)
    if tot > 0:
        rows.append({
            "week": w_label,
            "S4": per_sku.get("Apparel_Outsourced_S4", 0),
            "S5": per_sku.get("Apparel_Outsourced_S5", 0),
            "total": tot,
        })

res = pd.DataFrame(rows)
print(res.to_string(index=False))
print(f"\nmax S4 alone: {res['S4'].max()}  max S5 alone: {res['S5'].max()}  "
      f"max combined: {res['total'].max()}  (single-SKU cap_hard = 15,000)")
res.to_csv("/tmp/docxbuild/ex3_capacity_overlap_fixed.csv", index=False)
