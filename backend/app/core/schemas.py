from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ─────────────────────────────────────────────
# Intent enums & scoring
# ─────────────────────────────────────────────

class Intent(str, Enum):
    WAREHOUSE_OVERVIEW     = "warehouse_overview"
    LOW_STOCK              = "low_stock"
    INVENTORY_LOOKUP       = "inventory_lookup"
    ZONE_INVENTORY_COMPARE = "zone_inventory_compare"
    ORDER_STATUS           = "order_status"
    ORDERS_STUCK           = "orders_stuck"
    ACTIVE_TASKS           = "active_tasks"
    BLOCKED_TASKS          = "blocked_tasks"
    INBOUND_ACTIVITY       = "inbound_activity"
    OVERDUE_ASN            = "overdue_asn"
    WAREHOUSE_ALERTS       = "warehouse_alerts"
    KPI_SUMMARY            = "kpi_summary"
    UNKNOWN                = "unknown"


class IntentScore(BaseModel):
    intent: Intent
    confidence: float


class IntentResult(BaseModel):
    intents: List[IntentScore]


# ─────────────────────────────────────────────
# API request
# ─────────────────────────────────────────────

class IntentRequest(BaseModel):
    query: str


# ─────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────

class AlertRow(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    category: str
    timestamp: Optional[str] = None
    acknowledged: bool
    zone: Optional[str] = None


class AlertsResponse(BaseModel):
    count: int
    alerts: List[AlertRow]


# ─────────────────────────────────────────────
# Inbound / ASN
# ─────────────────────────────────────────────

class ASNRow(BaseModel):
    id: str
    asn_number: str
    status: str
    supplier_name: str
    expected_date: Optional[str] = None
    actual_date: Optional[str] = None
    total_lines: int
    received_lines: int
    total_units: int
    received_units: int
    dock: Optional[str] = None
    po_number: Optional[str] = None
    is_overdue: bool


class InboundActivityResponse(BaseModel):
    count: int
    asns: List[ASNRow]


class OverdueASNResponse(BaseModel):
    count: int
    asns: List[ASNRow]


# ─────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────

class InventoryItem(BaseModel):
    id: str
    sku: str
    product_name: str
    zone: str
    location: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    status: str
    last_updated: Optional[str] = None
    unit_of_measure: Optional[str] = None
    weight: Optional[float] = None
    category: Optional[str] = None


class LowStockResponse(BaseModel):
    threshold_mode: str
    count: int
    items: List[InventoryItem]


class ZoneInventorySummary(BaseModel):
    zone: str
    total_skus: int
    total_on_hand: int
    total_available: int
    low_stock_skus: int
    zero_stock_skus: int


class ZoneCompareResponse(BaseModel):
    zones: List[str]
    summary: List[ZoneInventorySummary]


# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────

class KPI(BaseModel):
    id: str
    label: str
    value: float
    previous_value: float
    unit: str
    trend: str
    change_percent: float
    category: str
    target: float
    is_on_target: bool


class KPISummaryResponse(BaseModel):
    count: int
    kpis: List[KPI]


# ─────────────────────────────────────────────
# Orders
# ─────────────────────────────────────────────

class OrderRow(BaseModel):
    id: str
    order_number: str
    status: str
    priority: str
    customer_name: str
    total_lines: int
    picked_lines: int
    packed_lines: int
    total_units: int
    created_at: Optional[str] = None
    due_date: Optional[str] = None
    wave_id: Optional[str] = None
    carrier: Optional[str] = None
    staging_zone: Optional[str] = None


class OrdersByStatusResponse(BaseModel):
    status: str
    count: int
    orders: List[OrderRow]


class StuckOrdersResponse(BaseModel):
    reason: str
    count: int
    orders: List[OrderRow]


# ─────────────────────────────────────────────
# Overview
# ─────────────────────────────────────────────

class WarehouseOverviewResponse(BaseModel):
    inventory: Dict
    orders: Dict
    tasks: Dict
    alerts: Dict
    kpis: Dict
    zones: Dict


# ─────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────

class TaskRow(BaseModel):
    id: str
    task_type: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assignee_name: Optional[str] = None
    zone: Optional[str] = None
    source_location: Optional[str] = None
    destination_location: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_minutes: Optional[int] = None
    is_blocked: bool
    block_reason: Optional[str] = None


class ActiveTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]


class BlockedTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]


# ─────────────────────────────────────────────
# Orchestrator / Summary LLM
# ─────────────────────────────────────────────

class WidgetConfig(BaseModel):
    type: str                               # e.g. "ALERT_LIST", "TABLE", "BAR_CHART"
    title: str
    data_key: str                           # dot-path into data dict, e.g. "alerts.alerts"
    props: Optional[Dict[str, Any]] = None  # optional renderer hints


class SummaryResponse(BaseModel):
    summary: str
    widgets: List[WidgetConfig]


# ─────────────────────────────────────────────
# Final /query API response
# ─────────────────────────────────────────────

class QueryResponse(BaseModel):
    query: str
    summary: str
    widgets: List[WidgetConfig]
    data: Dict[str, Any]


# ─────────────────────────────────────────────
# Legacy (kept for compatibility)
# ─────────────────────────────────────────────

class WidgetResponse(BaseModel):
    type: str
    widget: Optional[str] = None
    data: Optional[Dict] = None
    summary: Optional[List[str]] = None