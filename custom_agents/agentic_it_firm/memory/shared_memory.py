"""Simple durable shared memory for cross-agent coordination."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from custom_agents.agentic_it_firm.memory.memory_manager import MemoryManager
from custom_agents.agentic_it_firm.memory.schemas import MemoryScope


@dataclass(frozen=True)
class MemoryRecord:
    timestamp: str
    event_type: str
    agent_id: str | None
    task: str
    data: dict[str, Any]


class SharedMemory:
    def __init__(self, path: str | Path, semantic_memory: MemoryManager | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.semantic_memory = semantic_memory

    def add(self, event_type: str, task: str, data: dict[str, Any], agent_id: str | None = None) -> MemoryRecord:
        record = MemoryRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            agent_id=agent_id,
            task=task,
            data=data,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=True) + "\n")
        if self.semantic_memory is not None:
            self.semantic_memory.remember(
                scope=MemoryScope.AGENT if agent_id else MemoryScope.WORKFLOW,
                text=self._semantic_text(record),
                project_id=data.get("project_id"),
                agent_id=agent_id,
                workflow_id=data.get("workflow_id"),
                client_id=data.get("client_id"),
                conversation_id=data.get("conversation_id"),
                session_id=data.get("session_id"),
                metadata={"event_type": event_type, **data},
            )
        return record

    def recent(self, limit: int = 20) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        rows = self.path.read_text(encoding="utf-8").splitlines()
        records = []
        for row in rows[-limit:]:
            if row.strip():
                item = json.loads(row)
                records.append(MemoryRecord(**item))
        return records

    @staticmethod
    def _semantic_text(record: MemoryRecord) -> str:
        summary = record.data.get("summary") or record.data.get("status") or ""
        return f"{record.event_type}: {record.task}. {summary}".strip()
