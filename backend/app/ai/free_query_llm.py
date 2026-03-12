# app/ai/free_query_llm.py

import json
import re
import requests
from typing import Any, Dict, Tuple
from app.ai.db_schema_context import DB_SCHEMA
from backend.app.core.config import MODEL_NAME, OLLAMA_URL, LLM_TIMEOUT

SYSTEM_PROMPT = f"""
You are a warehouse data analyst with access to a MySQL database.

{DB_SCHEMA}

Given a natural language question, produce:
1. A safe, read-only SELECT SQL query to answer it (no INSERT/UPDATE/DELETE/DROP)
2. The best widget type to display the result
3. A title for the widget

Widget types:
- TABLE        : generic rows of data
- BAR_CHART    : comparing values across categories
- LINE_CHART   : trends over time
- KPI_CARDS    : single metric highlights
- ALERT_LIST   : list of alerts/warnings

Return STRICT JSON only:
{{
  "sql": "<SELECT query>",
  "widget_type": "<WIDGET_TYPE>",
  "widget_title": "<human readable title>",
  "explanation": "<one sentence: what this query answers>"
}}

Rules:
- Use only the tables and columns defined above
- Always add LIMIT 100 unless the query is an aggregation
- Use aliases for readability
- Return only JSON, no markdown, no explanation outside the JSON
"""

def generate_free_query(user_query: str) -> Dict[str, Any]:
    """Ask the LLM to generate SQL + widget config for an unknown query."""
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\nUser question: {user_query}",
        "stream": False,
        "options": {"temperature": 0},
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=LLM_TIMEOUT)
    raw = response.json().get("response", "").strip()
    print("🔍 Free query LLM raw:", raw[:300])
    return _extract_json(raw)

def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}