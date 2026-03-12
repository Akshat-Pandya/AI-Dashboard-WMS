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
from app.core.config import MODEL_NAME, OLLAMA_URL, LLM_TIMEOUT


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
- "zone a" → "Zone A"
- "a" → "Zone A"
- Keep non-letter zones as-is (e.g. "cold storage")

CRITICAL STATUS RULE:
- "outbound" is NOT a status
- "inbound" is NOT a status
- "all" is NOT a status

RULES:
- Only extract parameters explicitly mentioned.
- Return empty dict {} if no parameters found.
- Output MUST be valid JSON.
- Do NOT explain anything.
- Output ONLY the JSON object.

EXAMPLES:
Query: "show inventory of zone A"
Output: {"zone": "Zone A", "zones": ["Zone A"]}

Query: "compare inventory of zone A and zone B"
Output: {"zones": ["Zone A", "Zone B"]}

Query: "compare zon a and zone b inventory"
Output: {"zones": ["Zone A", "Zone B"]}

Query: "show top 5 critical alerts"
Output: {"limit": 5, "severity": "critical"}

Query: "show pending orders"
Output: {"status": "pending"}
"""


def extract_params(query: str, intents: List[IntentScore]) -> Dict[str, Any]:
    print("\n--------------------------------------------------")
    print("🔍 Param LLM called")

    intent_list = ", ".join(s.intent.value for s in intents)

    prompt = f"""{SYSTEM_PROMPT}

Query: "{query}"
Detected intents: {intent_list}

Return ONLY JSON.
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 80,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=LLM_TIMEOUT)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        print("📝 Raw param output:", raw)

        params = _extract_json(raw)
        params = _validate_and_clean(params)

        # ── Zone normalization ─────────────────────────────
        if "zone" in params:
            params["zone"] = _normalize_zone(str(params["zone"]))

        if "zones" in params and isinstance(params["zones"], list):
            params["zones"] = [_normalize_zone(str(z)) for z in params["zones"]]

        # ── FIX: merge zone + zones correctly ─────────────
        if "zone" in params and "zones" in params:
            combined = set(params["zones"])
            combined.add(params["zone"])
            params["zones"] = list(combined)
            del params["zone"]

        # if only zone exists convert to zones list
        if "zone" in params and "zones" not in params:
            params["zones"] = [params["zone"]]
            del params["zone"]

        print("✅ Extracted params:", params)
        return params

    except Exception as e:
        print("⚠️ Param LLM error:", e)
        return {}


def _validate_and_clean(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(params)

    if "status" in cleaned:
        s = str(cleaned["status"]).strip().lower()
        all_valid = VALID_ORDER_STATUSES | VALID_TASK_STATUSES | VALID_ASN_STATUSES
        if s not in all_valid:
            print(f"⚠️ Dropping invalid status={s!r}")
            del cleaned["status"]

    if "severity" in cleaned:
        sv = str(cleaned["severity"]).strip().lower()
        if sv not in VALID_SEVERITIES:
            print(f"⚠️ Dropping invalid severity={sv!r}")
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