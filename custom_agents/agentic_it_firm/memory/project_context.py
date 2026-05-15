"""Project context loading from persistent memory."""

from __future__ import annotations

from custom_agents.agentic_it_firm.memory.memory_manager import MemoryManager
from custom_agents.agentic_it_firm.memory.schemas import MemoryScope, RichMemoryRecord


class ProjectContextLoader:
    """Build shared context packages for agents and workflows."""

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def load(self, project_id: str, query: str, limit: int = 10) -> dict:
        results = self.memory.retrieve(query=query, project_id=project_id, limit=limit)
        records = [result.record for result in results]
        return {
            "project_id": project_id,
            "memory_count": len(records),
            "context_text": "\n".join(f"- [{record.scope}] {record.text}" for record in records),
            "memories": [record.to_dict() for record in records],
        }


class AgentLearningHistory:
    """Read agent-specific learning history from memory."""

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def for_agent(self, agent_id: str, limit: int = 20) -> list[RichMemoryRecord]:
        return self.memory.list_records(agent_id=agent_id, scope=MemoryScope.AGENT)[:limit]
