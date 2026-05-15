from pathlib import Path

from custom_agents.agentic_it_firm.agents.coding import (
    APIIntegrationAgent,
    ArchitecturePlanner,
    BackendEngineerAgent,
    CodeReviewAgent,
    CodeReviewPipeline,
    CodingTeamLeaderAgent,
    DatabaseEngineerAgent,
    FrontendEngineerAgent,
    ImplementationWorkflow,
    RefactoringAgent,
    RepositoryContextLoader,
)
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition, FirmConfig, NvidiaConfig, RouteDefinition, SystemConfig
from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.llm_config import LLMResult, TokenUsage


class FakeModelManager:
    def agent_model_config(self, model=None):
        return {
            "model": model or "nvidia_nim/meta/llama3-70b-instruct",
            "api_key": "nvapi-test",
            "base_url": "https://integrate.api.nvidia.com/v1",
        }

    def complete(self, request):
        return LLMResult(
            content="Generated coding department output.",
            model="nvidia_nim/meta/llama3-70b-instruct",
            usage=TokenUsage(total_tokens=10),
            latency_ms=1,
            estimated_cost=None,
            attempts=1,
        )


def agent_definition(agent_id: str, name: str, role: str) -> AgentDefinition:
    return AgentDefinition(
        id=agent_id,
        name=name,
        role=role,
        department="Coding",
        expertise=["Next.js", "React", "Tailwind", "FastAPI", "PostgreSQL", "Supabase"],
        years_of_experience=8,
        goal=f"Handle {role} responsibilities.",
        instructions=f"You are the {role} for the coding department.",
        capabilities=["coding"],
        allowed_actions=["plan", "generate", "review", "refactor", "integrate"],
        restricted_actions=["delete", "deploy"],
        memory_enabled=True,
    )


def test_repository_context_loader_scans_project_files(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "page.tsx").write_text("export default function Page() { return <main>Hello</main> }", encoding="utf-8")
    (tmp_path / "api.py").write_text("from fastapi import FastAPI\napp = FastAPI()", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=skip", encoding="utf-8")

    context = RepositoryContextLoader(tmp_path).load()

    assert "app/page.tsx" in context.files
    assert "api.py" in context.files
    assert ".env" not in context.files
    assert "Next.js" in context.detected_stack
    assert "FastAPI" in context.detected_stack


def test_architecture_planner_prefers_requested_stack():
    planner = ArchitecturePlanner()

    plan = planner.plan("Build a SaaS dashboard with API and database")

    assert plan["preferred_stack"]["frontend"] == ["Next.js", "React", "Tailwind"]
    assert plan["preferred_stack"]["backend"] == ["FastAPI"]
    assert plan["preferred_stack"]["database"] == ["PostgreSQL", "Supabase"]
    assert plan["phases"]


def test_implementation_workflow_assigns_coding_agents():
    workflow = ImplementationWorkflow()

    plan = workflow.create("Build dashboard, backend API, database schema, integration, refactor and review")

    assert [step["agent_id"] for step in plan["steps"]] == [
        "coding_team_leader",
        "frontend_engineer",
        "backend_engineer",
        "database_engineer",
        "api_integration_agent",
        "refactoring_agent",
        "code_review_agent",
    ]


def test_code_review_pipeline_detects_smells_and_risks(tmp_path: Path):
    target = tmp_path / "service.py"
    target.write_text(
        "password='secret'\n"
        "def handler():\n"
        "    try:\n"
        "        eval('1+1')\n"
        "    except Exception:\n"
        "        pass\n",
        encoding="utf-8",
    )

    report = CodeReviewPipeline().review(tmp_path)

    assert report["summary"]["risk_count"] >= 2
    assert any("hardcoded secret" in item["message"] for item in report["findings"])
    assert any("eval" in item["message"] for item in report["findings"])
    assert report["recommendations"]


def test_coding_agents_use_base_agent_and_generate_structured_outputs():
    leader = CodingTeamLeaderAgent(agent_definition("coding_team_leader", "Coding Team Leader", "Coding Team Leader"), FakeModelManager(), dry_run=True)
    frontend = FrontendEngineerAgent(agent_definition("frontend_engineer", "Frontend Engineer", "Frontend Engineer"), FakeModelManager(), dry_run=True)
    backend = BackendEngineerAgent(agent_definition("backend_engineer", "Backend Engineer", "Backend Engineer"), FakeModelManager(), dry_run=True)
    database = DatabaseEngineerAgent(agent_definition("database_engineer", "Database Engineer", "Database Engineer"), FakeModelManager(), dry_run=True)
    integration = APIIntegrationAgent(agent_definition("api_integration_agent", "API Integration Agent", "API Integration Agent"), FakeModelManager(), dry_run=True)
    refactor = RefactoringAgent(agent_definition("refactoring_agent", "Refactoring Agent", "Refactoring Agent"), FakeModelManager(), dry_run=True)
    reviewer = CodeReviewAgent(agent_definition("code_review_agent", "Code Review Agent", "Code Review Agent"), FakeModelManager(), dry_run=True)

    assert leader.plan_implementation("Build app")["department"] == "Coding"
    assert "React" in frontend.generate_frontend_plan("Build UI")["stack"]
    assert "FastAPI" in backend.generate_backend_plan("Build API")["stack"]
    assert "PostgreSQL" in database.generate_schema_plan("Create schema")["stack"]
    assert integration.generate_integration_plan("Connect Supabase")["agent_id"] == "api_integration_agent"
    assert refactor.generate_refactor_plan("Clean services")["quality_gates"]
    assert reviewer.generate_review_report({"findings": [], "summary": {"risk_count": 0}})["agent_id"] == "code_review_agent"


def test_registry_instantiates_coding_specialists(tmp_path: Path):
    config = FirmConfig(
        system=SystemConfig(name="Agentic IT Firm", default_model="nvidia_nim/meta/llama3-70b-instruct"),
        agents=[
            agent_definition("coding_team_leader", "Coding Team Leader", "Coding Team Leader"),
            agent_definition("database_engineer", "Database Engineer", "Database Engineer"),
            agent_definition("api_integration_agent", "API Integration Agent", "API Integration Agent"),
            agent_definition("refactoring_agent", "Refactoring Agent", "Refactoring Agent"),
            agent_definition("code_review_agent", "Code Review Agent", "Code Review Agent"),
        ],
        routes=[RouteDefinition(keywords=["code"], agent_id="coding_team_leader")],
        nvidia=NvidiaConfig(api_key="nvapi-test"),
        root_dir=tmp_path,
    )

    registry = AgentRegistry.from_config(config, dry_run=True, model_manager=FakeModelManager())

    assert isinstance(registry.get("coding_team_leader"), CodingTeamLeaderAgent)
    assert isinstance(registry.get("database_engineer"), DatabaseEngineerAgent)
    assert isinstance(registry.get("api_integration_agent"), APIIntegrationAgent)
    assert isinstance(registry.get("refactoring_agent"), RefactoringAgent)
    assert isinstance(registry.get("code_review_agent"), CodeReviewAgent)
