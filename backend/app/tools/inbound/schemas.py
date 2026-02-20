from pydantic import BaseModel
from typing import List


class ASNRow(BaseModel):
    id: str
    asn_number: str
    status: str
    supplier_name: str
    expected_date: str | None = None
    actual_date: str | None = None
    total_lines: int
    received_lines: int
    total_units: int
    received_units: int
    dock: str | None = None
    po_number: str | None = None
    is_overdue: bool


class InboundActivityResponse(BaseModel):
    count: int
    asns: List[ASNRow]


class OverdueASNResponse(BaseModel):
    count: int
    asns: List[ASNRow]