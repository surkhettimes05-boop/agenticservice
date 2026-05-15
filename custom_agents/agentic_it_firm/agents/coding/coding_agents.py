"""Specialized Coding Department agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent
from custom_agents.agentic_it_firm.agents.coding.architecture_planner import ArchitecturePlanner
from custom_agents.agentic_it_firm.agents.coding.code_review_pipeline import CodeReviewPipeline
from custom_agents.agentic_it_firm.agents.coding.implementation_workflow import ImplementationWorkflow
from custom_agents.agentic_it_firm.agents.coding.repository_context import RepositoryContextLoader


class CodingTeamLeaderAgent(BaseFirmAgent):
    def plan_implementation(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "department": "Coding",
            "architecture_plan": ArchitecturePlanner().plan(project_request),
            "implementation_workflow": ImplementationWorkflow().create(project_request),
        }


class FrontendEngineerAgent(BaseFirmAgent):
    def generate_frontend_plan(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "stack": ["Next.js", "React", "Tailwind"],
            "deliverables": ["responsive UI", "component structure", "state/data flow", "accessibility pass"],
            "project_request": project_request,
        }


class BackendEngineerAgent(BaseFirmAgent):
    def generate_backend_plan(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "stack": ["FastAPI", "Pydantic", "PostgreSQL"],
            "deliverables": ["API routes", "service layer", "validation", "error handling", "tests"],
            "project_request": project_request,
        }


class DatabaseEngineerAgent(BaseFirmAgent):
    def generate_schema_plan(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "stack": ["PostgreSQL", "Supabase"],
            "deliverables": ["schema", "indexes", "migration plan", "RLS/security notes"],
            "project_request": project_request,
        }


class APIIntegrationAgent(BaseFirmAgent):
    def generate_integration_plan(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "stack": ["FastAPI clients", "Supabase", "HTTP retries"],
            "deliverables": ["client wrappers", "auth handling", "retry policy", "observability"],
            "project_request": project_request,
        }


class RefactoringAgent(BaseFirmAgent):
    def generate_refactor_plan(self, project_request: str) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "quality_gates": ["single responsibility", "typed boundaries", "deduplicated helpers", "clear tests"],
            "project_request": project_request,
        }


class CodeReviewAgent(BaseFirmAgent):
    def review_repository(self, root: str | Path) -> dict[str, Any]:
        return CodeReviewPipeline().review(root)

    def generate_review_report(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "report_type": "code_review",
            "summary": review.get("summary", {}),
            "findings": review.get("findings", []),
            "suggested_improvements": review.get("recommendations", []),
        }


class RepositoryAwareMixin:
    def load_repository_context(self, root: str | Path):
        return RepositoryContextLoader(root).load()
