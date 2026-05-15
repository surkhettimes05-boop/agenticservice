from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent


class RevenuePackagingAgent(BaseFirmAgent):
    def package_offer(self, request: str, delivery_items: list[str]) -> dict:
        return {
            "agent_id": self.id,
            "offer_name": "Agentic IT Firm Delivery Package",
            "delivery_items": delivery_items,
            "pricing_notes": ["price by business value", "include implementation and support scope"],
            "request": request,
        }
