"""
intent_llm.py - with improved system prompt for clearer intent distinction
"""
import json
import re
import requests
from typing import List

from app.core.schemas import Intent, IntentResult, IntentScore
from app.ai.thresholds import INTENT_CONFIDENCE_THRESHOLD

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = """
You are an intent classification engine for a Warehouse Management System.

Analyze the user query and identify ALL relevant intents.

INTENTS AND WHEN TO USE THEM:

- warehouse_overview   : general warehouse status, overall health, dashboard summary
- low_stock            : items running low, below reorder point, need replenishment
- inventory_lookup     : view/show/list inventory items in a SINGLE zone or by SKU
                         USE THIS when user asks about inventory IN one specific zone
                         Examples: "show inventory of zone A", "what's in zone B",
                                   "list items in zone C", "show zone A inventory"
- zone_inventory_compare: COMPARE inventory ACROSS MULTIPLE zones side by side
                         USE THIS only when user explicitly wants to COMPARE 2+ zones
                         Examples: "compare zone A and B", "zone A vs zone B",
                                   "compare all zones", "which zone has more stock"
                         DO NOT use this for single zone queries
- order_status         : status of outbound orders, order progress
- orders_stuck         : orders that are delayed, stuck, not moving
- active_tasks         : currently running warehouse tasks
- blocked_tasks        : tasks that are blocked or cannot proceed
- inbound_activity     : incoming shipments, ASN status, receiving activity
- overdue_asn          : ASNs that are late or overdue
- warehouse_alerts     : active alerts, warnings, critical issues
- kpi_summary          : KPIs, performance metrics, statistics
- unknown              : query not related to warehouse operations

CRITICAL RULES:
- "show inventory of zone A"     → inventory_lookup      (single zone, showing items)
- "compare zone A and zone B"    → zone_inventory_compare (explicit comparison)
- "compare all zones"            → zone_inventory_compare (explicit comparison)
- "inventory in zone A"          → inventory_lookup
- "zone A vs zone B"             → zone_inventory_compare
- Return ONLY valid intents from the list above
- A query may map to multiple intents
- Confidence must be between 0 and 1
- NO explanations, NO extra text

Return STRICT JSON only.

FORMAT:
{
  "intents": [
    { "intent": "<intent_name>", "confidence": 0.0 }
  ]
}
"""


def classify_intent(query: str) -> IntentResult:
    print("\n--------------------------------------------------")
    print("🧠 Intent LLM called")
    print("Query:", query)

    payload = {
        "model":   MODEL_NAME,
        "prompt":  f"{SYSTEM_PROMPT}\nUser Query: {query}",
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()

        raw    = response.json().get("response", "").strip()
        parsed = _extract_json(raw)

        intent_items = parsed.get("intents", [])
        scores: List[IntentScore] = []

        for item in intent_items:
            intent_name = item.get("intent", "unknown")
            confidence  = float(item.get("confidence", 0.0))
            try:
                intent_enum = Intent(intent_name)
            except ValueError:
                intent_enum = Intent.UNKNOWN
            scores.append(IntentScore(intent=intent_enum, confidence=confidence))

        if not scores:
            scores = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        filtered = [s for s in scores if s.confidence >= INTENT_CONFIDENCE_THRESHOLD]
        if not filtered:
            filtered = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        print("Detected intents:")
        for s in filtered:
            print(f"  → {s.intent.value} ({s.confidence:.2f})")

        return IntentResult(intents=filtered)

    except Exception as e:
        print("⚠️ Intent LLM error:", e)
        return IntentResult(
            intents=[IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]
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