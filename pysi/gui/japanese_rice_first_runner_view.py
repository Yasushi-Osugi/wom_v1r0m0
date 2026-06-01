from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pysi.runners.run_japanese_rice_first_psi_vslice import (
    run_japanese_rice_first_psi_vslice,
)

TITLE = "WOM Japanese Rice First PSI Smoke"
DEFAULT_SCENARIO_ROOT = "examples/scenarios/japanese_rice_vslice_001"
_WEEKLY_COLUMNS = ("week", "requested", "capacity", "accepted", "blocked")


def _unavailable_model(error: str) -> dict[str, Any]:
    return {
        "available": False,
        "title": TITLE,
        "summary_text": f"Japanese Rice first PSI smoke could not be run: {error}",
        "weekly_rows": [],
        "totals": {},
        "management_message": "",
        "error": error,
    }


def _safe_number(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def build_japanese_rice_weekly_capacity_gate_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build GUI table rows from the runner's stable capacity-gate demo summary."""

    demo_summary = result.get("demo_summary", {})
    gate_summary = demo_summary.get("capacity_gate_summary", {})
    weekly = gate_summary.get("weekly", {})
    if not isinstance(weekly, dict):
        return []

    weeks = demo_summary.get("weeks")
    if not weeks:
        weeks = sorted(weekly)

    rows: list[dict[str, Any]] = []
    for week in weeks:
        week_values = weekly.get(week, {})
        if not isinstance(week_values, dict):
            continue
        rows.append(
            {
                "week": week,
                "requested": _safe_number(week_values.get("requested", 0)),
                "capacity": _safe_number(week_values.get("capacity", 0)),
                "accepted": _safe_number(week_values.get("accepted", 0)),
                "blocked": _safe_number(week_values.get("blocked", 0)),
            }
        )
    return rows


def format_japanese_rice_gui_summary_text(result: dict[str, Any]) -> str:
    """Format the GUI summary text directly from the stable CLI summary lines."""

    lines = result.get("cli_summary_lines", [])
    if not isinstance(lines, list):
        return ""
    return "\n".join(str(line) for line in lines)


def extract_japanese_rice_first_runner_gui_model(result: dict[str, Any]) -> dict[str, Any]:
    """Extract a small GUI model from the stable Japanese Rice runner contract.

    GUI display code should not need to understand runner internals. This helper
    intentionally consumes the public demo summary and CLI summary lines only.
    """

    if not isinstance(result, dict):
        return _unavailable_model("runner result is not a dictionary")
    if result.get("available") is not True:
        messages = result.get("messages")
        if isinstance(messages, list) and messages:
            return _unavailable_model("; ".join(str(message) for message in messages))
        return _unavailable_model("runner result is unavailable")

    try:
        demo_summary = result["demo_summary"]
        gate_summary = demo_summary["capacity_gate_summary"]
        totals = gate_summary["totals"]
        summary_text = format_japanese_rice_gui_summary_text(result)
        weekly_rows = build_japanese_rice_weekly_capacity_gate_rows(result)

        return {
            "available": True,
            "title": TITLE,
            "scenario_id": demo_summary["scenario_id"],
            "product_name": demo_summary["product_name"],
            "contract_version": result["contract_version"],
            "runner_mode": demo_summary["runner_mode"],
            "full_psi_plan": demo_summary["full_psi_plan"],
            "summary_text": summary_text,
            "weekly_rows": weekly_rows,
            "totals": {
                "requested": _safe_number(totals["requested"]),
                "capacity": _safe_number(totals["capacity"]),
                "accepted": _safe_number(totals["accepted"]),
                "blocked": _safe_number(totals["blocked"]),
            },
            "management_message": demo_summary.get("management_message", ""),
        }
    except Exception as exc:
        return _unavailable_model(str(exc))


def _launch_model_window(model: dict[str, Any]) -> None:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText

    root = tk.Tk()
    root.title(model.get("title", TITLE))
    root.geometry("860x620")

    container = ttk.Frame(root, padding=12)
    container.pack(fill=tk.BOTH, expand=True)

    title = ttk.Label(
        container,
        text=model.get("title", TITLE),
        font=("TkDefaultFont", 14, "bold"),
    )
    title.pack(anchor=tk.W, pady=(0, 8))

    info = ttk.Label(
        container,
        justify=tk.LEFT,
        text="\n".join(
            [
                f'Scenario: {model.get("scenario_id", "")}',
                f'Product: {model.get("product_name", "")}',
                f'Contract: {model.get("contract_version", "")}',
                f'Mode: {model.get("runner_mode", "")}',
                f'Full PSI plan: {model.get("full_psi_plan", "")}',
            ]
        ),
    )
    info.pack(anchor=tk.W, pady=(0, 8))

    summary = ScrolledText(container, height=13, wrap=tk.WORD)
    summary.insert(tk.END, model.get("summary_text", ""))
    summary.configure(state=tk.DISABLED)
    summary.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    table = ttk.Treeview(container, columns=_WEEKLY_COLUMNS, show="headings", height=4)
    headings = {
        "week": "Week",
        "requested": "Requested",
        "capacity": "Capacity",
        "accepted": "Accepted",
        "blocked": "Blocked",
    }
    widths = {
        "week": 130,
        "requested": 100,
        "capacity": 100,
        "accepted": 100,
        "blocked": 100,
    }
    for column in _WEEKLY_COLUMNS:
        table.heading(column, text=headings[column])
        table.column(column, width=widths[column], anchor=tk.CENTER)
    for row in model.get("weekly_rows", []):
        table.insert("", tk.END, values=tuple(row.get(column, "") for column in _WEEKLY_COLUMNS))
    table.pack(fill=tk.X, pady=(0, 10))

    totals = model.get("totals", {})
    totals_text = "\n".join(
        f"{key} = {totals[key]}"
        for key in ("requested", "capacity", "accepted", "blocked")
        if key in totals
    )
    ttk.Label(container, justify=tk.LEFT, text=totals_text).pack(anchor=tk.W, pady=(0, 8))
    ttk.Label(
        container,
        justify=tk.LEFT,
        text=model.get("management_message", ""),
        font=("TkDefaultFont", 10, "bold"),
    ).pack(anchor=tk.W)

    root.mainloop()


def launch_japanese_rice_first_runner_view(
    scenario_root: str | Path = DEFAULT_SCENARIO_ROOT,
) -> None:
    """Run the first Japanese Rice PSI smoke and show it in a small Tkinter view."""

    result = run_japanese_rice_first_psi_vslice(scenario_root)
    model = extract_japanese_rice_first_runner_gui_model(result)
    _launch_model_window(model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Launch the Japanese Rice first PSI smoke GUI wrapper."
    )
    parser.add_argument(
        "--scenario-root",
        default=DEFAULT_SCENARIO_ROOT,
        help="Path to the Japanese Rice scenario root.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_japanese_rice_first_psi_vslice(args.scenario_root)
        model = extract_japanese_rice_first_runner_gui_model(result)
        if not model.get("available"):
            print(model.get("summary_text", "Japanese Rice first PSI smoke unavailable."))
            return 1
        _launch_model_window(model)
    except Exception as exc:
        print(f"Japanese Rice first PSI smoke GUI failed: {exc}")
        return 1
    return 0


__all__ = [
    "build_japanese_rice_weekly_capacity_gate_rows",
    "extract_japanese_rice_first_runner_gui_model",
    "format_japanese_rice_gui_summary_text",
    "launch_japanese_rice_first_runner_view",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
