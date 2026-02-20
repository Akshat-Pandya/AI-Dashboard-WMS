from pydantic import BaseModel
from typing import List, Optional


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


class AlertsParams(BaseModel):
    severity: Optional[str] = None
    zone: Optional[str] = None
    only_unacknowledged: bool = False
    limit: int = 20