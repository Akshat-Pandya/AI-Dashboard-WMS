from pydantic import BaseModel
from typing import List, Optional


class TaskRow(BaseModel):
    id: str
    task_type: str
    status: str
    priority: str
    assigned_to: str | None = None
    assignee_name: str | None = None
    zone: str | None = None
    source_location: str | None = None
    destination_location: str | None = None
    reference_id: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    estimated_minutes: int | None = None
    is_blocked: bool
    block_reason: str | None = None


class ActiveTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]


class BlockedTasksResponse(BaseModel):
    count: int
    tasks: List[TaskRow]