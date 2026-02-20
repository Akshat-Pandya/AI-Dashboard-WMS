from pydantic import BaseModel
from typing import List, Optional


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


class OrdersByStatusParams(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    limit: int = 25


class StuckOrdersParams(BaseModel):
    reason: Optional[str] = None
    limit: int = 25