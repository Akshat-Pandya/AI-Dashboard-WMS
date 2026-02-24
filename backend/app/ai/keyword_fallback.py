from app.core.schemas import Intent

def keyword_fallback(query: str) -> Intent:
    q = query.lower()

    if "low stock" in q or "replenish" in q:
        return Intent.LOW_STOCK
    if "inventory" in q and "zone" in q:
        return Intent.ZONE_INVENTORY_COMPARE
    if "order" in q and "stuck" in q:
        return Intent.ORDERS_STUCK
    if "task" in q and "blocked" in q:
        return Intent.BLOCKED_TASKS
    if "alert" in q or "problem" in q:
        return Intent.WAREHOUSE_ALERTS
    if "kpi" in q or "performance" in q:
        return Intent.KPI_SUMMARY

    return Intent.UNKNOWN