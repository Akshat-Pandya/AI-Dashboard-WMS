from pydantic import BaseModel
from typing import List, Optional


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


class KPIParams(BaseModel):
    category: Optional[str] = None
    only_off_target: bool = False
    limit: int = 10