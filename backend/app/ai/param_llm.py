import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = """
Extract structured parameters from the warehouse query.

Return JSON ONLY.

Fields:
- zones: list of strings or null
- category: string or null
- date: string (YYYY-MM-DD) or null
- status: string or null
"""

def extract_params(query: str) -> dict:
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\nQuery: {query}",
        "stream": False,
        "options": {"temperature": 0}
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    raw = response.json().get("response", "")

    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(match.group()) if match else {}