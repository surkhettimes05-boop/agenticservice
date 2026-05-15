"""Startup script for the Agentic IT Firm operating system."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.llm_config import ModelManager
from custom_agents.agentic_it_firm.memory import MemoryManager
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory
from custom_agents.agentic_it_firm.tools.approvals import ApprovalCheckpoint
from custom_agents.agentic_it_firm.tools.output_writer import OutputWriter
from custom_agents.agentic_it_firm.tools.runtime_logging import configure_logging
from custom_agents.agentic_it_firm.workflows.orchestrator import WorkflowOrchestrator
from custom_agents.agentic_it_firm.workflows.router import TaskRouter


PACKAGE_ROOT = Path(__file__).resolve().parent


def build_orchestrator(args: argparse.Namespace) -> WorkflowOrchestrator:
    config = load_firm_config(args.config, args.env)
    logger = configure_logging(PACKAGE_ROOT / "logs", logging.INFO)
    model_manager = ModelManager.from_config(config)
    semantic_memory = MemoryManager.local(PACKAGE_ROOT / "memory" / "semantic_memory.jsonl")
    memory = SharedMemory(PACKAGE_ROOT / "memory" / "shared_memory.jsonl", semantic_memory=semantic_memory)
    registry = AgentRegistry.from_config(
        config,
        dry_run=args.dry_run,
        model_manager=model_manager,
        memory=memory,
        logger=logger,
    )
    logger.info("initialized_agents count=%s ids=%s", len(registry.ids()), ",".join(registry.ids()))
    return WorkflowOrchestrator(
        config=config,
        registry=registry,
        router=TaskRouter(config.routes, config.system.approval_required_for),
        memory=memory,
        output_writer=OutputWriter(PACKAGE_ROOT / "outputs"),
        approvals=ApprovalCheckpoint(auto_approve=args.auto_approve, persistence_dir=PACKAGE_ROOT / "memory"),
        logger=logger,
    )


def validate_nvidia_connection(config_path: str | None, env_path: str | None) -> None:
    config = load_firm_config(config_path, env_path)
    result = ModelManager.from_config(config).test_connection()
    print("NVIDIA NIM connection validated.")
    print(f"model={result.model}")
    print(f"latency_ms={result.latency_ms:.2f}")
    print(f"prompt_tokens={result.usage.prompt_tokens}")
    print(f"completion_tokens={result.usage.completion_tokens}")
    print(f"total_tokens={result.usage.total_tokens}")
    print(f"response={result.response_text}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Agentic IT Firm operating system.")
    parser.add_argument("--task", required=False, help="Task to route to the agentic IT firm.")
    parser.add_argument("--config", default=str(PACKAGE_ROOT / "configs" / "agents.json"), help="Path to agents JSON config.")
    parser.add_argument("--env", default=str(PACKAGE_ROOT / ".env"), help="Path to .env file.")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve human approval checkpoints.")
    parser.add_argument("--dry-run", action="store_true", help="Initialize real agents but avoid live LLM calls.")
    parser.add_argument("--validate-connection", action="store_true", help="Make a live NVIDIA NIM API request.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.validate_connection:
        validate_nvidia_connection(args.config, args.env)
        return 0
    if not args.task:
        print("--task is required unless --validate-connection is used.", file=sys.stderr)
        return 2
    orchestrator = build_orchestrator(args)
    result = orchestrator.execute(args.task)
    print(f"status={result.status}")
    print(f"agent_id={result.agent_id}")
    print(f"approval={result.approval.approved}")
    print(f"output_file={result.output_file}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
