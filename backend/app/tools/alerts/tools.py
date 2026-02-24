from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, to_bool


def get_alerts(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 20))
    severity = (params.get("severity") or "").strip().lower()  # optional
    only_unack = params.get("only_unacknowledged", False)

    where = []
    sql_params: Dict[str, Any] = {"limit": limit}

    if severity:
        where.append("LOWER(severity) = :severity")
        sql_params["severity"] = severity

    if only_unack:
        where.append("acknowledged = 0")

    where_clause = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
    SELECT id, severity, title, message, category, timestamp, acknowledged, zone
    FROM warehouse_alerts
    {where_clause}
    ORDER BY timestamp DESC
    LIMIT :limit
    """
    alerts = fetch_all(db, sql, sql_params)
    for a in alerts:
        a["acknowledged"] = to_bool(a.get("acknowledged"))

    return {"count": len(alerts), "alerts": alerts}