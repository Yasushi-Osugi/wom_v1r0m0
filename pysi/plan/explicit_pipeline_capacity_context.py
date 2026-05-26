from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_capability_lots(value: Any) -> int:
    lots = int(float(value))
    if lots < 0:
        raise ValueError("negative capability_lots")
    return lots


def _raise_or_skip(strict: bool, message: str) -> None:
    if strict:
        raise ValueError(message)


def build_explicit_pipeline_backward_weekly_capability(
    records: Iterable[Mapping[str, Any]],
    *,
    scenario: str | None = "base",
    strict: bool = False,
) -> dict[str, dict[str, dict[Any, int]]]:
    context: dict[str, dict[str, dict[Any, int]]] = {}

    for record in records:
        row_scenario = _to_text(record.get("scenario")) or "base"
        if scenario is not None and row_scenario != scenario:
            continue

        node = _to_text(record.get("node"))
        if not node:
            _raise_or_skip(strict, "missing node")
            continue

        product = _to_text(record.get("product"))
        if not product:
            _raise_or_skip(strict, "missing product")
            continue

        week = record.get("week")
        if week is None or _to_text(week) == "":
            _raise_or_skip(strict, "missing week")
            continue

        unit = _to_text(record.get("unit")) or "lot"
        if unit != "lot":
            _raise_or_skip(strict, "unsupported unit")
            continue

        capability_raw = record.get("capability_lots")
        try:
            capability_lots = _coerce_capability_lots(capability_raw)
        except (TypeError, ValueError) as exc:
            message = "negative capability_lots" if "negative" in str(exc) else "invalid capability_lots"
            _raise_or_skip(strict, message)
            continue

        context.setdefault(node, {}).setdefault(product, {})[week] = capability_lots

    return context


def load_explicit_pipeline_backward_weekly_capability_csv(
    path: str | Path,
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, dict[str, dict[Any, int]]]:
    csv_path = Path(path)
    with csv_path.open("r", newline="", encoding=encoding) as fp:
        rows = csv.DictReader(fp)
        return build_explicit_pipeline_backward_weekly_capability(
            rows,
            scenario=scenario,
            strict=strict,
        )


def attach_explicit_pipeline_backward_weekly_capability_to_env(
    env: Any,
    context: Mapping[str, Mapping[str, Mapping[Any, Any]]],
) -> Any:
    env.explicit_pipeline_backward_weekly_capability = context
    return env
