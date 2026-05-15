from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent


class ResearchTeamLeaderAgent(BaseFirmAgent):
    def summarize_research(self, request: str) -> dict:
        return {
            "agent_id": self.id,
            "market_questions": ["target users", "competitors", "pricing pressure"],
            "technical_questions": ["stack fit", "integration risk", "delivery constraints"],
            "request": request,
        }


class MarketResearchAgent(BaseFirmAgent):
    def research_market(self, request: str) -> dict:
        return {
            "agent_id": self.id,
            "findings": [
                "Clarify target customer segment.",
                "Identify competing products and differentiation.",
                "Estimate willingness to pay before packaging.",
            ],
            "request": request,
        }


class TechnicalResearchAgent(BaseFirmAgent):
    def research_technical(self, request: str) -> dict:
        return {
            "agent_id": self.id,
            "findings": [
                "Confirm system boundaries.",
                "Prefer proven libraries for core workflows.",
                "Document deployment and data risks early.",
            ],
            "request": request,
        }
