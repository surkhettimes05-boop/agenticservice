"""Chief Orchestrator Agent for the Agentic IT Firm OS."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from custom_agents.agentic_it_firm.agents.base_agent import BaseAgent
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition, RouteDefinition
from custom_agents.agentic_it_firm.llm_config import ModelManager
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory


PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(frozen=True)
class OrchestratorTask:
    task_id: str
    title: str
    description: str
    department: str
    agent_id: str
    priority: str
    dependencies: list[str] = field(default_factory=list)
    requires_approval: bool = False
    approval_reason: str | None = None
    status: str = "queued"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterAgentMessage:
    sender_agent_id: str
    recipient_agent_id: str
    task_id: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskState:
    task: OrchestratorTask
    status: str = "queued"
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = self.task.to_dict()
        data.update(
            {
                "status": self.status,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
            }
        )
        return data


class PriorityTaskQueue:
    """Small deterministic priority queue for orchestrator tasks."""

    def __init__(self) -> None:
        self._items: deque[OrchestratorTask] = deque()

    def add(self, task: OrchestratorTask) -> None:
        self._items.append(task)
        self._items = deque(
            sorted(
                self._items,
                key=lambda item: (PRIORITY_RANK.get(item.priority, 2), item.task_id),
            )
        )

    def add_many(self, tasks: list[OrchestratorTask]) -> None:
        for task in tasks:
            self.add(task)

    def pop_all(self) -> list[OrchestratorTask]:
        tasks = list(self._items)
        self._items.clear()
        return tasks

    def to_list(self) -> list[dict[str, Any]]:
        return [task.to_dict() for task in self._items]


class ExecutionStateTracker:
    """Tracks queued, running, completed, blocked tasks and agent messages."""

    def __init__(self) -> None:
        self.state: dict[str, TaskState] = {}
        self.messages: list[InterAgentMessage] = []

    def register_tasks(self, tasks: list[OrchestratorTask]) -> None:
        for task in tasks:
            self.state[task.task_id] = TaskState(task=task)

    def mark_started(self, task_id: str) -> None:
        record = self.state[task_id]
        record.status = "in_progress"
        record.started_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self, task_id: str) -> None:
        record = self.state[task_id]
        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_blocked(self, task_id: str) -> None:
        self.state[task_id].status = "blocked"

    def ready_tasks(self) -> list[OrchestratorTask]:
        completed = {task_id for task_id, record in self.state.items() if record.status == "completed"}
        ready = []
        for record in self.state.values():
            if record.status == "queued" and all(dep in completed for dep in record.task.dependencies):
                ready.append(record.task)
        return sorted(ready, key=lambda task: (PRIORITY_RANK.get(task.priority, 2), task.task_id))

    def add_message(self, message: InterAgentMessage) -> None:
        self.messages.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": {task_id: record.to_dict() for task_id, record in self.state.items()},
            "messages": [message.to_dict() for message in self.messages],
        }


class ProjectContextMemory:
    """Project-specific context facade over shared JSONL memory."""

    def __init__(self, memory: SharedMemory | None):
        self.memory = memory

    def save_project_context(self, project_id: str, project_request: str, context: dict[str, Any]) -> None:
        if self.memory is None:
            return
        self.memory.add(
            event_type="project_context",
            task=project_request,
            agent_id="chief_orchestrator",
            data={"project_id": project_id, "context": context},
        )


class RoutingEngine:
    """Converts project requests into agent-assigned work packages."""

    def __init__(self, routes: list[RouteDefinition], approval_required_for: list[str]):
        self.routes = routes
        self.approval_required_for = [item.lower() for item in approval_required_for]

    def route_project(self, project_request: str) -> list[OrchestratorTask]:
        request_lower = project_request.lower()
        routed_agent_ids: list[str] = []
        for route in self.routes:
            if any(keyword.lower() in request_lower for keyword in route.keywords):
                routed_agent_ids.append(route.agent_id)
        if not routed_agent_ids:
            routed_agent_ids = ["project_manager", "business_analyst", "solution_architect"]
        routed_agent_ids = self._ordered_unique(routed_agent_ids)
        return [self._build_task(index, agent_id, project_request) for index, agent_id in enumerate(routed_agent_ids, start=1)]

    def _build_task(self, index: int, agent_id: str, project_request: str) -> OrchestratorTask:
        task_id = f"task-{index:03d}"
        dependency = [] if index == 1 else [f"task-{index - 1:03d}"]
        requires_approval = self._requires_approval(project_request, agent_id)
        return OrchestratorTask(
            task_id=task_id,
            title=self._title_for(agent_id),
            description=f"{self._title_for(agent_id)} for project request: {project_request}",
            department=self._department_for(agent_id),
            agent_id=agent_id,
            priority=self._priority_for(agent_id, requires_approval),
            dependencies=dependency,
            requires_approval=requires_approval,
            approval_reason=self._approval_reason(project_request) if requires_approval else None,
        )

    def _requires_approval(self, project_request: str, agent_id: str) -> bool:
        request_lower = project_request.lower()
        if agent_id in {"devops_engineer", "security_reviewer"}:
            return True
        sensitive_agents = {"project_manager", "documentation_specialist"}
        return agent_id in sensitive_agents and any(term in request_lower for term in self.approval_required_for)

    def _approval_reason(self, project_request: str) -> str:
        request_lower = project_request.lower()
        for term in self.approval_required_for:
            if term in request_lower:
                return f"Project request contains approval-controlled term '{term}'."
        return "Agent assignment requires executive approval."

    @staticmethod
    def _ordered_unique(items: list[str]) -> list[str]:
        preferred = [
            "business_analyst",
            "solution_architect",
            "backend_engineer",
            "frontend_engineer",
            "qa_engineer",
            "devops_engineer",
            "security_reviewer",
            "documentation_specialist",
            "project_manager",
        ]
        unique = list(dict.fromkeys(items))
        return sorted(unique, key=lambda item: preferred.index(item) if item in preferred else len(preferred))

    @staticmethod
    def _department_for(agent_id: str) -> str:
        departments = {
            "business_analyst": "Business Analysis",
            "solution_architect": "Architecture",
            "backend_engineer": "Engineering",
            "frontend_engineer": "Engineering",
            "qa_engineer": "Quality Assurance",
            "devops_engineer": "Operations",
            "security_reviewer": "Security",
            "documentation_specialist": "Documentation",
            "project_manager": "Project Management",
        }
        return departments.get(agent_id, "General Operations")

    @staticmethod
    def _title_for(agent_id: str) -> str:
        titles = {
            "business_analyst": "Define requirements and acceptance criteria",
            "solution_architect": "Design technical architecture",
            "backend_engineer": "Implement backend services",
            "frontend_engineer": "Implement frontend workflow",
            "qa_engineer": "Validate quality and regression coverage",
            "devops_engineer": "Prepare deployment and operations plan",
            "security_reviewer": "Review security and approval risks",
            "documentation_specialist": "Prepare handoff documentation",
            "project_manager": "Coordinate project execution",
        }
        return titles.get(agent_id, f"Coordinate {agent_id}")

    @staticmethod
    def _priority_for(agent_id: str, requires_approval: bool) -> str:
        if requires_approval:
            return "critical"
        if agent_id in {"business_analyst", "solution_architect", "backend_engineer", "frontend_engineer"}:
            return "high"
        if agent_id in {"qa_engineer", "security_reviewer", "devops_engineer"}:
            return "medium"
        return "low"


class WorkflowPlanner:
    """Builds JSON-serializable execution plans."""

    def create_plan(
        self,
        project_request: str,
        routed_tasks: list[OrchestratorTask],
        approvals: list[str],
    ) -> dict[str, Any]:
        workflows = [
            {
                "workflow_id": "workflow-001",
                "name": "Project Delivery Workflow",
                "tasks": [task.to_dict() for task in routed_tasks],
            }
        ]
        return {
            "output_format": "json_structured_execution_plan",
            "project_request": project_request,
            "executive_summary": self._summary(project_request, routed_tasks),
            "workflows": workflows,
            "approval_escalations": approvals,
        }

    @staticmethod
    def _summary(project_request: str, tasks: list[OrchestratorTask]) -> str:
        return (
            f"Chief Orchestrator decomposed the request into {len(tasks)} coordinated tasks "
            f"across {len({task.department for task in tasks})} departments: {project_request}"
        )


class ChiefOrchestratorAgent(BaseAgent):
    """AI COO / Executive Orchestrator for project intake and coordination."""

    def __init__(
        self,
        definition: AgentDefinition,
        model_manager: ModelManager,
        routes: list[RouteDefinition],
        approval_required_for: list[str],
        dry_run: bool = False,
        memory: SharedMemory | None = None,
        logger: Any | None = None,
    ):
        super().__init__(definition=definition, model_manager=model_manager, dry_run=dry_run, memory=memory, logger=logger)
        self.routing_engine = RoutingEngine(routes, approval_required_for)
        self.workflow_planner = WorkflowPlanner()
        self.state_tracker = ExecutionStateTracker()
        self.project_context_memory = ProjectContextMemory(memory)
        self.task_queue = PriorityTaskQueue()

    def run(self, task: str, context: dict[str, Any] | None = None):
        from custom_agents.agentic_it_firm.agents.base import AgentRunResult

        result = self.execute_task(task, context)
        return AgentRunResult(
            agent_id=self.id,
            agent_name=self.name,
            role=self.role,
            task=task,
            output=result.formatted_output,
            dry_run=self.dry_run,
        )

    def create_execution_plan(self, project_request: str) -> dict[str, Any]:
        project_id = self._project_id(project_request)
        tasks = self.routing_engine.route_project(project_request)
        self.task_queue.add_many(tasks)
        queued_tasks = self.task_queue.pop_all()
        self.state_tracker.register_tasks(queued_tasks)
        approvals = [task.approval_reason for task in queued_tasks if task.requires_approval and task.approval_reason]
        plan = self.workflow_planner.create_plan(project_request, queued_tasks, approvals)
        plan.update(
            {
                "project_id": project_id,
                "chief_orchestrator": {
                    "agent_id": self.id,
                    "role": self.role,
                    "department": self.department,
                    "experience": f"{self.years_of_experience}+ years equivalent",
                    "responsibilities": [
                        "receive project requests",
                        "break projects into workflows",
                        "assign departments",
                        "coordinate agents",
                        "track execution",
                        "escalate approvals",
                        "generate execution plans",
                    ],
                },
                "task_queue": [task.to_dict() for task in queued_tasks],
                "execution_state": self.state_tracker.to_dict(),
                "inter_agent_communication": self._messages_for_tasks(queued_tasks),
            }
        )
        self.project_context_memory.save_project_context(
            project_id,
            project_request,
            {
                "plan": plan,
                "task_count": len(queued_tasks),
                "approval_count": len(approvals),
            },
        )
        if self.memory:
            self.memory.add(
                event_type="chief_orchestrator_plan",
                task=project_request,
                agent_id=self.id,
                data={"project_id": project_id, "plan": plan},
            )
        return plan

    def execute_task(self, task: str, context: dict[str, Any] | None = None):
        plan = self.create_execution_plan(task)
        output = json.dumps(plan, indent=2, sort_keys=True)
        self_check = self.self_check(task, output)
        validation = self.validate_response(output)
        status = "completed" if validation["valid"] else "needs_review"
        summary = self.generate_task_summary(task, output, status)
        formatted_output = self.format_output(task, output, summary, self_check, validation)
        from custom_agents.agentic_it_firm.agents.base_agent import AgentExecutionResult

        return AgentExecutionResult(
            agent_id=self.id,
            agent_name=self.name,
            role=self.role,
            department=self.department,
            task=task,
            output=output,
            formatted_output=formatted_output,
            summary=summary,
            self_check=self_check,
            validation=validation,
            status=status,
            dry_run=self.dry_run,
            metadata={"project_id": plan["project_id"]},
        )

    def validate_response(self, output: str) -> dict[str, Any]:
        try:
            decoded = json.loads(output)
        except json.JSONDecodeError:
            return {"valid": False, "errors": ["Output is not valid JSON."], "requires_review": True}
        required = {"output_format", "project_request", "workflows", "task_queue", "execution_state"}
        missing = sorted(required - set(decoded))
        return {
            "valid": not missing,
            "errors": [f"Missing required plan key: {key}" for key in missing],
            "requires_review": bool(decoded.get("approval_escalations")),
        }

    @staticmethod
    def _project_id(project_request: str) -> str:
        digest = hashlib.sha1(project_request.encode("utf-8")).hexdigest()[:10]
        return f"project-{digest}"

    def _messages_for_tasks(self, tasks: list[OrchestratorTask]) -> list[dict[str, Any]]:
        messages = []
        for task in tasks:
            message = InterAgentMessage(
                sender_agent_id=self.id,
                recipient_agent_id=task.agent_id,
                task_id=task.task_id,
                message=f"You are assigned: {task.title}. Dependencies: {', '.join(task.dependencies) or 'none'}.",
            )
            self.state_tracker.add_message(message)
            messages.append(message.to_dict())
        return messages
