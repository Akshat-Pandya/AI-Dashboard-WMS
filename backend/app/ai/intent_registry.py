# app/ai/intent_registry.py
from app.core.schemas import Intent

from app.tools.inventory.tools import get_low_stock_items, get_inventory_by_zone
from app.tools.orders.tools import get_orders_by_status, get_stuck_orders
from app.tools.tasks.tools import get_active_tasks, get_blocked_tasks
from app.tools.inbound.tools import get_inbound_activity, get_overdue_asns
from app.tools.alerts.tools import get_alerts
from app.tools.kpis.tools import get_kpi_summary
from app.tools.overview.tools import get_warehouse_overview


INTENT_REGISTRY = {
    Intent.WAREHOUSE_OVERVIEW: [get_warehouse_overview],
    Intent.LOW_STOCK: [get_low_stock_items],
    Intent.ZONE_INVENTORY_COMPARE: [get_inventory_by_zone],
    Intent.ORDER_STATUS: [get_orders_by_status],
    Intent.ORDERS_STUCK: [get_stuck_orders],
    Intent.ACTIVE_TASKS: [get_active_tasks],
    Intent.BLOCKED_TASKS: [get_blocked_tasks],
    Intent.INBOUND_ACTIVITY: [get_inbound_activity],
    Intent.OVERDUE_ASN: [get_overdue_asns],
    Intent.WAREHOUSE_ALERTS: [get_alerts],
    Intent.KPI_SUMMARY: [get_kpi_summary],
}