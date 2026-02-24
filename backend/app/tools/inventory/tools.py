from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from app.tools.common import fetch_all, fetch_one


def get_low_stock_items(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 50))

    sql = """
    SELECT id, sku, product_name, zone, location,
           quantity_on_hand, quantity_reserved, quantity_available,
           reorder_point, status, unit_of_measure, category
    FROM inventory_items
    WHERE quantity_available <= reorder_point
    ORDER BY quantity_available ASC
    LIMIT :limit
    """
    items = fetch_all(db, sql, {"limit": limit})
    return {
        "threshold_mode": "quantity_available <= reorder_point",
        "count": len(items),
        "items": items,
    }


def get_inventory_lookup(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    sku = params.get("sku", "").strip()
    zone = params.get("zone", "").strip()
    limit = int(params.get("limit", 100))

    where = []
    sql_params: Dict[str, Any] = {"limit": limit}
    if sku:
        where.append("sku LIKE :sku")
        sql_params["sku"] = f"%{sku}%"
    if zone:
        where.append("UPPER(zone) = UPPER(:zone)")
        sql_params["zone"] = zone

    where_clause = "WHERE " + " AND ".join(where) if where else ""
    sql = f"""
    SELECT id, sku, product_name, zone, location,
           quantity_on_hand, quantity_reserved, quantity_available,
           reorder_point, status, unit_of_measure, category, last_updated
    FROM inventory_items
    {where_clause}
    ORDER BY zone, product_name
    LIMIT :limit
    """
    items = fetch_all(db, sql, sql_params)
    return {"count": len(items), "items": items}


def compare_zones(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Aggregates inventory metrics per zone across ALL zones.
    No params required — works out of the box for any 'compare zones' query.
    """
    sql = """
    SELECT
        zone,
        COUNT(*)                                                                AS total_skus,
        COALESCE(SUM(quantity_on_hand), 0)                                      AS total_on_hand,
        COALESCE(SUM(quantity_available), 0)                                    AS total_available,
        COALESCE(SUM(quantity_reserved), 0)                                     AS total_reserved,
        COALESCE(SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END), 0)
                                                                                AS low_stock_skus,
        COALESCE(SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END), 0)   AS zero_stock_skus,
        COALESCE(ROUND(AVG(quantity_available), 1), 0)                          AS avg_available
    FROM inventory_items
    GROUP BY zone
    ORDER BY zone
    """
    zones = fetch_all(db, sql, {})

    return {
        "zone_count": len(zones),
        "zones": zones,
    }