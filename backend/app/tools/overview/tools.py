from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, fetch_one


def get_warehouse_overview(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}

    inv = fetch_one(db, """
    SELECT
      COUNT(*) AS total_skus,
      SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END) AS low_stock_items,
      SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END) AS zero_stock_items
    FROM inventory_items
    """)

    orders_by_status = fetch_all(db, """
    SELECT LOWER(status) AS status, COUNT(*) AS count
    FROM outbound_orders
    GROUP BY LOWER(status)
    ORDER BY count DESC
    """)
    orders_map = {r["status"]: int(r["count"]) for r in orders_by_status}

    stuck = fetch_one(db, """
    SELECT COUNT(*) AS stuck_orders
    FROM outbound_orders
    WHERE LOWER(status) IN ('pending', 'picking')
      AND (picked_lines < total_lines OR packed_lines < total_lines)
    """)

    tasks = fetch_one(db, """
    SELECT
      SUM(CASE WHEN LOWER(status) IN ('queued','in-progress') THEN 1 ELSE 0 END) AS active_tasks,
      SUM(CASE WHEN is_blocked = 1 OR LOWER(status) = 'blocked' THEN 1 ELSE 0 END) AS blocked_tasks
    FROM warehouse_tasks
    """)

    alerts = fetch_one(db, """
    SELECT
      SUM(CASE WHEN acknowledged = 0 AND LOWER(severity) = 'critical' THEN 1 ELSE 0 END) AS unacknowledged_critical_alerts
    FROM warehouse_alerts
    """)

    kpis = fetch_all(db, """
    SELECT label, value, trend, is_on_target
    FROM warehouse_kpis
    ORDER BY id ASC
    LIMIT 6
    """)
    for k in kpis:
        k["is_on_target"] = bool(int(k.get("is_on_target") or 0))

    zones_near = fetch_all(db, """
    SELECT zone_name
    FROM zone_utilization
    WHERE utilization_percent >= 85
    ORDER BY utilization_percent DESC
    """)
    zones_near_capacity = [z["zone_name"] for z in zones_near]

    return {
        "inventory": {
            "total_skus": int(inv.get("total_skus") or 0),
            "low_stock_items": int(inv.get("low_stock_items") or 0),
            "zero_stock_items": int(inv.get("zero_stock_items") or 0),
        },
        "orders": {
            "orders_by_status": orders_map,
            "stuck_orders": int(stuck.get("stuck_orders") or 0),
        },
        "tasks": {
            "active_tasks": int(tasks.get("active_tasks") or 0),
            "blocked_tasks": int(tasks.get("blocked_tasks") or 0),
        },
        "alerts": {
            "unacknowledged_critical_alerts": int(alerts.get("unacknowledged_critical_alerts") or 0),
        },
        "kpis": {"kpis": kpis},
        "zones": {"zones_near_capacity": zones_near_capacity},
    }