"""Compatibility wrapper for the enterprise BaseAgent."""

from __future__ import annotations

from dataclasses import dataclass

from custom_agents.agentic_it_firm.agents.base_agent import BaseAgent


@dataclass(frozen=True)
class AgentRunResult:
    agent_id: str
    agent_name: str
    role: str
    task: str
    output: str
    dry_run: bool


class BaseFirmAgent(BaseAgent):
    """Backward-compatible name for existing firm workflow code."""

    def run(self, task: str, context: dict | None = None) -> AgentRunResult:
        result = self.execute_task(task, context)
        return AgentRunResult(
            agent_id=self.id,
            agent_name=self.name,
            role=self.role,
            task=task,
            output=result.formatted_output,
            dry_run=self.dry_run,
        )
