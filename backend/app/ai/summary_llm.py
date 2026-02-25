"""
summary_llm.py
Receives the query, detected intents, and all tool outputs.
Decides which UI widgets to render and in what order,
then returns a short natural-language summary.

Changes from original:
  - _HALLUCINATION_GUARD added to system prompt           ← FIX 6
  - _build_data_snapshot always emits __total for lists   ← FIX 6
  - snapshot rows increased from 2 → 3                   ← FIX 6
  - OVERVIEW_PANEL enforcement note in prompt             ← FIX 5 (Bug A)
  - _DATA_KEY_RULES clarified for overview nested object  ← FIX 5 (Bug A)
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore, SummaryResponse, WidgetConfig
from app.ai.widget_registry import WIDGET_REGISTRY, FALLBACK_MAP

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


# ── Prompt generation ─────────────────────────────────────────────────────────

def _build_catalogue_table() -> str:
    """Generates the widget catalogue table from WIDGET_REGISTRY."""
    col1 = max(len(w["type"])     for w in WIDGET_REGISTRY) + 2
    col2 = max(len(w["use_for"])  for w in WIDGET_REGISTRY) + 2
    col3 = max(len(w["data_key"]) for w in WIDGET_REGISTRY) + 2

    header  = f"| {'widget type':<{col1}}| {'use for':<{col2}}| {'example data_key':<{col3}}|"
    divider = f"|{'-'*(col1+1)}|{'-'*(col2+1)}|{'-'*(col3+1)}|"
    rows = [
        f"| {w['type']:<{col1}}| {w['use_for']:<{col2}}| {w['data_key']:<{col3}}|"
        for w in WIDGET_REGISTRY
    ]
    return "\n".join([header, divider] + rows)


_DATA_KEY_RULES = """
IMPORTANT data_key rules:
- data_key is a dot-path into tool_outputs — maximum 2 levels deep
  e.g. "active_tasks.tasks" ✓    "active_tasks.tasks.estimated_minutes" ✗
- For zone comparison pass the whole object: "zone_comparison"
- For low stock:  "low_stock.items"
- For alerts:     "alerts.alerts"
- For tasks:      "blocked_tasks.tasks" or "active_tasks.tasks"
- For orders:     "orders.orders" or "stuck_orders.orders"
- For KPIs:       "kpis.kpis"
- For inbound:    "inbound.asns"
- For warehouse_overview: data_key MUST be "overview"
  The overview value is a NESTED OBJECT (inventory, orders, tasks, alerts, kpis, zones).
  It is NOT a list. The OVERVIEW_PANEL component reads nested objects directly.
  ALWAYS include OVERVIEW_PANEL with data_key="overview" when overview data is present.
  NEVER skip this widget just because the data has no top-level array.
- NEVER go deeper than 2 levels — sorting/filtering is done in SQL, not data_key
- NEVER invent a data_key that does not exist in the tool_outputs snapshot
- If a key ends in __total it is a count integer, NOT a data_key — never use __total as data_key
"""

# ── Hallucination guard ───────────────────────────────────────────────────────
# This is injected into the system prompt to constrain summary generation
# to only facts present in the tool_outputs snapshot.

_HALLUCINATION_GUARD = """
STRICT SUMMARY RULES — violations produce incorrect dashboards:

1. ONLY use numbers, statuses, and labels that appear VERBATIM in the
   tool_outputs JSON shown above. Do not infer or calculate new values.

2. If a list is truncated (has a corresponding __total key), use the __total
   number as the count — NOT the number of rows shown in the preview.
   Example: if alerts__total=12 and you see 3 rows, say "12 alerts", not "3 alerts".

3. DO NOT say "critical" unless severity="critical" appears explicitly in the data.
   DO NOT say "error" unless severity="error" appears explicitly in the data.
   DO NOT infer severity, priority, or category from widget type or intent name.

4. DO NOT say "all zones" unless every zone is present in the data.

5. DO NOT say a number is a percentage unless the field name or unit says so.

6. If you are uncertain about a specific number, say "several" or omit the number.

7. Summary must be 2-3 sentences MAXIMUM. No bullet points. No markdown. Plain text only.

8. Widget list must include OVERVIEW_PANEL (data_key="overview") whenever
   overview data is present in tool_outputs — even if the data is a nested object.
"""


def _build_system_prompt() -> str:
    return f"""You are the UI composition engine for a Warehouse Management System dashboard.

You receive:
1. The user's original query
2. The detected intents (with confidence scores)
3. The actual data fetched from the warehouse database (tool_outputs)

Your job:
1. Write a SHORT factual summary (2-3 sentences) using ONLY real numbers from tool_outputs.
   Do NOT invent or guess any numbers.
2. Choose which widgets to render, most important first.
   Use ONLY widget types from the catalogue below.

Available widgets:
{_build_catalogue_table()}

{_DATA_KEY_RULES}

{_HALLUCINATION_GUARD}

Return STRICT JSON only — no prose, no markdown fences.

FORMAT:
{{
  "summary": "<2-3 sentence factual summary>",
  "widgets": [
    {{
      "type": "<WIDGET_TYPE>",
      "title": "<human readable title>",
      "data_key": "<dot.path.into.tool_outputs>",
      "props": {{}}
    }}
  ]
}}"""


# Cache at module load — WIDGET_REGISTRY doesn't change at runtime
_SYSTEM_PROMPT = _build_system_prompt()

# Keys whose lists must NOT be trimmed in the snapshot
# (they are small enough that full data is safe to pass)
_NO_TRIM_KEYS = {"zones", "kpis"}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_summary_and_widgets(
    query: str,
    intents: List[IntentScore],
    tool_outputs: Dict[str, Any],
) -> SummaryResponse:
    print("\n--------------------------------------------------")
    print("🎨 Summary LLM called")

    data_snapshot = _build_data_snapshot(tool_outputs)
    intent_list   = ", ".join(f"{s.intent.value}({s.confidence:.2f})" for s in intents)

    user_context = f"""User query: {query}
Detected intents: {intent_list}
Tool outputs (actual warehouse data):
{data_snapshot}"""

    payload = {
        "model":   MODEL_NAME,
        "prompt":  f"{_SYSTEM_PROMPT}\n\n{user_context}",
        "stream":  False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        response.raise_for_status()

        raw = response.json().get("response", "").strip()
        print("📝 Raw summary LLM output:", raw[:300])

        parsed  = _extract_json(raw)
        widgets = [
            WidgetConfig(
                type=w.get("type", "TABLE"),
                title=w.get("title", ""),
                data_key=w.get("data_key", ""),
                props=w.get("props"),
            )
            for w in parsed.get("widgets", [])
        ]

        # ── Validate data_keys against actual tool_outputs ────────────────────
        # Strip any widgets whose data_key doesn't resolve into tool_outputs.
        # This prevents broken widget configs reaching the frontend silently.
        valid_widgets = _validate_widget_data_keys(widgets, tool_outputs)
        invalid_count = len(widgets) - len(valid_widgets)
        if invalid_count:
            print(f"  ⚠️ Dropped {invalid_count} widget(s) with invalid data_key")

        return SummaryResponse(
            summary=parsed.get("summary", "Here is your warehouse data."),
            widgets=valid_widgets,
        )

    except Exception as e:
        print("⚠️ Summary LLM error:", e)
        return _fallback_response(tool_outputs)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_data_snapshot(tool_outputs: Dict[str, Any]) -> str:
    """
    Builds a JSON snapshot of tool_outputs to pass to the summary LLM.

    For lists:
      - Always emits a __total key with the true count
      - Shows first 3 rows as preview (up from 2 — enough for pattern detection)
      - Exceptions: _NO_TRIM_KEYS lists are passed in full (zones, kpis are small)

    This ensures the summary LLM sees accurate totals even when lists are
    trimmed, preventing hallucinated counts like "3 alerts" when there are 12.
    """
    snapshot: Dict[str, Any] = {}

    for key, value in tool_outputs.items():
        if isinstance(value, dict):
            trimmed: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, list):
                    if k in _NO_TRIM_KEYS:
                        # Small known-safe lists — pass in full
                        trimmed[k] = v
                    else:
                        # Always emit __total so LLM uses real count
                        trimmed[f"{k}__total"] = len(v)
                        trimmed[k] = v[:3]          # 3 rows instead of 2
                else:
                    trimmed[k] = v
            snapshot[key] = trimmed
        else:
            snapshot[key] = value

    return json.dumps(snapshot, indent=2, default=str)


def _validate_widget_data_keys(
    widgets: List[WidgetConfig],
    tool_outputs: Dict[str, Any],
) -> List[WidgetConfig]:
    """
    Remove widgets whose data_key doesn't resolve into tool_outputs.
    Prevents silent frontend failures where a widget renders nothing
    because the LLM invented or mis-typed a data_key.

    Validation logic (max 2 levels deep):
      "overview"            → tool_outputs["overview"] must exist
      "alerts.alerts"       → tool_outputs["alerts"]["alerts"] must exist
      "zone_comparison"     → tool_outputs["zone_comparison"] must exist

    Special cases:
      - "free_query" is always allowed (free-SQL path).
      - OVERVIEW_PANEL MUST have data_key exactly "overview" (no sub-paths).
        The LLM sometimes generates "overview.kpis" or "overview.inventory"
        which would pass generic dot-path validation but is wrong — the
        OVERVIEW_PANEL component expects the full nested overview object.
        We correct it in-place rather than dropping it, because the intent
        is right even if the data_key is slightly off.

    EXACT data_key requirements per widget type:
      OVERVIEW_PANEL    → must be exactly "overview"  (corrected if wrong)
      ZONE_COMPARE_CHART→ must be exactly "zone_comparison"
    """
    # Canonical data_keys for specific widget types.
    # If the LLM drifts from these, we correct rather than drop.
    _CANONICAL_DATA_KEYS: Dict[str, str] = {
        "OVERVIEW_PANEL":     "overview",
        "ZONE_COMPARE_CHART": "zone_comparison",
    }

    valid = []
    for w in widgets:
        if not w.data_key:
            print(f"  ⚠️ Widget '{w.type}' has empty data_key — skipping")
            continue

        # ── Special case: free-SQL results are always valid ───────────────────
        if w.data_key == "free_query":
            valid.append(w)
            continue

        # ── Special case: widgets with canonical fixed data_keys ──────────────
        # Correct the data_key if LLM drifted (e.g. "overview.kpis" → "overview")
        if w.type in _CANONICAL_DATA_KEYS:
            canonical = _CANONICAL_DATA_KEYS[w.type]
            if w.data_key != canonical:
                print(
                    f"  🔧 Correcting '{w.type}' data_key "
                    f"'{w.data_key}' → '{canonical}'"
                )
                w = WidgetConfig(
                    type=w.type,
                    title=w.title,
                    data_key=canonical,
                    props=w.props,
                )
            # Validate the canonical key exists in tool_outputs
            top = canonical.split(".")[0]
            if top not in tool_outputs:
                print(
                    f"  ⚠️ Widget '{w.type}' requires '{canonical}' "
                    f"but '{top}' not in tool_outputs — skipping"
                )
                continue
            valid.append(w)
            continue

        # ── General case: dot-path validation (max 2 levels) ─────────────────
        parts = w.data_key.split(".", 1)
        top   = parts[0]

        if top not in tool_outputs:
            print(
                f"  ⚠️ Widget '{w.type}' data_key '{w.data_key}' "
                f"— top-level key '{top}' not in tool_outputs"
            )
            continue

        if len(parts) == 2:
            nested = tool_outputs[top]
            sub    = parts[1]
            if not isinstance(nested, dict) or sub not in nested:
                print(
                    f"  ⚠️ Widget '{w.type}' data_key '{w.data_key}' "
                    f"— sub-key '{sub}' not found in tool_outputs['{top}']"
                )
                continue

        valid.append(w)

    return valid


def _fallback_response(tool_outputs: Dict[str, Any]) -> SummaryResponse:
    """
    Used when the summary LLM call fails entirely.
    Builds a minimal widget list from FALLBACK_MAP so the UI
    always has something to render.
    """
    widgets = []
    for key in tool_outputs:
        widget_type, data_key = FALLBACK_MAP.get(key, ("TABLE", key))
        widgets.append(WidgetConfig(
            type=widget_type,
            title=key.replace("_", " ").title(),
            data_key=data_key,
            props=None,
        ))
    return SummaryResponse(
        summary="Here is your warehouse data.",
        widgets=widgets,
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