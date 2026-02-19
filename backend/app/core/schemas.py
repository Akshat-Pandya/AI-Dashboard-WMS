from enum import Enum
from pydantic import BaseModel
from typing import Dict, Optional, Any, List

class Intent(str, Enum):
    WAREHOUSE_OVERVIEW = "warehouse_overview"
    LOW_STOCK = "low_stock"
    INVENTORY_LOOKUP = "inventory_lookup"
    ZONE_INVENTORY_COMPARE = "zone_inventory_compare"
    ORDER_STATUS = "order_status"
    ORDERS_STUCK = "orders_stuck"
    ACTIVE_TASKS = "active_tasks"
    BLOCKED_TASKS = "blocked_tasks"
    INBOUND_ACTIVITY = "inbound_activity"
    OVERDUE_ASN = "overdue_asn"
    WAREHOUSE_ALERTS = "warehouse_alerts"
    KPI_SUMMARY = "kpi_summary"
    UNKNOWN = "unknown"


class IntentRequest(BaseModel):
    query: str

class IntentResult(BaseModel):
    intent: Intent
    confidence: float = 0.0
    filters: Optional[Dict[str, Any]] = None

class WidgetResponse(BaseModel):
    type: str
    widget: Optional[str] = None
    data: Optional[Dict] = None
    summary: Optional[List[str]] = None
