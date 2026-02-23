"""
registry.py
Maps every Intent enum value to the callable tool function that serves it.
Add a new intent here and it is automatically picked up by the orchestrator.
"""
from typing import Callable, Dict

from app.core.schemas import Intent

from app.tools.alerts.tools     import get_alerts
from app.tools.inventory.tools  import get_low_stock_items, get_inventory_by_zone
from app.tools.orders.tools     import get_orders_by_status, get_stuck_orders
from app.tools.tasks.tools      import get_active_tasks, get_blocked_tasks
from app.tools.inbound.tools    import get_inbound_activity, get_overdue_asns
from app.tools.kpis.tools       import get_kpi_summary
from app.tools.overview.tools   import get_warehouse_overview

# Each value is a callable: (db, params) -> Dict
INTENT_TOOL_MAP: Dict[Intent, Callable] = {
    Intent.WAREHOUSE_ALERTS:       get_alerts,
    Intent.LOW_STOCK:              get_low_stock_items,
    Intent.INVENTORY_LOOKUP:       get_inventory_by_zone,
    Intent.ZONE_INVENTORY_COMPARE: get_inventory_by_zone,
    Intent.ORDER_STATUS:           get_orders_by_status,
    Intent.ORDERS_STUCK:           get_stuck_orders,
    Intent.ACTIVE_TASKS:           get_active_tasks,
    Intent.BLOCKED_TASKS:          get_blocked_tasks,
    Intent.INBOUND_ACTIVITY:       get_inbound_activity,
    Intent.OVERDUE_ASN:            get_overdue_asns,
    Intent.KPI_SUMMARY:            get_kpi_summary,
    Intent.WAREHOUSE_OVERVIEW:     get_warehouse_overview,
}

# Stable key used in the data dict returned to the frontend
INTENT_DATA_KEY: Dict[Intent, str] = {
    Intent.WAREHOUSE_ALERTS:       "alerts",
    Intent.LOW_STOCK:              "low_stock",
    Intent.INVENTORY_LOOKUP:       "inventory",
    Intent.ZONE_INVENTORY_COMPARE: "zone_comparison",
    Intent.ORDER_STATUS:           "orders",
    Intent.ORDERS_STUCK:           "stuck_orders",
    Intent.ACTIVE_TASKS:           "active_tasks",
    Intent.BLOCKED_TASKS:          "blocked_tasks",
    Intent.INBOUND_ACTIVITY:       "inbound",
    Intent.OVERDUE_ASN:            "overdue_asn",
    Intent.KPI_SUMMARY:            "kpis",
    Intent.WAREHOUSE_OVERVIEW:     "overview",
}