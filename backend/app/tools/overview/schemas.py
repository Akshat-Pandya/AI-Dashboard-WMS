from pydantic import BaseModel
from typing import Dict


class WarehouseOverviewResponse(BaseModel):
    inventory: Dict
    orders: Dict
    tasks: Dict
    alerts: Dict
    kpis: Dict
    zones: Dict


class OverviewParams(BaseModel):
    include_inventory: bool = True
    include_orders: bool = True
    include_tasks: bool = True
    include_alerts: bool = True
    include_kpis: bool = True
    include_zones: bool = True