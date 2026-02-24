from app.core.schemas import Intent

KEYWORD_MAP = [
    # (keywords_any_of, intent)
    (["low stock", "replenish", "reorder", "out of stock", "stockout", "below threshold"], Intent.LOW_STOCK),
    (["inventory", "zone", "compare zone", "zone a", "zone b", "zone vs"], Intent.ZONE_INVENTORY_COMPARE),
    (["sku", "product", "item", "stock level", "on hand", "available qty", "how much"], Intent.INVENTORY_LOOKUP),
    (["stuck order", "delayed order", "order hold", "order not moving", "blocked order"], Intent.ORDERS_STUCK),
    (["order status", "order progress", "fulfillment", "shipped", "pending order"], Intent.ORDER_STATUS),
    (["picking task", "packing task", "putaway", "active task", "ongoing task", "in progress task"], Intent.ACTIVE_TASKS),
    (["blocked task", "task waiting", "task error", "cannot proceed"], Intent.BLOCKED_TASKS),
    (["inbound", "receiving", "asn", "shipment arriving", "dock", "supplier ship"], Intent.INBOUND_ACTIVITY),
    (["overdue asn", "late shipment", "past due", "delayed asn", "supplier late"], Intent.OVERDUE_ASN),
    (["alert", "warning", "critical", "issue", "problem", "error", "notification"], Intent.WAREHOUSE_ALERTS),
    (["kpi", "performance", "efficiency", "throughput", "fill rate", "sla", "metric"], Intent.KPI_SUMMARY),
    (["overview", "dashboard", "summary", "warehouse health", "overall", "status"], Intent.WAREHOUSE_OVERVIEW),
]

def keyword_fallback(query: str) -> list[Intent]:
    """Returns a list of matched intents (not just one)."""
    q = query.lower()
    matched = []
    for keywords, intent in KEYWORD_MAP:
        if any(kw in q for kw in keywords):
            matched.append(intent)
    return matched if matched else [Intent.UNKNOWN]