import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def choose_widget_and_summary(query: str, data):
    prompt = f"""
Allowed widgets: TABLE, BAR_CHART

Data:
{data}

User query:
{query}

Return JSON only:
{{ "widget": "...", "summary": ["...", "..."] }}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()
