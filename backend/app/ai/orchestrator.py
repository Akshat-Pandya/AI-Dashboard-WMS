"""
orchestrator.py
Full pipeline:
  1. Classify intents
  2. Extract params      ← NEW
  3. Run tools (with params)
  4. Summary LLM → widgets + summary
  5. Return QueryResponse
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.intent_llm   import classify_intent
from app.ai.param_llm    import extract_params
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
    intents       = intent_result.intents

    if all(i.intent == Intent.UNKNOWN for i in intents):
        print("ℹ️  No actionable intents detected")
        return QueryResponse(
            query=query,
            summary="I couldn't understand your query. Please try rephrasing.",
            widgets=[],
            data={},
            intents=[],
        )

    # ── Step 2: Parameter extraction ─────────────────────────────────────────
    # Merge LLM-extracted params with any caller-supplied params.
    # Caller params take precedence (allows programmatic override).
    extracted     = extract_params(query, intents)
    merged_params = {**extracted, **(params or {})}
    print(f"🔧 Merged params: {merged_params}")

    # ── Step 3: Run tools ────────────────────────────────────────────────────
    tool_outputs = run_tools(intents=intents, db=db, params=merged_params)
    print(f"✅ Tools executed, keys: {list(tool_outputs.keys())}")

    # ── Step 4: Summary LLM ──────────────────────────────────────────────────
    summary_response = generate_summary_and_widgets(
        query=query,
        intents=intents,
        tool_outputs=tool_outputs,
    )
    print(f"✅ Summary: {summary_response.summary[:80]}…")
    print(f"✅ Widgets: {[w.type for w in summary_response.widgets]}")

    # ── Step 5: Final response ────────────────────────────────────────────────
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
        intents=[{"intent": s.intent.value, "confidence": s.confidence} for s in intents],
    )