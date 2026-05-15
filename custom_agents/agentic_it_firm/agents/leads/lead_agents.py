from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent


class LeadResearchAgent(BaseFirmAgent):
    def research_sources(self, industries: list[str]) -> dict:
        return {
            "agent_id": self.id,
            "approved_sources": ["public_company_website", "licensed_directory", "manual_referral"],
            "blocked_sources": ["linkedin_scrape"],
            "industries": industries,
        }


class LeadEnrichmentAgent(BaseFirmAgent):
    def enrich(self, lead: dict) -> dict:
        return {
            **lead,
            "enrichment_status": "ready_for_human_review",
            "required_checks": ["source legitimacy", "fit", "contact permission"],
        }


class LeadQualificationAgent(BaseFirmAgent):
    def qualify(self, leads: list[dict], ideal_industries: list[str], min_employees: int = 1) -> dict:
        return LeadQualificationPipeline().qualify(leads, ideal_industries, min_employees)


class LeadQualificationPipeline:
    def qualify(self, leads: list[dict], ideal_industries: list[str], min_employees: int = 1) -> dict:
        qualified = []
        rejected = []
        for lead in leads:
            score = 0
            if lead.get("industry") in ideal_industries:
                score += 40
            if int(lead.get("employee_count", 0)) >= min_employees:
                score += 25
            signals = lead.get("signals", [])
            score += min(len(signals) * 20, 35)
            enriched = {**lead, "score": score, "recommended_action": "human_review_before_outreach"}
            if score >= 70 and lead.get("source") != "linkedin_scrape":
                qualified.append(enriched)
            else:
                rejected.append(enriched)
        return {
            "qualified_leads": sorted(qualified, key=lambda item: item["score"], reverse=True),
            "rejected_leads": rejected,
            "policy": "Use licensed or public sources only; human review is required before outreach.",
        }


class PublicLeadSourceClient:
    def __init__(self, search_client):
        self.search_client = search_client

    def search(self, query: str) -> list[dict]:
        results = self.search_client(query)
        return [
            {
                "company_name": item["title"],
                "website": item["url"],
                "industry": "",
                "employee_count": 0,
                "signals": [item.get("snippet", "")],
                "source": "public_web_search",
            }
            for item in results
        ]
