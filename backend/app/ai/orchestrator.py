"""
orchestrator.py
Full pipeline:
  1. Classify intents
  1.5 Early rejection for irrelevant queries
  2. Keyword fallback     (if unknown)
  3. Free SQL fallback    (if still unknown/unsupported)
     - warehouse-term guard before hitting DB
  4. Extract params
  5. Run tools (with params)
  5b. Trend aggregation   (if query is trend/history related)
  6. Summary LLM → widgets + summary
  6.5 Widget safety net  (ensure every intent has a widget)
  6.6 Priority-sort widgets
  7. Return QueryResponse
"""
from collections import defaultdict
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
_WIDGET_PRIORITY: Dict[str, int] = {
    "ALERT_LIST":         1,
    "OVERVIEW_PANEL":     2,
    "KPI_CARDS":          3,
    "TABLE":              4,
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

# ── Trend detection ───────────────────────────────────────────────────────────
_TREND_KEYWORDS = {
    "trend", "over time", "history", "historical",
    "last 7", "last week", "daily", "per day", "over the",
}

# Maps intent → (tool_output_key, list_key, date_field)
_TREND_CONFIG = {
    Intent.WAREHOUSE_ALERTS: ("alerts",       "alerts", "timestamp"),
    Intent.INBOUND_ACTIVITY: ("inbound",      "asns",   "expected_date"),
    Intent.ORDER_STATUS:     ("orders",       "orders", "created_at"),
    Intent.ACTIVE_TASKS:     ("active_tasks", "tasks",  "created_at"),
    Intent.BLOCKED_TASKS:    ("blocked_tasks","tasks",  "created_at"),
}


def _is_trend_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _TREND_KEYWORDS)


def _aggregate_trend(tool_outputs: Dict[str, Any], intents: List[IntentScore]) -> Dict[str, Any]:
    """
    Group rows by date for each intent that has a trend config.
    Adds tool_outputs["trend"] = { "alerts": [{date, count},...], ... }
    """
    trend_data: Dict[str, List[Dict[str, Any]]] = {}

    for intent_score in intents:
        cfg = _TREND_CONFIG.get(intent_score.intent)
        if not cfg:
            continue

        output_key, list_key, date_field = cfg
        output = tool_outputs.get(output_key, {})
        items  = output.get(list_key, []) if isinstance(output, dict) else []

        if not items:
            continue

        counts: Dict[str, int] = defaultdict(int)
        for item in items:
            raw_date = item.get(date_field) or ""
            date     = str(raw_date)[:10]   # "2026-02-17T10:30:00" → "2026-02-17"
            if date:
                counts[date] += 1

        if counts:
            series = sorted(
                [{"date": d, "count": c} for d, c in counts.items()],
                key=lambda x: x["date"],
            )
            trend_data[output_key] = series
            print(f"📈 Trend aggregated for {output_key}: {series}")

    if trend_data:
        tool_outputs["trend"] = trend_data

    return tool_outputs


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
            intents=[{"intent": Intent.IRRELEVANT_QUERY.value, "confidence": 0.99}],
        )

    # ── Step 2: Keyword fallback ──────────────────────────────────────────────
    if all_unknown:
        fallback_intents = keyword_fallback(query)
        if fallback_intents != [Intent.UNKNOWN] and \
           fallback_intents != [Intent.UNSUPPORTED_WAREHOUSE]:
            intents     = [IntentScore(intent=i, confidence=0.60) for i in fallback_intents]
            all_unknown = False
            print(f"🔑 Keyword fallback intents: {[i.intent.value for i in intents]}")

    # ── Step 3: Free SQL fallback ─────────────────────────────────────────────
    if all_unknown:
        q_lower            = query.lower()
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
                intents=[{"intent": Intent.IRRELEVANT_QUERY.value, "confidence": 0.99}],
            )

    # ── Step 4: Parameter extraction ─────────────────────────────────────────
    extracted     = extract_params(query, intents)
    merged_params = {**extracted, **(params or {})}
    print(f"🔧 Merged params: {merged_params}")

    # ── Step 5: Run tools ────────────────────────────────────────────────────
    tool_outputs = run_tools(intents=intents, db=db, params=merged_params)
    print(f"✅ Tools executed, keys: {list(tool_outputs.keys())}")

    # ── Step 5b: Trend aggregation ────────────────────────────────────────────
    is_trend = _is_trend_query(query)
    if is_trend:
        tool_outputs = _aggregate_trend(tool_outputs, intents)
        print(f"📊 Trend keys: {list(tool_outputs.get('trend', {}).keys())}")

    # ── Step 6: Summary LLM ──────────────────────────────────────────────────
    # For trend queries, summary_llm bypasses the LLM widget selection entirely
    # and builds LINE_CHART widgets directly from tool_outputs["trend"].
    summary_response = generate_summary_and_widgets(
        query=query,
        intents=intents,
        tool_outputs=tool_outputs,
    )
    print(f"✅ Summary:  {summary_response.summary[:80]}…")
    print(f"✅ Widgets (pre-fix): {[w.type for w in summary_response.widgets]}")

    # ── Step 6.5: Widget safety net ───────────────────────────────────────────
    # SKIP for trend queries — summary_llm already built the correct LINE_CHARTs.
    # Running _ensure_widgets would inject TABLE/KPI_CARDS on top of them.
    if not is_trend:
        summary_response.widgets = _ensure_widgets(
            intents=intents,
            widgets=summary_response.widgets,
            tool_outputs=tool_outputs,
        )

    # ── Step 6.6: Priority-sort widgets ──────────────────────────────────────
    summary_response.widgets = _sort_widgets(summary_response.widgets)

    print(f"✅ Widgets (final):   {[w.type for w in summary_response.widgets]}")

    # ── Step 7: Final response ────────────────────────────────────────────────
    return QueryResponse(
        query=query,
        summary=summary_response.summary,
        widgets=summary_response.widgets,
        data=tool_outputs,
        intents=[{"intent": s.intent.value, "confidence": s.confidence} for s in intents],
    )


# =============================================================================
#  FREE-SQL FALLBACK
# =============================================================================

def _handle_unknown_query(query: str, db: Session) -> QueryResponse:
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

    widget_props = {"explanation": explanation, "sql": sql}
    if "error" in result:
        widget_props["error"] = result["error"]

    return QueryResponse(
        query=query,
        summary=summary,
        widgets=[WidgetConfig(type=widget_type, title=widget_title, data_key="free_query", props=widget_props)],
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
    Safety net: inject fallback widgets for intents with data but no widget.
    Only called for non-trend queries.
    """
    if not tool_outputs:
        return widgets

    correctly_covered: set = set()
    for w in widgets:
        for tool_key, (_, canonical_dk) in FALLBACK_MAP.items():
            if w.data_key == canonical_dk:
                correctly_covered.add(tool_key)
                break

    extras: List[WidgetConfig] = []

    for score in intents:
        if score.intent in (Intent.UNKNOWN, Intent.IRRELEVANT_QUERY, Intent.UNSUPPORTED_WAREHOUSE):
            continue

        data_key = INTENT_DATA_KEY.get(score.intent)
        if not data_key:
            continue
        if data_key in correctly_covered:
            continue
        if data_key not in tool_outputs:
            continue

        widget_type, full_data_key = FALLBACK_MAP.get(data_key, ("TABLE", data_key))
        title = data_key.replace("_", " ").title()

        print(f"  🔧 Widget safety net: injecting {widget_type} for '{data_key}'")

        extras.append(WidgetConfig(
            type=widget_type,
            title=title,
            data_key=full_data_key,
            props=None,
        ))
        correctly_covered.add(data_key)

    return widgets + extras


def _sort_widgets(widgets: List[WidgetConfig]) -> List[WidgetConfig]:
    """Sort widgets by operational priority — alerts first, charts last."""
    return sorted(widgets, key=lambda w: _WIDGET_PRIORITY.get(w.type, 99))