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


def build_japanese_rice_weekly_capacity_gate_rows(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
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


def _ratio(numerator: Any, denominator: Any) -> float | int:
    if denominator > 0:
        return numerator / denominator
    return 0


def _capacity_gate_chart_row(row: dict[str, Any]) -> dict[str, Any]:
    requested = _safe_number(row.get("requested", 0))
    capacity = _safe_number(row.get("capacity", 0))
    accepted = _safe_number(row.get("accepted", 0))
    blocked = _safe_number(row.get("blocked", 0))
    capacity_usage_ratio = _ratio(accepted, capacity)
    blocked_ratio = _ratio(blocked, requested)

    return {
        "week": row.get("week", ""),
        "requested": requested,
        "capacity": capacity,
        "accepted": accepted,
        "blocked": blocked,
        "shortage": blocked,
        "unused_capacity": max(capacity - accepted, 0),
        "capacity_usage_ratio": capacity_usage_ratio,
        "blocked_ratio": blocked_ratio,
        "capacity_usage_pct": capacity_usage_ratio * 100,
        "blocked_pct": blocked_ratio * 100,
    }


def _capacity_gate_chart_totals(
    rows: list[dict[str, Any]], totals: dict[str, Any]
) -> dict[str, Any]:
    requested = _safe_number(
        totals.get("requested", sum(row.get("requested", 0) for row in rows))
    )
    capacity = _safe_number(
        totals.get("capacity", sum(row.get("capacity", 0) for row in rows))
    )
    accepted = _safe_number(
        totals.get("accepted", sum(row.get("accepted", 0) for row in rows))
    )
    blocked = _safe_number(
        totals.get("blocked", sum(row.get("blocked", 0) for row in rows))
    )
    capacity_usage_ratio = _ratio(accepted, capacity)
    blocked_ratio = _ratio(blocked, requested)

    return {
        "requested": requested,
        "capacity": capacity,
        "accepted": accepted,
        "blocked": blocked,
        "shortage": blocked,
        "unused_capacity": max(capacity - accepted, 0),
        "capacity_usage_ratio": capacity_usage_ratio,
        "blocked_ratio": blocked_ratio,
        "capacity_usage_pct": capacity_usage_ratio * 100,
        "blocked_pct": blocked_ratio * 100,
    }


def build_japanese_rice_capacity_gate_chart_dataset(
    model_or_result: dict[str, Any],
) -> dict[str, Any]:
    """Build a stable chart-ready capacity-gate dataset from the GUI model.

    The chart dataset intentionally mirrors the existing GUI weekly table and adds
    only presentation-neutral derived metrics. If a runner result is supplied
    instead of a GUI model, convert it through the GUI model extractor rather
    than duplicating runner summary logic.
    """

    source = model_or_result
    if not isinstance(source, dict):
        source = {}
    if "weekly_rows" not in source:
        source = extract_japanese_rice_first_runner_gui_model(source)

    weekly_rows = source.get("weekly_rows", [])
    if not isinstance(weekly_rows, list):
        weekly_rows = []
    rows = [
        _capacity_gate_chart_row(row) for row in weekly_rows if isinstance(row, dict)
    ]

    totals = source.get("totals", {})
    if not isinstance(totals, dict):
        totals = {}

    return {
        "title": "Japanese Rice DC_KANTO capacity gate",
        "x_key": "week",
        "series": ["requested", "capacity", "accepted", "blocked"],
        "rows": rows,
        "totals": _capacity_gate_chart_totals(rows, totals),
        "unit": "lot",
        "chart_hint": "line_or_grouped_bar",
    }


def build_capacity_override_chart_dataset(
    base_dataset: dict[str, Any],
    *,
    capacity_value: int,
    scenario_label: str = "Capacity-up",
) -> dict[str, Any]:
    """Build a deterministic capacity-override variant from a base chart dataset.

    This helper intentionally stays presentation-neutral and does not mutate any
    scenario master data or planner state. It reuses the requested lots by week
    from the supplied base dataset, replaces same-week capacity with the given
    override, and recalculates the simple capacity-gate metrics.
    """

    if not isinstance(base_dataset, dict):
        base_dataset = {}

    base_rows = base_dataset.get("rows", [])
    if not isinstance(base_rows, list):
        base_rows = []

    rows: list[dict[str, Any]] = []
    for row in base_rows:
        if not isinstance(row, dict):
            continue
        requested = _safe_number(row.get("requested", 0))
        capacity = _safe_number(capacity_value)
        accepted = min(requested, capacity)
        blocked = max(requested - capacity, 0)
        rows.append(
            _capacity_gate_chart_row(
                {
                    "week": row.get("week", ""),
                    "requested": requested,
                    "capacity": capacity,
                    "accepted": accepted,
                    "blocked": blocked,
                }
            )
        )

    return {
        "title": f"Japanese Rice DC_KANTO capacity gate - {scenario_label}",
        "scenario_label": scenario_label,
        "capacity_override": _safe_number(capacity_value),
        "unit": base_dataset.get("unit", "lot"),
        "x_key": base_dataset.get("x_key", "week"),
        "series": base_dataset.get(
            "series", ["requested", "capacity", "accepted", "blocked"]
        ),
        "rows": rows,
        "totals": _capacity_gate_chart_totals(rows, {}),
        "chart_hint": base_dataset.get("chart_hint", "line_or_grouped_bar"),
    }


def _capacity_gate_totals_from_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dataset, dict):
        dataset = {}
    rows = dataset.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    totals = dataset.get("totals", {})
    if not isinstance(totals, dict):
        totals = {}
    return _capacity_gate_chart_totals(
        [row for row in rows if isinstance(row, dict)], totals
    )


def build_capacity_gate_scenario_comparison(
    base_dataset: dict[str, Any],
    variant_dataset: dict[str, Any],
    *,
    base_label: str = "Base",
    variant_label: str = "Capacity-up",
) -> dict[str, Any]:
    """Compare two capacity-gate datasets week-by-week and in total."""

    if not isinstance(base_dataset, dict):
        base_dataset = {}
    if not isinstance(variant_dataset, dict):
        variant_dataset = {}

    base_rows_raw = base_dataset.get("rows", [])
    variant_rows_raw = variant_dataset.get("rows", [])
    base_rows = (
        [row for row in base_rows_raw if isinstance(row, dict)]
        if isinstance(base_rows_raw, list)
        else []
    )
    variant_rows = (
        [row for row in variant_rows_raw if isinstance(row, dict)]
        if isinstance(variant_rows_raw, list)
        else []
    )
    variant_by_week = {row.get("week", ""): row for row in variant_rows}

    comparison_rows: list[dict[str, Any]] = []
    seen_weeks: set[Any] = set()
    ordered_base_weeks = [row.get("week", "") for row in base_rows]
    ordered_variant_only_weeks = [
        row.get("week", "")
        for row in variant_rows
        if row.get("week", "") not in ordered_base_weeks
    ]

    for week in [*ordered_base_weeks, *ordered_variant_only_weeks]:
        if week in seen_weeks:
            continue
        seen_weeks.add(week)
        base_row = next((row for row in base_rows if row.get("week", "") == week), {})
        variant_row = variant_by_week.get(week, {})

        base_requested = _safe_number(base_row.get("requested", 0))
        base_capacity = _safe_number(base_row.get("capacity", 0))
        base_accepted = _safe_number(base_row.get("accepted", 0))
        base_blocked = _safe_number(base_row.get("blocked", 0))
        variant_requested = _safe_number(variant_row.get("requested", 0))
        variant_capacity = _safe_number(variant_row.get("capacity", 0))
        variant_accepted = _safe_number(variant_row.get("accepted", 0))
        variant_blocked = _safe_number(variant_row.get("blocked", 0))

        comparison_rows.append(
            {
                "week": week,
                "base_requested": base_requested,
                "base_capacity": base_capacity,
                "base_accepted": base_accepted,
                "base_blocked": base_blocked,
                "variant_requested": variant_requested,
                "variant_capacity": variant_capacity,
                "variant_accepted": variant_accepted,
                "variant_blocked": variant_blocked,
                "delta_capacity": variant_capacity - base_capacity,
                "delta_accepted": variant_accepted - base_accepted,
                "delta_blocked": variant_blocked - base_blocked,
            }
        )

    base_totals = _capacity_gate_totals_from_dataset(base_dataset)
    variant_totals = _capacity_gate_totals_from_dataset(variant_dataset)
    delta_totals = {
        "capacity": variant_totals["capacity"] - base_totals["capacity"],
        "accepted": variant_totals["accepted"] - base_totals["accepted"],
        "blocked": variant_totals["blocked"] - base_totals["blocked"],
    }
    blocked_reduction = base_totals["blocked"] - variant_totals["blocked"]
    blocked_reduction_ratio = _ratio(blocked_reduction, base_totals["blocked"])

    totals = {
        "base": {
            "requested": base_totals["requested"],
            "capacity": base_totals["capacity"],
            "accepted": base_totals["accepted"],
            "blocked": base_totals["blocked"],
        },
        "variant": {
            "requested": variant_totals["requested"],
            "capacity": variant_totals["capacity"],
            "accepted": variant_totals["accepted"],
            "blocked": variant_totals["blocked"],
        },
        "delta": delta_totals,
        "blocked_reduction": blocked_reduction,
        "blocked_reduction_ratio": blocked_reduction_ratio,
        "blocked_reduction_pct": blocked_reduction_ratio * 100,
    }
    comparison = {
        "title": "Japanese Rice DC_KANTO capacity scenario comparison",
        "base_label": base_label,
        "variant_label": variant_label,
        "rows": comparison_rows,
        "totals": totals,
        "management_message": "",
    }
    comparison["management_message"] = format_capacity_gate_scenario_comparison_text(
        comparison
    )
    return comparison


def format_capacity_gate_scenario_comparison_text(comparison: dict[str, Any]) -> str:
    """Format a concise management summary for the Base vs Capacity-up comparison."""

    if not isinstance(comparison, dict):
        comparison = {}
    totals = comparison.get("totals", {})
    if not isinstance(totals, dict):
        totals = {}
    base = totals.get("base", {}) if isinstance(totals.get("base", {}), dict) else {}
    variant = (
        totals.get("variant", {}) if isinstance(totals.get("variant", {}), dict) else {}
    )
    base_label = comparison.get("base_label", "Base")
    variant_label = comparison.get("variant_label", "Capacity-up")
    base_capacity = base.get("capacity", 0)
    variant_capacity = variant.get("capacity", 0)
    rows = comparison.get("rows", [])
    row_count = len(rows) if isinstance(rows, list) else 0
    if row_count > 0:
        base_capacity = _safe_number(base_capacity / row_count)
        variant_capacity = _safe_number(variant_capacity / row_count)

    return "\n".join(
        [
            "Scenario variation:",
            f"  {base_label} DC_KANTO capacity: {base_capacity}",
            f"  {variant_label} capacity: {variant_capacity}",
            f"  blocked lots: {base.get('blocked', 0)} -> {variant.get('blocked', 0)}",
            f"  blocked reduction: {totals.get('blocked_reduction', 0)} lots",
            f"  blocked reduction: {totals.get('blocked_reduction_pct', 0):.1f}%",
            f"  accepted lots: {base.get('accepted', 0)} -> {variant.get('accepted', 0)}",
        ]
    )


def build_japanese_rice_capacity_gate_chart_series(
    dataset: dict[str, Any],
) -> dict[str, Any]:
    """Convert a capacity-gate chart dataset into x values and numeric series.

    This helper is intentionally presentation-neutral: it consumes the stable
    chart dataset rows and returns arrays that can be plotted by Tkinter,
    Matplotlib, or another renderer without re-reading runner internals.
    """

    if not isinstance(dataset, dict):
        dataset = {}

    x_key = dataset.get("x_key", "week")
    if not isinstance(x_key, str) or not x_key:
        x_key = "week"

    series_names = dataset.get("series", list(_WEEKLY_COLUMNS[1:]))
    if not isinstance(series_names, list) or not series_names:
        series_names = list(_WEEKLY_COLUMNS[1:])
    series_names = [str(name) for name in series_names]

    rows = dataset.get("rows", [])
    if not isinstance(rows, list):
        rows = []

    weeks: list[Any] = []
    series = {name: [] for name in series_names}
    for row in rows:
        if not isinstance(row, dict):
            continue
        weeks.append(row.get(x_key, ""))
        for name in series_names:
            series[name].append(_safe_number(row.get(name, 0)))

    return {
        "title": dataset.get("title", "Japanese Rice DC_KANTO capacity gate"),
        "x_key": x_key,
        "unit": dataset.get("unit", "lot"),
        "weeks": weeks,
        "series": series,
    }


def format_japanese_rice_gui_summary_text(result: dict[str, Any]) -> str:
    """Format the GUI summary text directly from the stable CLI summary lines."""

    lines = result.get("cli_summary_lines", [])
    if not isinstance(lines, list):
        return ""
    return "\n".join(str(line) for line in lines)


def extract_japanese_rice_first_runner_gui_model(
    result: dict[str, Any],
) -> dict[str, Any]:
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


def add_capacity_gate_chart_to_window(parent: Any, dataset: dict[str, Any]) -> Any:
    """Add a simple Tkinter line chart for requested/capacity/accepted/blocked lots."""

    import tkinter as tk
    from tkinter import ttk

    chart = build_japanese_rice_capacity_gate_chart_series(dataset)
    frame = ttk.LabelFrame(parent, text=chart["title"], padding=8)

    canvas_width = 780
    canvas_height = 220
    canvas = tk.Canvas(
        frame, width=canvas_width, height=canvas_height, background="white"
    )
    canvas.pack(fill=tk.X, expand=True)

    margin_left = 56
    margin_right = 24
    margin_top = 20
    margin_bottom = 44
    plot_left = margin_left
    plot_right = canvas_width - margin_right
    plot_top = margin_top
    plot_bottom = canvas_height - margin_bottom
    plot_width = max(plot_right - plot_left, 1)
    plot_height = max(plot_bottom - plot_top, 1)

    weeks = [str(week) for week in chart["weeks"]]
    series = chart["series"]
    values = [
        value
        for values in series.values()
        for value in values
        if isinstance(value, (int, float))
    ]
    max_value = max(values) if values else 0
    y_max = max(max_value, 1)

    canvas.create_line(plot_left, plot_bottom, plot_right, plot_bottom, fill="#666666")
    canvas.create_line(plot_left, plot_top, plot_left, plot_bottom, fill="#666666")
    canvas.create_text(
        plot_left,
        6,
        anchor=tk.W,
        text=f'{chart["x_key"].title()} / {str(chart["unit"]).title()}s',
        fill="#444444",
    )

    for tick in range(0, 5):
        ratio = tick / 4
        y = plot_bottom - (ratio * plot_height)
        label_value = round(y_max * ratio)
        canvas.create_line(plot_left, y, plot_right, y, fill="#eeeeee")
        canvas.create_text(
            plot_left - 8, y, anchor=tk.E, text=str(label_value), fill="#666666"
        )

    if len(weeks) <= 1:
        x_positions = [plot_left + (plot_width / 2)] if weeks else []
    else:
        x_positions = [
            plot_left + (idx * plot_width / (len(weeks) - 1))
            for idx in range(len(weeks))
        ]

    for x, week in zip(x_positions, weeks, strict=True):
        canvas.create_line(x, plot_bottom, x, plot_bottom + 4, fill="#666666")
        canvas.create_text(x, plot_bottom + 16, text=week, fill="#444444")

    colors = {
        "requested": "#1f77b4",
        "capacity": "#ff7f0e",
        "accepted": "#2ca02c",
        "blocked": "#d62728",
    }
    legend_x = plot_left
    legend_y = plot_bottom + 31
    for name in series:
        color = colors.get(name, "#444444")
        canvas.create_line(
            legend_x, legend_y, legend_x + 18, legend_y, fill=color, width=2
        )
        canvas.create_text(
            legend_x + 24, legend_y, anchor=tk.W, text=name, fill="#333333"
        )
        legend_x += 118

    for name, raw_values in series.items():
        color = colors.get(name, "#444444")
        points: list[float] = []
        for x, value in zip(x_positions, raw_values, strict=True):
            numeric_value = value if isinstance(value, (int, float)) else 0
            y = plot_bottom - ((numeric_value / y_max) * plot_height)
            points.extend([x, y])
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)
        if len(points) >= 4:
            canvas.create_line(*points, fill=color, width=2)
        elif len(points) == 2:
            x, y = points
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)

    frame.pack(fill=tk.X, pady=(0, 10))
    return frame


def _create_scrollable_frame(parent: Any) -> tuple[Any, Any, Any]:
    """Create a vertically scrollable Tkinter frame for the GUI content."""

    import tkinter as tk
    from tkinter import ttk

    outer = ttk.Frame(parent)
    outer.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, padding=12)
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)

    def _refresh_scrollregion(_event: Any = None) -> None:
        canvas.configure(scrollregion=canvas.bbox(tk.ALL))

    def _fit_frame_width(event: Any) -> None:
        canvas.itemconfigure(canvas_window, width=event.width)

    def _on_mousewheel(event: Any) -> str:
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -int(event.delta / 120) if event.delta else 0
        if delta:
            canvas.yview_scroll(delta, "units")
        return "break"

    def _bind_mousewheel(_event: Any = None) -> None:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(_event: Any = None) -> None:
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    scrollable_frame.bind("<Configure>", _refresh_scrollregion)
    canvas.bind("<Configure>", _fit_frame_width)
    canvas.bind("<Enter>", _bind_mousewheel)
    canvas.bind("<Leave>", _unbind_mousewheel)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    return scrollable_frame, canvas, scrollbar


def _launch_model_window(model: dict[str, Any]) -> None:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText

    root = tk.Tk()
    root.title(model.get("title", TITLE))
    root.geometry("1280x900")

    container, _canvas, _scrollbar = _create_scrollable_frame(root)

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

    summary = ScrolledText(container, height=8, wrap=tk.WORD)
    summary.insert(tk.END, model.get("summary_text", ""))
    summary.configure(state=tk.DISABLED)
    summary.pack(fill=tk.X, pady=(0, 10))

    chart_dataset = build_japanese_rice_capacity_gate_chart_dataset(model)
    add_capacity_gate_chart_to_window(container, chart_dataset)

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
        table.insert(
            "",
            tk.END,
            values=tuple(row.get(column, "") for column in _WEEKLY_COLUMNS),
        )
    table.pack(fill=tk.X, pady=(0, 10))

    totals = model.get("totals", {})
    totals_text = "\n".join(
        f"{key} = {totals[key]}"
        for key in ("requested", "capacity", "accepted", "blocked")
        if key in totals
    )
    ttk.Label(container, justify=tk.LEFT, text=totals_text).pack(
        anchor=tk.W, pady=(0, 8)
    )
    ttk.Label(
        container,
        justify=tk.LEFT,
        text=model.get("management_message", ""),
        font=("TkDefaultFont", 10, "bold"),
    ).pack(anchor=tk.W)

    variant_dataset = build_capacity_override_chart_dataset(
        chart_dataset, capacity_value=100, scenario_label="Capacity-up"
    )
    scenario_comparison = build_capacity_gate_scenario_comparison(
        chart_dataset, variant_dataset
    )
    ttk.Label(
        container,
        justify=tk.LEFT,
        text=scenario_comparison["management_message"],
    ).pack(anchor=tk.W, pady=(8, 0))

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
            print(
                model.get("summary_text", "Japanese Rice first PSI smoke unavailable.")
            )
            return 1
        _launch_model_window(model)
    except Exception as exc:
        print(f"Japanese Rice first PSI smoke GUI failed: {exc}")
        return 1
    return 0


__all__ = [
    "add_capacity_gate_chart_to_window",
    "build_capacity_gate_scenario_comparison",
    "build_capacity_override_chart_dataset",
    "build_japanese_rice_capacity_gate_chart_dataset",
    "build_japanese_rice_capacity_gate_chart_series",
    "build_japanese_rice_weekly_capacity_gate_rows",
    "extract_japanese_rice_first_runner_gui_model",
    "format_capacity_gate_scenario_comparison_text",
    "format_japanese_rice_gui_summary_text",
    "launch_japanese_rice_first_runner_view",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
