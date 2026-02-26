"""
summary_llm.py
Receives the query, detected intents, and all tool outputs.
Decides which UI widgets to render and in what order,
then returns a short natural-language summary.
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore, SummaryResponse, WidgetConfig
from app.ai.widget_registry import WIDGET_REGISTRY, FALLBACK_MAP

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


# ── Prompt generation ─────────────────────────────────────────────────────────

def _build_catalogue_table() -> str:
    col1 = max(len(w["type"])     for w in WIDGET_REGISTRY) + 2
    col2 = max(len(w["use_for"])  for w in WIDGET_REGISTRY) + 2
    col3 = max(len(w["data_key"]) for w in WIDGET_REGISTRY) + 2

    header  = f"| {'widget type':<{col1}}| {'use for':<{col2}}| {'example data_key':<{col3}}|"
    divider = f"|{'-'*(col1+1)}|{'-'*(col2+1)}|{'-'*(col3+1)}|"
    rows = [
        f"| {w['type']:<{col1}}| {w['use_for']:<{col2}}| {w['data_key']:<{col3}}|"
        for w in WIDGET_REGISTRY
    ]
    return "\n".join([header, divider] + rows)


_DATA_KEY_RULES = """
WIDGET SELECTION RULES (follow strictly):

ORDER QUERIES ("show orders", "show outbound orders", "list orders", "get orders"):
  - ALWAYS use TABLE with data_key "orders.orders"
  - Only use BAR_CHART if user explicitly asks for "distribution", "breakdown", "chart", or "by status"

STUCK ORDERS:
  - TABLE with data_key "stuck_orders.orders"

ALERTS:
  - ALERT_LIST with data_key "alerts.alerts"

TASKS (active or blocked):
  - TABLE with data_key "active_tasks.tasks" or "blocked_tasks.tasks"

LOW STOCK / INVENTORY:
  - TABLE with data_key "low_stock.items" or "inventory.items"

ZONE COMPARISON:
  - ZONE_COMPARE_CHART with data_key "zone_comparison"

KPIs:
  - KPI_CARDS with data_key "kpis.kpis"

DATA KEY FORMAT:
  - data_key is a dot-path into tool_outputs e.g. "orders.orders" → tool_outputs["orders"]["orders"]
  - Maximum 2 levels deep
  - NEVER invent a data_key not present in tool_outputs
"""


def _build_system_prompt() -> str:
    return f"""You are the UI composition engine for a Warehouse Management System dashboard.

You receive:
1. The user's original query
2. The detected intents (with confidence scores)
3. The actual data fetched from the warehouse database (tool_outputs)

Your job:
1. Write a SHORT factual summary (2-3 sentences) using ONLY real numbers from tool_outputs.
   Do NOT invent or guess any numbers.
2. Choose which widgets to render, most important first.
   Use ONLY widget types from the catalogue below.

Available widgets:
{_build_catalogue_table()}

{_DATA_KEY_RULES}

Return STRICT JSON only — no prose, no markdown fences.

CRITICAL RULES:
- Return MAXIMUM ONE widget per data_key — never repeat the same data_key twice
- For order_status intent with no chart/distribution request: return exactly ONE TABLE with data_key "orders.orders" and nothing else
- Do not return both a BAR_CHART and a TABLE for the same data

FORMAT (return exactly this structure):
{{
  "summary": "<2-3 sentence factual summary>",
  "widgets": [
    {{
      "type": "<WIDGET_TYPE>",
      "title": "<human readable title>",
      "data_key": "<dot.path.into.tool_outputs>",
      "props": {{}}
    }}
  ]
}}

EXAMPLE for "show all orders":
{{
  "summary": "There are 10 orders across all statuses.",
  "widgets": [
    {{
      "type": "TABLE",
      "title": "Outbound Orders",
      "data_key": "orders.orders",
      "props": {{}}
    }}
  ]
}}"""


_SYSTEM_PROMPT = _build_system_prompt()
_NO_TRIM_KEYS  = {"zones", "kpis"}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_summary_and_widgets(
    query: str,
    intents: List[IntentScore],
    tool_outputs: Dict[str, Any],
) -> SummaryResponse:
    print("\n--------------------------------------------------")
    print("🎨 Summary LLM called")

    data_snapshot = _build_data_snapshot(tool_outputs)
    intent_list   = ", ".join(f"{s.intent.value}({s.confidence:.2f})" for s in intents)

    user_context = f"""User query: {query}

Detected intents: {intent_list}

Tool outputs (actual warehouse data):
{data_snapshot}"""

    payload = {
        "model":   MODEL_NAME,
        "prompt":  f"{_SYSTEM_PROMPT}\n\n{user_context}",
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        print("📝 Raw summary LLM output:", raw[:300])

        parsed  = _extract_json(raw)
        seen_keys: set = set()
        widgets = []
        for w in parsed.get("widgets", []):
            data_key = w.get("data_key", "")
            if data_key in seen_keys:
                continue
            seen_keys.add(data_key)
            widgets.append(WidgetConfig(
                type=w.get("type", "TABLE"),
                title=w.get("title", ""),
                data_key=data_key,
                props=w.get("props"),
            ))

        # ── Safety override: if intent is order_status and LLM chose BAR_CHART
        #    without user asking for a chart/distribution → force TABLE instead
        order_keywords = {"distribution", "breakdown", "chart", "by status", "summary"}
        is_order_intent = any(s.intent.value == "order_status" for s in intents)
        user_wants_chart = any(kw in query.lower() for kw in order_keywords)

        if is_order_intent and not user_wants_chart:
            widgets = [
                WidgetConfig(
                    type="TABLE",
                    title=w.title if w.type != "BAR_CHART" else "Orders",
                    data_key="orders.orders" if w.type == "BAR_CHART" else w.data_key,
                    props=w.props,
                ) if w.type == "BAR_CHART" else w
                for w in widgets
            ]
            # Ensure at least one TABLE widget exists — but don't duplicate
            has_order_table = any(w.type == "TABLE" and "orders" in w.data_key for w in widgets)
            if not has_order_table:
                widgets.insert(0, WidgetConfig(type="TABLE", title="Orders", data_key="orders.orders", props=None))

        return SummaryResponse(
            summary=parsed.get("summary", "Here is your warehouse data."),
            widgets=widgets,
        )

    except Exception as e:
        print("⚠️ Summary LLM error:", e)
        return _fallback_response(tool_outputs)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    snapshot: Dict[str, Any] = {}
    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    if k in _NO_TRIM_KEYS:
                        trimmed[k] = v
                    else:
                        trimmed[k] = v[:2]
                        trimmed[f"{k}__total"] = len(v)
                else:
                    trimmed[k] = v
            snapshot[key] = trimmed
        else:
            snapshot[key] = value
    return json.dumps(snapshot, indent=2, default=str)


def _fallback_response(tool_outputs: Dict[str, Any]) -> SummaryResponse:
    widgets = []
    for key in tool_outputs:
        widget_type, data_key = FALLBACK_MAP.get(key, ("TABLE", key))
        widgets.append(WidgetConfig(
            type=widget_type,
            title=key.replace("_", " ").title(),
            data_key=data_key,
            props=None,
        ))
    return SummaryResponse(
        summary="Here is your warehouse data.",
        widgets=widgets,
    )


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}