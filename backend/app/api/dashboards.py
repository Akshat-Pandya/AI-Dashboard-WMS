# app/api/dashboards.py
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.orchestrator  import orchestrate
from app.core.db_session  import get_db
from app.core.models      import SavedDashboard
from app.core.query_cache import query_cache

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


class SaveDashboardRequest(BaseModel):
    query:       str
    intent_name: Optional[str]            = None
    params:      Optional[Dict[str, Any]] = None
    label:       Optional[str]            = None
    user_id:     Optional[str]            = None


class DashboardMeta(BaseModel):
    id:          str
    query_text:  str
    intent_name: Optional[str]
    label:       Optional[str]
    created_at:  str
    already_saved: bool = False   # ← tells frontend it was a duplicate

    class Config:
        from_attributes = True


@router.post("/save", response_model=DashboardMeta)
def save_dashboard(
    body: SaveDashboardRequest,
    db:   Session = Depends(get_db),
):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    normalized = body.query.strip().lower()

    # ── Deduplication: return existing record if same query already saved ──────
    existing = (
        db.query(SavedDashboard)
        .filter(SavedDashboard.query_text_normalized == normalized)
        .first()
    )
    if existing:
        return DashboardMeta(
            id            = existing.id,
            query_text    = existing.query_text,
            intent_name   = existing.intent_name,
            label         = existing.label,
            created_at    = existing.created_at.isoformat(),
            already_saved = True,
        )

    record = SavedDashboard(
        query_text            = body.query.strip(),
        query_text_normalized = normalized,
        intent_name           = body.intent_name,
        params_json           = body.params or {},
        label                 = body.label or body.query.strip()[:80],
        user_id               = body.user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DashboardMeta(
        id            = record.id,
        query_text    = record.query_text,
        intent_name   = record.intent_name,
        label         = record.label,
        created_at    = record.created_at.isoformat(),
        already_saved = False,
    )


@router.get("", response_model=List[DashboardMeta])
def list_dashboards(
    user_id: Optional[str] = None,
    db:      Session = Depends(get_db),
):
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
    record = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    query  = record.query_text
    params = record.params_json or None

    if not params:
        cached = query_cache.get(query)
        if cached:
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
    record = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    db.delete(record)
    db.commit()


@router.get("/check")
def check_saved(
    query: str,
    db:    Session = Depends(get_db),
):
    """Check if a query is already saved. Used by frontend to restore saved state."""
    normalized = query.strip().lower()
    existing   = (
        db.query(SavedDashboard)
        .filter(SavedDashboard.query_text_normalized == normalized)
        .first()
    )
    return {"saved": existing is not None, "id": existing.id if existing else None}