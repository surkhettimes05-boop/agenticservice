"""Implementation workflow for the coding department."""

from __future__ import annotations

from typing import Any


class ImplementationWorkflow:
    ORDERED_STEPS = [
        ("coding_team_leader", "Plan implementation and split work"),
        ("frontend_engineer", "Generate frontend experience"),
        ("backend_engineer", "Generate backend API"),
        ("database_engineer", "Create database schema and migrations"),
        ("api_integration_agent", "Connect external APIs and Supabase services"),
        ("refactoring_agent", "Refactor for clarity and maintainability"),
        ("code_review_agent", "Review risks, smells, and improvements"),
    ]

    def create(self, project_request: str) -> dict[str, Any]:
        return {
            "workflow": "coding_department_implementation",
            "project_request": project_request,
            "steps": [
                {
                    "step": index,
                    "agent_id": agent_id,
                    "action": action,
                    "depends_on": [] if index == 1 else [index - 1],
                }
                for index, (agent_id, action) in enumerate(self.ORDERED_STEPS, start=1)
            ],
        }
