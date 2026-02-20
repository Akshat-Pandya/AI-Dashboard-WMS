from pydantic import BaseModel
from typing import List, Optional


class TaskRow(BaseModel):
    id: str
    task_type: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assignee_name: Optional[str] = None
    zone: Optional[str] = None
    source_location: Optional[str] = None
    destination_location: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_minutes: Optional[int] = None
    is_blocked: bool
    block_reason: Optional[str] = None


class ActiveTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]


class BlockedTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]


class TaskParams(BaseModel):
    status: Optional[str] = None
    zone: Optional[str] = None
    only_blocked: bool = False
    assignee: Optional[str] = None
    limit: int = 30