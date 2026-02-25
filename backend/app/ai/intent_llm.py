"""
intent_llm.py - with improved system prompt, confidence normalization,
and split unknown intent (irrelevant_query / unsupported_warehouse_query)
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

- warehouse_overview          : general warehouse status, overall health, dashboard summary
- low_stock                   : items running low, below reorder point, need replenishment
- inventory_lookup            : view/show/list inventory items in a SINGLE zone or by SKU
                                USE THIS when user asks about inventory IN one specific zone
                                Examples: "show inventory of zone A", "what's in zone B",
                                          "list items in zone C", "show zone A inventory"
- zone_inventory_compare      : COMPARE inventory ACROSS MULTIPLE zones side by side
                                USE THIS only when user explicitly wants to COMPARE 2+ zones
                                Examples: "compare zone A and B", "zone A vs zone B",
                                          "compare all zones", "which zone has more stock"
                                DO NOT use this for single zone queries
- order_status                : status of outbound orders, order progress
- orders_stuck                : orders that are delayed, stuck, not moving
- active_tasks                : currently running warehouse tasks
- blocked_tasks               : tasks that are blocked or cannot proceed
- inbound_activity            : incoming shipments, ASN status, receiving activity
- overdue_asn                 : ASNs that are late or overdue
- warehouse_alerts            : active alerts, warnings, critical issues
- kpi_summary                 : KPIs, performance metrics, statistics

- irrelevant_query            : COMPLETELY off-topic — has nothing to do with warehouse.
                                Use for: weather, jokes, sports, general knowledge,
                                coding help, math, history, geography, personal questions.
                                Examples: "what is the capital of France",
                                          "tell me a joke", "who won the world cup",
                                          "write a python script"

- unsupported_warehouse_query : Warehouse-related question but NO specific tool exists.
                                Use for: trend analysis, historical comparisons,
                                custom aggregations, cross-table analytics,
                                questions about specific workers/carriers/docks
                                that need custom SQL.
                                Examples: "which carrier has the most shipments",
                                          "average pick time per zone",
                                          "how many tasks were completed last week"

DECISION RULES:
- If the query mentions ANY warehouse entity (order, sku, zone, task, alert, kpi,
  shipment, dock, carrier, stock, inventory, pick, pack, putaway) → it is NOT irrelevant_query
- irrelevant_query is ONLY for queries with zero warehouse relevance
- unsupported_warehouse_query is for warehouse queries that don't fit the named intents above
- unknown should NOT be returned — use irrelevant_query or unsupported_warehouse_query instead

INTENT EXAMPLES (memorize these):
- "show inventory of zone A"         → inventory_lookup
- "compare zone A and zone B"        → zone_inventory_compare
- "compare all zones"                → zone_inventory_compare
- "show critical alerts and tasks"   → warehouse_alerts, active_tasks
- "what is the capital of France"    → irrelevant_query
- "tell me a joke"                   → irrelevant_query
- "which carrier ships the most"     → unsupported_warehouse_query
- "average minutes per pick task"    → unsupported_warehouse_query
- "warehouse overview"               → warehouse_overview
- "anything urgent I should know"    → warehouse_alerts, warehouse_overview

RULES:
- Return ONLY valid intents from the list above
- A query may map to multiple intents (max 3)
- Confidence must be between 0 and 1 — use the full range, do NOT always return 1.0
  * High confidence (0.85-0.95): query clearly and explicitly matches the intent
  * Medium confidence (0.65-0.84): query implies or relates to the intent
  * Low confidence (0.50-0.64): intent is possible but uncertain
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
                # This works automatically for ALL intent enum values including:
                # Intent.IRRELEVANT_QUERY       → "irrelevant_query"
                # Intent.UNSUPPORTED_WAREHOUSE  → "unsupported_warehouse_query"
                # as long as they are defined in the Intent enum in schemas.py
                intent_enum = Intent(intent_name)
            except ValueError:
                # LLM returned a string not in the enum — treat as unknown
                print(f"  ⚠️ Unrecognised intent from LLM: '{intent_name}' → mapped to UNKNOWN")
                intent_enum = Intent.UNKNOWN

            scores.append(IntentScore(intent=intent_enum, confidence=confidence))

        if not scores:
            scores = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        # ── Post-processing: normalize confidence scores ──────────────────────
        # Must happen BEFORE threshold filter so decay doesn't drop valid intents
        scores   = _normalize_confidence(scores, query)
        filtered = [s for s in scores if s.confidence >= INTENT_CONFIDENCE_THRESHOLD]

        if not filtered:
            # Nothing passed the threshold — check if it looks warehouse-related
            top = scores[0] if scores else None
            if top and top.intent in (Intent.IRRELEVANT_QUERY,):
                filtered = [IntentScore(intent=Intent.IRRELEVANT_QUERY, confidence=0.5)]
            else:
                filtered = [IntentScore(intent=Intent.UNSUPPORTED_WAREHOUSE, confidence=0.5)]

        print("Detected intents:")
        for s in filtered:
            print(f"  → {s.intent.value} ({s.confidence:.2f})")

        return IntentResult(intents=filtered)

    except Exception as e:
        print("⚠️ Intent LLM error:", e)
        return IntentResult(
            intents=[IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]
        )


def _normalize_confidence(scores: List[IntentScore], query: str) -> List[IntentScore]:
    """
    Post-process LLM confidence scores to make them semantically meaningful.

    Problems this solves:
      1. LLM always returns 1.0 — useless for ranking/filtering
      2. Vague queries look equally confident as precise queries
      3. Secondary intents in multi-intent queries aren't penalized

    Rules applied (in order):
      - Sort descending so primary intent is always index 0
      - Vague/short queries: cap all confidence at 0.75
      - Secondary+ intents: apply position-based decay (0.85^i)
      - Hard cap at 0.95 — model is never 100% certain
      - irrelevant/unsupported intents: never exceed 0.90
    """
    VAGUE_PATTERNS = [
        "anything", "what's going on", "how is", "give me", "tell me",
        "status", "summary", "overview", "attention", "urgent", "okay",
        "everything", "something", "should i know", "right now", "today",
        "what should", "is everything", "how are we doing",
    ]

    q_lower  = query.lower()
    is_vague = (
        any(p in q_lower for p in VAGUE_PATTERNS)
        and len(query.split()) < 8
    )

    if not scores:
        return scores

    # Ensure primary intent is at index 0
    scores = sorted(scores, key=lambda s: s.confidence, reverse=True)

    normalized = []
    for i, score in enumerate(scores):
        conf = score.confidence

        # Rule 1: vague queries — cap everything
        if is_vague:
            conf = min(conf, 0.75)

        # Rule 2: secondary intents in multi-intent — decay by position
        # i=0 → no decay, i=1 → ×0.85, i=2 → ×0.72
        if i > 0:
            conf = conf * (0.85 ** i)

        # Rule 3: hard global cap
        conf = min(conf, 0.95)

        # Rule 4: special intents that are inherently uncertain
        if score.intent in (Intent.IRRELEVANT_QUERY, Intent.UNSUPPORTED_WAREHOUSE, Intent.UNKNOWN):
            conf = min(conf, 0.90)

        conf = round(conf, 2)
        normalized.append(IntentScore(intent=score.intent, confidence=conf))

    return normalized


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