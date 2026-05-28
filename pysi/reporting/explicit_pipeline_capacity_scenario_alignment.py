"""Diagnostic helpers for explicit pipeline capacity scenario alignment."""

from __future__ import annotations

import re
from collections.abc import Iterable

_WEEK_LABEL_RE = re.compile(r"^\d{4}-W\d{2}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAMPLE_LIMIT = 10


def _sample(values: set[str], limit: int = _SAMPLE_LIMIT) -> list[str]:
    return sorted(values)[:limit]


def classify_week_key_domain(keys) -> str:
    items = list(keys or [])
    if not items:
        return "empty"

    tags: set[str] = set()
    for key in items:
        if isinstance(key, int) and not isinstance(key, bool):
            tags.add("integer_index")
        elif isinstance(key, str) and key.isdigit():
            tags.add("integer_string_index")
        elif isinstance(key, str) and _WEEK_LABEL_RE.match(key):
            tags.add("label_week")
        elif isinstance(key, str) and _DATE_RE.match(key):
            tags.add("date")
        else:
            tags.add("unknown")

    if len(tags) > 1:
        return "mixed"
    return next(iter(tags))


def extract_runtime_node_names(*roots) -> set[str]:
    names: set[str] = set()
    stack = [root for root in roots if root is not None]
    seen_ids: set[int] = set()

    while stack:
        node = stack.pop()
        node_id = id(node)
        if node_id in seen_ids:
            continue
        seen_ids.add(node_id)

        name = getattr(node, "name", None)
        if isinstance(name, str) and name:
            names.add(name)

        children = getattr(node, "children", None)
        if children is None:
            continue

        if isinstance(children, Iterable) and not isinstance(children, (str, bytes)):
            for child in children:
                if child is not None:
                    stack.append(child)

    return names


def infer_backward_capability_shape_version(context: dict | None) -> str:
    if context is None:
        return "not_available"
    if not context:
        return "empty"
    if not isinstance(context, dict):
        return "unknown"

    for node_map in context.values():
        if not isinstance(node_map, dict):
            return "unknown"
        for week_map in node_map.values():
            if not isinstance(week_map, dict):
                return "unknown"
    return "node_product_week_map_v1"


def infer_forward_capacity_shape_version(context: dict | None) -> str:
    if context is None:
        return "not_available"
    if not context:
        return "empty"
    if not isinstance(context, dict):
        return "unknown"

    found_dict = False
    found_list = False

    for node_map in context.values():
        if not isinstance(node_map, dict):
            return "unknown"
        for type_map in node_map.values():
            if not isinstance(type_map, dict):
                return "unknown"
            for capacity_value in type_map.values():
                if isinstance(capacity_value, dict):
                    found_dict = True
                elif isinstance(capacity_value, list):
                    found_list = True
                else:
                    return "unknown"

    if found_dict and not found_list:
        return "product_node_type_week_map_v1"
    if found_list and not found_dict:
        return "product_node_type_week_list_v0"
    return "unknown"


def build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
    *,
    selected_product: str | None,
    backward_weekly_capability: dict | None,
    forward_weekly_capacity: dict | None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    consumer_forward_capacity_shape_version: str = "product_node_type_week_list_v0",
    consumer_forward_week_domain: str = "integer_index",
) -> dict:
    forward = forward_weekly_capacity if isinstance(forward_weekly_capacity, dict) else {}
    backward = backward_weekly_capability if isinstance(backward_weekly_capability, dict) else {}

    forward_products = set(forward.keys())
    forward_nodes: set[str] = set()
    forward_types: set[str] = set()
    forward_week_keys: list = []

    for node_map in forward.values():
        if not isinstance(node_map, dict):
            continue
        forward_nodes.update(str(k) for k in node_map.keys())
        for type_map in node_map.values():
            if not isinstance(type_map, dict):
                continue
            forward_types.update(str(k) for k in type_map.keys())
            for week_obj in type_map.values():
                if isinstance(week_obj, dict):
                    forward_week_keys.extend(week_obj.keys())
                elif isinstance(week_obj, list):
                    forward_week_keys.extend(range(len(week_obj)))

    backward_nodes = set(backward.keys())
    backward_products: set[str] = set()
    backward_week_keys: list = []
    for product_map in backward.values():
        if not isinstance(product_map, dict):
            continue
        backward_products.update(str(k) for k in product_map.keys())
        for week_map in product_map.values():
            if isinstance(week_map, dict):
                backward_week_keys.extend(week_map.keys())

    forward_week_domain = classify_week_key_domain(forward_week_keys)
    backward_week_domain = classify_week_key_domain(backward_week_keys)
    forward_shape = infer_forward_capacity_shape_version(forward_weekly_capacity)
    backward_shape = infer_backward_capability_shape_version(backward_weekly_capability)

    runtime_nodes = extract_runtime_node_names(outbound_root, inbound_root)
    capacity_nodes = forward_nodes | backward_nodes
    matches = runtime_nodes & capacity_nodes
    unmatched = capacity_nodes - runtime_nodes

    fwd_match = selected_product in forward_products if selected_product else None
    bwd_match = selected_product in backward_products if selected_product else None

    if not selected_product:
        product_alignment = "unknown"
    else:
        checks = []
        if forward_weekly_capacity is not None:
            checks.append(bool(fwd_match))
        if backward_weekly_capability is not None:
            checks.append(bool(bwd_match))
        if not checks:
            product_alignment = "unknown"
        elif all(checks):
            product_alignment = "aligned"
        elif any(checks):
            product_alignment = "partial_match"
        else:
            product_alignment = "mismatch"

    if outbound_root is None and inbound_root is None:
        node_alignment = "unknown"
    elif not capacity_nodes:
        node_alignment = "unknown"
    elif capacity_nodes <= runtime_nodes:
        node_alignment = "aligned"
    elif matches:
        node_alignment = "partial_match"
    else:
        node_alignment = "mismatch"

    week_alignment = "aligned" if forward_week_domain == consumer_forward_week_domain else "mismatch"
    if forward_week_domain in {"empty", "unknown"}:
        week_alignment = "unknown"

    if forward_shape in {"not_available", "empty", "unknown"}:
        shape_alignment = "unknown"
    elif forward_shape == consumer_forward_capacity_shape_version:
        shape_alignment = "aligned"
    else:
        shape_alignment = "mismatch"

    if product_alignment == "mismatch" and node_alignment == "mismatch":
        scenario_alignment = "mismatch_or_sample_only"
    elif product_alignment == "aligned" and node_alignment in {"aligned", "partial_match"}:
        scenario_alignment = "likely_aligned"
    else:
        scenario_alignment = "unknown"

    if forward_weekly_capacity is None and backward_weekly_capability is None:
        effective = "not_evaluated"
    elif "mismatch" in {product_alignment, week_alignment, shape_alignment}:
        effective = "uncertain_or_not_applied"
    elif {product_alignment, week_alignment, shape_alignment} == {"aligned"}:
        effective = "applied"
    else:
        effective = "not_applied"

    messages: list[str] = []
    if selected_product and forward_weekly_capacity is not None and not fwd_match:
        messages.append(
            f"Selected product {selected_product} is not present in forward capacity context product set {sorted(forward_products)}."
        )
    if selected_product and backward_weekly_capability is not None and not bwd_match:
        messages.append(
            f"Selected product {selected_product} is not present in backward capability context product set {sorted(backward_products)}."
        )
    if week_alignment == "mismatch":
        messages.append(
            "Forward capacity uses week-key domain "
            f"{forward_week_domain}, while consumer expects {consumer_forward_week_domain}."
        )
    if shape_alignment == "mismatch":
        messages.append(
            f"Forward capacity producer shape appears to be {forward_shape}, while consumer expectation is "
            f"{consumer_forward_capacity_shape_version}."
        )
    if node_alignment == "mismatch":
        messages.append(
            "Capacity nodes do not match runtime tree nodes. "
            f"Unmatched capacity nodes: {sorted(unmatched)[:_SAMPLE_LIMIT]}."
        )

    severity = "info" if not messages else "warning"

    return {
        "available": True,
        "severity": severity,
        "selected_product": selected_product,
        "forward_capacity": {
            "available": forward_weekly_capacity is not None,
            "product_set": _sample(set(str(x) for x in forward_products)),
            "selected_product_present": bool(fwd_match) if fwd_match is not None else None,
            "node_set": _sample(set(str(x) for x in forward_nodes)),
            "capacity_type_set": _sample(set(str(x) for x in forward_types)),
            "week_key_sample": _sample(set(str(x) for x in forward_week_keys)),
            "week_key_domain": forward_week_domain,
            "shape_version": forward_shape,
        },
        "backward_capability": {
            "available": backward_weekly_capability is not None,
            "product_set": _sample(set(str(x) for x in backward_products)),
            "selected_product_present": bool(bwd_match) if bwd_match is not None else None,
            "node_set": _sample(set(str(x) for x in backward_nodes)),
            "week_key_sample": _sample(set(str(x) for x in backward_week_keys)),
            "week_key_domain": backward_week_domain,
            "shape_version": backward_shape,
        },
        "runtime_tree": {
            "runtime_node_count": len(runtime_nodes),
            "runtime_node_sample": _sample(runtime_nodes),
            "capacity_node_match_count": len(matches),
            "capacity_node_unmatched": _sample(unmatched),
        },
        "consumer_expectation": {
            "forward_capacity_week_domain": consumer_forward_week_domain,
            "forward_capacity_shape_version": consumer_forward_capacity_shape_version,
        },
        "alignment": {
            "product_alignment": product_alignment,
            "node_alignment": node_alignment,
            "week_domain_alignment": week_alignment,
            "shape_alignment": shape_alignment,
            "scenario_alignment": scenario_alignment,
            "effective_capacity_application": effective,
        },
        "messages": messages,
    }


def attach_explicit_pipeline_capacity_scenario_alignment_diagnostic_to_env(
    env,
    *,
    selected_product: str | None = None,
    outbound_root: object | None = None,
    inbound_root: object | None = None,
    backward_weekly_capability: dict | None = None,
    forward_weekly_capacity: dict | None = None,
) -> dict:
    """Compute and attach the explicit pipeline capacity scenario diagnostic.

    The diagnostic builder remains pure; this helper is the small runtime
    mutation point used by GUI preflight code to retain the diagnostic on env.
    Missing inputs are tolerated so the KPI view can still explain that the
    diagnostic was not fully evaluable.
    """
    selected_product = selected_product or getattr(env, "product_selected", None)
    backward_weekly_capability = backward_weekly_capability or getattr(
        env, "explicit_pipeline_backward_weekly_capability", None
    )
    forward_weekly_capacity = forward_weekly_capacity or getattr(
        env, "explicit_pipeline_forward_weekly_capacity", None
    )

    try:
        diagnostic = build_explicit_pipeline_capacity_scenario_alignment_diagnostic(
            selected_product=selected_product,
            backward_weekly_capability=backward_weekly_capability,
            forward_weekly_capacity=forward_weekly_capacity,
            outbound_root=outbound_root,
            inbound_root=inbound_root,
        )
    except Exception as exc:
        diagnostic = {
            "available": False,
            "severity": "warning",
            "selected_product": selected_product,
            "messages": [
                "Capacity scenario alignment diagnostic could not be evaluated: "
                f"{exc}"
            ],
        }

    env.explicit_pipeline_capacity_scenario_alignment_diagnostic = diagnostic
    return diagnostic
