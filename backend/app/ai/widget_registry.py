"""
widget_registry.py
Single source of truth for all widget types in the WMS dashboard.

TO ADD A NEW WIDGET:
  1. Add an entry to WIDGET_REGISTRY below
  2. Add the component to WIDGET_MAP in frontend/src/components/WidgetRenderer.tsx
  That's it — the prompt, fallback renderer, and catalogue update automatically.

DATA KEY RULES:
  - data_key must be the EXACT dot-path used by WidgetRenderer.resolvePath()
  - zone_comparison tool returns { zones: [...], summary: [...] }
    → correct data_key is "zone_comparison" (the whole object)
  - FALLBACK_MAP maps each tool_output key → (widget_type, correct data_key)
    Every entry is explicit — no key inherits another key's data_key.
"""
from typing import Any, Dict, List, Tuple

WIDGET_REGISTRY: List[Dict[str, Any]] = [
    {
        "type":         "ALERT_LIST",
        "use_for":      "active warehouse alerts, warnings, critical issues",
        "data_key":     "alerts.alerts",
        "fallback_for": ["alerts"],
    },
    {
        "type":         "TABLE",
        "use_for":      (
            "row-based lists: orders, tasks, ASNs, inventory items. "
            "Use for show/list/get requests. "
            "For orders: data_key is 'orders.orders'. "
            "For tasks: 'active_tasks.tasks' or 'blocked_tasks.tasks'. "
            "For inventory: 'low_stock.items' or 'inventory.items'. "
            "For inbound ASNs: 'inbound.asns'. "
            "For overdue ASNs: 'overdue_asn.asns'. "
            "For stuck orders: 'stuck_orders.orders'."
        ),
        "data_key":     "orders.orders",   # default — overridden per-key in FALLBACK_MAP
        "fallback_for": [
            "low_stock", "inventory", "stuck_orders",
            "active_tasks", "blocked_tasks", "overdue_asn", "orders",
        ],
    },
    {
        "type":         "BAR_CHART",
        "use_for":      (
            "numeric comparisons across categories. "
            "ONLY use when user explicitly says 'distribution', 'breakdown', "
            "'chart', 'by status', or 'comparison by category'. "
            "For order distribution: data_key is 'orders.by_status'. "
            "DO NOT use for listing rows — use TABLE instead."
        ),
        "data_key":     "orders.by_status",
        "fallback_for": [],
    },
    {
        "type":         "ZONE_COMPARE_CHART",
        "use_for":      (
            "side-by-side zone inventory comparison bar chart. "
            "Use when intent is zone_inventory_compare. "
            "data_key MUST be 'zone_comparison' — the full object. "
            "DO NOT use 'zone_comparison.zones' or 'zone_comparison.summary'."
        ),
        "data_key":     "zone_comparison",
        "fallback_for": ["zone_comparison"],
    },
    {
        "type":         "LINE_CHART",
        "use_for":      (
            "time-series trends. Use for any query containing 'trend', 'over time', "
            "'history', 'last N days/weeks/months', 'daily'. "
            "data_key is always 'trend.<source>' e.g. 'trend.alerts', 'trend.inbound', "
            "'trend.orders'. These keys are created by the orchestrator's trend aggregator."
        ),
        "data_key":     "trend.inbound",
        "fallback_for": [],
    },
    {
        "type":         "KPI_CARDS",
        "use_for":      (
            "warehouse KPIs and performance metrics. "
            "Use ONLY when user explicitly asks for KPIs, metrics, performance, "
            "throughput, fill rate, SLA, efficiency. "
            "DO NOT use for order queries — use TABLE or BAR_CHART for orders."
        ),
        "data_key":     "kpis.kpis",
        "fallback_for": ["kpis"],
    },
    {
        "type":         "INBOUND_SUMMARY",
        "use_for":      "inbound shipments table / ASN activity list (non-trend)",
        "data_key":     "inbound.asns",
        "fallback_for": ["inbound"],
    },
    {
        "type":         "OVERVIEW_PANEL",
        "use_for":      (
            "high-level warehouse overview with all-up metrics. "
            "ALWAYS use when intent is warehouse_overview. "
            "data_key MUST be 'overview' — a nested object, not a list. "
            "Do NOT skip this widget just because there is no array."
        ),
        "data_key":     "overview",
        "fallback_for": ["overview"],
    },
]

# ── Per-intent canonical data_key overrides ───────────────────────────────────
# These override the widget's default data_key for specific tool output keys.
# This is necessary because TABLE serves many intents, each with a different
# dot-path into tool_outputs (e.g. overdue_asn → "overdue_asn.asns",
# not the TABLE default of "orders.orders").
_DATA_KEY_OVERRIDES: Dict[str, str] = {
    "low_stock":    "low_stock.items",
    "inventory":    "inventory.items",
    "stuck_orders": "stuck_orders.orders",
    "active_tasks": "active_tasks.tasks",
    "blocked_tasks":"blocked_tasks.tasks",
    "overdue_asn":  "overdue_asn.asns",
    "orders":       "orders.orders",
    # Non-TABLE overrides (these already match their widget's data_key,
    # listed here for completeness / explicitness)
    "alerts":           "alerts.alerts",
    "zone_comparison":  "zone_comparison",
    "kpis":             "kpis.kpis",
    "inbound":          "inbound.asns",
    "overview":         "overview",
}

# ── Derived FALLBACK_MAP: tool_output key → (widget_type, canonical_data_key) ─
FALLBACK_MAP: Dict[str, Tuple[str, str]] = {}
for _w in WIDGET_REGISTRY:
    for _k in _w["fallback_for"]:
        # Use the per-intent override if available, else use widget's default data_key
        _canonical = _DATA_KEY_OVERRIDES.get(_k, _w["data_key"])
        FALLBACK_MAP[_k] = (_w["type"], _canonical)

# ── All valid canonical data_keys (used by orchestrator scrubber) ─────────────
# Includes both widget defaults AND per-intent overrides.
CANONICAL_DATA_KEYS: set = set(_DATA_KEY_OVERRIDES.values()) | {
    _w["data_key"] for _w in WIDGET_REGISTRY
}