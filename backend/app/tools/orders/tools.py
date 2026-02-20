from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all


def get_orders_by_status(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    status = (params.get("status") or "").strip().lower()
    limit = int(params.get("limit", 25))

    if not status:
        return {"status": "", "count": 0, "orders": []}

    sql = """
    SELECT
      id, order_number, status, priority, customer_name,
      total_lines, picked_lines, packed_lines, total_units,
      created_at, due_date, wave_id, carrier, staging_zone
    FROM outbound_orders
    WHERE LOWER(status) = :status
    ORDER BY due_date ASC
    LIMIT :limit
    """
    orders = fetch_all(db, sql, {"status": status, "limit": limit})

    return {"status": status, "count": len(orders), "orders": orders}


def get_stuck_orders(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 25))

    sql = """
    SELECT
      id, order_number, status, priority, customer_name,
      total_lines, picked_lines, packed_lines, total_units,
      created_at, due_date, wave_id, carrier, staging_zone
    FROM outbound_orders
    WHERE LOWER(status) IN ('pending', 'picking')
      AND (picked_lines < total_lines OR packed_lines < total_lines)
    ORDER BY due_date ASC
    LIMIT :limit
    """
    orders = fetch_all(db, sql, {"limit": limit})

    return {
        "reason": "pending/picking with incomplete pick/pack progress",
        "count": len(orders),
        "orders": orders,
    }