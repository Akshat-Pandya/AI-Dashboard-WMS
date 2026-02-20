from pydantic import BaseModel
from typing import List, Optional


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


class LowStockParams(BaseModel):
    threshold_mode: str = "reorder_point"
    zone: Optional[str] = None
    category: Optional[str] = None
    limit: int = 20


class ZoneCompareParams(BaseModel):
    zones: List[str]