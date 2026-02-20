from pydantic import BaseModel
from typing import List, Optional


class ASNRow(BaseModel):
    id: str
    asn_number: str
    status: str
    supplier_name: str
    expected_date: Optional[str] = None
    actual_date: Optional[str] = None
    total_lines: int
    received_lines: int
    total_units: int
    received_units: int
    dock: Optional[str] = None
    po_number: Optional[str] = None
    is_overdue: bool


class InboundActivityResponse(BaseModel):
    count: int
    asns: List[ASNRow]


class OverdueASNResponse(BaseModel):
    count: int
    asns: List[ASNRow]


class InboundParams(BaseModel):
    date: Optional[str] = None
    supplier: Optional[str] = None
    status: Optional[str] = None
    only_overdue: bool = False
    limit: int = 25