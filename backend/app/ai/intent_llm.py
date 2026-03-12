"""
intent_llm.py
Classifies user query into one or more warehouse intents.
Uses strict single-responsibility rules to prevent co-firing.
"""
import json
import re
import requests
from typing import List

from app.core.schemas import Intent, IntentResult, IntentScore
from app.ai.thresholds import INTENT_CONFIDENCE_THRESHOLD

from app.core.config import MODEL_NAME, OLLAMA_URL, LLM_TIMEOUT

SYSTEM_PROMPT = """
You are an intent classifier for a Warehouse Management System (WMS).
Map the user query to the MINIMUM number of intents needed. Default to ONE intent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTENT DEFINITIONS  (read each carefully)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

warehouse_overview
  → User wants a high-level all-up dashboard of the whole warehouse.
  → Triggers: "warehouse overview", "how is the warehouse", "overall status",
              "warehouse health", "morning briefing", "anything urgent"

low_stock
  → Items below reorder point / running out / need replenishment.
  → Triggers: "low stock", "out of stock", "reorder", "replenish", "stockout",
              "items below threshold", "which items are running low"

inventory_lookup
  → View inventory in ONE specific zone or search by SKU.
  → Triggers: "show inventory zone A", "what's in zone B", "find SKU X",
              "list items in zone C"
  → DO NOT use for multi-zone comparison.

zone_inventory_compare
  → Compare inventory metrics ACROSS 2+ zones side by side.
  → Triggers: "compare zone A and B", "zone A vs zone D", "compare all zones",
              "which zone has more stock", "zone comparison"
  → DO NOT use for single-zone queries.

order_status
  → Status, progress, or distribution of outbound orders.
  → Triggers: "show orders", "order status", "outbound orders", "list orders",
              "show distribution of orders", "order breakdown", "orders by status",
              "how many orders are pending/shipped/cancelled"
  → This is the ONLY intent for anything order-related.
  → DO NOT combine with kpi_summary for order queries.

orders_stuck
  → Orders that are delayed, stuck, or not progressing.
  → Triggers: "stuck orders", "delayed orders", "orders on hold",
              "orders not moving", "order backlog"

active_tasks
  → Warehouse tasks currently in progress (pick, pack, putaway).
  → Triggers: "active tasks", "ongoing tasks", "current tasks",
              "what tasks are running", "picking tasks"

blocked_tasks
  → Tasks that cannot proceed due to a blocker.
  → Triggers: "blocked tasks", "tasks waiting", "tasks stuck",
              "cannot proceed tasks"

inbound_activity
  → Incoming shipments, ASN status, receiving dock activity.
  → Triggers: "inbound shipments", "ASN status", "receiving", "what's arriving",
              "inbound activity", "supplier shipments", "dock schedule",
              "inbound trend", "trend of inbound", "inbound over time",
              "display inbound shipments trend"
  → USE THIS for ALL inbound/ASN trend queries — do not return unsupported.

overdue_asn
  → ASNs that are late or past their expected delivery date.
  → Triggers: "overdue ASN", "late shipment", "past due", "delayed ASN"

warehouse_alerts
  → Active alerts, warnings, critical system issues.
  → Triggers: "alerts", "warnings", "critical issues", "what's wrong",
              "active alerts", "alert trend", "trend of alerts",
              "what should I focus on", "what needs attention",
              "anything urgent", "what's critical"

kpi_summary
  → Warehouse KPIs and performance metrics ONLY.
  → Triggers: "KPI", "performance metrics", "throughput", "fill rate",
              "SLA compliance", "pick rate", "efficiency metrics",
              "show me the KPIs", "how are we performing"
  → DO NOT use for order queries. "distribution of orders" is NOT a KPI query.
  → DO NOT use alongside order_status unless user explicitly asks for both
    orders AND KPIs in the same query.

irrelevant_query
  → Query has ZERO warehouse relevance.
  → Triggers: weather, sports, jokes, general knowledge, coding help,
              geography, personal questions, math.

unsupported_warehouse_query
  → Warehouse-related but no specific tool covers it.
  → Triggers: custom analytics, carrier performance, worker productivity,
              queries needing ad-hoc SQL not covered by any intent above.
  → DO NOT use for inbound trend, alert trend, or order trend — those map
    to inbound_activity, warehouse_alerts, order_status respectively.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT SINGLE-INTENT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These queries map to EXACTLY ONE intent — do not add extras:

  "show distribution of orders"          → order_status          (NOT kpi_summary)
  "orders by status"                     → order_status          (NOT kpi_summary)
  "how many orders are pending"          → order_status          (NOT kpi_summary)
  "show all outbound orders"             → order_status
  "show inbound shipments"               → inbound_activity
  "display inbound shipments trend"      → inbound_activity
  "trend of inbound ASNs"                → inbound_activity
  "inbound ASN trend past month"         → inbound_activity
  "trend of warehouse alerts"            → warehouse_alerts
  "compare zone A and zone D"            → zone_inventory_compare
  "zone A vs zone B"                     → zone_inventory_compare
  "show KPIs"                            → kpi_summary
  "warehouse overview"                   → warehouse_overview
  "low stock items"                      → low_stock

These queries map to EXACTLY TWO intents:

  "show critical alerts and active tasks"  → warehouse_alerts, active_tasks
  "anything urgent I should know"          → warehouse_alerts, warehouse_overview
  "what should I focus on today"           → warehouse_alerts, warehouse_overview
  "what needs my attention"                → warehouse_alerts, warehouse_overview
  "morning briefing"                       → warehouse_alerts, warehouse_overview
  "what's critical right now"              → warehouse_alerts, warehouse_overview
  "overview and KPIs"                      → warehouse_overview, kpi_summary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIDENCE SCORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  0.90–0.95 : Query explicitly and clearly matches this intent
  0.70–0.89 : Query strongly implies this intent
  0.60–0.69 : Intent is plausible but not certain
  < 0.60    : Do not include — omit the intent entirely

DO NOT return 1.0 — the model is never perfectly certain.
Return max 3 intents. Default to 1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return STRICT JSON only. No prose. No markdown.

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
        "prompt":  f"{SYSTEM_PROMPT}\n\nUser Query: \"{query}\"",
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=LLM_TIMEOUT)
        response.raise_for_status()

        raw    = response.json().get("response", "").strip()
        parsed = _extract_json(raw)

        scores: List[IntentScore] = []
        for item in parsed.get("intents", []):
            intent_name = item.get("intent", "unknown")
            confidence  = float(item.get("confidence", 0.0))
            try:
                intent_enum = Intent(intent_name)
            except ValueError:
                print(f"  ⚠️ Unknown intent string '{intent_name}' → UNKNOWN")
                intent_enum = Intent.UNKNOWN
            scores.append(IntentScore(intent=intent_enum, confidence=confidence))

        if not scores:
            scores = [IntentScore(intent=Intent.UNKNOWN, confidence=0.0)]

        # Normalize and sort
        scores   = _normalize_confidence(scores, query)
        filtered = [s for s in scores if s.confidence >= INTENT_CONFIDENCE_THRESHOLD]

        if not filtered:
            top = scores[0] if scores else None
            if top and top.intent == Intent.IRRELEVANT_QUERY:
                filtered = [IntentScore(intent=Intent.IRRELEVANT_QUERY, confidence=0.5)]
            else:
                filtered = [IntentScore(intent=Intent.UNSUPPORTED_WAREHOUSE, confidence=0.5)]

        # Hard cap at MAX_INTENTS_PER_QUERY
        from app.ai.thresholds import MAX_INTENTS_PER_QUERY
        filtered = filtered[:MAX_INTENTS_PER_QUERY]

        print("Detected intents:")
        for s in filtered:
            print(f"  → {s.intent.value} ({s.confidence:.2f})")

        return IntentResult(intents=filtered)

    except Exception as e:
        print("⚠️ Intent LLM error:", e)
        return IntentResult(intents=[IntentScore(intent=Intent.UNKNOWN, confidence=0.0)])


def _normalize_confidence(scores: List[IntentScore], query: str) -> List[IntentScore]:
    """
    - Sort descending
    - Vague short queries: cap at 0.75
    - Secondary intents: decay by position
    - Hard cap 0.95
    """
    VAGUE_PATTERNS = [
        "anything", "what's going on", "how is", "give me", "tell me",
        "overview", "attention", "urgent", "everything", "right now",
        "today", "how are we doing", "status", "summary",
    ]
    q_lower  = query.lower()
    is_vague = any(p in q_lower for p in VAGUE_PATTERNS) and len(query.split()) < 8

    scores = sorted(scores, key=lambda s: s.confidence, reverse=True)

    normalized = []
    for i, score in enumerate(scores):
        conf = score.confidence
        if is_vague:
            conf = min(conf, 0.75)
        if i > 0:
            conf = conf * (0.85 ** i)
        conf = min(conf, 0.95)
        if score.intent in (Intent.IRRELEVANT_QUERY, Intent.UNSUPPORTED_WAREHOUSE, Intent.UNKNOWN):
            conf = min(conf, 0.90)
        normalized.append(IntentScore(intent=score.intent, confidence=round(conf, 2)))

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