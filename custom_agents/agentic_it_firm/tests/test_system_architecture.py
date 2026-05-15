import json
import logging
from pathlib import Path

import pytest

from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory
from custom_agents.agentic_it_firm.tools.approvals import ApprovalCheckpoint
from custom_agents.agentic_it_firm.tools.output_writer import OutputWriter
from custom_agents.agentic_it_firm.tools.runtime_logging import configure_logging
from custom_agents.agentic_it_firm.workflows.orchestrator import WorkflowOrchestrator
from custom_agents.agentic_it_firm.workflows.router import TaskRouter


def write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "agents.json"
    config_path.write_text(
        json.dumps(
            {
                "system": {
                    "name": "Agentic IT Firm",
                    "default_model": "nvidia_nim/meta/llama3-70b-instruct",
                    "approval_required_for": ["deployment", "billing"],
                },
                "agents": [
                    {
                        "id": "project_manager",
                        "name": "Project Manager",
                        "role": "Project Manager",
                        "goal": "Break requests into executable work",
                        "instructions": "Create concise execution plans.",
                        "capabilities": ["planning", "coordination"],
                    },
                    {
                        "id": "devops",
                        "name": "DevOps Engineer",
                        "role": "DevOps Engineer",
                        "goal": "Prepare deployment work safely",
                        "instructions": "Handle infrastructure and deployment tasks.",
                        "capabilities": ["deployment", "operations"],
                    },
                ],
                "routes": [
                    {"keywords": ["deploy", "deployment"], "agent_id": "devops"},
                    {"keywords": ["plan", "project"], "agent_id": "project_manager"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_config_loader_reads_json_and_environment(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")

    config = load_firm_config(config_path)

    assert config.system.name == "Agentic IT Firm"
    assert config.nvidia.api_key == "nvapi-test"
    assert config.nvidia.api_base == "https://integrate.api.nvidia.com/v1"
    assert config.agents[0].id == "project_manager"


def test_config_loader_requires_nvidia_key(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")

    with pytest.raises(ValueError, match="NVIDIA_NIM_API_KEY"):
        load_firm_config(config_path)


def test_registry_initializes_praison_agents_without_live_execution(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(config_path)

    registry = AgentRegistry.from_config(config, dry_run=True)

    assert registry.get("project_manager").role == "Project Manager"
    assert registry.get("devops").llm_config["model"].startswith("nvidia_nim/")
    assert registry.ids() == ["project_manager", "devops"]


def test_router_selects_agent_and_detects_human_approval(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(config_path)
    router = TaskRouter(config.routes, config.system.approval_required_for)

    route = router.route("Prepare a deployment checklist for a client portal")

    assert route.agent_id == "devops"
    assert route.requires_approval is True
    assert route.matched_keyword == "deployment"


def test_memory_output_logging_and_orchestrator_execute_end_to_end(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    memory_path = tmp_path / "memory" / "shared_memory.jsonl"
    output_dir = tmp_path / "outputs"
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")

    logger = configure_logging(log_dir, level=logging.INFO)
    config = load_firm_config(config_path)
    memory = SharedMemory(memory_path)
    registry = AgentRegistry.from_config(config, dry_run=True, memory=memory, logger=logger)
    output_writer = OutputWriter(output_dir)
    approvals = ApprovalCheckpoint(auto_approve=True)
    orchestrator = WorkflowOrchestrator(
        config=config,
        registry=registry,
        router=TaskRouter(config.routes, config.system.approval_required_for),
        memory=memory,
        output_writer=output_writer,
        approvals=approvals,
        logger=logger,
    )

    result = orchestrator.execute("Prepare a deployment checklist for a client portal")

    assert result.status == "completed"
    assert result.agent_id == "devops"
    assert result.approval.approved is True
    assert result.output_file.exists()
    assert "DevOps Engineer" in result.output_file.read_text(encoding="utf-8")
    assert memory_path.exists()
    assert "Prepare a deployment checklist" in memory_path.read_text(encoding="utf-8")
    assert any(path.suffix == ".log" for path in log_dir.iterdir())
