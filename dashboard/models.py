from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TaskRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    status: str
    agent_id: str
    approval_requested: bool = False
    approval_approved: bool = False
    dry_run: bool = True
    output: str = ""
    output_file: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class AgentSnapshot(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    role: str
    department: str
    goal: str
    updated_at: datetime = Field(default_factory=utc_now)
