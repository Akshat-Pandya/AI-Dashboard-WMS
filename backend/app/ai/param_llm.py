"""
param_llm.py
Extracts structured query parameters from the user's natural language query.

Runs AFTER intent classification, BEFORE tool execution.
The extracted params are passed to every tool so they can filter their SQL.

Examples:
  "show inventory of zone A"
    → { "zone": "A", "zones": ["A"] }

  "compare inventory of zone A and zone B"
    → { "zones": ["A", "B"] }

  "show last 10 stuck orders"
    → { "limit": 10 }

  "show critical alerts only"
    → { "severity": "critical" }
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = """
You are a parameter extraction engine for a Warehouse Management System.

Given a user query and the detected intents, extract any specific filter parameters mentioned.

EXTRACTABLE PARAMETERS:
- zone       : single zone name (e.g. "A", "B", "Zone A", "cold storage")
- zones      : list of zone names when comparing multiple (e.g. ["A", "B"])
- sku        : product SKU code mentioned
- severity   : alert severity filter ("critical", "warning", "error", "info")
- status     : order/task/ASN status filter
- limit      : number of results requested (e.g. "show top 10" → 10)
- hours_threshold: number of hours for stuck/overdue detection

RULES:
- Only extract parameters explicitly mentioned in the query
- Normalize zone names: "Zone A" → "A", "zone b" → "B"
- If a parameter is not mentioned, do not include it
- Return empty dict {} if no parameters are found
- Return STRICT JSON only — no prose, no markdown fences

EXAMPLES:
Query: "show inventory of zone A"
Output: {"zone": "A", "zones": ["A"]}

Query: "compare inventory of zone A and zone B"
Output: {"zones": ["A", "B"]}

Query: "show top 5 critical alerts"
Output: {"limit": 5, "severity": "critical"}

Query: "show stuck orders older than 48 hours"
Output: {"hours_threshold": 48}

Query: "show all blocked tasks"
Output: {}

Query: "show warehouse overview"
Output: {}
"""


def extract_params(query: str, intents: List[IntentScore]) -> Dict[str, Any]:
    """
    Extracts structured parameters from the user query.
    Returns empty dict if nothing relevant is found or if LLM fails.
    """
    print("\n--------------------------------------------------")
    print("🔍 Param LLM called")

    intent_list = ", ".join(s.intent.value for s in intents)

    prompt = f"""{SYSTEM_PROMPT}

Query: "{query}"
Detected intents: {intent_list}

Output:"""

    payload = {
        "model":   MODEL_NAME,
        "prompt":  prompt,
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=20)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        print("📝 Raw param output:", raw)

        params = _extract_json(raw)

        # Normalize zone names (remove "zone " prefix, uppercase)
        if "zone" in params:
            params["zone"] = _normalize_zone(params["zone"])
        if "zones" in params:
            params["zones"] = [_normalize_zone(z) for z in params["zones"]]

        print("✅ Extracted params:", params)
        return params

    except Exception as e:
        print("⚠️ Param LLM error:", e)
        return {}


def _normalize_zone(zone: str) -> str:
    z = zone.strip()
    # If already has "Zone " prefix, normalize capitalization and return
    if re.match(r"(?i)^zone\s+\w+$", z):
        parts = z.split()
        return f"{parts[0].capitalize()} {parts[1].upper()}"
    # No prefix — add it
    return f"Zone {z.upper()}"

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