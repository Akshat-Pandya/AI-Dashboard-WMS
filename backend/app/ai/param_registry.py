from app.core.schemas import Intent

from app.tools.alerts.schemas import AlertsParams
from app.tools.inventory.schemas import LowStockParams, ZoneCompareParams
from app.tools.orders.schemas import OrdersByStatusParams, StuckOrdersParams
from app.tools.tasks.schemas import TaskParams
from app.tools.inbound.schemas import InboundParams
from app.tools.kpis.schemas import KPIParams
from app.tools.overview.schemas import OverviewParams

PARAM_REGISTRY = {
    Intent.WAREHOUSE_ALERTS: AlertsParams,
    Intent.LOW_STOCK: LowStockParams,
    Intent.ZONE_INVENTORY_COMPARE: ZoneCompareParams,
    Intent.ORDER_STATUS: OrdersByStatusParams,
    Intent.ORDERS_STUCK: StuckOrdersParams,
    Intent.ACTIVE_TASKS: TaskParams,
    Intent.BLOCKED_TASKS: TaskParams,
    Intent.INBOUND_ACTIVITY: InboundParams,
    Intent.OVERDUE_ASN: InboundParams,
    Intent.KPI_SUMMARY: KPIParams,
    Intent.WAREHOUSE_OVERVIEW: OverviewParams,
}