"""Human Approval Agent for summarizing risky actions."""

from __future__ import annotations

from typing import Any

from custom_agents.agentic_it_firm.agents.base_agent import BaseAgent
from custom_agents.agentic_it_firm.approvals.approval_manager import RiskScorer


class HumanApprovalAgent(BaseAgent):
    """Summarizes approval requests for human decision makers."""

    def summarize_request(self, action: str, why_needed: str, requested_by: str) -> dict[str, Any]:
        risk = RiskScorer().score(f"{action} {why_needed}")
        possible_risks = [
            f"{trigger} can cause service disruption, data loss, compliance exposure, or client impact."
            for trigger in risk.triggers
        ] or ["No high-risk trigger detected, but human review may still be useful."]
        rollback = [
            f"Confirm rollback path before approving {trigger}."
            for trigger in risk.triggers
        ] or ["Use normal retry or reversal process if the action has side effects."]
        recommended = (
            "Approve only after safeguards, owner, and rollback plan are confirmed."
            if risk.score >= 75
            else "Approve if the business need and safeguards are clear."
        )
        return {
            "requested_by": requested_by,
            "what_action_is_requested": action,
            "why_it_is_needed": why_needed,
            "possible_risks": possible_risks,
            "rollback_considerations": rollback,
            "risk_score": risk.score,
            "approval_required": risk.requires_approval,
            "recommended_action": recommended,
        }
