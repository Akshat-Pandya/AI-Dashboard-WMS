"""
widget_registry.py
Single source of truth for all widget types in the WMS dashboard.

TO ADD A NEW WIDGET:
  1. Add an entry to WIDGET_REGISTRY below
  2. Add the component to WIDGET_MAP in frontend/src/components/WidgetRenderer.tsx
  That's it — the prompt, fallback renderer, and catalogue update automatically.

Fields:
  type        : widget type string — must match WIDGET_MAP key in WidgetRenderer.tsx
  use_for     : plain-English description shown to the LLM in the prompt
  data_key    : example/default dot-path into tool_outputs (e.g. "alerts.alerts")
  fallback_for: top-level tool_output keys this widget handles when LLM fails
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
        "use_for":      "generic tabular data — orders, tasks, ASNs, inventory items",
        "data_key":     "low_stock.items",
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
        "use_for":      "comparing numeric values across categories (non-zone)",
        "data_key":     "(relevant key)",
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
        # ── CRITICAL NOTE FOR LLM ────────────────────────────────────────────
        # overview data is a NESTED OBJECT (not a list).
        # Structure: { inventory: {...}, orders: {...}, tasks: {...},
        #              alerts: {...}, kpis: {...}, zones: {...} }
        # data_key must be exactly "overview" — do NOT go deeper.
        # ALWAYS include this widget when overview data is present.
        # NEVER skip it just because the data has no top-level array.
        # ─────────────────────────────────────────────────────────────────────
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
# Auto-built from fallback_for — do not edit manually.
FALLBACK_MAP: Dict[str, tuple] = {}
for _w in WIDGET_REGISTRY:
    for _k in _w["fallback_for"]:
        FALLBACK_MAP[_k] = (_w["type"], _w["data_key"])