"""
tests/test_step8_push_pull.py
Step 8 - PUSH / PULL buffer stock switching
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from wom.model.plan_node import S, CO, I, P, NODE_TYPE_LEAF_OUT
from wom.model.sc_tree       import build_demo_sc_tree
from wom.model.lot_generator import assign_demand_lots_from_dict
from wom.engine.backward_planner import BackwardPlanner
from wom.engine.plan_copy        import copy_demand_to_supply
from wom.engine.forward_planner  import ForwardPlanner
from wom.engine.push_pull        import (
    PushConfig, PushProductionPlanner,
    mark_pull_mode, get_push_pull_summary,
)


def build_base(regions=("JP",), demand_qty_per_region=4,
               demand_week="2024-W10", n_weeks=26):
    sku_id = "SKU-A"
    weeks  = [f"2024-W{i:02d}" for i in range(1, n_weeks + 1)]
    rows = [{"sku_id": sku_id, "sku_name": "A", "region": r,
             "lead_time_wks": 1} for r in regions]
    sc_tree = build_demo_sc_tree(pd.DataFrame(rows), weeks,
                                 lt_wks_ot=1, lt_wks_in=2)
    demand_dict = {(sku_id, r, demand_week): demand_qty_per_region
                   for r in regions}
    assign_demand_lots_from_dict(sc_tree, demand_dict, cpu_size=1)
    BackwardPlanner(sc_tree).run(sku_id)
    copy_demand_to_supply(sc_tree, sku_id)
    return sc_tree, weeks, sku_id


def get_node(sc_tree, prod_nm, node_id):
    for node in sc_tree.iter_all_nodes(prod_nm):
        if node.node_id == node_id:
            return node
    raise ValueError(f"{node_id!r} not found")


# ---------------------------------------------------------------------------
def test_pull_baseline():
    sc_tree, weeks, sku_id = build_base()
    result = ForwardPlanner(sc_tree).run(sku_id)
    print(result)

    leaf  = get_node(sc_tree, sku_id, f"OUT:Sales:JP:{sku_id}")
    w10   = weeks.index("2024-W10")
    assert len(leaf.psi4supply[w10][S]) == 4
    mom = get_node(sc_tree, sku_id, f"IN:MFG:{sku_id}")
    assert mom.plan_mode == "pull" and not mom.is_decoupling
    print("PASS: test_pull_baseline")


def test_push_fixed_overwrite():
    sc_tree, weeks, sku_id = build_base(demand_qty_per_region=4)
    push_result = PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=6, sku_id=sku_id))
    print(push_result)

    leaf_in = get_node(sc_tree, sku_id, f"IN:RAW:{sku_id}")
    w03 = weeks.index("2024-W03")
    w10 = weeks.index("2024-W10")
    assert len(leaf_in.psi4supply[w03][P]) == 6
    assert len(leaf_in.psi4supply[w10][P]) == 6
    assert push_result.push_lots_total == 6 * len(weeks)

    mom = get_node(sc_tree, sku_id, f"IN:MFG:{sku_id}")
    assert mom.is_decoupling and mom.plan_mode == "push"
    print("PASS: test_push_fixed_overwrite")


def test_push_vs_pull_leaf_in_p():
    sc_tree_pull, weeks, sku_id = build_base(demand_qty_per_region=4)
    leaf_pull = get_node(sc_tree_pull, sku_id, f"IN:RAW:{sku_id}")
    w08 = weeks.index("2024-W08")
    pull_p = len(leaf_pull.psi4supply[w08][P])
    print(f"PULL leaf_in P[W08] = {pull_p}")

    sc_tree_push, _, _ = build_base(demand_qty_per_region=4)
    PushProductionPlanner(sc_tree_push).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=6, sku_id=sku_id))
    leaf_push = get_node(sc_tree_push, sku_id, f"IN:RAW:{sku_id}")
    push_p = len(leaf_push.psi4supply[w08][P])
    print(f"PUSH leaf_in P[W08] = {push_p}  (expected 6)")

    assert push_p == 6
    assert push_p != pull_p or pull_p == 6
    print("PASS: test_push_vs_pull_leaf_in_p")


def test_push_replenishment():
    sc_tree, weeks, sku_id = build_base(demand_qty_per_region=4)
    push_result = PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=0, buffer_lots=8, sku_id=sku_id))
    print(push_result)

    leaf_in = get_node(sc_tree, sku_id, f"IN:RAW:{sku_id}")
    w01 = weeks.index("2024-W01")
    w08 = weeks.index("2024-W08")
    assert len(leaf_in.psi4supply[w01][P]) == 0, "No push at W01 (no demand)"
    assert len(leaf_in.psi4supply[w08][P]) > 0,  "Push at W08 (demand week)"
    print(f"PASS: test_push_replenishment  (W08 push={len(leaf_in.psi4supply[w08][P])})")


def test_push_region_distribution():
    sc_tree, weeks, sku_id = build_base(
        regions=("JP", "US"), demand_qty_per_region=5,
        demand_week="2024-W10")
    PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=10, sku_id=sku_id))

    leaf_in = get_node(sc_tree, sku_id, f"IN:RAW:{sku_id}")
    w08 = weeks.index("2024-W08")
    lots = leaf_in.psi4supply[w08][P]
    jp = sum(1 for l in lots if ":JP:" in l)
    us = sum(1 for l in lots if ":US:" in l)
    print(f"W08: total={len(lots)}  JP={jp}  US={us}")

    assert len(lots) == 10
    assert jp == 5 and us == 5
    print("PASS: test_push_region_distribution")


def test_mark_pull_mode_reset():
    sc_tree, weeks, sku_id = build_base()
    PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=3, sku_id=sku_id))
    mom = get_node(sc_tree, sku_id, f"IN:MFG:{sku_id}")
    assert mom.is_decoupling and mom.plan_mode == "push"

    mark_pull_mode(sc_tree, sku_id, f"IN:MFG:{sku_id}")
    assert not mom.is_decoupling and mom.plan_mode == "pull"

    # InBound sub-nodes also reset
    t1  = get_node(sc_tree, sku_id, f"IN:T1:{sku_id}")
    raw = get_node(sc_tree, sku_id, f"IN:RAW:{sku_id}")
    assert t1.plan_mode == "pull"
    assert raw.plan_mode == "pull"
    print("PASS: test_mark_pull_mode_reset")


def test_get_push_pull_summary():
    sc_tree, weeks, sku_id = build_base()
    PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=4, sku_id=sku_id))

    summary = get_push_pull_summary(sc_tree, sku_id)
    print(f"Summary rows: {len(summary)}")
    for row in summary:
        print(f"  {row['node_id']:40s}  mode={row['plan_mode']}")

    mom_rows = [r for r in summary if r["node_id"] == f"IN:MFG:{sku_id}"]
    assert mom_rows[0]["plan_mode"] == "push"
    assert mom_rows[0]["is_decoupling"] is True

    ot_rows = [r for r in summary if r["side"] == "outbound"]
    for r in ot_rows:
        assert r["plan_mode"] == "pull"

    in_sub = [r for r in summary
              if r["side"] == "inbound" and r["node_id"] != f"IN:MFG:{sku_id}"]
    for r in in_sub:
        assert r["plan_mode"] == "push_sub", f"Expected push_sub, got {r['plan_mode']}"
    print("PASS: test_get_push_pull_summary")


def test_e2e_push_produces_buffer_inventory():
    """PUSH=6, demand=4: leaf fulfills demand; MOM holds surplus as inventory."""
    sc_tree, weeks, sku_id = build_base(demand_qty_per_region=4)
    PushProductionPlanner(sc_tree).setup(
        sku_id, PushConfig(node_id=f"IN:MFG:{sku_id}",
                           push_qty_per_week=6, sku_id=sku_id))

    result = ForwardPlanner(sc_tree).run(sku_id)
    print(result)

    leaf  = get_node(sc_tree, sku_id, f"OUT:Sales:JP:{sku_id}")
    mom   = get_node(sc_tree, sku_id, f"IN:MFG:{sku_id}")
    w10   = weeks.index("2024-W10")

    leaf_s = len(leaf.psi4supply[w10][S])
    print(f"leaf S[W10]={leaf_s}  (demand=4)")
    assert leaf_s == 4, f"Expected 4, got {leaf_s}"

    mom_inv = sum(len(mom.psi4supply[w][I]) for w in range(len(weeks)))
    print(f"MOM total inventory lots: {mom_inv}")
    assert mom_inv > 0, "Expected positive MOM inventory (PUSH=6 > demand=4)"
    print("PASS: test_e2e_push_produces_buffer_inventory")


if __name__ == "__main__":
    tests = [
        test_pull_baseline,
        test_push_fixed_overwrite,
        test_push_vs_pull_leaf_in_p,
        test_push_replenishment,
        test_push_region_distribution,
        test_mark_pull_mode_reset,
        test_get_push_pull_summary,
        test_e2e_push_produces_buffer_inventory,
    ]
    for t in tests:
        print(f"\n{'='*60}")
        print(f"Running {t.__name__} ...")
        t()
    print(f"\n{'='*60}")
    print("All Step 8 PUSH/PULL tests passed.")
