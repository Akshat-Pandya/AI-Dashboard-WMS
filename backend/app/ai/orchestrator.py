"""
orchestrator.py
Full pipeline:
  1. Classify intents
  2. Keyword fallback     (if unknown)
  3. Free SQL fallback    (if still unknown)
  4. Extract params
  5. Run tools (with params)
  6. Summary LLM → widgets + summary
  7. Return QueryResponse
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.intent_llm          import classify_intent
from app.ai.param_llm           import extract_params
from app.ai.summary_llm         import generate_summary_and_widgets
from app.ai.free_query_llm      import generate_free_query
from app.ai.free_query_executor import execute_free_sql
from app.ai.free_summary_llm    import summarize_free_result
from app.ai.keyword_fallback    import keyword_fallback

from app.core.schemas import Intent, IntentScore, QueryResponse, WidgetConfig
from app.tools.runner import run_tools


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
    all_unknown   = all(i.intent == Intent.UNKNOWN for i in intents)

    # ── Step 2: Keyword fallback ──────────────────────────────────────────────
    if all_unknown:
        fallback_intents = keyword_fallback(query)
        if fallback_intents != [Intent.UNKNOWN]:
            intents     = [IntentScore(intent=i, confidence=0.60) for i in fallback_intents]
            all_unknown = False
            print(f"🔑 Keyword fallback intents: {[i.intent.value for i in intents]}")

    # ── Step 3: Free SQL fallback (truly unknown) ─────────────────────────────
    if all_unknown:
        return _handle_unknown_query(query, db)

    # ── Step 4: Parameter extraction ─────────────────────────────────────────
    extracted     = extract_params(query, intents)
    merged_params = {**extracted, **(params or {})}
    print(f"🔧 Merged params: {merged_params}")

    # ── Step 5: Run tools ────────────────────────────────────────────────────
    tool_outputs = run_tools(intents=intents, db=db, params=merged_params)
    print(f"✅ Tools executed, keys: {list(tool_outputs.keys())}")

    # ── Step 6: Summary LLM ──────────────────────────────────────────────────
    summary_response = generate_summary_and_widgets(
        query=query,
        intents=intents,
        tool_outputs=tool_outputs,
    )
    print(f"✅ Summary: {summary_response.summary[:80]}…")
    print(f"✅ Widgets: {[w.type for w in summary_response.widgets]}")

    # ── Step 7: Final response ────────────────────────────────────────────────
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
        intents=[{"intent": s.intent.value, "confidence": s.confidence} for s in intents],
    )


def _handle_unknown_query(query: str, db: Session) -> QueryResponse:
    """Free SQL fallback for queries that don't match any known intent."""
    print("🔄 Entering free-query fallback mode")

    llm_output = generate_free_query(query)

    if not llm_output or "sql" not in llm_output:
        return QueryResponse(
            query=query,
            summary="I couldn't determine how to answer that from the warehouse data.",
            widgets=[],
            data={},
            intents=[{"intent": "unknown", "confidence": 0.0}],
        )

    sql          = llm_output["sql"]
    widget_type  = llm_output.get("widget_type", "TABLE")
    widget_title = llm_output.get("widget_title", "Query Result")
    explanation  = llm_output.get("explanation", "")

    print(f"📝 Generated SQL: {sql}")
    print(f"🧩 Widget: {widget_type} — {widget_title}")

    result  = execute_free_sql(db, sql)
    summary = summarize_free_result(query, sql, result, widget_type)

    widget = WidgetConfig(
        type=widget_type,
        title=widget_title,
        data_key="free_query",
        props={"explanation": explanation, "sql": sql},
    )

    return QueryResponse(
        query=query,
        summary=summary,
        widgets=[widget] if "error" not in result else [],
        data={"free_query": result},
        intents=[{"intent": "unknown", "confidence": 0.0}],
    )