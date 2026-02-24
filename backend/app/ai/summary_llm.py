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
    """Generates the widget catalogue table from WIDGET_REGISTRY."""
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
IMPORTANT data_key rules:
- data_key is a dot-path into tool_outputs — maximum 2 levels deep
  e.g. "active_tasks.tasks" ✓    "active_tasks.tasks.estimated_minutes" ✗
- For zone comparison pass the whole object: "zone_comparison"
- For low stock:  "low_stock.items"
- For alerts:     "alerts.alerts"
- For tasks:      "blocked_tasks.tasks" or "active_tasks.tasks"
- For orders:     "orders.orders" or "stuck_orders.orders"
- For KPIs:       "kpis.kpis"
- NEVER go deeper than 2 levels — sorting/filtering is done in SQL, not data_key
- NEVER invent a data_key that does not exist in the tool_outputs snapshot
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
}}"""


# Cache at module load — WIDGET_REGISTRY doesn't change at runtime
_SYSTEM_PROMPT = _build_system_prompt()

# Keys whose lists must NOT be trimmed in the snapshot
_NO_TRIM_KEYS = {"zones", "kpis"}


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