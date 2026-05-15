"""Task routing for the agentic IT firm."""

from __future__ import annotations

from dataclasses import dataclass

from custom_agents.agentic_it_firm.configs.loader import RouteDefinition


@dataclass(frozen=True)
class RouteDecision:
    agent_id: str
    matched_keyword: str | None
    requires_approval: bool
    approval_reason: str


class TaskRouter:
    def __init__(self, routes: list[RouteDefinition], approval_required_for: list[str]):
        self.routes = routes
        self.approval_required_for = [item.lower() for item in approval_required_for]

    def route(self, task: str) -> RouteDecision:
        task_lower = task.lower()
        matched_keyword = None
        agent_id = self.routes[0].agent_id if self.routes else ""
        for route in self.routes:
            for keyword in sorted(route.keywords, key=len, reverse=True):
                if keyword.lower() in task_lower:
                    return RouteDecision(
                        agent_id=route.agent_id,
                        matched_keyword=keyword,
                        requires_approval=self._requires_approval(task_lower),
                        approval_reason=self._approval_reason(task_lower),
                    )

        return RouteDecision(
            agent_id=agent_id,
            matched_keyword=matched_keyword,
            requires_approval=self._requires_approval(task_lower),
            approval_reason=self._approval_reason(task_lower),
        )

    def _requires_approval(self, task_lower: str) -> bool:
        return any(term in task_lower for term in self.approval_required_for)

    def _approval_reason(self, task_lower: str) -> str:
        for term in self.approval_required_for:
            if term in task_lower:
                return f"task contains approval-controlled term '{term}'"
        return "approval policy did not match"
