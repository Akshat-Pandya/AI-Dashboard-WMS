# app/api/query.py
"""
/query       — full pipeline (intent LLM → param LLM → tools → summary LLM)
/query/refresh — data-only refresh (tools only, no LLM calls)
               Used by the frontend auto-refresh and manual refresh button.
               Accepts the intents and params already known from the last full
               run so only the SQL queries are re-executed.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.ai.orchestrator  import orchestrate
from app.core.schemas     import Intent, IntentScore, QueryResponse, WidgetConfig
from app.core.db_session  import get_db
from app.core.query_cache import query_cache
from app.tools.runner     import run_tools

router = APIRouter()


class QueryRequest(BaseModel):
    query:  str
    params: Optional[Dict[str, Any]] = None


class RefreshRequest(BaseModel):
    """
    Sent by the frontend on every auto/manual refresh.
    Contains everything from the last full response so we can
    skip intent classification, param extraction and summary LLM entirely.
    """
    query:   str
    intents: List[Dict[str, Any]]          # [{intent, confidence}, ...]
    params:  Optional[Dict[str, Any]] = None
    widgets: List[Dict[str, Any]]          # pass-through — returned unchanged
    summary: str                           # pass-through — returned unchanged


@router.post("/query", response_model=QueryResponse)
def query_endpoint(
    body: QueryRequest,
    db:   Session = Depends(get_db),
):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # ── Cache check (skip when caller passes explicit params) ─────────────────
    use_cache = not body.params
    if use_cache:
        cached = query_cache.get(body.query)
        if cached:
            print(f"⚡ Cache hit: {body.query!r}")
            return cached

    # ── Normal orchestration ──────────────────────────────────────────────────
    result = orchestrate(query=body.query, db=db, params=body.params)

    if use_cache:
        query_cache.set(body.query, result.model_dump())

    return result


@router.post("/query/refresh", response_model=QueryResponse)
def refresh_endpoint(
    body: RefreshRequest,
    db:   Session = Depends(get_db),
):
    """
    Data-only refresh — re-runs SQL tools only, no LLM calls.
    Returns the same query/summary/widgets as before, with fresh data.
    """
    print(f"\n🔄 Refresh endpoint called  |  query: {body.query!r}")

    # Reconstruct IntentScore list from the plain dicts sent by the frontend
    intent_scores: List[IntentScore] = []
    for item in body.intents:
        try:
            intent_scores.append(IntentScore(
                intent     = Intent(item["intent"]),
                confidence = float(item.get("confidence", 0.8)),
            ))
        except ValueError:
            # Skip any unknown intent strings gracefully
            print(f"  ⚠️ Skipping unknown intent: {item.get('intent')}")

    if not intent_scores:
        raise HTTPException(status_code=400, detail="No valid intents provided")

    # Re-run tools only — this is the only DB call
    tool_outputs = run_tools(
        intents = intent_scores,
        db      = db,
        params  = body.params or {},
    )
    print(f"  ✅ Tools refreshed, keys: {list(tool_outputs.keys())}")

    # Reconstruct WidgetConfig list from the plain dicts
    widgets = [
        WidgetConfig(
            type     = w["type"],
            title    = w["title"],
            data_key = w["data_key"],
            props    = w.get("props"),
        )
        for w in body.widgets
    ]

    return QueryResponse(
        query   = body.query,
        summary = body.summary,          # unchanged from last full run
        widgets = widgets,               # unchanged from last full run
        data    = tool_outputs,          # ← fresh from DB
        intents = body.intents,          # pass-through
    )


@router.get("/queries/cache")
def get_cache_keys():
    """Debug: returns all query keys currently in cache."""
    keys = query_cache.all_keys()
    return {"cached_queries": keys, "count": len(keys)}