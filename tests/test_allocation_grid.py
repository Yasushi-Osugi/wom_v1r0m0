# -*- coding: utf-8 -*-
"""
tests/test_allocation_grid.py — 231 点スキャンの回帰テスト（E2E 相当）
====================================================================
`wom/allocation/grid.py` が参照実装 proto_terrain2.py / Request Letter 付録 A の
回帰値を再現することを固定する。受け入れ基準 #11（台地サイズ）・#12（基準 FXB）・
#16（付録 A の最大利益・最適配分）に対応。利益は粗利ベース。
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from wom.allocation.cost_block import derive_cost_blocks
from wom.allocation.grid import (
    simplex_grid, scan_surface, demand_ceilings, best_point, evaluate_point, MARKETS,
)
from wom.allocation.transmission import Scenario

ALLOC_DIR = os.path.join(os.path.dirname(__file__), "..",
                         "data", "sample", "soysauce-jpy-2027-alloc")

BLOCKS, TP = derive_cost_blocks(ALLOC_DIR)


# --- 格子（231 点・単体） ------------------------------------------------------
def test_simplex_grid_231_points():
    pts = simplex_grid(0.05)
    assert len(pts) == 231
    for xjp, xus, xeu in pts:
        assert xjp == pytest.approx(1.0 - xus - xeu, abs=1e-9)   # x_JP は残余
        assert xus >= -1e-9 and xeu >= -1e-9 and xus + xeu <= 1 + 1e-9


# --- 尾根線（需要天井・能力800） -----------------------------------------------
def test_demand_ceilings_cap800():
    c = demand_ceilings(BLOCKS, cap_wk=800)
    assert c["JP"] == pytest.approx(0.362, abs=0.001)
    assert c["US"] == pytest.approx(0.423, abs=0.001)
    assert c["EU"] == pytest.approx(0.423, abs=0.001)
    assert sum(c.values()) == pytest.approx(1.208, abs=0.002)     # >1 → 配給が必要


# --- 付録 A の回帰（最大利益・台地サイズ・最適配分） -----------------------------
# (cap_wk, fx, mat) -> (max_M, plateau_size, argmax(JP,US,EU))
REGRESSION = [
    (1500, 150, 6.0, 148.5, 28, (0.50, 0.25, 0.25)),
    ( 800, 150, 6.0, 132.1,  1, (0.10, 0.45, 0.45)),
    ( 800, 200, 6.0, 207.2,  1, (0.10, 0.45, 0.45)),
    ( 800, 200, 8.0, 176.7,  3, (0.00, 0.45, 0.55)),
    ( 800, 115, 6.0,  85.8,  1, (0.35, 0.25, 0.40)),
]


@pytest.mark.parametrize("cap,fx,mat,max_m,plat,argmax", REGRESSION)
def test_appendix_a3_regression(cap, fx, mat, max_m, plat, argmax):
    surf = scan_surface(BLOCKS, TP, Scenario(fx_usd=fx, material_usd=mat), cap_wk=cap)
    best, plateau = best_point(surf)
    assert best / 1e6 == pytest.approx(max_m, abs=0.05), f"cap{cap}/fx{fx}/${mat} max"
    assert len(plateau) == plat, f"cap{cap}/fx{fx}/${mat} plateau"
    assert plateau[0]["x"] == pytest.approx(argmax, abs=1e-6), f"cap{cap}/fx{fx}/${mat} argmax"


def test_plateau_800_vs_1500():
    """#11: 能力800で台地1点、能力1500で台地28点（退化の再現）。"""
    s800 = scan_surface(BLOCKS, TP, Scenario(fx_usd=150), cap_wk=800)
    s1500 = scan_surface(BLOCKS, TP, Scenario(fx_usd=150), cap_wk=1500)
    assert len(best_point(s800)[1]) == 1
    assert len(best_point(s1500)[1]) == 28


# --- 基準配分の FXB（#12・全需要充足時） ---------------------------------------
def test_base_allocation_fxb():
    # 基準配分 (0.30,0.35,0.35)。全需要が満たせる能力（1500）で評価＝単位経済の需要加重。
    r = evaluate_point((0.30, 0.35, 0.35), BLOCKS, TP, Scenario(fx_usd=150), cap_wk=1500)
    assert r["FCR"] == pytest.approx(0.588, abs=0.001)
    assert r["FRR"] == pytest.approx(0.787, abs=0.001)
    assert r["FXB"] == pytest.approx(0.747, abs=0.001)


def test_profit_identity():
    """損益恒等式：profit = rev − cost（残差ゼロ）。"""
    surf = scan_surface(BLOCKS, TP, Scenario(fx_usd=150), cap_wk=800)
    for r in surf:
        assert r["profit"] == pytest.approx(r["rev"] - r["cost"], abs=1e-6)


if __name__ == "__main__":
    test_simplex_grid_231_points()
    test_demand_ceilings_cap800()
    for args in REGRESSION:
        test_appendix_a3_regression(*args)
    test_plateau_800_vs_1500()
    test_base_allocation_fxb()
    test_profit_identity()
    print("All allocation grid regression tests passed.")
