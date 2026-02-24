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

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

WIDGET_CATALOGUE = """
Available widget types and when to use them:

| widget type        | use for                                             | correct data_key example         |
|--------------------|-----------------------------------------------------|----------------------------------|
| ALERT_LIST         | warehouse alerts / critical issues                  | alerts.alerts                    |
| TABLE              | generic tabular data (orders, tasks, ASNs, items)  | low_stock.items / orders.orders  |
| BAR_CHART          | comparing numeric values across categories          | zone_comparison                  |
| ZONE_COMPARE_CHART | side-by-side zone inventory comparison              | zone_comparison                  |
| LINE_CHART         | trends over time                                    | (time-series data key)           |
| KPI_CARDS          | key performance indicators                          | kpis.kpis                        |
| INBOUND_SUMMARY    | inbound / ASN activity summary                      | inbound.items                    |
| OVERVIEW_PANEL     | high-level warehouse overview                       | overview                         |

IMPORTANT data_key rules:
- data_key is a dot-path into tool_outputs, e.g. "alerts.alerts" means tool_outputs["alerts"]["alerts"]
- For zone comparison the tool returns {{ "zone_count": N, "zones": [...] }}
  so use data_key "zone_comparison" (the whole object) — the chart component handles it internally
- For low stock use "low_stock.items"
- For alerts use "alerts.alerts"
- For tasks use "blocked_tasks.tasks" or "active_tasks.tasks"
- For orders use "orders.orders" or "stuck_orders.orders"
- For KPIs use "kpis.kpis"
- NEVER invent a data_key that does not exist in the tool_outputs snapshot below
"""

SYSTEM_PROMPT = f"""
You are the UI composition engine for a Warehouse Management System dashboard.

You receive:
1. The user's original query
2. The detected intents (with confidence scores)
3. The actual data fetched from the warehouse database (tool_outputs)

Your job:
1. Write a SHORT, factual summary (2-3 sentences max) based ONLY on the numbers in tool_outputs.
   - Do NOT invent or guess any numbers.
2. Choose which widgets to render and in what order (most important first).
   - Use ONLY widget types from the catalogue.
   - data_key MUST be a valid dot-path into tool_outputs as shown in the catalogue rules.

{WIDGET_CATALOGUE}

Return STRICT JSON only — no prose, no markdown fences.

FORMAT:
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
"""


def generate_summary_and_widgets(
    query: str,
    intents: List[IntentScore],
    tool_outputs: Dict[str, Any],
) -> SummaryResponse:
    print("\n--------------------------------------------------")
    print("🎨 Summary LLM called")

    data_snapshot = _build_data_snapshot(tool_outputs)
    intent_list   = ", ".join(f"{s.intent.value}({s.confidence:.2f})" for s in intents)

    user_context = f"""
User query: {query}

Detected intents: {intent_list}

Tool outputs (actual warehouse data):
{data_snapshot}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{user_context}",
        "stream": False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        print("📝 Raw summary LLM output:", raw[:300])

        parsed  = _extract_json(raw)
        widgets = [
            WidgetConfig(
                type=w.get("type", "TABLE"),
                title=w.get("title", ""),
                data_key=w.get("data_key", ""),
                props=w.get("props"),
            )
            for w in parsed.get("widgets", [])
        ]

        return SummaryResponse(
            summary=parsed.get("summary", "Here is your warehouse data."),
            widgets=widgets,
        )

    except Exception as e:
        print("⚠️ Summary LLM error:", e)
        return _fallback_response(tool_outputs)


# ── Helpers ───────────────────────────────────────────────────────────────────

# Keys where we should NOT trim the list — the full array IS the data
_NO_TRIM_KEYS = {"zones", "kpis"}


def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    """
    Compact snapshot sent to the LLM.
    - Lists are trimmed to first 2 rows to keep prompt small
    - Exception: keys in _NO_TRIM_KEYS are kept in full (e.g. zones array)
    - Counts are always preserved so the LLM can cite real numbers
    """
    snapshot: Dict[str, Any] = {}
    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    if k in _NO_TRIM_KEYS:
                        trimmed[k] = v          # keep full list
                    else:
                        trimmed[k] = v[:2]      # trim to 2 rows
                        trimmed[f"{k}__total"] = len(v)
                else:
                    trimmed[k] = v
            snapshot[key] = trimmed
        else:
            snapshot[key] = value
    return json.dumps(snapshot, indent=2, default=str)


def _fallback_response(tool_outputs: Dict[str, Any]) -> SummaryResponse:
    """Auto-generate one widget per data key if the LLM fails."""
    FALLBACK_TYPES: Dict[str, str] = {
        "alerts":          "ALERT_LIST",
        "zone_comparison": "ZONE_COMPARE_CHART",
        "low_stock":       "TABLE",
        "kpis":            "KPI_CARDS",
        "inbound":         "INBOUND_SUMMARY",
        "overview":        "OVERVIEW_PANEL",
    }
    FALLBACK_KEYS: Dict[str, str] = {
        "alerts":          "alerts.alerts",
        "zone_comparison": "zone_comparison",
        "low_stock":       "low_stock.items",
        "kpis":            "kpis.kpis",
        "inbound":         "inbound.items",
        "overview":        "overview",
    }

    widgets = []
    for key in tool_outputs:
        widgets.append(
            WidgetConfig(
                type=FALLBACK_TYPES.get(key, "TABLE"),
                title=key.replace("_", " ").title(),
                data_key=FALLBACK_KEYS.get(key, key),
                props=None,
            )
        )
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