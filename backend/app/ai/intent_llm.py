import requests
from app.core.schemas import IntentResult, Intent

OLLAMA_URL = "http://localhost:11434/api/generate"

def extract_intent(query: str) -> IntentResult:
    prompt = f"""
You are an intent classifier.
Allowed intents:
LOW_STOCK, INVENTORY, ORDERS, TASKS, OVERVIEW, UNKNOWN

Return JSON only.
{{ "intent": "...", "filters": {{}} }}

Query: {query}
"""

    r = requests.post(OLLAMA_URL, json={
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    })

    try:
        return IntentResult.model_validate_json(r.json()["response"])
    except Exception:
        return IntentResult(intent=Intent.UNKNOWN, filters={})
