from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, to_bool


def _normalize_asns(rows):
    for r in rows:
        r["is_overdue"] = to_bool(r.get("is_overdue"))
    return rows


def get_inbound_activity(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}

    limit = int(params.get("limit", 25))
    supplier = (params.get("supplier") or "").strip().lower()
    status = (params.get("status") or "").strip().lower()

    where = []
    sql_params = {"limit": limit}

    if supplier:
        where.append("LOWER(supplier_name) LIKE :supplier")
        sql_params["supplier"] = f"%{supplier}%"

    if status:
        where.append("LOWER(status) = :status")
        sql_params["status"] = status

    where_clause = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
    SELECT id, asn_number, status, supplier_name,
           expected_date, actual_date, total_lines,
           received_lines, total_units, received_units,
           dock, po_number, is_overdue
    FROM inbound_asns
    {where_clause}
    ORDER BY expected_date DESC
    LIMIT :limit
    """

    asns = _normalize_asns(fetch_all(db, sql, sql_params))
    return {"count": len(asns), "asns": asns}


def get_overdue_asns(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 25))

    sql = """
    SELECT id, asn_number, status, supplier_name,
           expected_date, actual_date, total_lines,
           received_lines, total_units, received_units,
           dock, po_number, is_overdue
    FROM inbound_asns
    WHERE is_overdue = 1
    ORDER BY expected_date ASC
    LIMIT :limit
    """

    asns = _normalize_asns(fetch_all(db, sql, {"limit": limit}))
    return {"count": len(asns), "asns": asns}