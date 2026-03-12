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
  → ONLY use this for explicit KPI/metric/performance queries.

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
  1. Write a SHORT factual summary (2–3 sentences) using ONLY real numbers from the data.
     Do NOT invent numbers.
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
    if "zone_inventory_compare" in intent_values:
        # Remove any duplicates or wrong data_keys
        zone_widgets = [w for w in widgets if w.type == "ZONE_COMPARE_CHART"]
        other        = [w for w in widgets if w.type != "ZONE_COMPARE_CHART"]
        if zone_widgets:
            # Keep only the first, force correct data_key
            best = zone_widgets[0]
            widgets = other + [WidgetConfig(type="ZONE_COMPARE_CHART",
                                            title=best.title or "Zone Inventory Comparison",
                                            data_key="zone_comparison",
                                            props=best.props)]
        else:
            widgets = other + [WidgetConfig(type="ZONE_COMPARE_CHART",
                                            title="Zone Inventory Comparison",
                                            data_key="zone_comparison", props=None)]

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

def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    snapshot: Dict[str, Any] = {}
    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    trimmed[k]                  = v[:2] if k not in _NO_TRIM_KEYS else v
                    trimmed[f"{k}__total"]       = len(v)
                else:
                    trimmed[k] = v
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