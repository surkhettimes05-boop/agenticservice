"""Enterprise-grade reusable base agent for the Agentic IT Firm."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from praisonaiagents import Agent

from custom_agents.agentic_it_firm.configs.loader import AgentDefinition
from custom_agents.agentic_it_firm.llm_config import LLMRequest, ModelManager
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory
from custom_agents.agentic_it_firm.quality import AgentQualityEvaluator


@dataclass(frozen=True)
class AgentExecutionResult:
    agent_id: str
    agent_name: str
    role: str
    department: str
    task: str
    output: str
    formatted_output: str
    summary: str
    self_check: dict[str, Any]
    validation: dict[str, Any]
    status: str
    dry_run: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Reusable base class for scalable enterprise agent implementations."""

    def __init__(
        self,
        definition: AgentDefinition,
        model_manager: ModelManager,
        dry_run: bool = False,
        memory: SharedMemory | None = None,
        logger: logging.Logger | None = None,
    ):
        self.definition = definition
        self.model_manager = model_manager
        self.dry_run = dry_run
        self.memory = memory
        self.logger = logger or logging.getLogger("agentic_it_firm.agents")
        self.llm_config = self.model_manager.agent_model_config(definition.model)
        self.agent = Agent(
            name=definition.name,
            role=definition.role,
            goal=definition.goal,
            instructions=definition.instructions,
            approval=False,
        )
        self.quality_evaluator = AgentQualityEvaluator()

    @property
    def id(self) -> str:
        return self.definition.id

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def role(self) -> str:
        return self.definition.role

    @property
    def department(self) -> str:
        return self.definition.department

    @property
    def expertise(self) -> list[str]:
        return list(self.definition.expertise)

    @property
    def years_of_experience(self) -> int:
        return self.definition.years_of_experience

    @property
    def goal(self) -> str:
        return self.definition.goal

    @property
    def instructions(self) -> str:
        return self.definition.instructions

    @property
    def tools(self) -> list[str]:
        return list(self.definition.tools)

    @property
    def allowed_actions(self) -> list[str]:
        return list(self.definition.allowed_actions)

    @property
    def restricted_actions(self) -> list[str]:
        return list(self.definition.restricted_actions)

    @property
    def escalation_rules(self) -> list[str]:
        return list(self.definition.escalation_rules)

    @property
    def approval_rules(self) -> list[str]:
        return list(self.definition.approval_rules)

    @property
    def memory_enabled(self) -> bool:
        return self.definition.memory_enabled

    @property
    def reviewer_agent(self) -> str | None:
        return self.definition.reviewer_agent

    @property
    def reporting_agent(self) -> str | None:
        return self.definition.reporting_agent

    @property
    def capabilities(self) -> list[str]:
        return list(self.definition.capabilities)

    def execute_task(self, task: str, context: dict[str, Any] | None = None) -> AgentExecutionResult:
        self._enforce_tool_permissions(task)
        self.logger.info("agent_task_started agent_id=%s department=%s role=%s", self.id, self.department, self.role)
        output = self._dry_run_output(task, context) if self.dry_run else self._execute_live(task, context)
        self_check = self.self_check(task, output)
        validation = self.validate_response(output)
        status = "completed" if self_check["passed"] and validation["valid"] else "needs_review"
        summary = self.generate_task_summary(task, output, status)
        formatted_output = self.format_output(task, output, summary, self_check, validation)
        result = AgentExecutionResult(
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
            metadata={
                "expertise": self.expertise,
                "years_of_experience": self.years_of_experience,
                "escalation_rules": self.escalation_rules,
                "approval_rules": self.approval_rules,
                "reviewer_agent": self.reviewer_agent,
                "reporting_agent": self.reporting_agent,
            },
        )
        self.save_to_memory(result)
        self.logger.info("agent_task_finished agent_id=%s status=%s", self.id, result.status)
        return result

    def self_check(self, task: str, output: str) -> dict[str, Any]:
        passed = bool(task.strip()) and bool(output.strip())
        return {
            "passed": passed,
            "checks": {
                "task_present": bool(task.strip()),
                "output_present": bool(output.strip()),
                "reviewer_agent": self.reviewer_agent,
                "reporting_agent": self.reporting_agent,
            },
        }

    def validate_response(self, output: str) -> dict[str, Any]:
        valid = bool(output.strip())
        quality = self.quality_evaluator.evaluate(self.role, output)
        return {
            "valid": valid,
            "errors": [] if valid else ["Agent output is empty."],
            "requires_review": not valid or bool(self.reviewer_agent),
            "quality": quality,
        }

    def format_output(
        self,
        task: str,
        output: str,
        summary: str,
        self_check: dict[str, Any],
        validation: dict[str, Any],
    ) -> str:
        return "\n".join(
            [
                f"# {self.name} Output",
                "",
                f"Agent ID: {self.id}",
                f"Role: {self.role}",
                f"Department: {self.department}",
                f"Experience: {self.years_of_experience} years",
                f"Reviewer Agent: {self.reviewer_agent or 'None'}",
                f"Reporting Agent: {self.reporting_agent or 'None'}",
                "",
                "## Task",
                task,
                "",
                "## Summary",
                summary,
                "",
                "## Self Check",
                f"Passed: {self_check['passed']}",
                "",
                "## Validation",
                f"Valid: {validation['valid']}",
                "",
                "## Output",
                output,
                "",
            ]
        )

    def save_to_memory(self, result: AgentExecutionResult) -> None:
        if not self.memory_enabled or self.memory is None:
            return
        self.memory.add(
            event_type="agent_task_execution",
            task=result.task,
            agent_id=self.id,
            data={
                "status": result.status,
                "summary": result.summary,
                "department": self.department,
                "role": self.role,
                "reviewer_agent": self.reviewer_agent,
                "reporting_agent": self.reporting_agent,
                "escalation_rules": self.escalation_rules,
                "approval_rules": self.approval_rules,
            },
        )

    def generate_task_summary(self, task: str, output: str, status: str = "completed") -> str:
        preview = " ".join(output.split())[:160]
        return f"{self.name} completed task '{task}' with status '{status}'. Output preview: {preview}"

    def _execute_live(self, task: str, context: dict[str, Any] | None) -> str:
        response = self.model_manager.complete(
            LLMRequest(
                prompt=self._build_prompt(task, context),
                agent_id=self.id,
                system_prompt=self.instructions,
                model=self.definition.model,
            )
        )
        return response.content

    def _dry_run_output(self, task: str, context: dict[str, Any] | None) -> str:
        context_lines = []
        if context:
            context_lines = [f"- {key}: {value}" for key, value in sorted(context.items())]
        return "\n".join(
            [
                f"Agent: {self.name}",
                f"Role: {self.role}",
                f"Department: {self.department}",
                f"Task: {task}",
                "Execution mode: dry-run validation",
                "Planned response:",
                self.instructions,
                *context_lines,
            ]
        )

    def _build_prompt(self, task: str, context: dict[str, Any] | None = None) -> str:
        metadata = "\n".join(
            [
                f"Agent: {self.name}",
                f"Role: {self.role}",
                f"Department: {self.department}",
                f"Expertise: {', '.join(self.expertise) or 'General'}",
                f"Years of experience: {self.years_of_experience}",
                f"Allowed actions: {', '.join(self.allowed_actions) or 'Not specified'}",
                f"Restricted actions: {', '.join(self.restricted_actions) or 'None'}",
                f"Escalation rules: {', '.join(self.escalation_rules) or 'None'}",
                f"Approval rules: {', '.join(self.approval_rules) or 'None'}",
            ]
        )
        if not context:
            return f"{metadata}\n\nTask:\n{task}"
        context_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(context.items()))
        return f"{metadata}\n\nTask:\n{task}\n\nContext:\n{context_lines}"

    def _enforce_tool_permissions(self, task: str) -> None:
        task_lower = task.lower()
        for action in self.restricted_actions:
            if action.lower() in task_lower:
                raise PermissionError(f"Task includes restricted action '{action}' for agent '{self.id}'.")
        if self.allowed_actions and not any(action.lower() in task_lower for action in self.allowed_actions):
            self.logger.info(
                "agent_task_outside_allowed_actions agent_id=%s allowed_actions=%s",
                self.id,
                ",".join(self.allowed_actions),
            )
