"""Semantic memory retrieval."""

from __future__ import annotations

from custom_agents.agentic_it_firm.memory.embedding_pipeline import DeterministicEmbeddingPipeline
from custom_agents.agentic_it_firm.memory.schemas import RetrievalResult
from custom_agents.agentic_it_firm.memory.vector_store import VectorMemoryStore


class RetrievalEngine:
    """Search persisted memories using vector similarity and metadata filters."""

    def __init__(self, store: VectorMemoryStore, embeddings: DeterministicEmbeddingPipeline):
        self.store = store
        self.embeddings = embeddings

    def search(
        self,
        query: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        query_embedding = self.embeddings.embed(query)
        return [
            RetrievalResult(record=record, score=score)
            for record, score in self.store.search(
                query_embedding,
                project_id=project_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                client_id=client_id,
                conversation_id=conversation_id,
                scope=scope,
                limit=limit,
            )
        ]
