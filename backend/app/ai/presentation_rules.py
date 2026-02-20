from app.core.schemas import Intent

INTENT_WIDGETS = {
    Intent.WAREHOUSE_OVERVIEW: ["KPI_CARD", "ALERT_BANNER"],
    Intent.LOW_STOCK: ["TABLE", "BAR_CHART"],
    Intent.ZONE_INVENTORY_COMPARE: ["BAR_CHART"],
    Intent.ORDER_STATUS: ["TABLE"],
    Intent.ORDERS_STUCK: ["TABLE"],
    Intent.ACTIVE_TASKS: ["TABLE"],
    Intent.BLOCKED_TASKS: ["TABLE"],
    Intent.INBOUND_ACTIVITY: ["TABLE"],
    Intent.OVERDUE_ASN: ["TABLE"],
    Intent.WAREHOUSE_ALERTS: ["ALERT_BANNER"],
    Intent.KPI_SUMMARY: ["KPI_CARD"],
}