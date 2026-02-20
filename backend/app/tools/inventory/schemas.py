from pydantic import BaseModel
from typing import List, Dict, Optional


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
    last_updated: str | None = None
    unit_of_measure: str | None = None
    weight: float | None = None
    category: str | None = None


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