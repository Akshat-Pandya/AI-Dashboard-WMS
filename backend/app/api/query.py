# app/api/query.py
"""
Existing /query endpoint — only change is cache check/fill.
No other behaviour is modified.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.ai.orchestrator  import orchestrate
from app.core.schemas     import QueryResponse
from app.core.db_session  import get_db
from app.core.query_cache import query_cache   # ← new

router = APIRouter()


class QueryRequest(BaseModel):
    query:  str
    params: Optional[Dict[str, Any]] = None


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


@router.get("/queries/cache")
def get_cache_keys():
    """Debug: returns all query keys currently in cache."""
    keys = query_cache.all_keys()
    return {"cached_queries": keys, "count": len(keys)}