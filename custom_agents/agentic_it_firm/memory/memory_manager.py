"""High-level memory manager for project, agent, workflow, client, and conversation memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from custom_agents.agentic_it_firm.memory.embedding_pipeline import DeterministicEmbeddingPipeline
from custom_agents.agentic_it_firm.memory.retrieval import RetrievalEngine
from custom_agents.agentic_it_firm.memory.schemas import MemoryScope, RetrievalResult, RichMemoryRecord
from custom_agents.agentic_it_firm.memory.session_tracking import SessionTracker
from custom_agents.agentic_it_firm.memory.vector_store import JsonVectorMemoryStore, VectorMemoryStore


class MemoryManager:
    """Coordinate embedding, storage, retrieval, and session state."""

    def __init__(
        self,
        store: VectorMemoryStore,
        embeddings: DeterministicEmbeddingPipeline | None = None,
        retrieval: RetrievalEngine | None = None,
        sessions: SessionTracker | None = None,
    ):
        self.store = store
        self.embeddings = embeddings or DeterministicEmbeddingPipeline()
        self.retrieval = retrieval or RetrievalEngine(store=self.store, embeddings=self.embeddings)
        self.sessions = sessions or SessionTracker(Path("memory") / "sessions.jsonl")

    @classmethod
    def local(cls, path: str | Path) -> "MemoryManager":
        path = Path(path)
        embeddings = DeterministicEmbeddingPipeline()
        store = JsonVectorMemoryStore(path)
        return cls(
            store=store,
            embeddings=embeddings,
            retrieval=RetrievalEngine(store=store, embeddings=embeddings),
            sessions=SessionTracker(path.parent / "sessions.jsonl"),
        )

    def remember(
        self,
        scope: MemoryScope,
        text: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RichMemoryRecord:
        if not text.strip():
            raise ValueError("Memory text cannot be empty.")
        record = RichMemoryRecord.create(
            scope=scope,
            text=text,
            embedding=self.embeddings.embed(text),
            project_id=project_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            client_id=client_id,
            conversation_id=conversation_id,
            session_id=session_id,
            metadata=metadata,
        )
        return self.store.save(record)

    def retrieve(
        self,
        query: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: MemoryScope | str | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        scope_value = scope.value if isinstance(scope, MemoryScope) else scope
        return self.retrieval.search(
            query,
            project_id=project_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            client_id=client_id,
            conversation_id=conversation_id,
            scope=scope_value,
            limit=limit,
        )

    def list_records(
        self,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: MemoryScope | str | None = None,
    ) -> list[RichMemoryRecord]:
        scope_value = scope.value if isinstance(scope, MemoryScope) else scope
        return self.store.list_records(
            project_id=project_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            client_id=client_id,
            conversation_id=conversation_id,
            scope=scope_value,
        )
