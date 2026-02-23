"""
orchestrator.py
The single entry-point that wires together:
  intent classification → tool execution → summary LLM → API response
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.intent_llm   import classify_intent
from app.ai.summary_llm  import generate_summary_and_widgets
from app.core.schemas    import Intent, QueryResponse
from app.tools.runner    import run_tools


def orchestrate(
    query: str,
    db: Session,
    params: Optional[Dict[str, Any]] = None,
) -> QueryResponse:
    print("\n══════════════════════════════════════════════════")
    print(f"🚀 Orchestrator started  |  query: {query!r}")

    # ── Step 1: Intent classification ────────────────────────────────────────
    intent_result = classify_intent(query)
    intents = intent_result.intents

    if all(i.intent == Intent.UNKNOWN for i in intents):
        print("ℹ️  No actionable intents detected")
        return QueryResponse(
            query=query,
            summary="I couldn't understand your query. Please try rephrasing.",
            widgets=[],
            data={},
        )

    # ── Step 2: Run tools ────────────────────────────────────────────────────
    tool_outputs = run_tools(intents=intents, db=db, params=params)
    print(f"✅ Tools executed, keys: {list(tool_outputs.keys())}")

    # ── Step 3: Summary LLM ──────────────────────────────────────────────────
    summary_response = generate_summary_and_widgets(
        query=query,
        intents=intents,
        tool_outputs=tool_outputs,
    )
    print(f"✅ Widgets: {[w.type for w in summary_response.widgets]}")

    # ── Step 4: Build final response ─────────────────────────────────────────
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
    )