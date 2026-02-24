# app/api/dashboards.py
"""
Saved Dashboards feature — new file, no changes to existing modules.

Endpoints:
  POST /dashboards/save          save a query for later re-execution
  GET  /dashboards               list all saved dashboards
  GET  /dashboards/{id}/run      re-execute a saved dashboard with fresh data
  DELETE /dashboards/{id}        remove a saved dashboard
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.orchestrator  import orchestrate
from app.core.db_session  import get_db
from app.core.models      import SavedDashboard
from app.core.query_cache import query_cache

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# ── Request / Response schemas ────────────────────────────────────────────────

class SaveDashboardRequest(BaseModel):
    query:       str
    intent_name: Optional[str]       = None
    params:      Optional[Dict[str, Any]] = None
    label:       Optional[str]       = None   # human-readable name shown in list
    user_id:     Optional[str]       = None


class DashboardMeta(BaseModel):
    id:          str
    query_text:  str
    intent_name: Optional[str]
    label:       Optional[str]
    created_at:  str

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/save", response_model=DashboardMeta)
def save_dashboard(
    body: SaveDashboardRequest,
    db:   Session = Depends(get_db),
):
    """Persist a query so it can be re-run later. Does NOT store result data."""
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    record = SavedDashboard(
        query_text  = body.query.strip(),
        intent_name = body.intent_name,
        params_json = body.params or {},
        label       = body.label or body.query.strip()[:80],
        user_id     = body.user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DashboardMeta(
        id          = record.id,
        query_text  = record.query_text,
        intent_name = record.intent_name,
        label       = record.label,
        created_at  = record.created_at.isoformat(),
    )


@router.get("", response_model=List[DashboardMeta])
def list_dashboards(
    user_id: Optional[str] = None,
    db:      Session = Depends(get_db),
):
    """Return all saved dashboards, newest first."""
    q = db.query(SavedDashboard)
    if user_id:
        q = q.filter(SavedDashboard.user_id == user_id)
    records = q.order_by(SavedDashboard.created_at.desc()).all()

    return [
        DashboardMeta(
            id          = r.id,
            query_text  = r.query_text,
            intent_name = r.intent_name,
            label       = r.label,
            created_at  = r.created_at.isoformat(),
        )
        for r in records
    ]


@router.get("/{dashboard_id}/run")
def run_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
):
    """
    Re-execute a saved dashboard with fresh live data.
    Checks cache first; falls through to orchestrator on miss.
    """
    record = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    query  = record.query_text
    params = record.params_json or None

    # Check cache (only for param-free queries)
    if not params:
        cached = query_cache.get(query)
        if cached:
            print(f"⚡ Dashboard cache hit: {query!r}")
            return cached

    result = orchestrate(query=query, db=db, params=params)

    if not params:
        query_cache.set(query, result.model_dump())

    return result


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
):
    """Remove a saved dashboard."""
    record = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    db.delete(record)
    db.commit()