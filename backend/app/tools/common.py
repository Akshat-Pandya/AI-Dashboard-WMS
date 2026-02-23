"""
common.py — shared DB helpers used by all tool modules
"""
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text


def fetch_all(db: Session, sql: str, params: Dict[str, Any] = None) -> List[Dict]:
    """Execute a raw SQL query and return rows as list of dicts."""
    params = params or {}
    result = db.execute(text(sql), params)
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]


def fetch_one(db: Session, sql: str, params: Dict[str, Any] = None) -> Dict | None:
    params = params or {}
    result = db.execute(text(sql), params)
    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row)) if row else None


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes")
    return False
