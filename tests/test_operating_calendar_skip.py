# -*- coding: utf-8 -*-
"""
tests/test_operating_calendar_skip.py — Phase 2 Slice 2-3（カレンダースキップ本実装）
==================================================================================
0-shift（閉鎖）週の生産 P を、最も近い **早めの稼働週へ前倒し**する（大杉さんと合意、
2026-07-31）。Lot_ID はそのまま移動、CO は出さない（出力保存・時間だけズレる）。

  - `_apply_operating_calendar_shift(node, n_weeks)` が閉鎖週(op_shifts==0)の
    psi4supply[w][P] を、直近の早い稼働週へ移す。
  - _process_node の per-week I/S 計算ループ**前**に呼ぶので、I/S はシフト後の P
    から算出される（閉鎖週は生産0＝目に見える空き、前倒し先が積み上がる）。
  - opt-in：op_shifts に 0 が無い（操業カレンダー未設定含む）ノードは no-op。
    → 既存全ケースの golden 不変（0-shift 週が無いため）。

禁足コア（forward_planner.py）改変を伴うため、本テスト緑 ＋ 既存全緑 ＋ golden 緑 ＋
オーナー差分レビューが受け入れ条件。
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from wom.model.plan_node import P
from wom.model.sc_tree import build_demo_sc_tree
from wom.engine.forward_planner import ForwardPlanner


def _demo_mom():
    sku_id, region = "SKU-A", "JP"
    weeks = [f"2024-W{i:02d}" for i in range(1, 27)]
    sku_master = pd.DataFrame([
        {"sku_id": sku_id, "sku_name": "Product A", "region": region, "lead_time_wks": 1},
    ])
    sc_tree = build_demo_sc_tree(sku_master, weeks, lt_wks_ot=1, lt_wks_in=2)
    mom = sc_tree.get_in_root(sku_id)
    return mom, len(weeks)


# ---------------------------------------------------------------------------
# 1. 閉鎖週の生産を直近の早い稼働週へ前倒し
# ---------------------------------------------------------------------------

def test_shift_moves_production_to_nearest_earlier_open_week():
    mom, n = _demo_mom()
    for w in range(n):
        mom.set_operating_shifts(w, 14)   # 全週 open
    mom.set_operating_shifts(5, 0)        # idx5(W06) を閉鎖

    mom.psi4supply[5][P] = ["L1", "L2", "L3"]
    ForwardPlanner._apply_operating_calendar_shift(mom, n)

    assert mom.psi4supply[5][P] == [], "閉鎖週の生産は空になるべき"
    assert mom.psi4supply[4][P] == ["L1", "L2", "L3"], "直近の早い稼働週(idx4)へ前倒し"


# ---------------------------------------------------------------------------
# 2. 連続閉鎖週はさらに手前の稼働週へ
# ---------------------------------------------------------------------------

def test_shift_skips_multiple_consecutive_closed_weeks():
    mom, n = _demo_mom()
    for w in range(n):
        mom.set_operating_shifts(w, 14)
    mom.set_operating_shifts(4, 0)        # idx4 閉鎖
    mom.set_operating_shifts(5, 0)        # idx5 閉鎖

    mom.psi4supply[5][P] = ["L1"]
    ForwardPlanner._apply_operating_calendar_shift(mom, n)

    assert mom.psi4supply[5][P] == []
    assert mom.psi4supply[3][P] == ["L1"], "idx4,5 が閉鎖なので idx3 へ前倒し"


# ---------------------------------------------------------------------------
# 3. 操業カレンダー未設定（0-shift 無し）は no-op（後方互換）
# ---------------------------------------------------------------------------

def test_no_calendar_is_noop():
    mom, n = _demo_mom()
    # op_shifts は全て None（既定）
    mom.psi4supply[5][P] = ["L1", "L2"]
    ForwardPlanner._apply_operating_calendar_shift(mom, n)
    assert mom.psi4supply[5][P] == ["L1", "L2"], "カレンダー未設定なら不変"

    # 全週 open（0 が無い）でも no-op
    for w in range(n):
        mom.set_operating_shifts(w, 14)
    ForwardPlanner._apply_operating_calendar_shift(mom, n)
    assert mom.psi4supply[5][P] == ["L1", "L2"]


if __name__ == "__main__":
    for t in [
        test_shift_moves_production_to_nearest_earlier_open_week,
        test_shift_skips_multiple_consecutive_closed_weeks,
        test_no_calendar_is_noop,
    ]:
        print(f"\n=== {t.__name__} ===")
        t()
        print("PASS")
    print("\nAll operating-calendar skip (Slice 2-3) tests passed.")
