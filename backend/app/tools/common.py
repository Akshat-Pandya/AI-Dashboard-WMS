from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def fetch_all(db: Session, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    rows = db.execute(text(sql), params or {}).mappings().all()
    return [dict(r) for r in rows]


def fetch_one(db: Session, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row = db.execute(text(sql), params or {}).mappings().first()
    return dict(row) if row else {}


def to_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("1", "true", "yes", "y", "t")