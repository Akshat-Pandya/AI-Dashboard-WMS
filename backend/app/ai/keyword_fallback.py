# app/ai/keyword_fallback.py

from app.core.schemas import Intent

KEYWORD_MAP = [
    # (keywords_any_of, intent)
    (["low stock", "replenish", "reorder", "out of stock", "stockout", "below threshold"],   Intent.LOW_STOCK),
    (["compare zone", "zone vs", "zone a vs", "zone b vs", "compare all zones",
      "compare zones", "zone comparison", "zones side by side"],                              Intent.ZONE_INVENTORY_COMPARE),
    (["inventory", "zone a", "zone b", "zone c", "zone d",
      "sku", "product", "item", "stock level", "on hand", "available qty", "how much"],      Intent.INVENTORY_LOOKUP),
    (["stuck order", "delayed order", "order hold", "order not moving", "blocked order"],     Intent.ORDERS_STUCK),
    (["order status", "order progress", "fulfillment", "shipped", "pending order"],           Intent.ORDER_STATUS),
    (["picking task", "packing task", "putaway", "active task",
      "ongoing task", "in progress task"],                                                    Intent.ACTIVE_TASKS),
    (["blocked task", "task waiting", "task error", "cannot proceed"],                        Intent.BLOCKED_TASKS),
    (["inbound", "receiving", "asn", "shipment arriving", "dock", "supplier ship"],           Intent.INBOUND_ACTIVITY),
    (["overdue asn", "late shipment", "past due", "delayed asn", "supplier late"],            Intent.OVERDUE_ASN),
    (["alert", "warning", "critical", "issue", "problem", "error", "notification"],           Intent.WAREHOUSE_ALERTS),
    (["kpi", "performance", "efficiency", "throughput", "fill rate", "sla", "metric"],        Intent.KPI_SUMMARY),
    (["overview", "dashboard", "summary", "warehouse health", "overall", "status"],           Intent.WAREHOUSE_OVERVIEW),
]

def keyword_fallback(query: str) -> list[Intent]:
    """
    Returns a list of matched intents based on keyword matching.

    Called by the orchestrator when the intent LLM returns UNKNOWN.
    Provides a fast, deterministic safety net before falling through
    to the free-SQL path.

    Default return changed from Intent.UNKNOWN → Intent.UNSUPPORTED_WAREHOUSE
    so the orchestrator can correctly route to free-SQL (warehouse-related
    but no mapped tool) vs early rejection (truly irrelevant).

    Intent.UNKNOWN is no longer returned here — if no keywords match,
    the query is still assumed to be warehouse-related (since it passed
    the orchestrator's irrelevant_query early-exit check first).
    """
    q = query.lower()
    matched = []
    for keywords, intent in KEYWORD_MAP:
        if any(kw in q for kw in keywords):
            matched.append(intent)

    # CHANGED: was Intent.UNKNOWN — now Intent.UNSUPPORTED_WAREHOUSE
    # Rationale: if keyword fallback also fails, the orchestrator will
    # run the warehouse-term guard and route to free-SQL if appropriate.
    # Returning UNKNOWN here used to bypass that logic incorrectly.
    return matched if matched else [Intent.UNSUPPORTED_WAREHOUSE]