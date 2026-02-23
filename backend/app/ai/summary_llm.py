"""
summary_llm.py
Receives the query, detected intents, and all tool outputs.
Decides which UI widgets to render and in what order,
then returns a short natural-language summary.

The LLM is NOT allowed to invent numbers — it must reference keys that
exist in tool_outputs.  The system prompt enforces this explicitly.
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore, SummaryResponse, WidgetConfig

# ── Ollama config (reuse same model) ────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL_NAME  = "qwen2.5:7b"

# ── Widget catalogue ─────────────────────────────────────────────────────────
# The LLM is shown only valid widget types so it cannot hallucinate unknown ones.
WIDGET_CATALOGUE = """
Available widget types and when to use them:

| type              | use for                                              | expected data shape              |
|-------------------|------------------------------------------------------|----------------------------------|
| ALERT_LIST        | warehouse alerts / critical issues                   | { alerts: AlertRow[] }           |
| TABLE             | generic tabular data (orders, tasks, ASNs, items)   | { columns: str[], rows: any[][] }|
| BAR_CHART         | comparing values across categories / zones          | { labels: str[], datasets: [...]}|
| LINE_CHART        | trends over time                                     | { labels: str[], datasets: [...]}|
| KPI_CARDS         | key performance indicators                           | { kpis: KPICard[] }              |
| ZONE_COMPARE_CHART| side-by-side zone inventory comparison              | same as BAR_CHART                |
| INBOUND_SUMMARY   | inbound / ASN activity summary                      | { summary: {...}, items: [...] } |
| OVERVIEW_PANEL    | high-level warehouse overview                       | { metrics: {...} }               |
"""

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are the UI composition engine for a Warehouse Management System dashboard.

You receive:
1. The user's original query
2. The detected intents (with confidence scores)
3. The actual data fetched from the warehouse database (tool_outputs)

Your job:
1. Write a SHORT, factual summary (2-3 sentences max) based ONLY on the data provided.
   - Reference real numbers from tool_outputs.
   - Do NOT invent or guess any numbers.
2. Choose which widgets to render and in what order (most important first).
   - Pick widget types ONLY from the catalogue below.
   - data_key must be a valid dot-path into tool_outputs (e.g. "alerts.alerts", "low_stock.items").
   - You may add a "props" object with optional hints like {{ "highlight": "severity" }}.

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
    """
    Calls the local LLM to decide UI composition.
    Falls back to a sensible default if the LLM fails.
    """
    print("\n--------------------------------------------------")
    print("🎨 Summary LLM called")

    # Build a compact, readable snapshot of what data we have
    data_snapshot = _build_data_snapshot(tool_outputs)

    intent_list = ", ".join(
        f"{s.intent.value}({s.confidence:.2f})" for s in intents
    )

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

        parsed = _extract_json(raw)
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


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    """
    Produce a compact JSON-like snapshot.
    For lists we show the first 2 items + total count to keep the prompt small.
    """
    snapshot: Dict[str, Any] = {}
    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    trimmed[k] = v[:2]   # first 2 rows only
                    trimmed[f"{k}__total"] = len(v)
                else:
                    trimmed[k] = v
            snapshot[key] = trimmed
        else:
            snapshot[key] = value
    return json.dumps(snapshot, indent=2, default=str)


def _fallback_response(tool_outputs: Dict[str, Any]) -> SummaryResponse:
    """
    If the LLM fails, auto-generate one TABLE widget per data key.
    This guarantees the frontend always gets something to render.
    """
    widgets = []
    for key in tool_outputs:
        widgets.append(
            WidgetConfig(
                type="TABLE",
                title=key.replace("_", " ").title(),
                data_key=key,
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
