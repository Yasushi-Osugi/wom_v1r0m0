"""
wom/ppc/ppc_export.py
=====================
Export PPC Simulation results to CSV and JSON files.

Output files:
    ppc_event_ledger.csv        - all PPCEvents (full audit trail)
    ppc_node_week_summary.csv   - aggregated by node+week
    ppc_profit_zone_summary.csv - aggregated by profit_zone
    ppc_lot_reconciliation.csv  - lot-level forward vs backward comparison
    ppc_kpi_summary.json        - top-level KPI dict
"""

from __future__ import annotations

import json
import os
from typing import List

import pandas as pd

from .ppc_models import PPCEvent, PPCSimulationResult


def export_results(result: PPCSimulationResult, output_dir: str) -> None:
    """
    Write all PPC output files to `output_dir`.

    Parameters
    ----------
    result     : PPCSimulationResult
    output_dir : directory path (created if not exists)
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── ppc_event_ledger.csv ───────────────────────────────────────────
    events_df = _events_to_df(result.ppc_events)
    events_df.to_csv(os.path.join(output_dir, "ppc_event_ledger.csv"), index=False)

    # ── ppc_node_week_summary.csv ──────────────────────────────────────
    result.node_week_summary.to_csv(
        os.path.join(output_dir, "ppc_node_week_summary.csv"), index=False
    )

    # ── ppc_profit_zone_summary.csv ────────────────────────────────────
    result.profit_zone_summary.to_csv(
        os.path.join(output_dir, "ppc_profit_zone_summary.csv"), index=False
    )

    # ── ppc_lot_reconciliation.csv ─────────────────────────────────────
    result.lot_reconciliation.to_csv(
        os.path.join(output_dir, "ppc_lot_reconciliation.csv"), index=False
    )

    # ── ppc_kpi_summary.json ───────────────────────────────────────────
    kpi_path = os.path.join(output_dir, "ppc_kpi_summary.json")
    with open(kpi_path, "w", encoding="utf-8") as f:
        json.dump(result.kpi_summary, f, indent=2, ensure_ascii=False)

    print(f"[PPC Export] Written to {output_dir}/")
    print(f"  ppc_event_ledger.csv        ({len(events_df)} events)")
    print(f"  ppc_node_week_summary.csv   ({len(result.node_week_summary)} rows)")
    print(f"  ppc_profit_zone_summary.csv ({len(result.profit_zone_summary)} rows)")
    print(f"  ppc_lot_reconciliation.csv  ({len(result.lot_reconciliation)} rows)")
    print(f"  ppc_kpi_summary.json")


def _events_to_df(events: List[PPCEvent]) -> pd.DataFrame:
    """Convert PPCEvent list to DataFrame with standard column order."""
    if not events:
        return pd.DataFrame(columns=[
            "event_id", "week", "lot_id", "node_id", "edge_id", "product_id",
            "qty", "ppc_event_type", "amount_local", "currency", "fx_rate",
            "amount_base", "amount_per_unit_base", "source_rule", "direction",
            "profit_zone",
        ])
    return pd.DataFrame([
        {
            "event_id":            ev.event_id,
            "week":                ev.week,
            "lot_id":              ev.lot_id,
            "node_id":             ev.node_id,
            "edge_id":             ev.edge_id,
            "product_id":          ev.product_id,
            "qty":                 ev.qty,
            "ppc_event_type":      ev.ppc_event_type,
            "amount_local":        ev.amount_local,
            "currency":            ev.currency,
            "fx_rate":             ev.fx_rate,
            "amount_base":         ev.amount_base,
            "amount_per_unit_base": ev.amount_per_unit_base,
            "source_rule":         ev.source_rule,
            "direction":           ev.direction,
            "profit_zone":         ev.profit_zone,
        }
        for ev in events
    ])
