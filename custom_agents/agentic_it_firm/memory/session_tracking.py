"""Session tracking for long-running workflows."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from custom_agents.agentic_it_firm.memory.schemas import WorkflowSession, utc_now


class SessionTracker:
    """Persist workflow sessions and step history in JSONL."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def start_session(
        self,
        project_id: str | None = None,
        client_id: str | None = None,
        workflow_id: str | None = None,
    ) -> WorkflowSession:
        session = WorkflowSession.start(project_id=project_id, client_id=client_id, workflow_id=workflow_id)
        self._upsert(session)
        return session

    def record_step(self, session_id: str, agent_id: str, summary: str) -> WorkflowSession:
        session = self._require_session(session_id)
        updated = replace(
            session,
            updated_at=utc_now(),
            steps=[
                *session.steps,
                {"timestamp": utc_now(), "agent_id": agent_id, "summary": summary},
            ],
        )
        self._upsert(updated)
        return updated

    def end_session(self, session_id: str, status: str = "completed") -> WorkflowSession | None:
        session = self.get_session(session_id)
        if session is None:
            return None
        updated = replace(session, status=status, updated_at=utc_now())
        self._upsert(updated)
        return updated

    def get_session(self, session_id: str) -> WorkflowSession | None:
        for session in self._read_all():
            if session.session_id == session_id:
                return session
        return None

    def _require_session(self, session_id: str) -> WorkflowSession:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        return session

    def _read_all(self) -> list[WorkflowSession]:
        if not self.path.exists():
            return []
        latest: dict[str, WorkflowSession] = {}
        for row in self.path.read_text(encoding="utf-8").splitlines():
            if row.strip():
                session = WorkflowSession.from_dict(json.loads(row))
                latest[session.session_id] = session
        return list(latest.values())

    def _upsert(self, session: WorkflowSession) -> None:
        existing = {item.session_id: item for item in self._read_all()}
        existing[session.session_id] = session
        with self.path.open("w", encoding="utf-8") as handle:
            for item in existing.values():
                handle.write(json.dumps(item.to_dict(), ensure_ascii=True) + "\n")
