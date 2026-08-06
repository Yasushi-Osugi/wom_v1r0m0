# -*- coding: utf-8 -*-
"""
tests/test_allocation_plot.py — 可視化のスモークテスト（Phase 2）
================================================================
`tools/plot_allocation_map` の各描画関数が例外なく画像を生成することを固定する。
（matplotlib Agg。中身の見た目は人手 QA。ここは "コード経路が壊れていない" ことの網。）
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib
matplotlib.use("Agg")

from tools.plot_allocation_map import plot_tile, plot_layers, plot_single, bx_s

ALLOC_DIR = os.path.join(os.path.dirname(__file__), "..",
                         "data", "sample", "soysauce-jpy-2027-alloc")


def _nonempty(p):
    return os.path.exists(p) and os.path.getsize(p) > 1000


def test_plot_tile(tmp_path):
    out = str(tmp_path / "tile.png")
    assert _nonempty(plot_tile(ALLOC_DIR, 800, out))


def test_plot_layers(tmp_path):
    out = str(tmp_path / "layers.png")
    assert _nonempty(plot_layers(ALLOC_DIR, 800, out))


def test_plot_single_with_point(tmp_path):
    out = str(tmp_path / "s4.png")
    assert _nonempty(plot_single(ALLOC_DIR, "s4_compound", 800, out, point=(0.45, 0.55)))


def test_bx_s_format():
    assert bx_s((0.1, 0.45, 0.45)) == "0.10/0.45/0.45"


if __name__ == "__main__":
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        test_plot_tile(p); test_plot_layers(p); test_plot_single_with_point(p)
    test_bx_s_format()
    print("All allocation plot smoke tests passed.")
