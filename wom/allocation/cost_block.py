# -*- coding: utf-8 -*-
"""
wom/allocation/cost_block.py — Step 0.5 原価ブロック導出器
=========================================================
**原価ブロックは入力ではなく導出物である。** 既存 21 CSV から、市場（JP/US/EU）ごとの
通貨別ブロック（USD / EUR / JPY・関税前）＋販売条件を機械的に導出し、`transmission.py`
の `CostBlock` を組み立てる。関税は transmission.py 側（Step 3）で `tariff_rate ×
transfer_price` として加算されるため、本モジュールのブロックには含めない。

正典：docs/design/ask_global_allocation_spec.md §5 Step 0.5 / §5.1（導出表）
参照：tools/proto_terrain2.py（CHANNELS の固定値と一致すること）

導出元:
  経路      sc_tree（実体は ppc_edge_cost_rule の "A->B" フロー）を leaf_out から遡る
  ノード費  ppc_node_cost_rule（node × currency の fixed_amount）
  エッジ費  ppc_edge_cost_rule（edge × currency の fixed_amount）
  原料費    ppc_supplier_cost（leaf_in・base_week の latest-prior 参照）
  関税率    ppc_tariff_rule（leaf_out への最終エッジ）
  販売価格  ppc_market_price（region × base_week）
  移転価格  sku_master.unit_cost / base_fx × (1 + ppc_transfer_price_rule.margin_rate)
  市場集約  ga_market_aggregation（region → market・internal_ratio）

【要確認・設計判断】移転価格の base（$16）は sku_master.unit_cost(2400 JPY) ÷ base_fx(150)
として導出した（proto_terrain2 の 16.0 と一致）。「終端 MOM 累積 unit_cost」からの厳密導出
とは僅かに異なりうる（cumulative ≒ $16.7）。回帰値（付録 A / #10）は 17.6 前提のため本式を採る。
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from wom.allocation.transmission import CostBlock

BASE_WEEK = "2027-W01"
BASE_FX = 150.0


def _rows(model_dir: str, fname: str) -> List[dict]:
    path = os.path.join(model_dir, fname)
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _latest_prior(rows: List[dict], week_key: str, base_week: str) -> dict:
    cand = [r for r in rows if r[week_key] <= base_week]
    return max(cand, key=lambda r: r[week_key]) if cand else max(rows, key=lambda r: r[week_key])


def derive_cost_blocks(model_dir: str, base_week: str = BASE_WEEK,
                       base_fx: float = BASE_FX) -> Tuple[Dict[str, CostBlock], float]:
    """(market -> CostBlock, transfer_price_usd) を返す。"""
    # --- CSV 読み込み ---
    agg = _rows(model_dir, "ga_market_aggregation.csv")
    node_rows = _rows(model_dir, "ppc_node_cost_rule.csv")
    edge_rows = _rows(model_dir, "ppc_edge_cost_rule.csv")
    sup_rows = _rows(model_dir, "ppc_supplier_cost.csv")
    tar_rows = _rows(model_dir, "ppc_tariff_rule.csv")
    price_rows = _rows(model_dir, "ppc_market_price.csv")
    sct_rows = _rows(model_dir, "sc_tree_master.csv")
    sku_rows = _rows(model_dir, "sku_master.csv")
    tp_rows = _rows(model_dir, "ppc_transfer_price_rule.csv")

    # node_id -> {currency: amount}
    node_cost: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in node_rows:
        node_cost[r["node_id"]][r["currency"]] += float(r["fixed_amount"])
    # edge_id -> {currency: amount}
    edge_cost: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in edge_rows:
        edge_cost[r["edge_id"]][r["currency"]] += float(r["fixed_amount"])
    # フロー先行ノード（"A->B" → pred[B]=A）
    pred: Dict[str, str] = {}
    for eid in edge_cost:
        a, b = eid.split("->")
        pred[b] = a
    # region -> leaf_out node
    leaf_of_region = {r["region"]: r["node_name"]
                      for r in sct_rows if r["node_type"] == "leaf_out"}
    # leaf_out への最終エッジの関税率
    tariff_of_edge = {r["edge_id"]: float(r["tariff_rate"]) for r in tar_rows}
    # leaf_out node -> (price, currency)
    price_by_market_node = {r["market_node"]: (float(r["market_price"]), r["currency"])
                            for r in price_rows}
    # 原料 base（USD）
    mat_usd = float(_latest_prior(sup_rows, "week", base_week)["purchase_price"])
    # 移転価格（USD）
    unit_cost_jpy = float(sku_rows[0]["unit_cost"])
    margin_rate = float(tp_rows[0]["margin_rate"])
    transfer_price_usd = (unit_cost_jpy / base_fx) * (1.0 + margin_rate)

    def region_block(region: str):
        leaf = leaf_of_region[region]
        blk = defaultdict(float)          # currency -> amount（関税前）
        cur = leaf
        final_edge = None
        while cur in pred:
            a = pred[cur]
            eid = f"{a}->{cur}"
            if final_edge is None:
                final_edge = eid          # leaf への最終エッジ
            for ccy, amt in edge_cost.get(eid, {}).items():
                blk[ccy] += amt
            for ccy, amt in node_cost.get(cur, {}).items():
                blk[ccy] += amt
            cur = a
        # ルート（Materials_JP）のノード費
        for ccy, amt in node_cost.get(cur, {}).items():
            blk[ccy] += amt
        blk["USD"] += mat_usd             # 原料
        trate = tariff_of_edge.get(final_edge, 0.0)
        price, pccy = price_by_market_node[leaf]
        return blk, trate, price, pccy

    # 市場ごとに集約
    by_market: Dict[str, List[dict]] = defaultdict(list)
    for r in agg:
        by_market[r["market_group"]].append(r)

    result: Dict[str, CostBlock] = {}
    for market, regs in by_market.items():
        tot_ratio = sum(float(r["internal_ratio"]) for r in regs)
        usd = eur = jpy = trate = 0.0
        price = ccy = None
        demand = 0
        for r in regs:
            region = r["region"]
            w = float(r["internal_ratio"]) / tot_ratio
            blk, tr, pr, pc = region_block(region)
            usd += w * blk.get("USD", 0.0)
            eur += w * blk.get("EUR", 0.0)
            jpy += w * blk.get("JPY", 0.0)
            trate += w * tr
            price, ccy = pr, pc           # 市場内で共通
            demand += int(r["base_qty_lot"])
        result[market] = CostBlock(
            usd=round(usd, 6), eur=round(eur, 6), jpy=round(jpy, 6),
            tariff_rate=round(trate, 6), price_local=price, ccy=ccy,
            demand_qty=demand, material_usd_base=mat_usd)
    return result, transfer_price_usd
