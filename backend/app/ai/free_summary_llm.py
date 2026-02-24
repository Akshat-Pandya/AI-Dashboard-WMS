# app/ai/free_summary_llm.py

import json
import re
import requests
from typing import Any, Dict

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

def summarize_free_result(
    user_query: str,
    sql: str,
    query_result: Dict[str, Any],
    widget_type: str,
) -> str:
    """Generate a natural language summary of the free-query result."""
    if "error" in query_result:
        return f"I tried to answer your question but encountered an error: {query_result['error']}"

    rows = query_result.get("rows", [])
    columns = query_result.get("columns", [])
    preview = rows[:5]  # show first 5 rows to LLM

    prompt = f"""
You are summarizing warehouse data for an operations manager.

User asked: {user_query}

SQL executed: {sql}

Result preview ({len(rows)} total rows):
Columns: {columns}
First rows: {preview}

Write a 2-3 sentence factual summary of what the data shows.
Be specific — mention key numbers, trends, or outliers if visible.
No markdown. Plain text only.
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        return response.json().get("response", "").strip()
    except Exception:
        return f"Query returned {len(rows)} rows across {len(columns)} columns."