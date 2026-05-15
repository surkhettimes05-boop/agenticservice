import logging
from pathlib import Path

import pytest

from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent
from custom_agents.agentic_it_firm.agents.base_agent import AgentExecutionResult, BaseAgent
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition
from custom_agents.agentic_it_firm.llm_config import LLMResult, ModelManager, TokenUsage
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory


class FakeModelManager:
    def __init__(self):
        self.requests = []

    def agent_model_config(self, model=None):
        return {
            "model": model or "nvidia_nim/meta/llama3-70b-instruct",
            "api_key": "nvapi-test",
            "base_url": "https://integrate.api.nvidia.com/v1",
        }

    def complete(self, request):
        self.requests.append(request)
        return LLMResult(
            content="Validated execution result",
            model=request.model or "nvidia_nim/meta/llama3-70b-instruct",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=4, total_tokens=14),
            latency_ms=12.5,
            estimated_cost=None,
            attempts=1,
        )


def definition(**overrides):
    data = {
        "id": "qa_engineer",
        "name": "QA Engineer",
        "role": "Quality Assurance Engineer",
        "department": "Engineering",
        "expertise": ["test planning", "regression testing"],
        "years_of_experience": 8,
        "goal": "Verify work before delivery",
        "instructions": "Validate outputs against acceptance criteria.",
        "tools": ["pytest"],
        "allowed_actions": ["test", "review"],
        "restricted_actions": ["deploy", "delete"],
        "escalation_rules": ["Escalate security findings to security_reviewer"],
        "approval_rules": ["Require human approval before production validation"],
        "memory_enabled": True,
        "reviewer_agent": "security_reviewer",
        "reporting_agent": "project_manager",
        "capabilities": ["testing"],
    }
    data.update(overrides)
    return AgentDefinition(**data)


def test_base_agent_exposes_enterprise_metadata_and_praison_agent():
    agent = BaseAgent(definition(), FakeModelManager(), dry_run=True)

    assert agent.name == "QA Engineer"
    assert agent.role == "Quality Assurance Engineer"
    assert agent.department == "Engineering"
    assert agent.expertise == ["test planning", "regression testing"]
    assert agent.years_of_experience == 8
    assert agent.tools == ["pytest"]
    assert agent.allowed_actions == ["test", "review"]
    assert agent.restricted_actions == ["deploy", "delete"]
    assert agent.escalation_rules == ["Escalate security findings to security_reviewer"]
    assert agent.approval_rules == ["Require human approval before production validation"]
    assert agent.reviewer_agent == "security_reviewer"
    assert agent.reporting_agent == "project_manager"
    assert agent.agent is not None


def test_execute_task_dry_run_validates_formats_summarizes_and_saves_memory(tmp_path: Path):
    memory = SharedMemory(tmp_path / "memory.jsonl")
    agent = BaseAgent(
        definition(),
        FakeModelManager(),
        dry_run=True,
        memory=memory,
        logger=logging.getLogger("test_base_agent"),
    )

    result = agent.execute_task("Review the release checklist", context={"priority": "high"})

    assert isinstance(result, AgentExecutionResult)
    assert result.status == "completed"
    assert result.self_check["passed"] is True
    assert result.validation["valid"] is True
    assert result.summary.startswith("QA Engineer completed task")
    assert "# QA Engineer Output" in result.formatted_output
    assert "Review the release checklist" in memory.path.read_text(encoding="utf-8")


def test_execute_task_blocks_restricted_actions_before_llm_call():
    manager = FakeModelManager()
    agent = BaseAgent(definition(), manager, dry_run=False)

    with pytest.raises(PermissionError, match="restricted action"):
        agent.execute_task("Deploy and delete production data")

    assert manager.requests == []


def test_execute_task_live_uses_central_model_manager():
    manager = FakeModelManager()
    agent = BaseAgent(definition(memory_enabled=False), manager, dry_run=False)

    result = agent.execute_task("Create a regression test plan")

    assert result.output == "Validated execution result"
    assert manager.requests[0].agent_id == "qa_engineer"
    assert manager.requests[0].system_prompt == "Validate outputs against acceptance criteria."


def test_base_firm_agent_remains_compatible_alias():
    agent = BaseFirmAgent(definition(), FakeModelManager(), dry_run=True)

    assert isinstance(agent, BaseAgent)
    assert agent.run("Review build health").output
