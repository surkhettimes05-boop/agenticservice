"""Coding Department agents and workflows."""

from .architecture_planner import ArchitecturePlanner
from .code_review_pipeline import CodeReviewPipeline
from .coding_agents import (
    APIIntegrationAgent,
    BackendEngineerAgent,
    CodeReviewAgent,
    CodingTeamLeaderAgent,
    DatabaseEngineerAgent,
    FrontendEngineerAgent,
    RefactoringAgent,
)
from .implementation_workflow import ImplementationWorkflow
from .repository_context import RepositoryContext, RepositoryContextLoader

CODING_AGENT_CLASSES = {
    "coding_team_leader": CodingTeamLeaderAgent,
    "frontend_engineer": FrontendEngineerAgent,
    "backend_engineer": BackendEngineerAgent,
    "database_engineer": DatabaseEngineerAgent,
    "api_integration_agent": APIIntegrationAgent,
    "refactoring_agent": RefactoringAgent,
    "code_review_agent": CodeReviewAgent,
}

__all__ = [
    "APIIntegrationAgent",
    "ArchitecturePlanner",
    "BackendEngineerAgent",
    "CODING_AGENT_CLASSES",
    "CodeReviewAgent",
    "CodeReviewPipeline",
    "CodingTeamLeaderAgent",
    "DatabaseEngineerAgent",
    "FrontendEngineerAgent",
    "ImplementationWorkflow",
    "RefactoringAgent",
    "RepositoryContext",
    "RepositoryContextLoader",
]
