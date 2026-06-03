from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from pysi.gui.wom_run_full_plan_graph_panel_adapter import (
    build_run_full_plan_capacity_gate_chart_dataset,
    build_run_full_plan_capacity_gate_chart_series,
    extract_run_full_plan_graph_panel_model_from_output_dir,
)

VIEWER_NAME = "WOM Run Full Plan Result Viewer"
TABLE_FIELDS = [
    "week",
    "requested",
    "capacity",
    "accepted",
    "blocked",
    "capacity_usage_pct",
    "blocked_pct",
]
TOTAL_LABELS = [
    ("Requested", "requested"),
    ("Capacity", "capacity"),
    ("Accepted", "accepted"),
    ("Blocked", "blocked"),
]
SERIES_STYLES = {
    "requested": {"color": "#1f77b4", "label": "Requested"},
    "capacity": {"color": "#ff7f0e", "label": "Capacity"},
    "accepted": {"color": "#2ca02c", "label": "Accepted"},
    "blocked": {"color": "#d62728", "label": "Blocked"},
}


def build_viewer_title(model: dict) -> str:
    """Build a safe human-readable window title for a graph-panel model."""

    if not isinstance(model, dict):
        return f"{VIEWER_NAME} - unavailable"

    scenario_id = model.get("scenario_id")
    run_id = model.get("run_id")
    identifier = scenario_id or run_id
    if identifier:
        return f"{VIEWER_NAME} - {identifier}"

    status = model.get("status") or (
        "unavailable" if not model.get("available") else ""
    )
    if status:
        return f"{VIEWER_NAME} - {status}"
    return VIEWER_NAME


def _numeric_or_zero(value: Any) -> int | float:
    if isinstance(value, (int, float)):
        return value
    if value in (None, ""):
        return 0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0
    if number.is_integer():
        return int(number)
    return number


def _format_number(value: Any) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
    return str(value)


def format_capacity_gate_weekly_table_rows(model: dict) -> list[dict]:
    """Format capacity-gate weekly rows for a read-only table display."""

    if not isinstance(model, dict) or not model.get("available", False):
        return []

    formatted_rows = []
    for row in model.get("rows", []):
        table_row = {field: row.get(field, "") for field in TABLE_FIELDS}
        for field in TABLE_FIELDS[1:]:
            table_row[field] = _numeric_or_zero(table_row.get(field))
        formatted_rows.append(table_row)
    return formatted_rows


def build_totals_display_rows(model: dict) -> list[dict]:
    """Build label/value rows for the totals section."""

    if not isinstance(model, dict) or not model.get("available", False):
        return []

    totals = model.get("totals", {})
    return [
        {"label": label, "value": _numeric_or_zero(totals.get(key, 0)), "key": key}
        for label, key in TOTAL_LABELS
    ]


def _summary_text(model: dict) -> str:
    if not isinstance(model, dict):
        return "Status: unavailable\nReason: invalid graph-panel model\nNo graph data is available."
    if model.get("available", False):
        return model.get("summary_text") or "WOM Run Full Plan summary is unavailable."
    reason = model.get("reason", "unknown reason")
    return f"Status: unavailable\nReason: {reason}\nNo graph data is available."


def _diagnostic_lines(model: dict) -> list[str]:
    if not isinstance(model, dict):
        return ["invalid graph-panel model"]

    lines = []
    for message in model.get("messages", []):
        lines.append(f"Message: {message}")
    management_message = model.get("management_message")
    if management_message:
        lines.append(f"Management: {management_message}")
    for diagnostic in model.get("diagnostics", []):
        lines.append(f"Diagnostic: {diagnostic}")
    if not model.get("available", False) and model.get("reason"):
        lines.append(f"Reason: {model.get('reason')}")
    return lines


def _section(parent: Any, title: str) -> Any:
    import tkinter as tk

    frame = tk.LabelFrame(parent, text=title, padx=8, pady=8)
    frame.pack(fill="both", expand=False, padx=12, pady=6)
    return frame


def _add_header(parent: Any, model: dict) -> None:
    import tkinter as tk

    frame = _section(parent, "Header")
    tk.Label(
        frame,
        text=VIEWER_NAME,
        font=("TkDefaultFont", 16, "bold"),
        anchor="w",
    ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

    fields = [
        ("Scenario", model.get("scenario_id", "")),
        ("Run ID", model.get("run_id", "")),
        ("Run mode", model.get("run_mode", "")),
        ("Full PSI plan", model.get("full_psi_plan", "")),
        ("Status", model.get("status", "")),
    ]
    for index, (label, value) in enumerate(fields, start=1):
        column = 0 if index <= 3 else 2
        row = index if index <= 3 else index - 3
        tk.Label(frame, text=f"{label}:", font=("TkDefaultFont", 10, "bold")).grid(
            row=row, column=column, sticky="w", padx=(0, 6), pady=2
        )
        tk.Label(frame, text=str(value), anchor="w").grid(
            row=row, column=column + 1, sticky="w", pady=2
        )
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(3, weight=1)


def _add_summary(parent: Any, model: dict) -> None:
    import tkinter as tk

    frame = _section(parent, "Summary")
    tk.Message(frame, text=_summary_text(model), width=1180, anchor="w").pack(
        fill="x", expand=True
    )


def _draw_capacity_gate_chart(
    canvas: Any, model: dict, width: int = 1180, height: int = 300
) -> None:
    dataset = build_run_full_plan_capacity_gate_chart_dataset(model)
    chart = build_run_full_plan_capacity_gate_chart_series(dataset)
    weeks = chart.get("weeks", [])
    series = chart.get("series", {})

    canvas.delete("all")
    if not model.get("available", False) or not weeks:
        canvas.create_text(
            width // 2,
            height // 2,
            text="No graph data is available.",
            fill="#666666",
            font=("TkDefaultFont", 12, "bold"),
        )
        return

    left = 70
    right = width - 30
    top = 25
    bottom = height - 65
    values = [
        _numeric_or_zero(value)
        for key in SERIES_STYLES
        for value in series.get(key, [])
    ]
    max_value = max(values) if values else 0
    y_max = max(1, max_value * 1.15)

    canvas.create_line(left, bottom, right, bottom, fill="#333333")
    canvas.create_line(left, top, left, bottom, fill="#333333")
    for tick in range(0, 5):
        ratio = tick / 4
        y = bottom - ratio * (bottom - top)
        value = y_max * ratio
        canvas.create_line(left - 5, y, right, y, fill="#eeeeee")
        canvas.create_text(
            left - 10, y, text=f"{value:.0f}", anchor="e", fill="#555555"
        )

    x_step = (right - left) / max(1, len(weeks) - 1)
    x_positions = [left + index * x_step for index in range(len(weeks))]
    for x, week in zip(x_positions, weeks):
        canvas.create_line(x, bottom, x, bottom + 5, fill="#333333")
        canvas.create_text(x, bottom + 20, text=week, fill="#333333")

    for key, style in SERIES_STYLES.items():
        points = []
        for x, value in zip(x_positions, series.get(key, [])):
            y = bottom - (_numeric_or_zero(value) / y_max) * (bottom - top)
            points.extend([x, y])
            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4, fill=style["color"], outline=""
            )
        if len(points) >= 4:
            canvas.create_line(*points, fill=style["color"], width=2)

    legend_x = left
    legend_y = height - 25
    for key, style in SERIES_STYLES.items():
        canvas.create_rectangle(
            legend_x,
            legend_y - 6,
            legend_x + 14,
            legend_y + 6,
            fill=style["color"],
            outline="",
        )
        canvas.create_text(
            legend_x + 20, legend_y, text=style["label"], anchor="w", fill="#333333"
        )
        legend_x += 130


def _add_chart(parent: Any, model: dict) -> None:
    import tkinter as tk

    frame = _section(parent, "Capacity Gate Chart")
    canvas = tk.Canvas(frame, width=1180, height=300, background="white")
    canvas.pack(fill="x", expand=True)
    _draw_capacity_gate_chart(canvas, model)


def _add_weekly_table(parent: Any, model: dict) -> None:
    import tkinter as tk

    frame = _section(parent, "Weekly Table")
    headers = [
        "Week",
        "Requested",
        "Capacity",
        "Accepted",
        "Blocked",
        "Usage %",
        "Blocked %",
    ]
    for column, header in enumerate(headers):
        tk.Label(frame, text=header, font=("TkDefaultFont", 10, "bold"), padx=8).grid(
            row=0, column=column, sticky="w"
        )

    rows = format_capacity_gate_weekly_table_rows(model)
    if not rows:
        tk.Label(frame, text="No graph data is available.", padx=8, pady=4).grid(
            row=1, column=0, columnspan=len(headers), sticky="w"
        )
        return

    for row_index, row in enumerate(rows, start=1):
        values = [
            row.get("week", ""),
            _format_number(row.get("requested", 0)),
            _format_number(row.get("capacity", 0)),
            _format_number(row.get("accepted", 0)),
            _format_number(row.get("blocked", 0)),
            f"{float(row.get('capacity_usage_pct', 0)):.1f}%",
            f"{float(row.get('blocked_pct', 0)):.1f}%",
        ]
        for column, value in enumerate(values):
            tk.Label(frame, text=value, padx=8, pady=2).grid(
                row=row_index, column=column, sticky="w"
            )


def _add_totals(parent: Any, model: dict) -> None:
    import tkinter as tk

    frame = _section(parent, "Totals")
    rows = build_totals_display_rows(model)
    if not rows:
        tk.Label(frame, text="No totals are available.").pack(anchor="w")
        return
    for index, row in enumerate(rows):
        tk.Label(
            frame, text=f"{row['label']}:", font=("TkDefaultFont", 10, "bold")
        ).grid(row=0, column=index * 2, sticky="w", padx=(0, 4))
        tk.Label(frame, text=_format_number(row["value"])).grid(
            row=0, column=index * 2 + 1, sticky="w", padx=(0, 24)
        )


def _add_diagnostics(parent: Any, model: dict) -> None:
    import tkinter as tk

    lines = _diagnostic_lines(model)
    if not lines:
        return
    frame = _section(parent, "Messages / Diagnostics")
    tk.Message(frame, text="\n".join(lines), width=1180, anchor="w").pack(
        fill="x", expand=True
    )


def _build_viewer_window(model: dict) -> Any:
    import tkinter as tk

    root = tk.Tk()
    root.title(build_viewer_title(model))
    root.geometry("1280x900")

    canvas = tk.Canvas(root, borderwidth=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas)
    content.bind(
        "<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    _add_header(content, model)
    _add_summary(content, model)
    _add_chart(content, model)
    _add_weekly_table(content, model)
    _add_totals(content, model)
    _add_diagnostics(content, model)
    return root


def launch_run_full_plan_result_viewer(run_dir: str | Path) -> int:
    """Load a Run Full Plan output directory and open the read-only Tk viewer."""

    model = extract_run_full_plan_graph_panel_model_from_output_dir(run_dir)
    try:
        root = _build_viewer_window(model)
        root.mainloop()
    except Exception as exc:  # pragma: no cover - depends on local GUI/display state
        print(f"Unable to open WOM Run Full Plan result viewer: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Open the WOM Run Full Plan result viewer."
    )
    parser.add_argument(
        "--run-dir", required=True, help="Run Full Plan output directory."
    )
    args = parser.parse_args(argv)
    return launch_run_full_plan_result_viewer(args.run_dir)


__all__ = [
    "build_viewer_title",
    "format_capacity_gate_weekly_table_rows",
    "build_totals_display_rows",
    "launch_run_full_plan_result_viewer",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
