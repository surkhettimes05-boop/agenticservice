"""Approval manager with risk scoring and terminal interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from custom_agents.agentic_it_firm.approvals.approval_logger import ApprovalAuditLogger
from custom_agents.agentic_it_firm.approvals.approval_queue import ApprovalQueue, ApprovalRequest
from custom_agents.agentic_it_firm.tools.approvals import ApprovalDecision


@dataclass(frozen=True)
class RiskScore:
    score: int
    triggers: list[str]
    requires_approval: bool


class RiskScorer:
    APPROVAL_TRIGGERS = {
        "production deployment": ["production deployment", "deploy to production", "production", "deployment"],
        "deleting files": ["delete files", "deleting files", "delete", "remove files"],
        "modifying secrets": ["modify secrets", "secret", "secrets", "api key"],
        "sending client emails": ["send client email", "sending client emails", "client email", "email client"],
        "spending money": ["spend money", "spending money", "purchase", "billing", "paid"],
        "changing databases": ["change database", "changing databases", "database", "migration"],
        "changing credentials": ["change credentials", "changing credentials", "credential", "password"],
    }

    def score(self, text: str) -> RiskScore:
        lowered = text.lower()
        triggers = [
            label
            for label, patterns in self.APPROVAL_TRIGGERS.items()
            if any(pattern in lowered for pattern in patterns)
        ]
        score = min(100, 25 + (len(triggers) * 25)) if triggers else 10
        return RiskScore(score=score, triggers=triggers, requires_approval=bool(triggers))


class ApprovalManager:
    def __init__(
        self,
        queue: ApprovalQueue,
        audit_logger: ApprovalAuditLogger,
        prompt: Callable[[str], str] = input,
        auto_approve: bool = False,
    ):
        self.queue = queue
        self.audit_logger = audit_logger
        self.prompt = prompt
        self.auto_approve = auto_approve
        self.risk_scorer = RiskScorer()

    def request_approval(
        self,
        action: str,
        requested_by: str,
        why_needed: str,
        possible_risks: list[str] | None = None,
        rollback_considerations: list[str] | None = None,
        recommended_action: str | None = None,
    ) -> ApprovalDecision:
        summary = self.human_readable_summary(action, why_needed)
        risk = self.risk_scorer.score(f"{action} {why_needed}")
        risks = possible_risks or self._risks_for(risk.triggers)
        rollback = rollback_considerations or self._rollback_for(risk.triggers)
        recommendation = recommended_action or self._recommendation(risk)
        request = ApprovalRequest.create(
            action=action,
            requested_by=requested_by,
            summary=summary,
            risk_score=risk.score,
            risks=risks,
            rollback_considerations=rollback,
            recommended_action=recommendation,
        )
        self.queue.enqueue(request)
        self.audit_logger.log_request(request)

        if self.auto_approve:
            decided = self.queue.decide(request.request_id, True, "system:auto_approve", "Auto-approved by configuration.")
            self.audit_logger.log_decision(decided, "approved", "system:auto_approve", decided.decision_reason or "")
            return ApprovalDecision(True, f"Auto-approved: {summary}", True)

        approved = self._terminal_prompt(request)
        reason = "Human approved." if approved else "Human rejected."
        decided = self.queue.decide(request.request_id, approved, "human", reason)
        self.audit_logger.log_decision(decided, decided.decision or "unknown", "human", reason)
        return ApprovalDecision(approved=approved, reason=f"{reason} {summary}", requested=True)

    @staticmethod
    def human_readable_summary(action: str, why_needed: str) -> str:
        return f"Requested action: {action}. Reason: {why_needed}."

    def _terminal_prompt(self, request: ApprovalRequest) -> bool:
        prompt_text = "\n".join(
            [
                "",
                "Human approval required",
                f"Request ID: {request.request_id}",
                f"Action: {request.action}",
                f"Summary: {request.summary}",
                f"Risk score: {request.risk_score}/100",
                f"Risks: {', '.join(request.risks) or 'None'}",
                f"Rollback: {', '.join(request.rollback_considerations) or 'None'}",
                f"Recommended action: {request.recommended_action}",
                "Approve? [y/N] ",
            ]
        )
        return self.prompt(prompt_text).strip().lower() in {"y", "yes"}

    @staticmethod
    def _risks_for(triggers: list[str]) -> list[str]:
        if not triggers:
            return ["Low operational risk."]
        return [f"Risk from {trigger}: service disruption, data loss, compliance exposure, or customer impact." for trigger in triggers]

    @staticmethod
    def _rollback_for(triggers: list[str]) -> list[str]:
        if not triggers:
            return ["Confirm normal retry path."]
        return [f"Prepare rollback plan before {trigger}." for trigger in triggers]

    @staticmethod
    def _recommendation(risk: RiskScore) -> str:
        if risk.score >= 75:
            return "Approve only with explicit human sign-off and rollback plan."
        if risk.requires_approval:
            return "Approve after confirming scope and safeguards."
        return "Approval can proceed if operational context is clear."
