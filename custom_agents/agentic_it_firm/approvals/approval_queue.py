"""JSON-persistent approval queue and history."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    action: str
    requested_by: str
    summary: str
    risk_score: int
    risks: list[str]
    rollback_considerations: list[str]
    recommended_action: str
    status: str
    created_at: str
    decision: str | None = None
    decided_by: str | None = None
    decided_at: str | None = None
    decision_reason: str | None = None

    @classmethod
    def create(
        cls,
        action: str,
        requested_by: str,
        summary: str,
        risk_score: int,
        risks: list[str],
        rollback_considerations: list[str],
        recommended_action: str,
    ) -> "ApprovalRequest":
        return cls(
            request_id=f"approval-{uuid.uuid4().hex[:12]}",
            action=action,
            requested_by=requested_by,
            summary=summary,
            risk_score=risk_score,
            risks=risks,
            rollback_considerations=rollback_considerations,
            recommended_action=recommended_action,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalRequest":
        return cls(**data)

    def with_decision(self, decision: str, decided_by: str, reason: str) -> "ApprovalRequest":
        data = asdict(self)
        data.update(
            {
                "status": "decided",
                "decision": decision,
                "decided_by": decided_by,
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "decision_reason": reason,
            }
        )
        return ApprovalRequest(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApprovalQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"pending": [], "history": []})

    def enqueue(self, request: ApprovalRequest) -> None:
        data = self._read()
        data["pending"].append(request.to_dict())
        self._write(data)

    def pending(self) -> list[ApprovalRequest]:
        return [ApprovalRequest.from_dict(item) for item in self._read()["pending"]]

    def history(self) -> list[ApprovalRequest]:
        return [ApprovalRequest.from_dict(item) for item in self._read()["history"]]

    def decide(self, request_id: str, approved: bool, decided_by: str, reason: str) -> ApprovalRequest:
        data = self._read()
        pending = [ApprovalRequest.from_dict(item) for item in data["pending"]]
        request = next((item for item in pending if item.request_id == request_id), None)
        if request is None:
            raise KeyError(f"Unknown approval request: {request_id}")
        decided = request.with_decision("approved" if approved else "rejected", decided_by, reason)
        data["pending"] = [item.to_dict() for item in pending if item.request_id != request_id]
        data["history"].append(decided.to_dict())
        self._write(data)
        return decided

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
