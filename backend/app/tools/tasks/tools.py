from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, to_bool


def _normalize_tasks(rows):
    for r in rows:
        r["is_blocked"] = to_bool(r.get("is_blocked"))
    return rows


def get_active_tasks(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 30))

    sql = """
    SELECT
      id, task_type, status, priority, assigned_to, assignee_name, zone,
      source_location, destination_location, reference_id,
      created_at, started_at, completed_at, estimated_minutes,
      is_blocked, block_reason
    FROM warehouse_tasks
    WHERE LOWER(status) IN ('queued', 'in-progress')
    ORDER BY created_at DESC
    LIMIT :limit
    """
    tasks = _normalize_tasks(fetch_all(db, sql, {"limit": limit}))
    return {"count": len(tasks), "tasks": tasks}


def get_blocked_tasks(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 30))

    sql = """
    SELECT
      id, task_type, status, priority, assigned_to, assignee_name, zone,
      source_location, destination_location, reference_id,
      created_at, started_at, completed_at, estimated_minutes,
      is_blocked, block_reason
    FROM warehouse_tasks
    WHERE is_blocked = 1 OR LOWER(status) = 'blocked'
    ORDER BY created_at DESC
    LIMIT :limit
    """
    tasks = _normalize_tasks(fetch_all(db, sql, {"limit": limit}))
    return {"count": len(tasks), "tasks": tasks}