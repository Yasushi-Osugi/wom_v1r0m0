"""Allocation rule engine skeleton.

Allocation is intentionally centralized here.
This version supports:
- blank market exclusion
- region-scoped market allocation based on source node naming
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _group_sum(lines: list[dict[str, Any]], dim: str, key: str, categories: set[str]) -> float:
    return sum(
        float(line.get("amount", 0.0) or 0.0)
        for line in lines
        if line.get(dim) == key and line.get("cost_category") in categories
    )


def _is_blank_bucket(bucket: Any) -> bool:
    return bucket is None or str(bucket).strip() == ""


def _infer_region_from_node(node_name: str) -> str:
    """
    Infer allocation region from current WOM node naming.

    Examples:
    - WS_NA, DAD_FAS_AMER -> AMER
    - WS_APAC, DAD_FAS_APAC, supply_point -> APAC/GLOBAL
    - WS_EU, DAD_FAS_EURO -> EURO
    """
    name = str(node_name or "").strip()

    if name in {"WS_NA", "DAD_FAS_AMER"}:
        return "AMER"
    if name in {"WS_APAC", "DAD_FAS_APAC"}:
        return "APAC"
    if name in {"WS_EU", "DAD_FAS_EURO"}:
        return "EURO"
    if name == "supply_point":
        return "GLOBAL"

    if "AMER" in name or "_NA" in name or name.startswith("RT_US") or name.startswith("CS_US"):
        return "AMER"
    if "APAC" in name or name.startswith("RT_CN") or name.startswith("RT_IN") or name.startswith("RT_JP") \
            or name.startswith("CS_CN") or name.startswith("CS_IN") or name.startswith("CS_JP"):
        return "APAC"
    if "EURO" in name or "_EU" in name or name.startswith("RT_DE") or name.startswith("RT_UK") \
            or name.startswith("CS_DE") or name.startswith("CS_UK"):
        return "EURO"

    return "GLOBAL"


def _infer_region_from_market(market_id: str) -> str:
    """
    Infer region from current MarketEntity naming.

    Examples:
    - MKT_US_* -> AMER
    - MKT_CN_*, MKT_IN_*, MKT_JP_* -> APAC
    - MKT_DE_*, MKT_UK_* -> EURO
    """
    m = str(market_id or "").strip()

    if m.startswith("MKT_US_"):
        return "AMER"
    if m.startswith("MKT_CN_") or m.startswith("MKT_IN_") or m.startswith("MKT_JP_"):
        return "APAC"
    if m.startswith("MKT_DE_") or m.startswith("MKT_UK_"):
        return "EURO"

    return "GLOBAL"


def _market_allowed_for_source(from_key: str, target_market: str) -> bool:
    """
    Region-limited allocation.

    Rules:
    - AMER source -> AMER markets only
    - APAC source -> APAC markets only
    - EURO source -> EURO markets only
    - GLOBAL source -> all concrete markets
    """
    source_region = _infer_region_from_node(from_key)
    market_region = _infer_region_from_market(target_market)

    if _is_blank_bucket(target_market):
        return False

    if source_region == "GLOBAL":
        return True

    return source_region == market_region


def _driver_weights(
    report_input: dict[str, Any],
    to_dim: str,
    driver: str,
    from_key: str | None = None,
) -> dict[str, float]:
    weights = defaultdict(float)

    for rec in report_input.get("records", []):
        bucket = rec.get(to_dim)

        if to_dim == "market":
            if _is_blank_bucket(bucket):
                continue

            if from_key and not _market_allowed_for_source(from_key, str(bucket)):
                continue

        if bucket is None:
            continue

        weights[str(bucket)] += float(rec.get(driver, 0.0) or 0.0)

    total = sum(weights.values())
    if total <= 0:
        keys = list(weights.keys())
        if not keys:
            return {}
        eq = 1.0 / len(keys)
        return {k: eq for k in keys}

    return {k: v / total for k, v in weights.items()}


def apply_allocation_rules(
    cost_result: dict[str, Any],
    allocation_rules: list[dict[str, Any]],
    report_input: dict[str, Any],
) -> dict[str, Any]:
    """Apply simple pool allocation and keep before/after trace."""
    source_lines = list(cost_result.get("cost_lines", []))
    allocated_lines = list(source_lines)
    breakdown: list[dict[str, Any]] = []

    for rule in allocation_rules:
        from_dim = rule.get("from_dim", "node")
        to_dim = rule.get("to_dim", "market")
        from_key = rule.get("from_key")
        driver = rule.get("driver", "sales_units")
        categories = set(rule.get("pool_categories", []))

        if from_key is None or not categories:
            continue

        pool_total = _group_sum(allocated_lines, from_dim, from_key, categories)
        if pool_total <= 0:
            continue

        weights = _driver_weights(
            report_input=report_input,
            to_dim=to_dim,
            driver=driver,
            from_key=from_key,
        )
        if not weights:
            continue

        for target_key, weight in weights.items():
            if to_dim == "market" and _is_blank_bucket(target_key):
                continue

            amount = pool_total * weight
            allocated_lines.append(
                {
                    "product": "ALL",
                    "node": from_key,
                    "week": "ALL",
                    "market": target_key if to_dim == "market" else None,
                    "cost_type": "allocation",
                    "cost_category": "allocated_pool",
                    "amount": amount,
                    "allocation_status": "allocated",
                    "allocation_rule": rule.get("name", "unnamed_rule"),
                    "from_dim": from_dim,
                    "to_dim": to_dim,
                    "driver": driver,
                    "weight": weight,
                }
            )
            breakdown.append(
                {
                    "rule_name": rule.get("name", "unnamed_rule"),
                    "from_key": from_key,
                    "to_key": target_key,
                    "driver": driver,
                    "weight": weight,
                    "allocated_amount": amount,
                }
            )

    return {
        "cost_lines_before": source_lines,
        "cost_lines_after": allocated_lines,
        "allocation_breakdown": breakdown,
    }