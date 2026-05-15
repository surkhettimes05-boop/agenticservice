from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    prompt: str
    auto_approve: bool = True
    dry_run: bool | None = None


class TaskRunRead(BaseModel):
    id: int
    prompt: str
    status: str
    agent_id: str
    approval_requested: bool
    approval_approved: bool
    dry_run: bool
    output: str
    output_file: str
    created_at: datetime
    completed_at: datetime | None


class AgentRead(BaseModel):
    id: str
    name: str
    role: str
    department: str
    goal: str
