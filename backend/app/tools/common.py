from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def fetch_all(
    db: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict]:
    """Execute a parameterised SELECT and return rows as list of dicts."""
    params = params or {}
    result = db.execute(text(sql), params)
    columns = list(result.keys())
    return [dict(zip(columns, row)) for row in result.fetchall()]


def fetch_one(
    db: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> Optional[Dict]:
    params = params or {}
    result = db.execute(text(sql), params)
    columns = list(result.keys())
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


def safe_int(value: Any, default: int = 20) -> int:
    """Parse an integer param safely with a fallback default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default