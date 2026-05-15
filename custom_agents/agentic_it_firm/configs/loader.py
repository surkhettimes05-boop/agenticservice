"""Configuration loading and validation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


DEFAULT_NVIDIA_NIM_API_BASE = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "nvidia_nim/meta/llama3-70b-instruct"


@dataclass(frozen=True)
class NvidiaConfig:
    api_key: str
    api_base: str = DEFAULT_NVIDIA_NIM_API_BASE


@dataclass(frozen=True)
class SystemConfig:
    name: str
    default_model: str
    approval_required_for: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    timeout_seconds: int = 60
    max_retries: int = 2
    streaming: bool = True


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    role: str
    goal: str
    instructions: str
    department: str = "General"
    expertise: list[str] = field(default_factory=list)
    years_of_experience: int = 0
    capabilities: list[str] = field(default_factory=list)
    model: str | None = None
    tools: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    restricted_actions: list[str] = field(default_factory=list)
    escalation_rules: list[str] = field(default_factory=list)
    approval_rules: list[str] = field(default_factory=list)
    memory_enabled: bool = True
    reviewer_agent: str | None = None
    reporting_agent: str | None = None


@dataclass(frozen=True)
class RouteDefinition:
    keywords: list[str]
    agent_id: str


@dataclass(frozen=True)
class FirmConfig:
    system: SystemConfig
    agents: list[AgentDefinition]
    routes: list[RouteDefinition]
    nvidia: NvidiaConfig
    root_dir: Path


def load_firm_config(config_path: str | Path | None = None, env_path: str | Path | None = None) -> FirmConfig:
    """Load agent, route, and NVIDIA settings from JSON and environment variables."""
    package_root = Path(__file__).resolve().parents[1]
    root_dir = package_root
    apply_env_model_override = env_path is not None or config_path is None
    if env_path is None and config_path is None:
        env_path = root_dir / ".env"
    if env_path is not None:
        load_dotenv(env_path)

    resolved_config_path = Path(config_path) if config_path else root_dir / "configs" / "agents.json"
    if not resolved_config_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_config_path}")

    raw = json.loads(resolved_config_path.read_text(encoding="utf-8"))
    _validate_config_shape(raw, resolved_config_path)

    api_key = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("NVIDIA_NIM_API_KEY is required for agent initialization.")

    api_base = os.getenv("NVIDIA_NIM_API_BASE", DEFAULT_NVIDIA_NIM_API_BASE).strip()
    if not api_base.startswith("https://"):
        raise ValueError("NVIDIA_NIM_API_BASE must be an HTTPS URL.")

    system_raw = raw["system"]
    env_default_model = os.getenv("NVIDIA_NIM_MODEL", "").strip() if apply_env_model_override else ""
    system = SystemConfig(
        name=system_raw["name"],
        default_model=env_default_model or system_raw.get("default_model", DEFAULT_NVIDIA_MODEL),
        approval_required_for=list(system_raw.get("approval_required_for", [])),
        fallback_models=list(system_raw.get("fallback_models", [])),
        timeout_seconds=int(system_raw.get("timeout_seconds", 60)),
        max_retries=int(system_raw.get("max_retries", 2)),
        streaming=bool(system_raw.get("streaming", True)),
    )
    agents = [
        AgentDefinition(
            id=item["id"],
            name=item["name"],
            role=item["role"],
            goal=item["goal"],
            instructions=item["instructions"],
            department=item.get("department", "General"),
            expertise=list(item.get("expertise", item.get("capabilities", []))),
            years_of_experience=int(item.get("years_of_experience", 0)),
            capabilities=list(item.get("capabilities", [])),
            model=item.get("model"),
            tools=list(item.get("tools", [])),
            allowed_actions=list(item.get("allowed_actions", [])),
            restricted_actions=list(item.get("restricted_actions", [])),
            escalation_rules=list(item.get("escalation_rules", [])),
            approval_rules=list(item.get("approval_rules", [])),
            memory_enabled=bool(item.get("memory_enabled", True)),
            reviewer_agent=item.get("reviewer_agent"),
            reporting_agent=item.get("reporting_agent"),
        )
        for item in raw["agents"]
    ]
    routes = [
        RouteDefinition(keywords=list(item["keywords"]), agent_id=item["agent_id"])
        for item in raw.get("routes", [])
    ]
    _validate_references(agents, routes)
    return FirmConfig(
        system=system,
        agents=agents,
        routes=routes,
        nvidia=NvidiaConfig(api_key=api_key, api_base=api_base),
        root_dir=root_dir,
    )


def _validate_config_shape(raw: dict[str, Any], path: Path) -> None:
    required_top_level = {"system", "agents", "routes"}
    missing = sorted(required_top_level - set(raw))
    if missing:
        raise ValueError(f"{path} is missing required keys: {', '.join(missing)}")
    if not isinstance(raw["agents"], list) or not raw["agents"]:
        raise ValueError("Config must define at least one agent.")
    for agent in raw["agents"]:
        missing_agent_keys = {"id", "name", "role", "goal", "instructions"} - set(agent)
        if missing_agent_keys:
            raise ValueError(
                f"Agent config is missing keys: {', '.join(sorted(missing_agent_keys))}"
            )


def _validate_references(agents: list[AgentDefinition], routes: list[RouteDefinition]) -> None:
    agent_ids = {agent.id for agent in agents}
    if len(agent_ids) != len(agents):
        raise ValueError("Agent IDs must be unique.")
    for route in routes:
        if route.agent_id not in agent_ids:
            raise ValueError(f"Route references unknown agent_id: {route.agent_id}")
