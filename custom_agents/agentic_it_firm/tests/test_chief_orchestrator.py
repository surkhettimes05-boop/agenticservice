import json
import logging
from pathlib import Path

from custom_agents.agentic_it_firm.agents.orchestrator.chief_orchestrator import (
    ChiefOrchestratorAgent,
    ExecutionStateTracker,
    InterAgentMessage,
    OrchestratorTask,
    PriorityTaskQueue,
    ProjectContextMemory,
    RoutingEngine,
    WorkflowPlanner,
)
from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.configs.loader import FirmConfig, NvidiaConfig, SystemConfig
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition, RouteDefinition
from custom_agents.agentic_it_firm.llm_config import LLMResult, TokenUsage
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory


class FakeModelManager:
    def agent_model_config(self, model=None):
        return {
            "model": model or "nvidia_nim/meta/llama3-70b-instruct",
            "api_key": "nvapi-test",
            "base_url": "https://integrate.api.nvidia.com/v1",
        }

    def complete(self, request):
        return LLMResult(
            content='{"executive_summary":"Plan generated"}',
            model=request.model or "nvidia_nim/meta/llama3-70b-instruct",
            usage=TokenUsage(total_tokens=12),
            latency_ms=10.0,
            estimated_cost=None,
            attempts=1,
        )


def orchestrator_definition():
    return AgentDefinition(
        id="chief_orchestrator",
        name="Chief Orchestrator",
        role="AI COO / Executive Orchestrator",
        department="Executive Operations",
        expertise=[
            "operations management",
            "technical leadership",
            "workflow orchestration",
            "project routing",
            "multi-agent coordination",
        ],
        years_of_experience=10,
        goal="Receive project requests, break them into workflows, and coordinate execution.",
        instructions="Produce JSON structured execution plans and escalate human approvals.",
        capabilities=["orchestration", "planning", "routing", "coordination"],
        allowed_actions=["plan", "route", "coordinate", "track", "escalate"],
        restricted_actions=["deploy", "delete", "bill"],
        escalation_rules=["Escalate approval-controlled tasks to human decision makers."],
        approval_rules=["Require approval for production, billing, secrets, deployment, and external messages."],
        memory_enabled=True,
        reviewer_agent="project_manager",
        reporting_agent="human_owner",
    )


def routes():
    return [
        RouteDefinition(keywords=["requirement", "user story"], agent_id="business_analyst"),
        RouteDefinition(keywords=["architecture", "database"], agent_id="solution_architect"),
        RouteDefinition(keywords=["backend", "api"], agent_id="backend_engineer"),
        RouteDefinition(keywords=["frontend", "dashboard"], agent_id="frontend_engineer"),
        RouteDefinition(keywords=["test", "qa"], agent_id="qa_engineer"),
        RouteDefinition(keywords=["deploy", "production"], agent_id="devops_engineer"),
        RouteDefinition(keywords=["security", "secret"], agent_id="security_reviewer"),
        RouteDefinition(keywords=["documentation", "readme"], agent_id="documentation_specialist"),
    ]


def test_workflow_planner_outputs_json_execution_plan():
    planner = WorkflowPlanner()

    plan = planner.create_plan(
        project_request="Build a secure client portal with dashboard, API, tests, and deployment plan",
        routed_tasks=[
            OrchestratorTask(
                task_id="task-001",
                title="Define client portal requirements",
                description="Gather requirements",
                department="Analysis",
                agent_id="business_analyst",
                priority="high",
            )
        ],
        approvals=["Deployment approval required"],
    )

    encoded = json.dumps(plan)
    decoded = json.loads(encoded)
    assert decoded["output_format"] == "json_structured_execution_plan"
    assert decoded["executive_summary"]
    assert decoded["workflows"][0]["tasks"][0]["agent_id"] == "business_analyst"


def test_routing_engine_assigns_departments_priorities_dependencies_and_approvals():
    engine = RoutingEngine(routes(), approval_required_for=["deploy", "production", "secret"])

    tasks = engine.route_project("Build frontend dashboard, backend API, security review, tests, and deploy to production")

    assert [task.agent_id for task in tasks] == [
        "backend_engineer",
        "frontend_engineer",
        "qa_engineer",
        "devops_engineer",
        "security_reviewer",
    ]
    assert tasks[0].priority == "high"
    assert tasks[-1].requires_approval is True
    assert tasks[2].dependencies


def test_priority_queue_orders_critical_high_medium_low():
    queue = PriorityTaskQueue()
    queue.add(OrchestratorTask("low", "Low", "Low", "Ops", "project_manager", "low"))
    queue.add(OrchestratorTask("critical", "Critical", "Critical", "Security", "security_reviewer", "critical"))
    queue.add(OrchestratorTask("high", "High", "High", "Engineering", "backend_engineer", "high"))

    assert [task.task_id for task in queue.pop_all()] == ["critical", "high", "low"]


def test_state_tracker_tracks_dependencies_and_messages():
    tracker = ExecutionStateTracker()
    first = OrchestratorTask("task-001", "Requirements", "Define scope", "Analysis", "business_analyst", "high")
    second = OrchestratorTask(
        "task-002",
        "Architecture",
        "Design system",
        "Architecture",
        "solution_architect",
        "high",
        dependencies=["task-001"],
    )

    tracker.register_tasks([first, second])
    tracker.mark_started("task-001")
    tracker.mark_completed("task-001")
    tracker.add_message(InterAgentMessage("chief_orchestrator", "solution_architect", "task-002", "Requirements ready"))

    assert tracker.ready_tasks()[0].task_id == "task-002"
    assert tracker.state["task-001"].status == "completed"
    assert tracker.messages[0].recipient_agent_id == "solution_architect"


def test_project_context_memory_persists_plan_context(tmp_path: Path):
    shared = SharedMemory(tmp_path / "shared_memory.jsonl")
    context_memory = ProjectContextMemory(shared)

    context_memory.save_project_context("project-001", "Build portal", {"status": "planned"})

    contents = shared.path.read_text(encoding="utf-8")
    assert "project_context" in contents
    assert "project-001" in contents


def test_chief_orchestrator_generates_structured_plan_and_saves_memory(tmp_path: Path):
    memory = SharedMemory(tmp_path / "shared_memory.jsonl")
    agent = ChiefOrchestratorAgent(
        definition=orchestrator_definition(),
        model_manager=FakeModelManager(),
        routes=routes(),
        approval_required_for=["deploy", "production", "secret"],
        dry_run=True,
        memory=memory,
        logger=logging.getLogger("test_chief_orchestrator"),
    )

    result = agent.create_execution_plan(
        "Build a secure client portal with frontend dashboard, backend API, tests, and deploy to production"
    )

    assert result["chief_orchestrator"]["role"] == "AI COO / Executive Orchestrator"
    assert result["approval_escalations"]
    assert result["task_queue"][0]["priority"] in {"critical", "high"}
    assert result["execution_state"]["tasks"]
    assert "json_structured_execution_plan" in json.dumps(result)
    assert "chief_orchestrator_plan" in memory.path.read_text(encoding="utf-8")


def test_registry_instantiates_chief_orchestrator_for_configured_agent(tmp_path: Path):
    config = FirmConfig(
        system=SystemConfig(
            name="Agentic IT Firm",
            default_model="nvidia_nim/meta/llama3-70b-instruct",
            approval_required_for=["deploy"],
        ),
        agents=[orchestrator_definition()],
        routes=routes(),
        nvidia=NvidiaConfig(api_key="nvapi-test"),
        root_dir=tmp_path,
    )

    registry = AgentRegistry.from_config(config, dry_run=True, model_manager=FakeModelManager())

    assert isinstance(registry.get("chief_orchestrator"), ChiefOrchestratorAgent)
