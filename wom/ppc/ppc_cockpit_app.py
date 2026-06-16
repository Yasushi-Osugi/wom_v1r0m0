"""
wom/ppc/ppc_cockpit_app.py
==========================
PPC Evaluation Cockpit — Interactive Tkinter Application (B0).

Filter controls:
  - SKU (product_id) dropdown
  - Channel dropdown (All channels in data)
  - Period: Start week / End week spinboxes
  - Aggregation: Weekly / Monthly / Quarterly radio buttons

Usage:
    python -m wom.ppc --app [--output-dir output/ppc]

Architecture note:
    PPCCockpitApp is a tk.Frame subclass so it can later be
    embedded in the WOM GUI Management tab (B1 integration).
"""

from __future__ import annotations

import json
import os
from typing import Optional, List

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import pandas as pd


# ── Color palette ──────────────────────────────────────────────────────────────
C_REVENUE  = "#2196F3"
C_COST     = "#F44336"
C_PROFIT   = "#4CAF50"
C_TARIFF   = "#FF9800"
C_BACKWARD = "#00BCD4"
C_PANEL_BG = "#FAFAFA"
C_HEADER   = "#37474F"
C_SIDEBAR  = "#ECEFF1"

# Dynamic color palette for multiple channels
CHANNEL_COLORS = [
    "#1565C0", "#6A1B9A", "#00695C", "#E65100",
    "#4527A0", "#558B2F", "#AD1457", "#37474F",
]


def _channel_short(ch: str) -> str:
    """'Retail_AMER' → 'AMER', 'JP_Channel' → 'JP'"""
    return ch.replace("Retail_", "").replace("_Channel", "")


def _fmt(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    elif abs(v) >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:.0f}"


def _week_to_order(week: str) -> int:
    """'2026-W03' -> 202603"""
    try:
        year, wk = week.split("-W")
        return int(year) * 100 + int(wk)
    except Exception:
        return 0


def _short_period(p: str) -> str:
    """Remove year prefix for axis labels: '2027-W03' → 'W03', 'M01' → 'M01'"""
    if "-W" in p:
        parts = p.split("-W")
        return f"W{parts[1]}"
    return p


def _aggregate_weekly(df_nw: pd.DataFrame, df_rec: pd.DataFrame,
                      granularity: str) -> tuple:
    if granularity == "weekly":
        weeks = sorted(df_nw["week"].unique(), key=_week_to_order)
        return df_nw.copy(), df_rec.copy(), weeks

    weeks_sorted = sorted(df_nw["week"].unique(), key=_week_to_order)
    n = len(weeks_sorted)

    if granularity == "monthly":
        chunk = 4
        label_fmt = "M{:02d}"
    else:  # quarterly
        chunk = 13
        label_fmt = "Q{:02d}"

    week_to_period: dict = {}
    period_idx = 1
    for i, w in enumerate(weeks_sorted):
        week_to_period[w] = label_fmt.format(period_idx)
        if (i + 1) % chunk == 0:
            period_idx += 1

    df_nw  = df_nw.copy()
    df_rec = df_rec.copy()
    df_nw["period"]  = df_nw["week"].map(week_to_period)
    df_rec["period"] = df_rec["week"].map(week_to_period)

    nw_agg = (
        df_nw.groupby(["node_id", "period", "product_id"])[
            ["revenue_base", "cost_base", "tariff_base", "gross_profit_base"]
        ].sum().reset_index().rename(columns={"period": "week"})
    )
    rec_agg = df_rec.copy()
    rec_agg["week"] = rec_agg["period"]

    periods = sorted(set(week_to_period.values()))
    return nw_agg, rec_agg, periods


# ── Chart drawing helpers ─────────────────────────────────────────────────────

def _draw_kpi_text(ax, kpi: dict, rec_filtered: pd.DataFrame, cur: str) -> None:
    ax.set_facecolor(C_PANEL_BG)
    ax.axis("off")

    total_rev    = rec_filtered["market_revenue_base"].sum()
    total_cost   = rec_filtered["forward_cost_base"].sum()
    gross_profit = total_rev - total_cost
    gross_margin = gross_profit / total_rev if total_rev > 0 else 0.0
    n_lots       = len(rec_filtered.dropna(subset=["forward_cost_base"]))
    tariff       = (rec_filtered["tariff_in_base"].sum()
                    + rec_filtered["tariff_out_base"].sum())

    lines = [
        ("PPC KPI Summary", 0.95, 13, C_HEADER, "bold"),
        (f"Base currency: {cur}", 0.86, 8, "#607D8B", "normal"),
        (f"Lots: {n_lots}", 0.79, 8, "#607D8B", "normal"),
        ("", 0.73, 9, "black", "normal"),
        (f"Revenue       {_fmt(total_rev)} {cur}", 0.67, 10, C_REVENUE, "bold"),
        (f"Total Cost    {_fmt(total_cost)} {cur}", 0.58, 10, C_COST, "bold"),
        (f"Gross Profit  {_fmt(gross_profit)} {cur}", 0.49, 10, C_PROFIT, "bold"),
        (f"Gross Margin  {gross_margin:.1%}", 0.41, 10, C_PROFIT, "bold"),
        ("", 0.33, 9, "black", "normal"),
        (f"Tariff Cost   {_fmt(tariff)} {cur}", 0.28, 9, C_TARIFF, "normal"),
    ]

    # Dynamic channel revenue breakdown (top 4 channels)
    if "channel_node" in rec_filtered.columns:
        ch_rev = (
            rec_filtered.groupby("channel_node")["market_revenue_base"]
            .sum().sort_values(ascending=False)
        )
        y_pos = 0.20
        lines += [("", 0.22, 9, "black", "normal")]
        for i, (ch_name, ch_val) in enumerate(ch_rev.head(4).items()):
            color = CHANNEL_COLORS[i % len(CHANNEL_COLORS)]
            label = _channel_short(ch_name)
            lines += [(f"{label:<10}  {_fmt(ch_val)} {cur}", y_pos, 8, color, "normal")]
            y_pos -= 0.065

    for text, y, fs, color, weight in lines:
        ax.text(0.06, y, text, transform=ax.transAxes,
                fontsize=fs, color=color, fontweight=weight,
                va="top", fontfamily="monospace")

    trust = kpi.get("trust_event_count", 0)
    badge_color = "#F44336" if trust > 0 else "#4CAF50"
    badge_text  = f"! {trust} trust event(s)" if trust > 0 else "OK  No trust events"
    ax.text(0.5, -0.02, badge_text, transform=ax.transAxes,
            fontsize=9, color="white", fontweight="bold", ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", fc=badge_color, ec="none"))


def _draw_profit_zone(ax, ev_filtered: pd.DataFrame, cur: str) -> None:
    ax.set_facecolor(C_PANEL_BG)
    COST_TYPES = {
        "supplier_cost", "conversion_cost", "logistics_cost",
        "insurance_cost", "tariff_cost", "warehouse_cost",
        "sga_cost", "marketing_cost",
    }
    zone_order = [
        "SUPPLIER_COST_BASE", "MOM_PLANT_PROFIT",
        "OPERATION_NODE_COST_BASE", "OUTBOUND_CHANNEL_PROFIT",
    ]
    labels = {
        "SUPPLIER_COST_BASE":        "Supplier",
        "MOM_PLANT_PROFIT":          "MOM Plant",
        "OPERATION_NODE_COST_BASE":  "DAD/Operation",
        "OUTBOUND_CHANNEL_PROFIT":   "Channel (All)",
    }
    ev_f = ev_filtered.dropna(subset=["profit_zone"])

    def _zone_sum(zone, is_rev):
        mask = ev_f["profit_zone"] == zone
        if is_rev:
            return ev_f.loc[mask & (ev_f["ppc_event_type"] == "market_revenue"), "amount_base"].sum()
        return ev_f.loc[mask & (ev_f["ppc_event_type"].isin(COST_TYPES)), "amount_base"].sum()

    costs    = [_zone_sum(z, False) / 1e6 for z in zone_order]
    revenues = [_zone_sum(z, True)  / 1e6 for z in zone_order]
    tariffs  = [
        ev_f.loc[(ev_f["profit_zone"] == z) & (ev_f["ppc_event_type"] == "tariff_cost"),
                 "amount_base"].sum() / 1e6
        for z in zone_order
    ]

    y = np.arange(len(zone_order))
    bh = 0.35
    ax.barh(y, costs,    bh, color=C_COST,   label="Cost",    alpha=0.85)
    ax.barh(y, revenues, bh, color=C_REVENUE, label="Revenue", alpha=0.85)
    ax.barh(y - bh, tariffs, bh * 0.7, color=C_TARIFF, label="Tariff", alpha=0.75)
    ax.set_yticks(y)
    ax.set_yticklabels([labels.get(z, z) for z in zone_order], fontsize=9)
    ax.set_xlabel(f"Amount ({cur}, M)", fontsize=8)
    ax.set_title("Profit Zone Breakdown", fontsize=10, fontweight="bold", color=C_HEADER)
    ax.legend(fontsize=7, loc="lower right")
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.grid(axis="x", alpha=0.3)


def _draw_weekly_revenue(ax, nw: pd.DataFrame, periods: list, cur: str) -> None:
    """Revenue trend — dynamically use all channel nodes with revenue > 0."""
    ax.set_facecolor(C_PANEL_BG)

    # Find channel-like nodes: nodes that have revenue (not zero)
    node_rev = nw.groupby("node_id")["revenue_base"].sum()
    channel_nodes = node_rev[node_rev > 0].sort_values(ascending=False).index.tolist()

    if not channel_nodes:
        ax.text(0.5, 0.5, "No revenue data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Revenue Trend", fontsize=10, fontweight="bold", color=C_HEADER)
        return

    # Limit to top 6 channels
    top_channels = channel_nodes[:6]
    weekly = nw[nw["node_id"].isin(top_channels)].pivot_table(
        index="week", columns="node_id", values="revenue_base", aggfunc="sum"
    ).reindex(periods).fillna(0.0)

    x = np.arange(len(periods))
    xlabels = [_short_period(p) for p in periods]

    cumulative = np.zeros(len(periods))
    for i, ch in enumerate(top_channels):
        if ch not in weekly.columns:
            continue
        vals = weekly[ch].values / 1e6
        color = CHANNEL_COLORS[i % len(CHANNEL_COLORS)]
        ax.fill_between(x, cumulative, cumulative + vals, alpha=0.25, color=color)
        ax.plot(x, cumulative + vals, color=color, linewidth=1.6,
                label=_channel_short(ch))
        cumulative = cumulative + vals

    step = max(1, len(periods) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(xlabels[::step], fontsize=7, rotation=30)
    ax.set_ylabel(f"{cur} (M)", fontsize=8)
    ax.set_title("Revenue Trend (by Channel)", fontsize=10, fontweight="bold", color=C_HEADER)
    ax.legend(fontsize=6, loc="upper left", ncol=2)
    ax.grid(alpha=0.3)


def _draw_weekly_cost(ax, nw: pd.DataFrame, periods: list, cur: str) -> None:
    ax.set_facecolor(C_PANEL_BG)
    weekly = nw.groupby("week")[["cost_base", "tariff_base"]].sum().reindex(periods).fillna(0.0)
    x = np.arange(len(periods))
    xlabels = [_short_period(p) for p in periods]

    cost   = weekly["cost_base"].values   / 1e6
    tariff = weekly["tariff_base"].values / 1e6
    op     = cost - tariff

    ax.bar(x, op,     color=C_COST,   alpha=0.75, label="Op Cost")
    ax.bar(x, tariff, bottom=op, color=C_TARIFF, alpha=0.85, label="Tariff")

    step = max(1, len(periods) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(xlabels[::step], fontsize=7, rotation=30)
    ax.set_ylabel(f"{cur} (M)", fontsize=8)
    ax.set_title("Total Cost & Tariff", fontsize=10, fontweight="bold", color=C_HEADER)
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.3)


def _draw_margin_dist(ax, rec: pd.DataFrame, selected_channels: list) -> None:
    """Lot Gross Margin boxplot — uses actual channels from data."""
    ax.set_facecolor(C_PANEL_BG)

    # Determine which channels to show
    available = sorted(rec["channel_node"].dropna().unique().tolist())
    if not available:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Lot Gross Margin by Channel", fontsize=10, fontweight="bold", color=C_HEADER)
        return

    if len(selected_channels) == 1 and selected_channels[0] != "Both":
        use_channels = [ch for ch in selected_channels if ch in available]
    else:
        use_channels = available

    data, xlabels, colors = [], [], []
    for i, ch in enumerate(use_channels[:8]):
        vals = rec.loc[rec["channel_node"] == ch, "gross_margin_pct"].dropna() * 100
        if len(vals) > 0:
            data.append(vals.values)
            xlabels.append(_channel_short(ch))
            colors.append(CHANNEL_COLORS[i % len(CHANNEL_COLORS)])

    if not data:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Lot Gross Margin by Channel", fontsize=10, fontweight="bold", color=C_HEADER)
        return

    bp = ax.boxplot(data, labels=xlabels, patch_artist=True,
                    medianprops=dict(color="white", linewidth=2),
                    whiskerprops=dict(linewidth=1.2),
                    boxprops=dict(linewidth=1.2))
    for box, color in zip(bp["boxes"], colors):
        box.set_facecolor(color)
        box.set_alpha(0.7)

    for i, (vals, color) in enumerate(zip(data, colors)):
        jitter = np.random.uniform(-0.08, 0.08, len(vals))
        ax.scatter(np.full(len(vals), i + 1) + jitter, vals,
                   color=color, alpha=0.25, s=10, zorder=3)

    ax.set_ylabel("Gross Margin (%)", fontsize=8)
    ax.set_title("Lot Gross Margin by Channel", fontsize=10, fontweight="bold", color=C_HEADER)
    ax.grid(axis="y", alpha=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f%%"))
    if len(xlabels) > 4:
        ax.tick_params(axis="x", labelsize=7, rotation=20)


def _draw_fwd_bwd(ax, rec: pd.DataFrame, periods: list, cur: str) -> None:
    """Forward vs Backward vs Revenue — top 2 channels, dynamic."""
    ax.set_facecolor(C_PANEL_BG)

    # Find top 2 channels by revenue
    if rec.empty or "channel_node" not in rec.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Forward vs Backward vs Revenue", fontsize=9, fontweight="bold", color=C_HEADER)
        return

    top_channels = (
        rec.groupby("channel_node")["market_revenue_base"].sum()
        .sort_values(ascending=False).index.tolist()
    )
    if not top_channels:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Forward vs Backward vs Revenue", fontsize=9, fontweight="bold", color=C_HEADER)
        return

    ch1 = top_channels[0]
    ch2 = top_channels[1] if len(top_channels) > 1 else None

    agg = (
        rec.dropna(subset=["forward_cost_base"])
        .groupby(["week", "channel_node"])[
            ["forward_cost_base", "backward_allowable_base", "market_revenue_base"]
        ].mean().reset_index()
    )

    def _get_ch(ch):
        return agg[agg["channel_node"] == ch].set_index("week").reindex(periods).fillna(0.0)

    d1 = _get_ch(ch1)
    x = np.arange(len(periods))
    xlabels = [_short_period(p) for p in periods]
    color1 = CHANNEL_COLORS[0]

    w = 0.28
    ax.bar(x - w, d1["forward_cost_base"].values / 1e3,       w, color=C_COST,     alpha=0.8,
           label=f"{_channel_short(ch1)} Fwd Cost")
    ax.bar(x,     d1["backward_allowable_base"].values / 1e3, w, color=C_BACKWARD, alpha=0.8,
           label=f"{_channel_short(ch1)} Bwd Allow.")
    ax.bar(x + w, d1["market_revenue_base"].values / 1e3,     w, color=color1,     alpha=0.8,
           label=f"{_channel_short(ch1)} Revenue")

    if ch2:
        d2 = _get_ch(ch2)
        color2 = CHANNEL_COLORS[1]
        ax2 = ax.twinx()
        ax2.plot(x, d2["forward_cost_base"].values / 1e3,       color=C_COST,     linewidth=1.5, linestyle="--")
        ax2.plot(x, d2["backward_allowable_base"].values / 1e3, color=C_BACKWARD, linewidth=1.5, linestyle="--")
        ax2.plot(x, d2["market_revenue_base"].values / 1e3,     color=color2,      linewidth=1.5, linestyle="--")
        ax2.set_ylabel(f"{_channel_short(ch2)} (K {cur}) --", fontsize=7, color="#888")
        ax2.tick_params(axis="y", labelsize=7)

    step = max(1, len(periods) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(xlabels[::step], fontsize=7, rotation=30)
    ax.set_ylabel(f"{_channel_short(ch1)} (K {cur})", fontsize=8)
    ax.set_title("Forward vs Backward vs Revenue (avg/lot)", fontsize=9, fontweight="bold", color=C_HEADER)
    ax.legend(fontsize=6, loc="upper left")
    ax.grid(axis="y", alpha=0.3)


# ── Main App Class ────────────────────────────────────────────────────────────

class PPCCockpitApp(tk.Frame):
    """
    Interactive PPC Cockpit as a Tk Frame.
    Can be embedded in the WOM GUI Management tab (B1 integration).
    """

    def __init__(self, parent: tk.Widget, output_dir: str = "output/ppc"):
        super().__init__(parent, bg=C_SIDEBAR)
        self.output_dir = output_dir
        self._load_data()
        self._build_ui()
        self._redraw()

    # ── Data loading ──────────────────────────────────────────────────────
    def _load_data(self) -> None:
        kpi_path = os.path.join(self.output_dir, "ppc_kpi_summary.json")
        if not os.path.exists(kpi_path):
            raise FileNotFoundError(
                f"PPC output not found at '{self.output_dir}'. "
                "Run  python -m wom.ppc  first."
            )
        with open(kpi_path, encoding="utf-8") as f:
            self._kpi = json.load(f)
        self._cur = self._kpi["base_currency"]
        self._nw  = pd.read_csv(os.path.join(self.output_dir, "ppc_node_week_summary.csv"))
        self._rec = pd.read_csv(os.path.join(self.output_dir, "ppc_lot_reconciliation.csv"))
        self._ev  = pd.read_csv(os.path.join(self.output_dir, "ppc_event_ledger.csv"), low_memory=False)

        # Clean rows
        self._nw  = self._nw.dropna(subset=["week"])
        self._rec = self._rec.dropna(subset=["week", "channel_node"])
        self._ev  = self._ev.dropna(subset=["week"])

        all_weeks = sorted(self._nw["week"].unique().tolist(), key=_week_to_order)
        self._all_weeks = all_weeks
        self._skus      = sorted(self._rec["product_id"].dropna().unique().tolist())
        self._channels  = sorted(self._rec["channel_node"].dropna().unique().tolist())

    # ── UI Construction ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Left sidebar
        sidebar = tk.Frame(self, bg=C_SIDEBAR, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="PPC Filters", font=("Helvetica", 12, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(pady=(8, 4))
        ttk.Separator(sidebar, orient="horizontal").pack(fill=tk.X, padx=4, pady=4)

        # SKU
        tk.Label(sidebar, text="SKU", font=("Helvetica", 9, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(anchor="w", padx=8)
        self._sku_var = tk.StringVar(value="All")
        ttk.Combobox(sidebar, textvariable=self._sku_var,
                     values=["All"] + self._skus,
                     state="readonly", width=18).pack(padx=8, pady=(0, 8))

        # Channel
        tk.Label(sidebar, text="Channel", font=("Helvetica", 9, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(anchor="w", padx=8)
        self._channel_var = tk.StringVar(value="All")
        ttk.Combobox(sidebar, textvariable=self._channel_var,
                     values=["All"] + self._channels,
                     state="readonly", width=18).pack(padx=8, pady=(0, 8))

        ttk.Separator(sidebar, orient="horizontal").pack(fill=tk.X, padx=4, pady=4)

        # Start / End week
        tk.Label(sidebar, text="Start Week", font=("Helvetica", 9, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(anchor="w", padx=8)
        self._start_var = tk.StringVar(value=self._all_weeks[0])
        ttk.Combobox(sidebar, textvariable=self._start_var,
                     values=self._all_weeks, state="readonly", width=18).pack(padx=8, pady=(0, 6))

        tk.Label(sidebar, text="End Week", font=("Helvetica", 9, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(anchor="w", padx=8)
        self._end_var = tk.StringVar(value=self._all_weeks[-1])
        ttk.Combobox(sidebar, textvariable=self._end_var,
                     values=self._all_weeks, state="readonly", width=18).pack(padx=8, pady=(0, 8))

        ttk.Separator(sidebar, orient="horizontal").pack(fill=tk.X, padx=4, pady=4)

        # Aggregation
        tk.Label(sidebar, text="Aggregation", font=("Helvetica", 9, "bold"),
                 bg=C_SIDEBAR, fg=C_HEADER).pack(anchor="w", padx=8)
        self._agg_var = tk.StringVar(value="Weekly")
        for val in ("Weekly", "Monthly", "Quarterly"):
            tk.Radiobutton(sidebar, text=val, variable=self._agg_var, value=val,
                           bg=C_SIDEBAR, fg=C_HEADER, selectcolor="#B0BEC5",
                           font=("Helvetica", 9)).pack(anchor="w", padx=16)

        ttk.Separator(sidebar, orient="horizontal").pack(fill=tk.X, padx=4, pady=8)

        # Buttons
        tk.Button(sidebar, text="Apply Filters",
                  font=("Helvetica", 10, "bold"),
                  bg="#1565C0", fg="white",
                  activebackground="#1976D2", activeforeground="white",
                  relief=tk.FLAT, padx=10, pady=6,
                  command=self._redraw).pack(fill=tk.X, padx=8, pady=4)

        tk.Button(sidebar, text="Save PNG",
                  font=("Helvetica", 9),
                  bg="#455A64", fg="white",
                  activebackground="#546E7A", activeforeground="white",
                  relief=tk.FLAT, padx=8, pady=4,
                  command=self._save_png).pack(fill=tk.X, padx=8, pady=2)

        self._status_var = tk.StringVar(value="")
        tk.Label(sidebar, textvariable=self._status_var, bg=C_SIDEBAR,
                 fg="#78909C", font=("Helvetica", 8), wraplength=180,
                 justify=tk.LEFT).pack(padx=8, pady=(8, 0))

        # Right chart area
        chart_frame = tk.Frame(self, bg="white")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._fig = plt.Figure(figsize=(14, 8), facecolor="white")
        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_frame)
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(chart_frame, bg="white")
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self._canvas, toolbar_frame)

    # ── Filter & Redraw ───────────────────────────────────────────────────
    def _get_filtered_weeks(self) -> list:
        start = self._start_var.get()
        end   = self._end_var.get()
        s_ord = _week_to_order(start)
        e_ord = _week_to_order(end)
        if s_ord > e_ord:
            s_ord, e_ord = e_ord, s_ord
        return [w for w in self._all_weeks if s_ord <= _week_to_order(w) <= e_ord]

    def _filter_data(self):
        sku     = self._sku_var.get()
        channel = self._channel_var.get()
        weeks   = self._get_filtered_weeks()

        nw  = self._nw[self._nw["week"].isin(weeks)].copy()
        rec = self._rec[self._rec["week"].isin(weeks)].copy()
        ev  = self._ev[self._ev["week"].isin(weeks)].copy()

        if sku != "All":
            nw  = nw[nw["product_id"] == sku]
            rec = rec[rec["product_id"] == sku]
            ev  = ev[ev["product_id"] == sku]

        if channel != "All":
            rec = rec[rec["channel_node"] == channel]
            ev  = ev[ev["lot_id"].isin(rec["lot_id"])]
            # Keep supply-chain nodes + selected channel for cost chart
            supply_nodes = nw[nw["revenue_base"] == 0]["node_id"].unique().tolist()
            nw = nw[nw["node_id"].isin(supply_nodes + [channel])]

        return nw, rec, ev, weeks

    def _redraw(self) -> None:
        nw_raw, rec_raw, ev_raw, weeks = self._filter_data()
        granularity = self._agg_var.get().lower()
        nw, rec, periods = _aggregate_weekly(nw_raw, rec_raw, granularity)

        selected_channels = (
            [self._channel_var.get()]
            if self._channel_var.get() != "All"
            else ["Both"]
        )

        n_lots = len(rec_raw.dropna(subset=["forward_cost_base"]))
        self._status_var.set(
            f"{len(weeks)} weeks | {n_lots} lots\n"
            f"SKU: {self._sku_var.get()}\n"
            f"Ch: {self._channel_var.get()}"
        )

        self._fig.clear()
        gs = gridspec.GridSpec(2, 3, figure=self._fig, hspace=0.45, wspace=0.40)
        ax1 = self._fig.add_subplot(gs[0, 0])
        ax2 = self._fig.add_subplot(gs[0, 1])
        ax3 = self._fig.add_subplot(gs[0, 2])
        ax4 = self._fig.add_subplot(gs[1, 0])
        ax5 = self._fig.add_subplot(gs[1, 1])
        ax6 = self._fig.add_subplot(gs[1, 2])

        cur = self._cur
        _draw_kpi_text(ax1, self._kpi, rec_raw, cur)
        _draw_profit_zone(ax2, ev_raw, cur)
        _draw_weekly_revenue(ax3, nw, periods, cur)
        _draw_weekly_cost(ax4, nw, periods, cur)
        _draw_margin_dist(ax5, rec_raw, selected_channels)
        _draw_fwd_bwd(ax6, rec, periods, cur)

        sku_tag = self._sku_var.get()
        ch_tag  = self._channel_var.get()
        w_tag   = (f"{weeks[0]}~{weeks[-1]}" if weeks else "—")
        self._fig.suptitle(
            f"WOM PPC Evaluation Cockpit  |  SKU: {sku_tag}  Channel: {ch_tag}  "
            f"Period: {w_tag}  [{granularity.capitalize()}]",
            fontsize=11, fontweight="bold", color=C_HEADER, y=0.99,
        )
        self._canvas.draw()

    def _save_png(self) -> None:
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("PDF", "*.pdf")],
            initialfile="ppc_cockpit_filtered.png",
        )
        if path:
            self._fig.savefig(path, dpi=150, bbox_inches="tight")
            self._status_var.set(f"Saved:\n{os.path.basename(path)}")


# ── Standalone launcher ───────────────────────────────────────────────────────

def run_app(output_dir: str = "output/ppc") -> None:
    """Launch the PPC Cockpit as a standalone Tk window."""
    root = tk.Tk()
    root.title("WOM PPC Evaluation Cockpit")
    root.geometry("1280x760")
    root.configure(bg=C_SIDEBAR)
    app = PPCCockpitApp(root, output_dir=output_dir)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
