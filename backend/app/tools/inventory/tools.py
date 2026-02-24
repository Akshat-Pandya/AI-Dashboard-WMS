from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.tools.common import fetch_all, fetch_one


def get_low_stock_items(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit = int(params.get("limit", 50))
    zone  = (params.get("zone") or "").strip()

    where = ["quantity_available <= reorder_point"]
    sql_params: Dict[str, Any] = {"limit": limit}

    if zone:
        where.append("UPPER(zone) = UPPER(:zone)")
        sql_params["zone"] = zone

    where_clause = "WHERE " + " AND ".join(where)
    sql = f"""
    SELECT id, sku, product_name, zone, location,
           quantity_on_hand, quantity_reserved, quantity_available,
           reorder_point, status, unit_of_measure, category
    FROM inventory_items
    {where_clause}
    ORDER BY quantity_available ASC
    LIMIT :limit
    """
    items = fetch_all(db, sql, sql_params)
    return {
        "threshold_mode": "quantity_available <= reorder_point",
        "count": len(items),
        "items": items,
    }


def get_inventory_lookup(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Single-zone or general inventory lookup.
    If params["zone"] is set, filters to that zone only.
    """
    params = params or {}
    sku   = params.get("sku", "").strip()
    zone  = params.get("zone", "").strip()
    limit = int(params.get("limit", 100))

    where: List[str] = []
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
    return {"count": len(items), "items": items, "zone_filter": zone or "all"}


def compare_zones(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Aggregates inventory metrics per zone.

    If params["zones"] is provided, filters to only those zones.
    Otherwise compares ALL zones (default behaviour for general compare queries).

    Examples:
      "compare zone A and B"  → params["zones"] = ["A", "B"] → filters to A, B
      "compare all zones"     → params["zones"] = []          → shows all zones
    """
    params = params or {}
    zones: List[str] = params.get("zones") or []

    where_clause = ""
    sql_params: Dict[str, Any] = {}

    if zones:
        placeholders = ", ".join(f":z{i}" for i in range(len(zones)))
        where_clause = f"WHERE UPPER(zone) IN ({placeholders})"
        sql_params   = {f"z{i}": z.upper() for i, z in enumerate(zones)}

    sql = f"""
    SELECT
        zone,
        COUNT(*)                                                                  AS total_skus,
        COALESCE(SUM(quantity_on_hand), 0)                                        AS total_on_hand,
        COALESCE(SUM(quantity_available), 0)                                      AS total_available,
        COALESCE(SUM(quantity_reserved), 0)                                       AS total_reserved,
        COALESCE(SUM(CASE WHEN quantity_available <= reorder_point THEN 1 ELSE 0 END), 0)
                                                                                  AS low_stock_skus,
        COALESCE(SUM(CASE WHEN quantity_available = 0 THEN 1 ELSE 0 END), 0)     AS zero_stock_skus,
        COALESCE(ROUND(AVG(quantity_available), 1), 0)                            AS avg_available
    FROM inventory_items
    {where_clause}
    GROUP BY zone
    ORDER BY zone
    """
    zones_data = fetch_all(db, sql, sql_params)
    return {
        "zone_count":    len(zones_data),
        "zones_filter":  zones or "all",
        "zones":         zones_data,
    }