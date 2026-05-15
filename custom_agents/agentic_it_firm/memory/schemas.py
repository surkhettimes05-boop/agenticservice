"""Typed memory schemas for the Agentic IT Firm."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class MemoryScope(str, Enum):
    PROJECT = "project"
    AGENT = "agent"
    WORKFLOW = "workflow"
    CLIENT = "client"
    CONVERSATION = "conversation"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class RichMemoryRecord:
    memory_id: str
    scope: str
    text: str
    embedding: list[float]
    project_id: str | None = None
    agent_id: str | None = None
    workflow_id: str | None = None
    client_id: str | None = None
    conversation_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        scope: MemoryScope,
        text: str,
        embedding: list[float],
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "RichMemoryRecord":
        return cls(
            memory_id=f"mem_{uuid4().hex}",
            scope=scope.value,
            text=text,
            embedding=embedding,
            project_id=project_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            client_id=client_id,
            conversation_id=conversation_id,
            session_id=session_id,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "RichMemoryRecord":
        return cls(**item)


@dataclass(frozen=True)
class RetrievalResult:
    record: RichMemoryRecord
    score: float


@dataclass(frozen=True)
class WorkflowSession:
    session_id: str
    project_id: str | None
    client_id: str | None
    workflow_id: str | None
    status: str
    started_at: str
    updated_at: str
    steps: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def start(
        cls,
        project_id: str | None = None,
        client_id: str | None = None,
        workflow_id: str | None = None,
    ) -> "WorkflowSession":
        now = utc_now()
        return cls(
            session_id=f"session_{uuid4().hex}",
            project_id=project_id,
            client_id=client_id,
            workflow_id=workflow_id,
            status="running",
            started_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "WorkflowSession":
        return cls(**item)
