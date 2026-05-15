"""Workflow orchestration for routed agent execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.configs.loader import FirmConfig
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory
from custom_agents.agentic_it_firm.tools.approvals import ApprovalCheckpoint, ApprovalDecision
from custom_agents.agentic_it_firm.tools.output_writer import OutputWriter
from custom_agents.agentic_it_firm.workflows.router import TaskRouter


@dataclass(frozen=True)
class WorkflowResult:
    status: str
    agent_id: str
    approval: ApprovalDecision
    output_file: Path


class WorkflowOrchestrator:
    def __init__(
        self,
        config: FirmConfig,
        registry: AgentRegistry,
        router: TaskRouter,
        memory: SharedMemory,
        output_writer: OutputWriter,
        approvals: ApprovalCheckpoint,
        logger: logging.Logger,
    ):
        self.config = config
        self.registry = registry
        self.router = router
        self.memory = memory
        self.output_writer = output_writer
        self.approvals = approvals
        self.logger = logger

    def execute(self, task: str) -> WorkflowResult:
        self.logger.info("workflow_started task=%s", task)
        route = self.router.route(task)
        agent = self.registry.get(route.agent_id)
        self.memory.add(
            event_type="task_routed",
            task=task,
            agent_id=agent.id,
            data={
                "matched_keyword": route.matched_keyword,
                "requires_approval": route.requires_approval,
                "approval_reason": route.approval_reason,
            },
        )

        approval = self.approvals.request(task, route.approval_reason, route.requires_approval)
        self.memory.add(
            event_type="approval_decision",
            task=task,
            agent_id=agent.id,
            data={"approved": approval.approved, "reason": approval.reason, "requested": approval.requested},
        )
        if not approval.approved:
            content = f"# Workflow blocked\n\nTask: {task}\n\nReason: {approval.reason}\n"
            output_file = self.output_writer.save(agent.id, task, content)
            self.logger.warning("workflow_blocked agent_id=%s output=%s", agent.id, output_file)
            return WorkflowResult(status="blocked", agent_id=agent.id, approval=approval, output_file=output_file)

        run_result = agent.run(
            task,
            context={
                "firm": self.config.system.name,
                "approval": approval.reason,
                "memory_records": len(self.memory.recent()),
            },
        )
        content = "\n".join(
            [
                f"# {self.config.system.name} Output",
                "",
                f"Agent ID: {run_result.agent_id}",
                f"Agent Name: {run_result.agent_name}",
                f"Role: {run_result.role}",
                f"Dry Run: {run_result.dry_run}",
                "",
                "## Task",
                task,
                "",
                "## Result",
                run_result.output,
                "",
            ]
        )
        output_file = self.output_writer.save(agent.id, task, content)
        self.memory.add(
            event_type="task_completed",
            task=task,
            agent_id=agent.id,
            data={"output_file": str(output_file), "dry_run": run_result.dry_run},
        )
        self.logger.info("workflow_completed agent_id=%s output=%s", agent.id, output_file)
        return WorkflowResult(status="completed", agent_id=agent.id, approval=approval, output_file=output_file)
