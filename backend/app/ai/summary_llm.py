"""
summary_llm.py
Receives the query, detected intents, and all tool outputs.
Decides which UI widgets to render and returns a short factual summary.

Widget selection strategy:
  - Trend queries: hard-coded LINE_CHART, bypasses LLM widget selection entirely
  - All other queries: LLM chooses from catalogue with strict per-intent rules
  - Post-LLM safety overrides fix the most common LLM mistakes
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore, SummaryResponse, WidgetConfig
from app.ai.widget_registry import WIDGET_REGISTRY, FALLBACK_MAP
from app.core.config import MODEL_NAME, OLLAMA_URL

# ── Trend keywords — must match orchestrator._TREND_KEYWORDS exactly ─────────
_TREND_KEYWORDS = {
    "trend", "over time", "history", "historical",
    "last 7", "last week", "last month", "past month",
    "daily", "per day", "over the past",
}

_NO_TRIM_KEYS = {"zones", "kpis"}


def _is_trend_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _TREND_KEYWORDS)


# ── Widget catalogue table (auto-built from registry) ─────────────────────────

def _build_catalogue_table() -> str:
    col1 = max(len(w["type"])     for w in WIDGET_REGISTRY) + 2
    col2 = max(len(w["use_for"])  for w in WIDGET_REGISTRY) + 2
    col3 = max(len(w["data_key"]) for w in WIDGET_REGISTRY) + 2
    header  = f"| {'widget type':<{col1}}| {'use for':<{col2}}| {'data_key':<{col3}}|"
    divider = f"|{'-'*(col1+1)}|{'-'*(col2+1)}|{'-'*(col3+1)}|"
    rows    = [f"| {w['type']:<{col1}}| {w['use_for']:<{col2}}| {w['data_key']:<{col3}}|" for w in WIDGET_REGISTRY]
    return "\n".join([header, divider] + rows)


# ── System prompt ─────────────────────────────────────────────────────────────

_WIDGET_RULES = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WIDGET SELECTION — ONE RULE PER INTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

intent: order_status
  → User says "show orders", "list orders", "outbound orders", "order status":
      widget: TABLE   data_key: "orders.orders"
  → User says "distribution", "breakdown", "by status", "chart of orders":
      widget: BAR_CHART   data_key: "orders.by_status"
  → NEVER add KPI_CARDS for an order query.

intent: orders_stuck
  → widget: TABLE   data_key: "stuck_orders.orders"

intent: warehouse_alerts
  → widget: ALERT_LIST   data_key: "alerts.alerts"

intent: active_tasks
  → widget: TABLE   data_key: "active_tasks.tasks"

intent: blocked_tasks
  → widget: TABLE   data_key: "blocked_tasks.tasks"

intent: low_stock
  → widget: TABLE   data_key: "low_stock.items"

intent: inventory_lookup
  → widget: TABLE   data_key: "inventory.items"

intent: zone_inventory_compare
  → widget: ZONE_COMPARE_CHART   data_key: "zone_comparison"
  → ONLY ONE widget. data_key is EXACTLY "zone_comparison" — never "zone_comparison.zones".

intent: kpi_summary
  → widget: KPI_CARDS   data_key: "kpis.kpis"
  → use this for KPI/warehouse metric/warehouse performance queries.
  → MUST use this for warehouse metric/warehouse performance queries.

intent: inbound_activity
  → widget: INBOUND_SUMMARY   data_key: "inbound.asns"
  → For non-trend inbound queries only. Trend is handled separately.

intent: overdue_asn
  → widget: TABLE   data_key: "overdue_asn.asns"

intent: warehouse_overview
  → widget: OVERVIEW_PANEL   data_key: "overview"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Return MAXIMUM ONE widget per data_key — never the same data_key twice.
2. Return ONLY the widget(s) that match the detected intents.
3. data_key must be EXACTLY as shown above — no additions, no alternatives.
4. "show distribution of orders" → BAR_CHART only, NOT KPI_CARDS.
5. "zone comparison" → EXACTLY ONE ZONE_COMPARE_CHART with data_key "zone_comparison".
6. Do NOT invent data_keys. Only use keys from the rules above.
"""


def _build_system_prompt() -> str:
    return f"""You are the UI composition engine for a Warehouse Management System dashboard.

You receive:
  1. The user's original query
  2. Detected intents (with confidence scores)
  3. Actual warehouse data from tool outputs

Your job:
  1. Write a SHORT factual summary (2-3 sentences) using ONLY real numbers from the data.
     CRITICAL counting rules:
     - Fields ending in "_COUNT" (e.g. "items_COUNT") are EXACT totals — use them directly.
     - "_SAMPLE" fields are partial previews — never count rows in them.
     - If the data contains "inventory_summary_hint", copy it VERBATIM as the inventory
       part of your summary — do not rephrase or invent different numbers.
     - If the data contains "alerts_summary_hint", copy it VERBATIM as the alerts
       part of your summary — do not rephrase or invent different numbers.
     - If you cannot determine accurate counts, say "Here is the requested warehouse data."
  2. Select the correct widget(s) for each detected intent using the rules below.

Available widget types:
{_build_catalogue_table()}

{_WIDGET_RULES}

Return STRICT JSON only — no prose, no markdown fences.

FORMAT:
{{
  "summary": "<2-3 sentence factual summary>",
  "widgets": [
    {{
      "type": "<WIDGET_TYPE>",
      "title": "<human readable title>",
      "data_key": "<exact data_key from rules>",
      "props": {{}}
    }}
  ]
}}

EXAMPLES:

Query: "show all orders"
→ {{
    "summary": "There are 10 orders across all statuses.",
    "widgets": [{{"type":"TABLE","title":"Outbound Orders","data_key":"orders.orders","props":{{}}}}]
  }}

Query: "show distribution of orders"
→ {{
    "summary": "Orders are distributed across 5 statuses.",
    "widgets": [{{"type":"BAR_CHART","title":"Order Distribution","data_key":"orders.by_status","props":{{}}}}]
  }}

Query: "compare zone A and zone D"
→ {{
    "summary": "Comparing inventory across Zone A and Zone D.",
    "widgets": [{{"type":"ZONE_COMPARE_CHART","title":"Zone Inventory Comparison","data_key":"zone_comparison","props":{{}}}}]
  }}

Query: "show active alerts and tasks"
→ {{
    "summary": "There are 5 active alerts and 12 active tasks.",
    "widgets": [
      {{"type":"ALERT_LIST","title":"Active Alerts","data_key":"alerts.alerts","props":{{}}}},
      {{"type":"TABLE","title":"Active Tasks","data_key":"active_tasks.tasks","props":{{}}}}
    ]
  }}
"""


_SYSTEM_PROMPT = _build_system_prompt()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_summary_and_widgets(
    query: str,
    intents: List[IntentScore],
    tool_outputs: Dict[str, Any],
) -> SummaryResponse:
    print("\n--------------------------------------------------")
    print("🎨 Summary LLM called")

    # ── HARD BYPASS: trend queries skip LLM widget selection entirely ─────────
    # The LLM always picks TABLE/KPI because it sees the raw arrays.
    # We build LINE_CHARTs directly from orchestrator-aggregated trend data.
    if _is_trend_query(query) and "trend" in tool_outputs and tool_outputs["trend"]:
        print("  📈 Trend query — bypassing LLM widget selection")
        widgets      = _build_trend_widgets(tool_outputs["trend"])
        summary_text = _fetch_summary_text_only(query, intents, tool_outputs)
        return SummaryResponse(summary=summary_text, widgets=widgets)

    # ── Normal path: call LLM ─────────────────────────────────────────────────
    data_snapshot = _build_data_snapshot(tool_outputs)
    intent_list   = ", ".join(f"{s.intent.value}({s.confidence:.2f})" for s in intents)

    user_msg = f"""User query: {query}
Detected intents: {intent_list}
Tool outputs:
{data_snapshot}"""

    payload = {
        "model":   MODEL_NAME,
        "prompt":  f"{_SYSTEM_PROMPT}\n\n{user_msg}",
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=45)
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()
        print("📝 Raw summary LLM output:", raw[:300])

        parsed    = _extract_json(raw)
        seen_keys: set = set()
        widgets: List[WidgetConfig] = []

        for w in parsed.get("widgets", []):
            dk = w.get("data_key", "")
            if dk in seen_keys:
                continue
            seen_keys.add(dk)
            widgets.append(WidgetConfig(
                type     = w.get("type", "TABLE"),
                title    = w.get("title", ""),
                data_key = dk,
                props    = w.get("props"),
            ))

        # ── Post-LLM safety overrides ─────────────────────────────────────────
        widgets = _apply_safety_overrides(query, intents, widgets)

        return SummaryResponse(
            summary = parsed.get("summary", "Here is your warehouse data."),
            widgets = widgets,
        )

    except Exception as e:
        print("⚠️ Summary LLM error:", e)
        return _fallback_response(tool_outputs)


# ── Safety overrides ──────────────────────────────────────────────────────────

def _apply_safety_overrides(
    query: str,
    intents: List[IntentScore],
    widgets: List[WidgetConfig],
) -> List[WidgetConfig]:
    """
    Post-LLM fixes for the most common LLM widget mistakes.
    Applied in order; each fix is independent.
    """
    q = query.lower()
    intent_values = {s.intent.value for s in intents}

    # ── Fix 1: order_status without chart keyword → must be TABLE ────────────
    CHART_KEYWORDS = {"distribution", "breakdown", "by status", "chart", "pie", "graph"}
    if "order_status" in intent_values and not any(kw in q for kw in CHART_KEYWORDS):
        fixed = []
        for w in widgets:
            if w.type == "BAR_CHART" and "orders" in w.data_key:
                fixed.append(WidgetConfig(type="TABLE", title="Outbound Orders",
                                          data_key="orders.orders", props=w.props))
            else:
                fixed.append(w)
        # ensure TABLE exists
        if not any(w.type == "TABLE" and "orders" in w.data_key for w in fixed):
            fixed.insert(0, WidgetConfig(type="TABLE", title="Outbound Orders",
                                         data_key="orders.orders", props=None))
        widgets = fixed

    # ── Fix 2: order distribution → must be BAR_CHART, remove KPI_CARDS ─────
    if "order_status" in intent_values and any(kw in q for kw in CHART_KEYWORDS):
        widgets = [w for w in widgets if w.type != "KPI_CARDS"]
        if not any(w.type == "BAR_CHART" for w in widgets):
            widgets.insert(0, WidgetConfig(type="BAR_CHART", title="Order Distribution",
                                           data_key="orders.by_status", props=None))

    # ── Fix 3: zone_compare → exactly ONE ZONE_COMPARE_CHART, correct key ────
    # IMPORTANT: only touch ZONE_COMPARE_CHART widgets — preserve all others
    # (e.g. the TABLE for inventory_lookup must survive this override).
    if "zone_inventory_compare" in intent_values:
        zone_widgets = [w for w in widgets if w.type == "ZONE_COMPARE_CHART"]
        other        = [w for w in widgets if w.type != "ZONE_COMPARE_CHART"]
        if zone_widgets:
            best        = zone_widgets[0]
            fixed_chart = WidgetConfig(
                type     = "ZONE_COMPARE_CHART",
                title    = best.title or "Zone Inventory Comparison",
                data_key = "zone_comparison",
                props    = best.props,
            )
        else:
            fixed_chart = WidgetConfig(
                type     = "ZONE_COMPARE_CHART",
                title    = "Zone Inventory Comparison",
                data_key = "zone_comparison",
                props    = None,
            )
        # Re-combine: non-zone widgets first, then the single fixed chart
        widgets = other + [fixed_chart]

        # Ensure inventory TABLE is present when inventory_lookup also fired
        if "inventory_lookup" in intent_values:
            has_inv_table = any(
                w.type == "TABLE" and "inventory" in w.data_key
                for w in widgets
            )
            if not has_inv_table:
                widgets.append(WidgetConfig(
                    type     = "TABLE",
                    title    = "Inventory Items",
                    data_key = "inventory.items",
                    props    = None,
                ))

    # ── Fix 4: kpi_summary fired alongside order_status → drop KPI_CARDS ─────
    if "order_status" in intent_values and "kpi_summary" in intent_values:
        widgets = [w for w in widgets if w.type != "KPI_CARDS"]

    # ── Fix 5: final dedup by data_key ───────────────────────────────────────
    seen: set = set()
    deduped   = []
    for w in widgets:
        if w.data_key not in seen:
            seen.add(w.data_key)
            deduped.append(w)
    widgets = deduped

    return widgets


# ── Trend helpers ─────────────────────────────────────────────────────────────

_TREND_LABEL_MAP = {
    "alerts":       "Alert",
    "inbound":      "Inbound ASN",
    "orders":       "Order",
    "active_tasks": "Active Task",
    "blocked_tasks":"Blocked Task",
}

def _build_trend_widgets(trend: Dict[str, Any]) -> List[WidgetConfig]:
    widgets = []
    for tkey, series in trend.items():
        if not series:
            continue
        label = _TREND_LABEL_MAP.get(tkey, tkey.replace("_", " ").title())
        widgets.append(WidgetConfig(
            type     = "LINE_CHART",
            title    = f"{label} Trend Over Time",
            data_key = f"trend.{tkey}",
            props    = None,
        ))
        print(f"  ✅ Built LINE_CHART for trend.{tkey} ({len(series)} points)")
    return widgets


def _fetch_summary_text_only(
    query: str,
    intents: List[IntentScore],
    tool_outputs: Dict[str, Any],
) -> str:
    """Calls LLM for summary text only — used when widget selection is bypassed."""
    snap        = _build_data_snapshot(tool_outputs)
    intent_list = ", ".join(f"{s.intent.value}({s.confidence:.2f})" for s in intents)
    prompt = (
        "You are a warehouse assistant. Write a SHORT factual summary (1–2 sentences) "
        "using ONLY real numbers from the data. Plain text only — no JSON.\n\n"
        f"Query: {query}\nIntents: {intent_list}\nData: {snap}"
    )
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "options": {"temperature": 0}}
    try:
        r    = requests.post(OLLAMA_URL, json=payload, timeout=30)
        text = r.json().get("response", "").strip()
        # Strip any accidental JSON wrapper
        text = re.sub(r'^\{.*?"summary"\s*:\s*"', "", text, flags=re.DOTALL)
        text = re.sub(r'"\s*,?\s*"widgets".*$', "", text, flags=re.DOTALL)
        return text.strip('" \n') or "Here is the trend data."
    except Exception:
        return "Here is the trend data."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_alerts_summary_hint(alerts_output: Dict[str, Any]) -> str:
    """
    Pre-compute a factual alerts summary sentence in Python.

    Examples:
      severity_filter="all",      breakdown={critical:2,warning:3}
        → "There are 5 active alerts: 2 critical, 3 warning."
      severity_filter="critical", count=2
        → "There are 2 critical alerts."
      count=0
        → "There are no active alerts."
    """
    count      = alerts_output.get("alerts_COUNT", alerts_output.get("count", 0))
    sev_filter = alerts_output.get("severity_filter", "all")
    breakdown  = alerts_output.get("severity_breakdown", {})

    if count == 0:
        return "There are no active alerts."

    alert_word = "alert" if count == 1 else "alerts"

    # Filtered by a specific severity
    if sev_filter and sev_filter != "all":
        return f"There are {count} {sev_filter} {alert_word}."

    # All alerts — include breakdown if available
    if breakdown:
        # Order by severity priority
        _ORDER = ["critical", "high", "warning", "medium", "info", "low"]
        parts  = [
            f"{breakdown[s]} {s}"
            for s in _ORDER
            if s in breakdown
        ]
        # Also include any unexpected severity values
        for k in breakdown:
            if k not in _ORDER:
                parts.append(f"{breakdown[k]} {k}")

        if parts:
            return f"There are {count} active {alert_word}: {', '.join(parts)}."

    return f"There are {count} active {alert_word}."


def _build_inventory_summary_hint(inv: Dict[str, Any]) -> str:
    """
    Pre-compute a factual inventory summary sentence in Python so the LLM
    never has to count or infer — it just uses this string verbatim.

    Examples:
      zone_filter="Zone D"          → "There are 4 inventory items in Zone D."
      zone_filter=["Zone D","Zone E"]→ "There are 6 inventory items across Zone D and Zone E."
      zone_filter="all"             → "There are 30 inventory items across all zones."
      active_filters category=Motors→ "There are 3 inventory items matching the applied filters."
    """
    count       = inv.get("items_COUNT", inv.get("count", 0))
    zone_filter = inv.get("zone_filter", "all")
    active_f    = inv.get("active_filters", {})

    # Non-zone filters (category, status, location, sku) → generic sentence
    non_zone_active = {
        k: v for k, v in (active_f.items() if isinstance(active_f, dict) else {}.items())
        if k not in ("zone", "zones", "zone_filter")
    }
    if non_zone_active:
        filter_desc = ", ".join(f"{k}={v!r}" for k, v in non_zone_active.items())
        return f"There are {count} inventory item(s) matching the applied filters ({filter_desc})."

    # Zone-based sentence
    item_word = "item" if count == 1 else "items"
    if isinstance(zone_filter, list) and len(zone_filter) > 1:
        zone_str = " and ".join(zone_filter)
        return f"There are {count} inventory {item_word} across {zone_str}."
    elif isinstance(zone_filter, list) and len(zone_filter) == 1:
        return f"There are {count} inventory {item_word} in {zone_filter[0]}."
    elif isinstance(zone_filter, str) and zone_filter.lower() not in ("all", "", "none"):
        return f"There are {count} inventory {item_word} in {zone_filter}."
    else:
        return f"There are {count} inventory {item_word} across all zones."


def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    """
    Build a compact snapshot of tool outputs for the summary LLM.

    For each list field we emit:
      - "<field>_COUNT": exact integer  ← LLM MUST use this for any counts/totals
      - "<field>_SAMPLE": first 2 rows  ← for context only, NOT for counting

    For the inventory tool output specifically, we also inject a pre-computed
    "inventory_summary_hint" sentence so the LLM never has to guess counts.
    """
    snapshot: Dict[str, Any] = {}
    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    trimmed[f"{k}_COUNT"] = len(v)          # exact count
                    if k not in _NO_TRIM_KEYS:
                        trimmed[f"{k}_SAMPLE"] = v[:2]      # partial preview
                    else:
                        trimmed[k] = v                      # full list (kpis, zones)
                else:
                    trimmed[k] = v

            # Pre-compute summaries so LLM never has to count/infer
            if key == "inventory":
                trimmed["inventory_summary_hint"] = _build_inventory_summary_hint(trimmed)
            elif key == "alerts":
                trimmed["alerts_summary_hint"] = _build_alerts_summary_hint(trimmed)

            snapshot[key] = trimmed
        else:
            snapshot[key] = value
    return json.dumps(snapshot, indent=2, default=str)


def _fallback_response(tool_outputs: Dict[str, Any]) -> SummaryResponse:
    widgets = []
    for key in tool_outputs:
        wtype, dk = FALLBACK_MAP.get(key, ("TABLE", key))
        widgets.append(WidgetConfig(type=wtype, title=key.replace("_", " ").title(),
                                    data_key=dk, props=None))
    return SummaryResponse(summary="Here is your warehouse data.", widgets=widgets)


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}