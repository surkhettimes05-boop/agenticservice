"""Human approval checkpoints for sensitive work."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str
    requested: bool


class ApprovalCheckpoint:
    def __init__(
        self,
        auto_approve: bool = False,
        prompt: Callable[[str], str] = input,
        manager: object | None = None,
        persistence_dir: str | Path | None = None,
    ):
        self.auto_approve = auto_approve
        self.prompt = prompt
        self.manager = manager
        self.persistence_dir = Path(persistence_dir) if persistence_dir else None

    def request(self, task: str, reason: str, required: bool) -> ApprovalDecision:
        if not required:
            return ApprovalDecision(approved=True, reason="Approval not required.", requested=False)
        manager = self.manager or self._default_manager()
        if manager is not None:
            return manager.request_approval(
                action=task,
                requested_by="workflow_orchestrator",
                why_needed=reason,
            )
        if self.auto_approve:
            return ApprovalDecision(approved=True, reason=f"Auto-approved: {reason}", requested=True)

        answer = self.prompt(f"Approval required for {reason}. Proceed? [y/N] ").strip().lower()
        approved = answer in {"y", "yes"}
        decision_reason = "Human approved." if approved else "Human rejected."
        return ApprovalDecision(approved=approved, reason=decision_reason, requested=True)

    def _default_manager(self):
        if self.persistence_dir is None:
            return None
        from custom_agents.agentic_it_firm.approvals.approval_logger import ApprovalAuditLogger
        from custom_agents.agentic_it_firm.approvals.approval_manager import ApprovalManager
        from custom_agents.agentic_it_firm.approvals.approval_queue import ApprovalQueue

        return ApprovalManager(
            queue=ApprovalQueue(self.persistence_dir / "approval_queue.json"),
            audit_logger=ApprovalAuditLogger(self.persistence_dir / "approval_audit.jsonl"),
            prompt=self.prompt,
            auto_approve=self.auto_approve,
        )
