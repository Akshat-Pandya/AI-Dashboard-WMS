"""
param_llm.py
Extracts structured query parameters from the user's natural language query.
Runs AFTER intent classification, BEFORE tool execution.
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

Given a user query and detected intents, extract specific filter parameters.

EXTRACTABLE PARAMETERS:
- zone       : single zone name for lookup (e.g. "Zone A", "Zone B")
- zones      : list of zone names for comparison (e.g. ["Zone A", "Zone B"])
- sku        : product SKU code mentioned
- severity   : alert severity ("critical", "warning", "error", "info")
- status     : order/task/ASN status filter
- limit      : number of results (e.g. "top 10" → 10)
- hours_threshold: hours for stuck/overdue detection

ZONE NORMALIZATION RULES:
- Always return zones in "Zone X" format with capital Z and uppercase letter
- "zone a" → "Zone A"
- "zone b" → "Zone B"  
- "Zone A" → "Zone A"
- "A" → "Zone A"
- "cold storage" → "cold storage" (keep as-is if not a letter zone)

RULES:
- Only extract parameters explicitly mentioned in the query
- If a parameter is not mentioned, do not include it
- Return empty dict {} if no parameters found
- Return STRICT JSON only — no prose, no markdown fences

EXAMPLES:
Query: "show inventory of zone A"
Output: {"zone": "Zone A", "zones": ["Zone A"]}

Query: "compare inventory of zone A and zone B"
Output: {"zones": ["Zone A", "Zone B"]}

Query: "show top 5 critical alerts"
Output: {"limit": 5, "severity": "critical"}

Query: "show stuck orders older than 48 hours"
Output: {"hours_threshold": 48}

Query: "show all blocked tasks"
Output: {}

Query: "compare all zones"
Output: {}
"""


def extract_params(query: str, intents: List[IntentScore]) -> Dict[str, Any]:
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

        # Safety normalization in case LLM doesn't follow format perfectly
        if "zone" in params:
            params["zone"] = _normalize_zone(str(params["zone"]))
        if "zones" in params and isinstance(params["zones"], list):
            params["zones"] = [_normalize_zone(str(z)) for z in params["zones"]]

        print("✅ Extracted params:", params)
        return params

    except Exception as e:
        print("⚠️ Param LLM error:", e)
        return {}


def _normalize_zone(zone: str) -> str:
    """
    Normalizes zone names to match DB format: "Zone A", "Zone B", etc.

    "A"      → "Zone A"
    "zone a" → "Zone A"
    "Zone A" → "Zone A"
    "Zone b" → "Zone B"
    "cold storage" → "cold storage"  (non-letter zones kept as-is)
    """
    z = zone.strip()

    # Already in "Zone X" format — just normalize case
    match = re.match(r"(?i)^zone[\s\-_]+(.+)$", z)
    if match:
        suffix = match.group(1).strip()
        # Single letter → uppercase
        if len(suffix) == 1:
            suffix = suffix.upper()
        return f"Zone {suffix}"

    # Just a single letter like "A", "b"
    if len(z) == 1 and z.isalpha():
        return f"Zone {z.upper()}"

    # Multi-word non-standard zone — return as-is
    return z


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