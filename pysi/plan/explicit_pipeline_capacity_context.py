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


def _count_capability_context(
    context: Mapping[str, Mapping[str, Mapping[Any, Any]]],
) -> tuple[int, int, int]:
    node_count = len(context)
    product_count = 0
    record_count = 0
    for product_map in context.values():
        product_count += len(product_map)
        for week_map in product_map.values():
            record_count += len(week_map)
    return node_count, product_count, record_count


def maybe_attach_explicit_pipeline_backward_weekly_capability_from_csv(
    env: Any,
    path: str | Path = "data/explicit_pipeline_backward_weekly_capability.csv",
    *,
    scenario: str | None = "base",
    strict: bool = False,
    encoding: str = "utf-8-sig",
) -> dict[str, Any]:
    csv_path = Path(path)
    result: dict[str, Any] = {
        "path": str(csv_path),
        "scenario": scenario,
        "file_exists": csv_path.exists(),
        "attached": False,
        "record_count": 0,
        "node_count": 0,
        "product_count": 0,
        "reason": "",
    }

    if not result["file_exists"]:
        result["reason"] = "file_missing"
    else:
        context = load_explicit_pipeline_backward_weekly_capability_csv(
            csv_path,
            scenario=scenario,
            strict=strict,
            encoding=encoding,
        )
        node_count, product_count, record_count = _count_capability_context(context)
        result["record_count"] = record_count
        result["node_count"] = node_count
        result["product_count"] = product_count

        if record_count == 0:
            result["reason"] = "empty_context"
        else:
            attach_explicit_pipeline_backward_weekly_capability_to_env(env, context)
            result["attached"] = True

    env.explicit_pipeline_backward_weekly_capability_attach_result = result
    env.explicit_pipeline_backward_weekly_capability_source_path = str(csv_path)
    env.explicit_pipeline_backward_weekly_capability_source_scenario = scenario
    env.explicit_pipeline_backward_weekly_capability_attached = result["attached"]
    return result
