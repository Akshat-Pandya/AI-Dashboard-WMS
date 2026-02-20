import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

def choose_widget_and_summary(query: str, data, allowed_widgets):
    prompt = f"""
You are a UI planning assistant.

Allowed widgets: {allowed_widgets}

Data:
{json.dumps(data, indent=2)}

User query:
{query}

Return JSON ONLY:
{{ "widget": "<one_of_allowed>", "summary": ["...", "..."] }}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
    )

    return response.json()