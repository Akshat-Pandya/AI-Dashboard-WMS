from typing import Any, Dict, Optional
 
from sqlalchemy.orm import Session
 
from app.ai.intent_llm   import classify_intent
from app.ai.summary_llm  import generate_summary_and_widgets
from app.ai.free_query_llm      import generate_free_query
from app.ai.free_query_executor import execute_free_sql
from app.ai.free_summary_llm    import summarize_free_result
 
from app.core.schemas    import Intent, QueryResponse, WidgetConfig
from app.tools.runner    import run_tools
 
from app.ai.keyword_fallback import keyword_fallback
 
def orchestrate(
    query: str,
    db: Session,
    params: Optional[Dict[str, Any]] = None,
) -> QueryResponse:
    print("\n══════════════════════════════════════════════════")
    print(f"🚀 Orchestrator started  |  query: {query!r}")

    intent_result = classify_intent(query)
    intents = intent_result.intents
 
    all_unknown = all(i.intent == Intent.UNKNOWN for i in intents)
 
    if all_unknown:
        # Try keyword fallback first before going to free-SQL mode
        fallback_intents = keyword_fallback(query)
        if fallback_intents != [Intent.UNKNOWN]:
            from app.core.schemas import IntentScore
            intents = [IntentScore(intent=i, confidence=0.60) for i in fallback_intents]
            all_unknown = False
 
    if all_unknown:
        # ── FREE SQL FALLBACK (Problem 2) ──
        return handle_unknown_query(query, db)
 
    tool_outputs = run_tools(intents=intents, db=db, params=params)
    summary_response = generate_summary_and_widgets(
        query=query, intents=intents, tool_outputs=tool_outputs
    )
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
        intents=[{"intent": s.intent.value, "confidence": s.confidence} for s in intents],
    )
 
def handle_unknown_query(query: str, db: Session) -> QueryResponse:
    print("🔄 Entering free-query fallback mode")
 
    # 1. LLM generates SQL + widget hint
    llm_output = generate_free_query(query)
 
    if not llm_output or "sql" not in llm_output:
        return QueryResponse(
            query=query,
            summary="I couldn't determine how to answer that question from the warehouse data.",
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
 
    # 2. Execute SQL
    result = execute_free_sql(db, sql)
 
    # 3. Generate summary
    summary = summarize_free_result(query, sql, result, widget_type)
 
    # 4. Build widget config
    widget = WidgetConfig(
        type=widget_type,
        title=widget_title,
        data_key="free_query",
        props={"explanation": explanation, "sql": sql},
    )
 
    data = {"free_query": result}
 
    return QueryResponse(
        query=query,
        summary=summary,
        widgets=[widget] if "error" not in result else [],
        data=data,
        intents=[{"intent": "unknown", "confidence": 0.0}],
    )