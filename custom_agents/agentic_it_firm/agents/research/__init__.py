from .research_agents import MarketResearchAgent, ResearchTeamLeaderAgent, TechnicalResearchAgent

RESEARCH_AGENT_CLASSES = {
    "research_team_leader": ResearchTeamLeaderAgent,
    "market_research_agent": MarketResearchAgent,
    "technical_research_agent": TechnicalResearchAgent,
}

__all__ = ["MarketResearchAgent", "ResearchTeamLeaderAgent", "TechnicalResearchAgent", "RESEARCH_AGENT_CLASSES"]
