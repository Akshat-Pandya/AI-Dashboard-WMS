# app/ai/summary_llm.py
import requests
import json
import re
from typing import List, Dict

from app.ai.json_utils import make_json_safe

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


def choose_widget_and_summary(
    query: str,
    data: Dict,
    allowed_widgets: List[str]
) -> Dict:
    """
    Decide which predefined widget to render and generate a short summary.
    Safely serializes DB output (Decimal, datetime, etc).
    """

    if not allowed_widgets:
        allowed_widgets = ["TABLE"]

    # 🔑 CRITICAL FIX: make data JSON-safe
    safe_data = make_json_safe(data)

    prompt = f"""
You are a UI planning assistant for a warehouse dashboard.

Rules:
- Choose EXACTLY ONE widget from the allowed list
- Do NOT invent new widgets
- Summary must be concise (2–3 bullet points max)
- Return JSON ONLY

Allowed widgets:
{allowed_widgets}

Data:
{json.dumps(safe_data, indent=2)}

User query:
{query}

Output format:
{{
  "widget": "<one_of_allowed_widgets>",
  "summary": ["...", "..."]
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    raw = response.json().get("response", "")

    parsed = _extract_json(raw)

    widget = parsed.get("widget")
    if widget not in allowed_widgets:
        widget = allowed_widgets[0]

    summary = parsed.get("summary", [])
    if not isinstance(summary, list) or not summary:
        summary = ["No additional insights available."]

    return {
        "widget": widget,
        "summary": summary
    }


def _extract_json(text: str) -> Dict:
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