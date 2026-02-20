from pydantic import BaseModel
from typing import Dict, List


class WarehouseOverviewResponse(BaseModel):
    inventory: Dict
    orders: Dict
    tasks: Dict
    alerts: Dict
    kpis: Dict
    zones: Dict