from pydantic import BaseModel
from typing import List


class AlertRow(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    category: str
    timestamp: str | None = None
    acknowledged: bool
    zone: str | None = None


class AlertsResponse(BaseModel):
    count: int
    alerts: List[AlertRow]