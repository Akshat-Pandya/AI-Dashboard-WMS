from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all


def get_low_stock_items(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}

    limit = int(params.get("limit", 20))
    category = (params.get("category") or "").strip().lower()
    zone = (params.get("zone") or "").strip()

    where = ["quantity_available <= reorder_point"]
    sql_params = {"limit": limit}

    if category:
        where.append("LOWER(category) = :category")
        sql_params["category"] = category

    if zone:
        where.append("zone = :zone")
        sql_params["zone"] = zone

    where_clause = " AND ".join(where)

    sql = f"""
    SELECT id, sku, product_name, zone, location,
           quantity_on_hand, quantity_reserved,
           quantity_available, reorder_point,
           status, last_updated, unit_of_measure,
           weight, category
    FROM inventory_items
    WHERE {where_clause}
    ORDER BY (reorder_point - quantity_available) DESC
    LIMIT :limit
    """

    items = fetch_all(db, sql, sql_params)

    return {
        "threshold_mode": "reorder_point",
        "count": len(items),
        "items": items
    }


def get_inventory_by_zone(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    zones: List[str] = params.get("zones") or []

    if not zones:
        return {"zones": [], "summary": []}

    zone_params = {f"z{i}": z for i, z in enumerate(zones)}
    in_clause = ", ".join(f":z{i}" for i in range(len(zones)))

    sql = f"""
    SELECT zone,
           COUNT(*) AS total_skus,
           SUM(quantity_on_hand) AS total_on_hand,
           SUM(quantity_available) AS total_available,
           SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END) AS low_stock_skus,
           SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END) AS zero_stock_skus
    FROM inventory_items
    WHERE zone IN ({in_clause})
    GROUP BY zone
    ORDER BY zone
    """

    summary = fetch_all(db, sql, zone_params)
    return {"zones": zones, "summary": summary}