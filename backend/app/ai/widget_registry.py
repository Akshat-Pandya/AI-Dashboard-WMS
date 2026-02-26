"""
widget_registry.py
Single source of truth for all widget types in the WMS dashboard.

TO ADD A NEW WIDGET:
  1. Add an entry to WIDGET_REGISTRY below
  2. Add the component to WIDGET_MAP in frontend/src/components/WidgetRenderer.tsx
  That's it — the prompt, fallback renderer, and catalogue update automatically.
"""
from typing import Any, Dict, List

WIDGET_REGISTRY: List[Dict[str, Any]] = [
    {
        "type":         "ALERT_LIST",
        "use_for":      "warehouse alerts, critical issues, warnings",
        "data_key":     "alerts.alerts",
        "fallback_for": ["alerts"],
    },
    {
        "type":         "TABLE",
        "use_for":      "showing lists of orders, tasks, ASNs, inventory items — any row-based data. Use TABLE when user asks to show/list/get orders or items.",
        "data_key":     "orders.orders",
        "fallback_for": ["low_stock", "inventory", "stuck_orders",
                         "active_tasks", "blocked_tasks", "overdue_asn", "orders"],
    },
    {
        "type":         "ZONE_COMPARE_CHART",
        "use_for":      "side-by-side zone inventory comparison",
        "data_key":     "zone_comparison",
        "fallback_for": ["zone_comparison"],
    },
    {
        "type":         "BAR_CHART",
        "use_for":      "comparing numeric values across categories. ONLY use when user explicitly asks for a chart, distribution, breakdown, or comparison by category. Do NOT use for listing orders or items — use TABLE instead.",
        "data_key":     "orders.by_status",
        "fallback_for": [],
    },
    {
        "type":         "LINE_CHART",
        "use_for":      "trends over time with time-series numeric data",
        "data_key":     "(time-series key)",
        "fallback_for": [],
    },
    {
        "type":         "KPI_CARDS",
        "use_for":      "key performance indicators, metrics summary",
        "data_key":     "kpis.kpis",
        "fallback_for": ["kpis"],
    },
    {
        "type":         "INBOUND_SUMMARY",
        "use_for":      "inbound shipments, ASN activity summary",
        "data_key":     "inbound.asns",
        "fallback_for": ["inbound"],
    },
    {
        "type":         "OVERVIEW_PANEL",
        "use_for":      (
            "high-level warehouse overview, all-up metrics. "
            "Data is a nested object (not a list) — data_key must be 'overview'. "
            "ALWAYS include this widget when the intent is warehouse_overview. "
            "Do NOT skip it because there is no array — the component handles nested objects."
        ),
        "data_key":     "overview",
        "fallback_for": ["overview"],
    },
]

# ── Derived lookup: tool_output key → (widget_type, data_key) ─────────────────
FALLBACK_MAP: Dict[str, tuple] = {}
for _w in WIDGET_REGISTRY:
    for _k in _w["fallback_for"]:
        FALLBACK_MAP[_k] = (_w["type"], _w["data_key"])