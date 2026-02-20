import requests
import json
import re
from typing import Type
from pydantic import BaseModel

from app.core.schemas import Intent
from app.ai.param_registry import PARAM_REGISTRY

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


def extract_params(query: str, intent: Intent) -> dict:
    schema: Type[BaseModel] | None = PARAM_REGISTRY.get(intent)

    if not schema:
        return {}

    schema_json = schema.model_json_schema()

    prompt = f"""
You extract structured parameters for a warehouse query.

Intent: {intent.value}

Allowed JSON schema:
{json.dumps(schema_json, indent=2)}

User query:
{query}

Rules:
- Return ONLY valid JSON
- Do not add explanations
- Use null if value not found
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        raw = response.json().get("response", "")

        parsed = _extract_json(raw)

        # Validate & coerce
        return schema(**parsed).model_dump()

    except Exception:
        # Safe fallback → default schema values
        return schema().model_dump()


def _extract_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group()) if match else {}