import json
import re
import requests
from typing import List

from app.core.schemas import Intent, IntentResult, IntentScore
from app.ai.thresholds import INTENT_CONFIDENCE_THRESHOLD

# -----------------------------------------------------
# Ollama configuration
# -----------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

# -----------------------------------------------------
# System prompt
# -----------------------------------------------------
SYSTEM_PROMPT = """
You are an intent classification engine for a Warehouse Management System.

Analyze the user query and identify ALL relevant intents.

INTENTS:
- warehouse_overview
- low_stock
- inventory_lookup
- zone_inventory_compare
- order_status
- orders_stuck
- active_tasks
- blocked_tasks
- inbound_activity
- overdue_asn
- warehouse_alerts
- kpi_summary
- unknown

Rules:
- Return ONLY valid intents from the list
- A query may map to multiple intents
- Confidence must be between 0 and 1
- If unsure, include "unknown"
- NO explanations, NO extra text

Return STRICT JSON only.

FORMAT:
{
  "intents": [
    { "intent": "<intent_name>", "confidence": 0.0 }
  ]
}
"""

# -----------------------------------------------------
# Public API
# -----------------------------------------------------
def classify_intent(query: str) -> IntentResult:
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\nUser Query: {query}",
        "stream": False,
        "options": {"temperature": 0}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()

        raw = response.json().get("response", "").strip()
        parsed = _extract_json(raw)

        intent_items = parsed.get("intents", [])
        scores: List[IntentScore] = []

        for item in intent_items:
            intent_name = item.get("intent", "unknown")
            confidence = float(item.get("confidence", 0.0))

            try:
                intent_enum = Intent(intent_name)
            except ValueError:
                intent_enum = Intent.UNKNOWN

            scores.append(
                IntentScore(
                    intent=intent_enum,
                    confidence=confidence
                )
            )

        # 🔒 Safety: fallback if model returns garbage
        if not scores:
            scores = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        # 🔑 Filter weak intents
        filtered = [
            s for s in scores
            if s.confidence >= INTENT_CONFIDENCE_THRESHOLD
        ]

        if not filtered:
            filtered = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        return IntentResult(intents=filtered)

    except Exception as e:
        print("⚠️ Intent LLM error:", e)
        return IntentResult(
            intents=[IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]
        )

# -----------------------------------------------------
# JSON extraction helper
# -----------------------------------------------------
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

# -----------------------------------------------------
# Local test (dev only)
# -----------------------------------------------------
if __name__ == "__main__":
    tests = [
        "Compare Zone A vs Zone B inventory",
        "Show blocked tasks and overdue shipments",
        "Give me KPI summary and warehouse overview",
        "What items need replenishment?",
        "Explain what WMS is"
    ]

    for q in tests:
        result = classify_intent(q)
        print("\nQuery:", q)
        for i in result.intents:
            print(f"  → {i.intent.value} ({i.confidence:.2f})")