from app.core.schemas import Intent

def keyword_fallback(query: str) -> Intent:
    q = query.lower()
    if "stock" in q:
        return Intent.LOW_STOCK
    if "inventory" in q:
        return Intent.INVENTORY
    if "order" in q:
        return Intent.ORDERS
    if "task" in q:
        return Intent.TASKS
    return Intent.UNKNOWN
