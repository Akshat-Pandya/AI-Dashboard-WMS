"""
orchestrator.py
Full pipeline:
  1. Classify intents
  1.5 Early rejection for irrelevant queries         ← NEW
  2. Keyword fallback     (if unknown)
  3. Free SQL fallback    (if still unknown/unsupported)
     - warehouse-term guard before hitting DB         ← NEW
  4. Extract params
  5. Run tools (with params)
  6. Summary LLM → widgets + summary
  6.5 Widget safety net  (ensure every intent has a widget) ← NEW
  6.6 Priority-sort widgets                          ← NEW
  7. Return QueryResponse
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.intent_llm          import classify_intent
from app.ai.param_llm           import extract_params
from app.ai.summary_llm         import generate_summary_and_widgets
from app.ai.free_query_llm      import generate_free_query
from app.ai.free_query_executor import execute_free_sql
from app.ai.free_summary_llm    import summarize_free_result
from app.ai.keyword_fallback    import keyword_fallback
from app.ai.widget_registry     import FALLBACK_MAP

from app.core.schemas import Intent, IntentScore, QueryResponse, WidgetConfig
from app.tools.registry import INTENT_DATA_KEY
from app.tools.runner import run_tools

# ── Widget priority order (lower number = shown first) ────────────────────────
# Operators need alerts and blockers before summaries and charts.
_WIDGET_PRIORITY: Dict[str, int] = {
    "ALERT_LIST":         1,
    "OVERVIEW_PANEL":     2,
    "KPI_CARDS":          3,
    "TABLE":              4,   # blocked tasks, stuck orders, low stock
    "ZONE_COMPARE_CHART": 5,
    "INBOUND_SUMMARY":    6,
    "BAR_CHART":          7,
    "LINE_CHART":         8,
}

# ── Warehouse entity terms used to guard free-SQL fallback ────────────────────
_WAREHOUSE_TERMS = {
    "order", "sku", "inventory", "zone", "task", "pick", "pack",
    "ship", "asn", "inbound", "outbound", "alert", "kpi", "dock",
    "carrier", "stock", "warehouse", "pallet", "putaway", "location",
    "receiving", "shipment", "replenish", "reorder", "fulfillment",
}


# =============================================================================
#  PUBLIC ENTRY POINT
# =============================================================================

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

    # ── Step 1.5: Early rejection — irrelevant queries ────────────────────────
    # If EVERY intent is irrelevant/unknown → reject immediately.
    # This short-circuits before keyword fallback, param extraction,
    # tool execution, and free-SQL — saving up to 27s per bad query.
    has_irrelevant = any(i.intent == Intent.IRRELEVANT_QUERY for i in intents)
    if has_irrelevant and all(
        i.intent in (Intent.IRRELEVANT_QUERY, Intent.UNKNOWN)
        for i in intents
    ):
        print("🚫 Irrelevant query detected — early exit")
        return QueryResponse(
            query=query,
            summary=(
                "I can only answer questions about warehouse operations — "
                "inventory, orders, tasks, shipments, alerts, and KPIs."
            ),
            widgets=[],
            data={},
            intents=[{
                "intent":     Intent.IRRELEVANT_QUERY.value,
                "confidence": 0.99,
            }],
        )

    # ── Step 2: Keyword fallback ──────────────────────────────────────────────
    if all_unknown:
        fallback_intents = keyword_fallback(query)
        if fallback_intents != [Intent.UNKNOWN] and \
           fallback_intents != [Intent.UNSUPPORTED_WAREHOUSE]:
            intents     = [IntentScore(intent=i, confidence=0.60) for i in fallback_intents]
            all_unknown = False
            print(f"🔑 Keyword fallback intents: {[i.intent.value for i in intents]}")

    # ── Step 3: Free SQL fallback (warehouse-related but no mapped tool) ───────
    # Guard: only hit the DB if the query actually references warehouse entities.
    # Purely irrelevant queries that slipped past Step 1.5 are caught here.
    if all_unknown:
        q_lower          = query.lower()
        is_warehouse_query = any(term in q_lower for term in _WAREHOUSE_TERMS)

        if is_warehouse_query:
            print("🔄 Routing to free-SQL fallback (warehouse entity detected)")
            return _handle_unknown_query(query, db)
        else:
            print("🚫 No warehouse terms found — rejecting without DB call")
            return QueryResponse(
                query=query,
                summary=(
                    "I can only answer questions about warehouse operations — "
                    "inventory, orders, tasks, shipments, alerts, and KPIs."
                ),
                widgets=[],
                data={},
                intents=[{
                    "intent":     Intent.IRRELEVANT_QUERY.value,
                    "confidence": 0.99,
                }],
            )

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
    print(f"✅ Summary:  {summary_response.summary[:80]}…")
    print(f"✅ Widgets (pre-fix): {[w.type for w in summary_response.widgets]}")

    # ── Step 6.5: Widget safety net ───────────────────────────────────────────
    # Guarantees every intent that produced data has at least one widget.
    # Only adds fallback widgets — never removes LLM-chosen ones.
    summary_response.widgets = _ensure_widgets(
        intents=intents,
        widgets=summary_response.widgets,
        tool_outputs=tool_outputs,
    )

    # ── Step 6.6: Priority-sort widgets ──────────────────────────────────────
    # Alerts first, then overview, KPIs, tables, charts.
    # Python sort is stable — same-type widgets keep their relative order.
    summary_response.widgets = _sort_widgets(summary_response.widgets)

    print(f"✅ Widgets (final):   {[w.type for w in summary_response.widgets]}")

    # ── Step 7: Final response ────────────────────────────────────────────────
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
        intents=[{
            "intent":     s.intent.value,
            "confidence": s.confidence,
        } for s in intents],
    )


# =============================================================================
#  FREE-SQL FALLBACK  (warehouse queries with no mapped intent)
# =============================================================================

def _handle_unknown_query(query: str, db: Session) -> QueryResponse:
    """
    Free SQL fallback for warehouse queries that don't match any known intent.
    Only called when the query contains warehouse entity terms (Step 3 guard).
    """
    print("🔄 Entering free-query fallback mode")

    llm_output = generate_free_query(query)

    if not llm_output or "sql" not in llm_output:
        return QueryResponse(
            query=query,
            summary="I couldn't determine how to answer that from the warehouse data.",
            widgets=[],
            data={},
            intents=[{"intent": Intent.UNSUPPORTED_WAREHOUSE.value, "confidence": 0.0}],
        )

    sql          = llm_output["sql"]
    widget_type  = llm_output.get("widget_type", "TABLE")
    widget_title = llm_output.get("widget_title", "Query Result")
    explanation  = llm_output.get("explanation", "")

    print(f"📝 Generated SQL:  {sql}")
    print(f"🧩 Widget:         {widget_type} — {widget_title}")

    result  = execute_free_sql(db, sql)
    summary = summarize_free_result(query, sql, result, widget_type)

    # Always include the widget — if SQL errored, surface the error in props
    # rather than silently returning 0 widgets (which breaks the frontend).
    widget_props = {"explanation": explanation, "sql": sql}
    if "error" in result:
        widget_props["error"] = result["error"]

    widget = WidgetConfig(
        type=widget_type,
        title=widget_title,
        data_key="free_query",
        props=widget_props,
    )

    return QueryResponse(
        query=query,
        summary=summary,
        widgets=[widget],          # always return the widget
        data={"free_query": result},
        intents=[{"intent": Intent.UNSUPPORTED_WAREHOUSE.value, "confidence": 0.0}],
    )


# =============================================================================
#  HELPERS
# =============================================================================

def _ensure_widgets(
    intents: List[IntentScore],
    widgets: List[WidgetConfig],
    tool_outputs: Dict[str, Any],
) -> List[WidgetConfig]:
    """
    Safety net: for every intent that has tool output data but no corresponding
    widget, inject a fallback widget using FALLBACK_MAP defaults.

    This fixes:
      - warehouse_overview returning 0 widgets (LLM forgets OVERVIEW_PANEL)
      - Any intent where the summary LLM omits a widget by mistake

    Guarantee: only ADDS widgets, never removes existing ones.
    """
    if not tool_outputs:
        return widgets

    # Collect the top-level data keys already covered by existing widgets
    # e.g. widget with data_key="alerts.alerts" covers top-level key "alerts"
    covered: set = {w.data_key.split(".")[0] for w in widgets}

    extras: List[WidgetConfig] = []

    for score in intents:
        if score.intent in (
            Intent.UNKNOWN,
            Intent.IRRELEVANT_QUERY,
            Intent.UNSUPPORTED_WAREHOUSE,
        ):
            continue

        data_key = INTENT_DATA_KEY.get(score.intent)
        if not data_key:
            continue
        if data_key in covered:
            continue
        if data_key not in tool_outputs:
            continue  # tool didn't run or returned nothing

        # Data exists but no widget covers it — inject fallback
        widget_type, full_data_key = FALLBACK_MAP.get(data_key, ("TABLE", data_key))
        title = data_key.replace("_", " ").title()

        print(f"  🔧 Widget safety net: injecting {widget_type} for '{data_key}'")

        extras.append(WidgetConfig(
            type=widget_type,
            title=title,
            data_key=full_data_key,
            props=None,
        ))
        covered.add(data_key)

    return widgets + extras


def _sort_widgets(widgets: List[WidgetConfig]) -> List[WidgetConfig]:
    """
    Sort widgets by operational priority so the most actionable information
    appears first in the UI — regardless of LLM output order.

    Priority (ascending = shown first):
      1. ALERT_LIST       — operators need to see problems immediately
      2. OVERVIEW_PANEL   — warehouse health at a glance
      3. KPI_CARDS        — performance metrics
      4. TABLE            — detail rows (tasks, orders, stock)
      5. ZONE_COMPARE_CHART
      6. INBOUND_SUMMARY
      7. BAR_CHART / LINE_CHART

    Unknown widget types fall to the end (priority 99).
    Python sort is stable: same-priority widgets keep their LLM-assigned order.
    """
    return sorted(
        widgets,
        key=lambda w: _WIDGET_PRIORITY.get(w.type, 99),
    )