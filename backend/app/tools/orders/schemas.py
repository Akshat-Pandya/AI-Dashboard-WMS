from pydantic import BaseModel
from typing import Dict, List, Optional


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
    created_at: str | None = None
    due_date: str | None = None
    wave_id: str | None = None
    carrier: str | None = None
    staging_zone: str | None = None


class OrdersByStatusResponse(BaseModel):
    status: str
    count: int
    orders: List[OrderRow]


class StuckOrdersResponse(BaseModel):
    reason: str
    count: int
    orders: List[OrderRow]