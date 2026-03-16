from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.tools.common import fetch_all, fetch_one


def get_low_stock_items(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    limit  = int(params.get("limit", 50))

    zone:  str       = (params.get("zone") or "").strip()
    zones: List[str] = params.get("zones") or []

    where: List[str]           = ["quantity_available <= reorder_point"]
    sql_params: Dict[str, Any] = {"limit": limit}

    if zones:
        placeholders = ", ".join(f":z{i}" for i in range(len(zones)))
        where.append(f"UPPER(zone) IN ({placeholders})")
        for i, z in enumerate(zones):
            sql_params[f"z{i}"] = z.upper()
    elif zone:
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
        "zone_filter":    zones or zone or "all",
        "count":          len(items),
        "items":          items,
    }


def get_inventory_lookup(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Flexible inventory lookup — filters by any combination of:
      zone, zones, sku, category, location, status, limit.

    Query examples that now work:
      "show items in mechanical category"    → category="Mechanical"
      "list motors in zone B"               → category="Motors", zone="Zone B"
      "show available items"                → status="available"
      "find items at location A-01-03"      → location="A-01-03"
      "show bearings"                       → category="Bearings"
      "show reserved items in zone A"       → status="reserved", zone="Zone A"
    """
    params   = params or {}
    sku      = (params.get("sku")      or "").strip()
    zone     = (params.get("zone")     or "").strip()
    zones: List[str] = params.get("zones") or []
    category = (params.get("category") or "").strip()
    location = (params.get("location") or "").strip()
    status   = (params.get("status")   or "").strip().lower()
    limit    = int(params.get("limit", 100))

    where: List[str]           = []
    sql_params: Dict[str, Any] = {"limit": limit}

    # Zone filter — supports both single zone and multi-zone list
    if zones:
        placeholders = ", ".join(f":z{i}" for i in range(len(zones)))
        where.append(f"UPPER(zone) IN ({placeholders})")
        for i, z in enumerate(zones):
            sql_params[f"z{i}"] = z.upper()
    elif zone:
        where.append("UPPER(zone) = UPPER(:zone)")
        sql_params["zone"] = zone

    # SKU filter — partial match
    if sku:
        where.append("sku LIKE :sku")
        sql_params["sku"] = f"%{sku}%"

    # Category filter — case-insensitive exact match
    if category:
        where.append("UPPER(category) = UPPER(:category)")
        sql_params["category"] = category

    # Location filter — exact match
    if location:
        where.append("UPPER(location) = UPPER(:location)")
        sql_params["location"] = location

    # Status filter — available / reserved / damaged / quarantine
    if status:
        where.append("LOWER(status) = :status")
        sql_params["status"] = status

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

    # Build a human-readable description of what was filtered
    active_filters = {}
    if zones:        active_filters["zones"]    = zones
    elif zone:       active_filters["zone"]     = zone
    if category:     active_filters["category"] = category
    if sku:          active_filters["sku"]       = sku
    if location:     active_filters["location"] = location
    if status:       active_filters["status"]   = status

    return {
        "count":          len(items),
        "items":          items,
        "active_filters": active_filters or "none",
        # Keep zone_filter for backwards-compat with existing widgets
        "zone_filter":    zones or zone or "all",
    }


def compare_zones(db: Session, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Aggregates inventory metrics per zone.
    If params["zones"] is provided, filters to those zones only.
    Otherwise compares ALL zones.
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
        "zone_count":   len(zones_data),
        "zones_filter": zones or "all",
        "zones":        zones_data,
    }