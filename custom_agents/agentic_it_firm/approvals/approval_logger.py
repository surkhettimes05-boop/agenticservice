"""Approval audit logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from custom_agents.agentic_it_firm.approvals.approval_queue import ApprovalRequest


class ApprovalAuditLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_request(self, request: ApprovalRequest) -> None:
        self._write("approval_requested", request.to_dict())

    def log_decision(self, request: ApprovalRequest, decision: str, decided_by: str, reason: str) -> None:
        data = request.to_dict()
        data.update({"decision": decision, "decided_by": decided_by, "decision_reason": reason})
        self._write("approval_decided", data)

    def _write(self, event_type: str, data: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
