from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.ai.orchestrator import orchestrate
from app.core.schemas import QueryResponse
from app.core.db_session import get_db

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None  # e.g. {"limit": 50, "zone": "A"}


@router.post("/query", response_model=QueryResponse)
def query_wms(body: QueryRequest, db: Session = Depends(get_db)):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return orchestrate(
        query=body.query,
        db=db,
        params=body.params,
    )