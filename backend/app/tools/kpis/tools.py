from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all, to_bool


def get_kpi_summary(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 10))
    category = (params.get("category") or "").strip().lower()

    where = ""
    sql_params: Dict[str, Any] = {"limit": limit}
    if category:
        where = "WHERE LOWER(category) = :category"
        sql_params["category"] = category

    sql = f"""
    SELECT
      id, label, value, previous_value, unit,
      trend, change_percent, category, target, is_on_target
    FROM warehouse_kpis
    {where}
    ORDER BY id ASC
    LIMIT :limit
    """
    kpis = fetch_all(db, sql, sql_params)
    for k in kpis:
        k["is_on_target"] = to_bool(k.get("is_on_target"))

    return {"count": len(kpis), "kpis": kpis}