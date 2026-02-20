from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.tools.common import fetch_all


def get_low_stock_items(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 20))

    sql = """
    SELECT
      id, sku, product_name, zone, location,
      quantity_on_hand, quantity_reserved, quantity_available,
      reorder_point, status, last_updated, unit_of_measure, weight, category
    FROM inventory_items
    WHERE quantity_available <= reorder_point
    ORDER BY (reorder_point - quantity_available) DESC
    LIMIT :limit
    """
    items = fetch_all(db, sql, {"limit": limit})

    return {
        "threshold_mode": "quantity_available <= reorder_point",
        "count": len(items),
        "items": items,
    }


def get_inventory_by_zone(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    zones: List[str] = params.get("zones") or []
    if not zones:
        return {"zones": [], "summary": []}

    zone_params = {f"z{i}": z for i, z in enumerate(zones)}
    in_clause = ", ".join([f":z{i}" for i in range(len(zones))])

    sql = f"""
    SELECT
      zone AS zone,
      COUNT(*) AS total_skus,
      COALESCE(SUM(quantity_on_hand), 0) AS total_on_hand,
      COALESCE(SUM(quantity_available), 0) AS total_available,
      COALESCE(SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END), 0) AS low_stock_skus,
      COALESCE(SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END), 0) AS zero_stock_skus
    FROM inventory_items
    WHERE zone IN ({in_clause})
    GROUP BY zone
    ORDER BY zone
    """
    summary = fetch_all(db, sql, zone_params)

    return {"zones": zones, "summary": summary}