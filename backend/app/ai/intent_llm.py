import requests
import json
import re

from app.core.schemas import IntentResult, IntentScore, Intent


# -----------------------------------------------------
# Ollama configuration
# -----------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


# -----------------------------------------------------
# System prompt for intent classification
# -----------------------------------------------------
SYSTEM_PROMPT = """
You are an intent classification engine for a Warehouse Management System.

Your task is to analyze the user query and identify ALL relevant intents from the list below.
A query may map to one or multiple intents.

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

GUIDELINES:
- Return every intent that is reasonably relevant
- If only one intent applies, return a list with one item
- If nothing matches confidently, return only ["unknown"]
- Confidence score must be between 0 and 1
- Do NOT include explanations or extra text

OUTPUT FORMAT (STRICT JSON):

{
  "intents": [
    { "intent": "<intent_name>", "confidence": 0.0 }
  ]
}
"""



# -----------------------------------------------------
# Main classification function
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

        raw_output = response.json().get("response", "").strip()

        parsed = _extract_json(raw_output)

        intents_list = parsed.get("intents", [])

        scores = []

        for item in intents_list:
            intent_name = item.get("intent", "unknown")
            confidence = float(item.get("confidence", 0.0))

            try:
                intent_enum = Intent(intent_name)
            except ValueError:
                intent_enum = Intent.UNKNOWN

            scores.append(IntentScore(intent=intent_enum, confidence=confidence))

        if not scores:
            scores.append(IntentScore(intent=Intent.UNKNOWN, confidence=0.0))

        return IntentResult(intents=scores)

    except Exception as e:
        print("⚠️ Intent classification error:", e)
        return IntentResult(intents=[IntentScore(intent=Intent.UNKNOWN, confidence=0.0)])


# -----------------------------------------------------
# Helper: Extract JSON safely
# -----------------------------------------------------

def _extract_json(text: str):
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
# Test block (run with python -m app.ai.intent_llm)
# -----------------------------------------------------
if __name__ == "__main__":

    test_queries = [
        "Show me the warehouse overview",
        "What items are running low on stock?",
        "Which orders are stuck in picking?",
        "Are there any blocked tasks?",
        "Show me today's inbound activity",
        "What problems should I know about?",
        "Compare Zone A vs Zone B inventory",
        "How many orders are pending?",
        "Show active tasks in the warehouse",
        "Which shipments are overdue?",
        "Give me KPI summary",
        "What alerts are critical right now?",
        "Show all outbound orders",
        "Which tasks are in progress?",
        "Any issues in Zone C?",
        "Show stock for servo motors",
        "How is warehouse utilization?",
        "List delayed orders",
        "Show receiving activity today",
        "Any safety alerts?",
        "Which items need replenishment?",
        "Show performance metrics",
        "What is happening in the warehouse?",
        "Which zones are over capacity?",
        "Show me operational summary"
    ]

    complex_queries = [
    "Show me warehouse overview and highlight any critical alerts",
    "What items are low on stock and which orders are affected?",
    "Give me KPI summary along with warehouse utilization",
    "Compare Zone A and Zone B and tell me if any tasks are blocked there",
    "Show today's inbound activity and overdue shipments",
    "Which orders are stuck in picking and who is assigned to them?",
    "Give me all active tasks and highlight blocked ones",
    "Show alerts and operational issues in the warehouse",
    "Compare inventory levels across zones and show low stock items",
    "Show inbound activity and receiving performance for today",
    "Give me overview, KPIs, and any risks I should know",
    "Show warehouse utilization and zones nearing capacity",
    "Which orders are pending and what is the pick progress?",
    "Show stock levels and replenishment needs for motors category",
    "Display alerts along with affected zones",
    "What is happening in the warehouse and are there any issues?",
    "Show tasks in progress and any bottlenecks",
    "Compare performance today vs yesterday and show KPIs",
    "Show operational summary with inbound and outbound activity",
    "Which zones have blocked tasks and low inventory?",
    "Give me all problems: alerts, overdue ASNs, and blocked tasks",
    "Show inbound shipments and any delays",
    "Which items are low and what replenishment tasks are pending?",
    "Show warehouse overview and current task workload",
    "Give me utilization and compare with target KPIs"
]


    print("\n🧠 Running Intent Classification Tests...\n")

    results = []
    questions = complex_queries
    for i, query in enumerate(questions, start=1):
        result = classify_intent(query)

        primary_intent = result.intents[0].intent.value
        confidence = result.intents[0].confidence

        results.append((query, primary_intent, confidence))

        print(f"{i:02d}. Query: {query}")

        for score in result.intents:
            print(f"    → Intent: {score.intent.value}")
            print(f"    → Confidence: {score.confidence:.2f}")

        print()


    # Summary
    print("\n📊 Test Summary")
    print("-" * 40)

    intent_counts = {}

    for _, intent, _ in results:
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    for intent, count in intent_counts.items():
        print(f"{intent}: {count}")
