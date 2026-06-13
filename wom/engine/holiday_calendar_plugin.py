"""
wom/engine/holiday_calendar_plugin.py
======================================
HolidayCalendarPlugin — Global holiday effects on supply and demand.

Business context
----------------
Global SCM planning must account for the dual effect of long holidays:

  1. Supply closure  (工場閉鎖 / 物流停滞)
       e.g. 春節: MOM_China / Supplier_CN が 2-3 週停止
       e.g. GW : DAD_Japan の物流が 2 週減速
     → 該当 node の cap_hard = 0 (または部分閉鎖値) を設定
     → ForwardPlanner が自動的に CO 繰越

  2. Demand adjustment  (需要増減)
       e.g. 春節前: JP/US_Channel の需要が 1.3 倍 (買い溜め)
       e.g. GW 後 : 反動減で需要 0.9 倍
     → leaf_out ノードの psi4demand[w][S] lot 数を乗数で増減

  3. Pre-holiday buffer build  (事前バッファ生産)
       供給閉鎖週に BackwardPlanner が割り当てた P-lot を
       閉鎖直前の開放週へ前倒しシフト (HarvestBatchPlugin と同機構)
     → 閉鎖前に工場が需要分を先行生産し在庫を積む挙動を再現

CSV schema  (holiday_calendar.csv)
----------------------------------
holiday_id    : 休暇イベント識別子 (同一イベントの複数行に同じ値)
holiday_name  : 表示名 (日本語可)
start_week    : 開始週 ISO label (例: 2027-W05)
end_week      : 終了週 ISO label (含む)
node_name     : 対象 PlanNode.node_name (完全一致)
effect        : supply_closure | demand_multiplier
value         : supply_closure → cap_hard 値 (0.0=全閉鎖, 0.5=半稼働)
                demand_multiplier → 乗数 (1.3=+30%, 0.8=-20%)

Example rows
------------
CNY_2027,春節2027（工場閉鎖）,2027-W05,2027-W07,MOM_China,supply_closure,0.0
CNY_2027_pre_JP,春節前JP需要増,2027-W02,2027-W04,JP_Channel,demand_multiplier,1.3

Execution order in app._planning_thread
-----------------------------------------
HOOK_PRE_PLAN      → on_pre_plan     (cap_hard 設定 + demand lot 調整)
BackwardPlanner    → demand 伝播
HOOK_POST_BACKWARD → on_post_backward (P-lot を閉鎖前週へ前倒しシフト)
copy_demand_to_supply
ForwardPlanner     → cap_hard=0 週は CO 繰越で自動スキップ
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional, Tuple

from wom.engine.plugin_base import WOMPlugin
from wom.model.plan_node import S, P as P_IDX, NODE_TYPE_LEAF_IN, NODE_TYPE_LEAF_OUT


# ---------------------------------------------------------------------------
# HolidayCalendarPlugin
# ---------------------------------------------------------------------------

class HolidayCalendarPlugin(WOMPlugin):
    """
    Dual-effect holiday modeling for Global SCM weekly planning.

    Usage
    -----
    1. Prepare holiday_calendar.csv (see module docstring for schema).
    2. Enable the plugin in WOM GUI (checkbox).
    3. Set the CSV path via config["holiday_cal_path"] or set_csv_path().

    Hooks fired
    -----------
    on_pre_plan      : supply_closure → cap_hard; demand_multiplier → lot delta
    on_post_backward : pre-holiday buffer — shift P-lots from closure weeks
                       to nearest pre-closure open weeks
    """

    name        = "holiday_calendar"
    label       = "休暇カレンダー (Holiday Calendar)"
    description = (
        "春節・GW など長期休暇の工場閉鎖と需要変動をモデル化。\n"
        "• supply_closure: 閉鎖週の cap_hard を設定\n"
        "• demand_multiplier: leaf_out の需要 lot を乗数調整\n"
        "• Pre-holiday buffer: 閉鎖前週へ生産 P-lot を前倒しシフト"
    )

    def __init__(self, csv_path: str = "") -> None:
        self.csv_path   = csv_path
        self._rules: List[dict] = []
        # Synthetic lot sequence counters: (holiday_id, prod, region, week) → int
        self._hol_seq:  Dict[Tuple, int] = {}

    def set_csv_path(self, path: str) -> None:
        """Set CSV path explicitly (alternative to config dict)."""
        self.csv_path = path

    # ======================================================================
    # Hook: PRE_PLAN
    # ======================================================================

    def on_pre_plan(self, sc_tree, weeks: list, config: dict, **kw) -> None:
        """
        Apply supply closures and demand adjustments before the planning loop.

        Reads config["holiday_cal_path"] if set; falls back to self.csv_path.
        """
        path = config.get("holiday_cal_path", "") or self.csv_path
        if not path or not os.path.exists(path):
            return

        rules = self._load_rules(path, weeks)
        if not rules:
            return
        self._rules = rules

        # Build node_name → [PlanNode] lookup across all products
        node_lookup: Dict[str, List] = {}
        for prod_nm in sc_tree.products:
            for node in sc_tree.iter_all_nodes(prod_nm):
                node_lookup.setdefault(node.node_name, []).append(node)

        for rule in rules:
            nodes = node_lookup.get(rule["node_name"], [])
            if not nodes:
                print(f"[HolidayCalendar] ⚠ node '{rule['node_name']}' not found "
                      f"(holiday: {rule['holiday_id']})")
                continue

            effect = rule["effect"]
            value  = rule["value"]
            w_idxs = rule["week_idxs"]
            w_lbls = rule["week_labels"]

            if effect == "supply_closure":
                self._apply_supply_closure(nodes, w_idxs, w_lbls,
                                           value, rule["holiday_name"])

            elif effect == "demand_multiplier":
                self._apply_demand_multiplier(nodes, w_idxs, w_lbls,
                                              value, rule["holiday_id"])

            else:
                print(f"[HolidayCalendar] Unknown effect '{effect}' — skipped")

    def _apply_supply_closure(self, nodes, w_idxs, w_lbls, cap_val, name):
        """Set cap_hard = cap_val on all matching nodes for the holiday window."""
        for node in nodes:
            for w in w_idxs:
                node.set_capacity(w, cap_hard=cap_val)
        print(
            f"[HolidayCalendar] Supply closure '{name}': "
            f"{nodes[0].node_name} cap_hard={cap_val} "
            f"{w_lbls[0]}..{w_lbls[-1]} "
            f"({len(w_idxs)} weeks, {len(nodes)} node(s))"
        )

    def _apply_demand_multiplier(self, nodes, w_idxs, w_lbls, multiplier, holiday_id):
        """Add or remove lots from leaf_out psi4demand[w][S] per multiplier."""
        for node in nodes:
            # Only modify leaf_out nodes (no children in OT tree)
            if node.children:
                continue

            prod   = node.product
            region = self._infer_region(node)

            for w, wk_label in zip(w_idxs, w_lbls):
                existing   = node.psi4demand[w][S]
                current_qty = len(existing)
                if current_qty == 0:
                    continue

                target_qty = max(0, round(current_qty * multiplier))
                delta      = target_qty - current_qty

                if delta > 0:
                    # Demand spike — generate synthetic lots
                    key       = (holiday_id, prod, region, wk_label)
                    seq_start = self._hol_seq.get(key, 1)
                    for i in range(delta):
                        lot_id = (f"HOL:{holiday_id}:{prod}:{region}:"
                                  f"{wk_label}:{seq_start + i:05d}")
                        existing.append(lot_id)
                    self._hol_seq[key] = seq_start + delta

                elif delta < 0:
                    # Demand drop — remove lots from the tail
                    remove = min(-delta, current_qty)
                    node.psi4demand[w][S] = existing[: current_qty - remove]

                new_qty = len(node.psi4demand[w][S])
                if delta != 0:
                    print(
                        f"[HolidayCalendar] Demand ×{multiplier:.2f}: "
                        f"{node.node_name} {wk_label} "
                        f"{current_qty}→{new_qty} lots (Δ{delta:+d})"
                    )

    # ======================================================================
    # Hook: POST_BACKWARD
    # ======================================================================

    def on_post_backward(self, sc_tree, prod_nm: str,
                         weeks: list, config: dict, **kw) -> None:
        """
        Pre-holiday buffer build: shift P-lots from closure weeks
        to the nearest pre-closure open weeks.

        Logic mirrors HarvestBatchPlugin but operates on *all* leaf_in
        nodes that have cap_hard=0 weeks assigned by on_pre_plan.

        Greedy fill: fills the week closest to closure first (LIFO order)
        so the buffer arrives as late as possible before the holiday.
        """
        n_weeks = len(weeks)

        for node in sc_tree.iter_all_nodes(prod_nm):
            if node.node_type != NODE_TYPE_LEAF_IN:
                continue

            # Identify closure weeks (cap_hard == 0) that carry P-lots
            closure_idxs = [
                w for w in range(n_weeks)
                if node.cap_hard(w) == 0.0
                and len(node.psi4demand[w][P_IDX]) > 0
            ]
            if not closure_idxs:
                continue

            # Collect displaced lots
            displaced: List[str] = []
            for w in closure_idxs:
                displaced.extend(node.psi4demand[w][P_IDX])
                node.psi4demand[w][P_IDX] = []

            if not displaced:
                continue

            # Find candidate target weeks: pre-closure open weeks (descending)
            first_closure = min(closure_idxs)
            last_closure  = max(closure_idxs)

            pre_open = [
                w for w in range(first_closure - 1, -1, -1)
                if node.cap_hard(w) != 0.0
            ]
            if not pre_open:
                # No room before closure → defer to first post-closure open week
                pre_open = [
                    w for w in range(last_closure + 1, n_weeks)
                    if node.cap_hard(w) != 0.0
                ]

            if not pre_open:
                # Nowhere to shift — restore original (ForwardPlanner will CO)
                for w in closure_idxs:
                    node.psi4demand[w][P_IDX] = displaced
                print(
                    f"[HolidayCalendar] ⚠ {node.node_name} ({prod_nm}): "
                    f"no open weeks found — {len(displaced)} lots left in closure weeks"
                )
                continue

            # Distribute: fill nearest-to-closure weeks first (pre_open is desc order)
            lot_iter = iter(displaced)
            placed   = 0
            for w in pre_open:
                ch = node.cap_hard(w)
                current_p = len(node.psi4demand[w][P_IDX])
                if ch > 0:
                    space = max(0, int(ch) - current_p)
                else:
                    space = len(displaced)   # unconstrained

                chunk: List[str] = []
                for _ in range(space):
                    lot = next(lot_iter, None)
                    if lot is None:
                        break
                    chunk.append(lot)

                node.psi4demand[w][P_IDX].extend(chunk)
                placed += len(chunk)
                if placed >= len(displaced):
                    break

            # Any remainder (all slots full) → put in earliest available
            remaining = list(lot_iter)
            if remaining:
                fallback_w = pre_open[-1]   # earliest week in list (list is desc)
                node.psi4demand[fallback_w][P_IDX].extend(remaining)
                placed += len(remaining)
                print(
                    f"[HolidayCalendar] ⚠ {node.node_name} ({prod_nm}): "
                    f"{len(remaining)} overflow lots added to {weeks[fallback_w]}"
                )

            closure_labels = [weeks[w] for w in closure_idxs]
            target_labels  = [weeks[w] for w in pre_open
                              if len(node.psi4demand[w][P_IDX]) > 0]
            print(
                f"[HolidayCalendar] Pre-holiday buffer: {node.node_name} ({prod_nm}) "
                f"{placed} lots  "
                f"closure={closure_labels} → buffer={target_labels}"
            )

    # ======================================================================
    # CSV loader
    # ======================================================================

    @staticmethod
    def _load_rules(path: str, weeks: list) -> List[dict]:
        """
        Parse holiday_calendar.csv into a list of rule dicts.
        Rows whose start_week / end_week fall outside the planning horizon
        are silently skipped.
        """
        week_idx_map = {wk: i for i, wk in enumerate(weeks)}
        rules = []

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    start = row.get("start_week", "").strip()
                    end   = row.get("end_week",   "").strip()

                    si = week_idx_map.get(start)
                    ei = week_idx_map.get(end)
                    if si is None or ei is None:
                        continue   # outside planning horizon

                    rules.append({
                        "holiday_id":   row.get("holiday_id",   "").strip(),
                        "holiday_name": row.get("holiday_name", "").strip(),
                        "node_name":    row.get("node_name",    "").strip(),
                        "effect":       row.get("effect",       "").strip(),
                        "value":        float(row.get("value", "0") or 0),
                        "week_idxs":    list(range(si, ei + 1)),
                        "week_labels":  weeks[si: ei + 1],
                    })

        except Exception as exc:
            print(f"[HolidayCalendarPlugin] Error loading {path}: {exc}")

        print(
            f"[HolidayCalendar] Loaded {len(rules)} rules "
            f"from {os.path.basename(path)}"
        )
        return rules

    # ======================================================================
    # Helper
    # ======================================================================

    @staticmethod
    def _infer_region(node) -> str:
        """
        Extract region string from a leaf_out PlanNode.

        Convention: node_id = "OUT:Sales:{region}:{sku_id}"
        Falls back to "XX" if region cannot be determined.
        """
        parts = node.node_id.split(":")
        if len(parts) >= 4 and parts[0] == "OUT":
            return parts[2]
        name = node.node_name
        if name.startswith("Sales "):
            return name[6:].split(" ")[0]
        return "XX"
