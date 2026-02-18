from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, List


class Intent(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    INVENTORY = "INVENTORY"
    ORDERS = "ORDERS"
    TASKS = "TASKS"
    OVERVIEW = "OVERVIEW"
    UNKNOWN = "UNKNOWN"


class IntentRequest(BaseModel):
    query: str


class IntentResult(BaseModel):
    intent: Intent
    filters: Dict = {}


class WidgetResponse(BaseModel):
    type: str
    widget: Optional[str] = None
    data: Optional[Dict] = None
    summary: Optional[List[str]] = None
