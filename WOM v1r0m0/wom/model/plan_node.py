"""
wom/model/plan_node.py
======================
WOM Planning Layer — PlanNode dataclass

PSI Bucket index convention (confirmed):
    S  = 0   Sales / Fulfilled shipment
    CO = 1   Carry Over (受注残) — unfulfilled demand rolled forward
    I  = 2   Inventory
    P  = 3   Purchase / Production plan (replenishment)

    psi4demand[week_idx][bucket] = list[lot_ID: str]
    psi4supply[week_idx][bucket] = list[lot_ID: str]
    capacity[week_idx][0: CapHard, 1: CapSoft] = float

CO is generated ONLY in Forward Planning when I+P < S demand.
Backward Planning (demand allocation, ideal/unconstrained) never touches CO.

Tier numbering:
    tier = 0  →  closest to supply_point
    tier increases toward leaf (farthest from supply_point)

    OutBound example:
        supply_point   (bridge)
        └─ DAD         tier=0  (出荷ヤード)
           └─ ...      tier=1  (域内倉庫)
              └─ leaf  tier=N  (sales channel)

    InBound example:
        supply_point   (bridge)
        └─ MOM         tier=0  (Mother Plant / 最終組立)
           └─ ...      tier=1  (Tier-1 Supplier)
              └─ leaf  tier=N  (raw material)

lt_wks usage:
    Backward Planning:  child.S[w]  →  parent.P[w + lt_wks]   (demand propagation)
    Forward  Planning:  parent.P[w] →  child.S[w + lt_wks]    (supply propagation)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# PSI bucket index constants
# ---------------------------------------------------------------------------
S  = 0   # Sales / Fulfilled shipment
CO = 1   # Carry Over (受注残)
I  = 2   # Inventory
P  = 3   # Purchase / Production plan

PSI_BUCKETS = (S, CO, I, P)
PSI_BUCKET_NAMES = {S: "S", CO: "CO", I: "I", P: "P"}

# Capacity index constants
CAP_HARD = 0   # Equipment / physical limit
CAP_SOFT = 1   # Operational plan limit (softer ceiling)


# ---------------------------------------------------------------------------
# PlanNode
# ---------------------------------------------------------------------------
@dataclass
class PlanNode:
    """
    One node in the WOM Planning Layer tree.

    A PlanNode represents one supply chain location for one product.
    Physical layer (NetworkX GUI node) is linked separately via
    gui_node.sku_dict[product_name] = plan_node.

    Tree entry points (held on the SCTree / WOMModel level):
        prod_tree_dict_OT[prod_nm]  →  OutBound tree root PlanNode
        prod_tree_dict_IN[prod_nm]  →  InBound  tree root PlanNode
    """

    # ── Identity ──────────────────────────────────────────────────────────
    node_id:   str          # unique ID, e.g. "OUT:RegionA:SKU-001"
    node_name: str          # human-readable label
    product:   str          # product name (key into prod_tree_dict_OT/IN)
    side:      str          # "outbound" | "inbound"

    # ── Topology ──────────────────────────────────────────────────────────
    node_type: str          # see NODE_TYPE_* constants below
    tier:      int          # 0 = closest to supply_point, increases to leaf

    # ── Planning parameters ───────────────────────────────────────────────
    lt_wks:   int = 1       # lead time to parent [weeks]
                            #   Backward: child.S[w] → parent.P[w + lt_wks]
                            #   Forward:  parent.P[w] → child.S[w + lt_wks]
    cpu_size: int = 1       # Common Planning Unit (minimum lot size)

    # ── PSI lists  (initialized by init_psi) ─────────────────────────────
    # psi4demand[week_idx][bucket] = [lot_ID, ...]   (demand side)
    # psi4supply[week_idx][bucket] = [lot_ID, ...]   (supply side)
    # capacity  [week_idx][0:CapHard, 1:CapSoft] = float
    psi4demand: List[List[List[str]]] = field(default_factory=list)
    psi4supply: List[List[List[str]]] = field(default_factory=list)
    capacity:   List[List[float]]     = field(default_factory=list)

    # ── Tree linkage ──────────────────────────────────────────────────────
    parent:   Optional["PlanNode"]  = field(default=None,  repr=False)
    children: List["PlanNode"]      = field(default_factory=list, repr=False)

    # ── Planning mode ─────────────────────────────────────────────────────
    is_decoupling: bool = False    # True → PUSH/PULL boundary (buffer stock)
    plan_mode:     str  = "pull"   # "pull" (backward/demand-driven)
                                   # "push" (forward/supply-driven)

    # ── Week index lookup (set after init_psi) ────────────────────────────
    # week_labels[week_idx] = ISO week string, e.g. "2026-W01"
    week_labels: List[str] = field(default_factory=list, repr=False)

    # ======================================================================
    # Initialisation
    # ======================================================================

    def init_psi(self, week_labels: List[str]) -> None:
        """
        Allocate PSI list space for all weeks.

        Parameters
        ----------
        week_labels:
            Ordered list of ISO week strings, e.g. ["2026-W01", "2026-W02", ...]
            Length defines the planning horizon.
        """
        n = len(week_labels)
        self.week_labels = list(week_labels)

        def _empty_buckets() -> List[List[str]]:
            return [[], [], [], []]   # index 0:S  1:CO  2:I  3:P

        self.psi4demand = [_empty_buckets() for _ in range(n)]
        self.psi4supply = [_empty_buckets() for _ in range(n)]
        self.capacity   = [[0.0, 0.0] for _ in range(n)]

    # ======================================================================
    # Week index helper
    # ======================================================================

    def week_idx(self, week_label: str) -> int:
        """Return the integer index for an ISO week label string."""
        return self.week_labels.index(week_label)

    # ======================================================================
    # Quantity accessors  (quantity = len of lot-ID list)
    # ======================================================================

    def qty_demand(self, week: int, bucket: int) -> int:
        """Number of lots in psi4demand[week][bucket]."""
        return len(self.psi4demand[week][bucket])

    def qty_supply(self, week: int, bucket: int) -> int:
        """Number of lots in psi4supply[week][bucket]."""
        return len(self.psi4supply[week][bucket])

    # ======================================================================
    # Lot mutation helpers
    # ======================================================================

    def add_lot_demand(self, week: int, bucket: int, lot_id: str) -> None:
        """Append a lot-ID to psi4demand[week][bucket]."""
        self.psi4demand[week][bucket].append(lot_id)

    def add_lot_supply(self, week: int, bucket: int, lot_id: str) -> None:
        """Append a lot-ID to psi4supply[week][bucket]."""
        self.psi4supply[week][bucket].append(lot_id)

    def pop_lot_demand(self, week: int, bucket: int) -> str:
        """Remove and return the last lot-ID from psi4demand[week][bucket]."""
        return self.psi4demand[week][bucket].pop()

    def pop_lot_supply(self, week: int, bucket: int) -> str:
        """Remove and return the last lot-ID from psi4supply[week][bucket]."""
        return self.psi4supply[week][bucket].pop()

    def move_lot_demand(
        self,
        src_week: int, src_bucket: int,
        dst_week: int, dst_bucket: int,
        lot_id: str,
    ) -> None:
        """
        Move a specific lot-ID within psi4demand from one (week, bucket)
        to another.  Raises ValueError if lot_id is not found in src.
        """
        self.psi4demand[src_week][src_bucket].remove(lot_id)
        self.psi4demand[dst_week][dst_bucket].append(lot_id)

    # ======================================================================
    # Capacity accessors
    # ======================================================================

    def cap_hard(self, week: int) -> float:
        """Equipment / physical capacity ceiling for the week [lot units]."""
        return self.capacity[week][CAP_HARD]

    def cap_soft(self, week: int) -> float:
        """Operational plan capacity ceiling for the week [lot units]."""
        return self.capacity[week][CAP_SOFT]

    def set_capacity(
        self,
        week: int,
        cap_hard: float = 0.0,
        cap_soft: float = 0.0,
    ) -> None:
        self.capacity[week][CAP_HARD] = cap_hard
        self.capacity[week][CAP_SOFT] = cap_soft

    # ======================================================================
    # Carry Over helper (Forward Planning only)
    # ======================================================================

    def apply_carry_over_demand(self, week: int) -> None:
        """
        Forward Planning: if S demand cannot be fulfilled by I+P this week,
        roll the unfulfilled S lots into CO of the NEXT week.

        Called week-by-week during forward pass.
        CO is NEVER touched in Backward Planning.
        """
        if week + 1 >= len(self.psi4demand):
            return   # last week — nowhere to carry over

        supply_lots = (
            self.psi4demand[week][I]
            + self.psi4demand[week][P]
        )
        demand_lots = self.psi4demand[week][S]

        supplied_ids = set(supply_lots)
        unfulfilled = [lot for lot in demand_lots if lot not in supplied_ids]

        for lot_id in unfulfilled:
            self.psi4demand[week][S].remove(lot_id)
            self.psi4demand[week + 1][CO].append(lot_id)

    # ======================================================================
    # Tree traversal helpers
    # ======================================================================

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def is_root(self) -> bool:
        return self.parent is None

    def walk_postorder(self):
        """
        Yield nodes in POST-ORDER (children before parent).
        Used for:
          - Backward planning on OutBound tree (Leaf → DAD → supply_point)
          - Forward  planning on InBound tree  (Leaf → MOM → supply_point)
        """
        for child in self.children:
            yield from child.walk_postorder()
        yield self

    def walk_preorder(self):
        """
        Yield nodes in PRE-ORDER (parent before children).
        Used for:
          - Backward planning on InBound tree  (MOM → Tier-1 → Leaf)
          - Forward  planning on OutBound tree  (DAD → Intermediate → Leaf)
        """
        yield self
        for child in self.children:
            yield from child.walk_preorder()

    # ======================================================================
    # Utility
    # ======================================================================

    def add_child(self, child: "PlanNode") -> None:
        """Attach a child node and set its parent back-pointer."""
        child.parent = self
        self.children.append(child)

    def psi_summary(self, week: int) -> dict:
        """
        Return a dict summarising demand-side PSI quantities for one week.
        Useful for logging and GUI display.
        """
        return {
            "week":    self.week_labels[week] if self.week_labels else week,
            "node_id": self.node_id,
            "S":  self.qty_demand(week, S),
            "CO": self.qty_demand(week, CO),
            "I":  self.qty_demand(week, I),
            "P":  self.qty_demand(week, P),
            "cap_hard": self.cap_hard(week),
            "cap_soft": self.cap_soft(week),
        }

    def __repr__(self) -> str:
        n_children = len(self.children)
        n_weeks    = len(self.psi4demand)
        return (
            f"PlanNode("
            f"id={self.node_id!r}, "
            f"side={self.side!r}, "
            f"type={self.node_type!r}, "
            f"tier={self.tier}, "
            f"lt={self.lt_wks}w, "
            f"children={n_children}, "
            f"weeks={n_weeks})"
        )


# ---------------------------------------------------------------------------
# node_type string constants (for readability — not enforced by dataclass)
# ---------------------------------------------------------------------------
NODE_TYPE_LEAF_OUT     = "leaf_out"      # OutBound leaf (sales channel)
NODE_TYPE_DAD          = "dad"           # OutBound intermediate (倉庫, DC等)
NODE_TYPE_SUPPLY_POINT = "supply_point"  # Bridge between OutBound / InBound
NODE_TYPE_MOM          = "mom"           # InBound intermediate (Mother Plant, Tier-N)
NODE_TYPE_LEAF_IN      = "leaf_in"       # InBound leaf (raw material supplier)
