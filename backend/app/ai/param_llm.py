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

# ── Valid values — LLM must only return these for status ─────────────────────
VALID_ORDER_STATUSES = {"pending", "picking", "packed", "shipped", "cancelled"}
VALID_TASK_STATUSES  = {"pending", "active", "blocked", "completed"}
VALID_ASN_STATUSES   = {"expected", "in_transit", "receiving", "received", "overdue"}
VALID_SEVERITIES     = {"critical", "high", "warning", "medium", "info", "low"}

SYSTEM_PROMPT = """
You are a parameter extraction engine for a Warehouse Management System.

Given a user query and detected intents, extract specific filter parameters.

EXTRACTABLE PARAMETERS:
- zone       : single zone name for lookup (e.g. "Zone A", "Zone B")
- zones      : list of zone names for comparison (e.g. ["Zone A", "Zone B"])
- sku        : product SKU code mentioned
- severity   : alert severity — ONLY one of: critical, high, warning, medium, info, low
- status     : ONLY extract if an explicit status word is mentioned.
               Valid order statuses: pending, picking, packed, shipped, cancelled
               Valid task statuses:  pending, active, blocked, completed
               Do NOT extract adjectives like "outbound", "inbound", "all" as status.
- limit      : number of results (e.g. "top 10" → 10)
- hours_threshold: hours for stuck/overdue detection

ZONE NORMALIZATION RULES:
- Always return zones in "Zone X" format with capital Z and uppercase letter
- "zone a" → "Zone A", "A" → "Zone A"
- Keep non-letter zones as-is (e.g. "cold storage")

CRITICAL STATUS RULE:
- "outbound" is NOT a status — it describes the table/type of order, not a status value
- "inbound" is NOT a status
- "all" is NOT a status
- Only extract status if the query contains an explicit status word like "pending orders", "shipped orders", "picking"
- If the query says "show all orders" or "show outbound orders" with no status word → return {}

RULES:
- Only extract parameters explicitly mentioned
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

Query: "show all outbound orders"
Output: {}

Query: "show outbound orders"
Output: {}

Query: "show pending orders"
Output: {"status": "pending"}

Query: "show shipped orders"
Output: {"status": "shipped"}

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
        params = _validate_and_clean(params)

        # Zone normalization
        if "zone" in params:
            params["zone"] = _normalize_zone(str(params["zone"]))
        if "zones" in params and isinstance(params["zones"], list):
            params["zones"] = [_normalize_zone(str(z)) for z in params["zones"]]

        print("✅ Extracted params:", params)
        return params

    except Exception as e:
        print("⚠️ Param LLM error:", e)
        return {}


def _validate_and_clean(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-extraction guard — removes any params that don't match known valid values.
    Prevents LLM hallucinations like status="outbound" slipping through.
    """
    cleaned = dict(params)

    # Drop invalid status values
    if "status" in cleaned:
        s = str(cleaned["status"]).strip().lower()
        all_valid = VALID_ORDER_STATUSES | VALID_TASK_STATUSES | VALID_ASN_STATUSES
        if s not in all_valid:
            print(f"⚠️  Dropping invalid status={s!r} (not in valid list)")
            del cleaned["status"]

    # Drop invalid severity values
    if "severity" in cleaned:
        sv = str(cleaned["severity"]).strip().lower()
        if sv not in VALID_SEVERITIES:
            print(f"⚠️  Dropping invalid severity={sv!r}")
            del cleaned["severity"]

    return cleaned


def _normalize_zone(zone: str) -> str:
    z = zone.strip()
    match = re.match(r"(?i)^zone[\s\-_]+(.+)$", z)
    if match:
        suffix = match.group(1).strip()
        if len(suffix) == 1:
            suffix = suffix.upper()
        return f"Zone {suffix}"
    if len(z) == 1 and z.isalpha():
        return f"Zone {z.upper()}"
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