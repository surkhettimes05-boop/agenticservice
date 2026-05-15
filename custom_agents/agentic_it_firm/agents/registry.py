"""Registry for configured firm agents."""

from __future__ import annotations

from collections import OrderedDict
import logging

from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent
from custom_agents.agentic_it_firm.agents.coding import CODING_AGENT_CLASSES
from custom_agents.agentic_it_firm.agents.orchestrator import ChiefOrchestratorAgent
from custom_agents.agentic_it_firm.agents.qa import QA_AGENT_CLASSES
from custom_agents.agentic_it_firm.agents.research import RESEARCH_AGENT_CLASSES
from custom_agents.agentic_it_firm.agents.revenue import REVENUE_AGENT_CLASSES
from custom_agents.agentic_it_firm.agents.leads import LEAD_AGENT_CLASSES
from custom_agents.agentic_it_firm.configs.loader import FirmConfig
from custom_agents.agentic_it_firm.llm_config import ModelManager
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory


class AgentRegistry:
    def __init__(self, agents: list[BaseFirmAgent]):
        self._agents: OrderedDict[str, BaseFirmAgent] = OrderedDict()
        for agent in agents:
            if agent.id in self._agents:
                raise ValueError(f"Duplicate agent id registered: {agent.id}")
            self._agents[agent.id] = agent

    @classmethod
    def from_config(
        cls,
        config: FirmConfig,
        dry_run: bool = False,
        model_manager: ModelManager | None = None,
        memory: SharedMemory | None = None,
        logger: logging.Logger | None = None,
    ) -> "AgentRegistry":
        manager = model_manager or ModelManager.from_config(config)
        return cls(
            [
                cls._build_agent(
                    definition=definition,
                    manager=manager,
                    config=config,
                    dry_run=dry_run,
                    memory=memory,
                    logger=logger,
                )
                for definition in config.agents
            ]
        )

    @staticmethod
    def _build_agent(definition, manager, config, dry_run, memory, logger):
        if definition.id == "chief_orchestrator":
            return ChiefOrchestratorAgent(
                definition=definition,
                model_manager=manager,
                routes=config.routes,
                approval_required_for=config.system.approval_required_for,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        if definition.id in CODING_AGENT_CLASSES:
            return CODING_AGENT_CLASSES[definition.id](
                definition=definition,
                model_manager=manager,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        if definition.id in QA_AGENT_CLASSES:
            return QA_AGENT_CLASSES[definition.id](
                definition=definition,
                model_manager=manager,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        if definition.id in RESEARCH_AGENT_CLASSES:
            return RESEARCH_AGENT_CLASSES[definition.id](
                definition=definition,
                model_manager=manager,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        if definition.id in REVENUE_AGENT_CLASSES:
            return REVENUE_AGENT_CLASSES[definition.id](
                definition=definition,
                model_manager=manager,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        if definition.id in LEAD_AGENT_CLASSES:
            return LEAD_AGENT_CLASSES[definition.id](
                definition=definition,
                model_manager=manager,
                dry_run=dry_run,
                memory=memory,
                logger=logger,
            )
        return BaseFirmAgent(
            definition=definition,
            model_manager=manager,
            dry_run=dry_run,
            memory=memory,
            logger=logger,
        )

    def get(self, agent_id: str) -> BaseFirmAgent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent id: {agent_id}") from exc

    def ids(self) -> list[str]:
        return list(self._agents.keys())

    def all(self) -> list[BaseFirmAgent]:
        return list(self._agents.values())
