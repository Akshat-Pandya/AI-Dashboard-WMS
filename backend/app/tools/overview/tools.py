from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, fetch_one


def get_warehouse_overview(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    inv = fetch_one(db, """
    SELECT COUNT(*) AS total_skus,
           SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END) AS low_stock_items,
           SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END) AS zero_stock_items
    FROM inventory_items
    """)

    orders = fetch_all(db, """
    SELECT LOWER(status) AS status, COUNT(*) AS count
    FROM outbound_orders
    GROUP BY LOWER(status)
    """)

    tasks = fetch_one(db, """
    SELECT SUM(CASE WHEN LOWER(status) IN ('queued','in-progress') THEN 1 ELSE 0 END) AS active_tasks,
           SUM(CASE WHEN is_blocked = 1 THEN 1 ELSE 0 END) AS blocked_tasks
    FROM warehouse_tasks
    """)

    alerts = fetch_one(db, """
    SELECT COUNT(*) AS unack_critical
    FROM warehouse_alerts
    WHERE acknowledged = 0 AND LOWER(severity) = 'critical'
    """)

    kpis = fetch_all(db, """
    SELECT label, value, trend, is_on_target
    FROM warehouse_kpis
    ORDER BY id ASC
    LIMIT 6
    """)

    zones = fetch_all(db, """
    SELECT zone_name
    FROM zone_utilization
    WHERE utilization_percent >= 85
    """)

    return {
        "inventory": dict(inv),
        "orders": {o["status"]: o["count"] for o in orders},
        "tasks": dict(tasks),
        "alerts": {"critical_unacknowledged": alerts["unack_critical"]},
        "kpis": {"kpis": kpis},
        "zones": {"near_capacity": [z["zone_name"] for z in zones]}
    }