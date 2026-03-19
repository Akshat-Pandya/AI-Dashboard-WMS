from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, to_bool


# Severity priority order — used for sorting when no severity filter applied
_SEVERITY_ORDER = {
    "critical": 1,
    "high":     2,
    "warning":  3,
    "medium":   4,
    "info":     5,
    "low":      6,
}


def get_alerts(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params     = params or {}
    severity   = (params.get("severity") or "").strip().lower()
    only_unack = params.get("only_unacknowledged", False)

    # Use a higher default limit when no severity filter is applied so general
    # queries like "show all alerts" or "what should I focus on" return
    # everything meaningful rather than an arbitrary slice.
    default_limit = 20 if severity else 100
    limit = int(params.get("limit", default_limit))

    where: list         = []
    sql_params: Dict[str, Any] = {"limit": limit}

    if severity:
        where.append("LOWER(severity) = :severity")
        sql_params["severity"] = severity

    if only_unack:
        where.append("acknowledged = 0")

    where_clause = "WHERE " + " AND ".join(where) if where else ""

    # When no severity filter, order by severity priority (critical first)
    # then by timestamp so the most urgent and recent appear first.
    # order_clause = (
    #     "ORDER BY timestamp DESC"
    #     if severity
    #     else "ORDER BY FIELD(LOWER(severity), 'critical','high','warning','medium','info','low'), timestamp DESC"
    # )

    order_clause = (
        "ORDER BY id DESC"
    )

    sql = f"""
    SELECT id, severity, title, message, category, timestamp, acknowledged, zone
    FROM warehouse_alerts
    {where_clause}
    {order_clause}
    LIMIT :limit
    """
    alerts = fetch_all(db, sql, sql_params)

    for a in alerts:
        a["acknowledged"] = to_bool(a.get("acknowledged"))

    # Build a severity breakdown so the summary LLM can describe the alerts
    # accurately without counting individual rows.
    breakdown: Dict[str, int] = {}
    for a in alerts:
        sev = (a.get("severity") or "unknown").lower()
        breakdown[sev] = breakdown.get(sev, 0) + 1

    return {
        "count":             len(alerts),
        "severity_filter":   severity or "all",
        "severity_breakdown": breakdown,   # e.g. {"critical": 2, "warning": 3}
        "alerts":            alerts,
    }