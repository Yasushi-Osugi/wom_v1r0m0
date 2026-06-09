"""
wom/engine/capacity_sealer.py
==============================
WOM Step 7 — Capacity Profile Management

Provides utilities for:
  1. Defining CapHard / CapSoft capacity profiles per node per week
  2. Bulk-applying profiles to SCTree PlanNodes
  3. Summarising capacity vs load for management reporting

CapHard vs CapSoft
──────────────────
CapHard  [CAP_HARD = 0]
    Physical equipment limit.  P[w] is HARD-SEALED at this ceiling.
    Excess lots are moved to CO[w+1] during Forward Planning.
    Cannot be overridden.

CapSoft  [CAP_SOFT = 1]
    Operational plan limit (preferred ceiling, e.g. regular-shift target).
    Excess lots are NOT moved — they are FLAGGED as a management alert.
    This models overtime / burst capacity that is possible but costly.

Integration with ForwardPlanner
────────────────────────────────
Capacity sealing is applied inside ForwardPlanner._process_node()
BEFORE the normal PSI roll-forward calculation:

    step 0a: if CapHard > 0 and P[w] > CapHard → seal P, push excess → CO[w+1]
    step 0b: if CapSoft > 0 and P[w] > CapSoft → record violation, no movement
    step 1+: normal available = I[w-1] + P[w] calculation (with sealed P)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from wom.model.plan_node import PlanNode, CAP_HARD, CAP_SOFT
from wom.model.sc_tree   import SCTree


# ---------------------------------------------------------------------------
# CapacityEntry — one node × one week specification
# ---------------------------------------------------------------------------

@dataclass
class CapacityEntry:
    """
    Capacity specification for one node in one week.

    Parameters
    ----------
    node_id:   PlanNode.node_id string
    week:      ISO week label, e.g. "2024-W10"
    cap_hard:  Hard ceiling in lots (0 = unlimited)
    cap_soft:  Soft ceiling in lots (0 = unlimited)
    """
    node_id:  str
    week:     str
    cap_hard: float = 0.0
    cap_soft: float = 0.0


# ---------------------------------------------------------------------------
# CapacityProfile — full profile for a product / all products
# ---------------------------------------------------------------------------

@dataclass
class CapacityProfile:
    """
    Collection of CapacityEntry records that can be applied to an SCTree.
    """
    entries: List[CapacityEntry] = field(default_factory=list)

    def add(
        self,
        node_id:  str,
        week:     str,
        cap_hard: float = 0.0,
        cap_soft: float = 0.0,
    ) -> "CapacityProfile":
        """Append one entry (returns self for chaining)."""
        self.entries.append(
            CapacityEntry(node_id=node_id, week=week,
                          cap_hard=cap_hard, cap_soft=cap_soft)
        )
        return self

    def add_flat(
        self,
        node_id:   str,
        weeks:     List[str],
        cap_hard:  float = 0.0,
        cap_soft:  float = 0.0,
    ) -> "CapacityProfile":
        """
        Apply the same CapHard/CapSoft to a list of weeks for one node.
        Convenient for setting a constant weekly capacity across a horizon.
        """
        for wk in weeks:
            self.add(node_id, wk, cap_hard, cap_soft)
        return self


# ---------------------------------------------------------------------------
# Apply profile to SCTree
# ---------------------------------------------------------------------------

def apply_capacity_profile(
    sc_tree: SCTree,
    profile: CapacityProfile,
) -> Dict[str, int]:
    """
    Write CapHard / CapSoft from a CapacityProfile onto the corresponding
    PlanNode instances in the SCTree.

    Parameters
    ----------
    sc_tree:
        SCTree with init_psi() already called.
    profile:
        CapacityProfile containing the entries to apply.

    Returns
    -------
    dict
        Summary: {"applied": N, "node_not_found": M, "week_out_of_range": K}
    """
    # Build a flat node_id → PlanNode index across all products
    node_index: Dict[str, PlanNode] = {}
    for prod_nm in sc_tree.products:
        for node in sc_tree.iter_all_nodes(prod_nm):
            node_index[node.node_id] = node

    stats = {"applied": 0, "node_not_found": 0, "week_out_of_range": 0}

    for entry in profile.entries:
        node = node_index.get(entry.node_id)
        if node is None:
            stats["node_not_found"] += 1
            continue

        if not node.week_labels:
            stats["week_out_of_range"] += 1
            continue

        try:
            w_idx = node.week_idx(entry.week)
        except ValueError:
            stats["week_out_of_range"] += 1
            continue

        node.set_capacity(w_idx, entry.cap_hard, entry.cap_soft)
        stats["applied"] += 1

    return stats


# ---------------------------------------------------------------------------
# Convenience builder — uniform capacity from sku_master
# ---------------------------------------------------------------------------

def build_mom_capacity_profile(
    sc_tree:      SCTree,
    cap_hard_per_week: float,
    cap_soft_per_week: float,
    prod_nm:      Optional[str] = None,
) -> CapacityProfile:
    """
    Build a CapacityProfile that applies uniform CapHard / CapSoft
    to all MOM (InBound root) nodes across the full planning horizon.

    Parameters
    ----------
    sc_tree:
        SCTree with week_labels set.
    cap_hard_per_week:
        Hard capacity ceiling in lots per week (0 = unlimited).
    cap_soft_per_week:
        Soft capacity target in lots per week (0 = unlimited).
    prod_nm:
        If given, apply only to that product; otherwise apply to all.

    Returns
    -------
    CapacityProfile
    """
    from wom.model.plan_node import NODE_TYPE_MOM

    profile  = CapacityProfile()
    products = [prod_nm] if prod_nm else sc_tree.products

    for p in products:
        in_root = sc_tree.get_in_root(p)
        # Apply to all MOM nodes (tier-0 and deeper) in the InBound tree
        for node in in_root.walk_preorder():
            if node.node_type == NODE_TYPE_MOM:
                profile.add_flat(
                    node_id  = node.node_id,
                    weeks    = sc_tree.week_labels,
                    cap_hard = cap_hard_per_week,
                    cap_soft = cap_soft_per_week,
                )
    return profile


# ---------------------------------------------------------------------------
# Capacity load summary
# ---------------------------------------------------------------------------

@dataclass
class CapacityLoadSummary:
    """
    Per-node, per-week capacity utilisation report generated
    AFTER forward planning (reads psi4supply[P] vs capacity).
    """
    node_id:  str
    week:     str
    p_qty:    int    # lots received (P)
    cap_hard: float
    cap_soft: float
    hard_util: float  # p_qty / cap_hard  (0.0 if cap_hard=0)
    soft_util: float  # p_qty / cap_soft  (0.0 if cap_soft=0)
    over_hard: bool
    over_soft: bool


def build_capacity_load_report(
    sc_tree:  SCTree,
    prod_nm:  str,
) -> List[CapacityLoadSummary]:
    """
    Scan all PlanNodes for a product and return capacity utilisation
    records for weeks where either CapHard or CapSoft is set.

    Call this AFTER forward planning to see the post-sealing load.
    """
    report: List[CapacityLoadSummary] = []
    n_weeks = sc_tree.num_weeks()

    for node in sc_tree.iter_all_nodes(prod_nm):
        if not node.week_labels:
            continue
        for w in range(n_weeks):
            ch = node.cap_hard(w)
            cs = node.cap_soft(w)
            if ch == 0.0 and cs == 0.0:
                continue   # no capacity set for this week

            p_qty = node.qty_supply(w, 1)   # index 1 = P (bucket P=3, but qty_supply uses bucket idx)

            # Recompute using correct bucket index
            from wom.model.plan_node import P as P_IDX
            p_qty = len(node.psi4supply[w][P_IDX])

            hard_util = (p_qty / ch) if ch > 0 else 0.0
            soft_util = (p_qty / cs) if cs > 0 else 0.0

            report.append(CapacityLoadSummary(
                node_id   = node.node_id,
                week      = node.week_labels[w],
                p_qty     = p_qty,
                cap_hard  = ch,
                cap_soft  = cs,
                hard_util = hard_util,
                soft_util = soft_util,
                over_hard = (ch > 0 and p_qty > ch),
                over_soft = (cs > 0 and p_qty > cs),
            ))

    return report
