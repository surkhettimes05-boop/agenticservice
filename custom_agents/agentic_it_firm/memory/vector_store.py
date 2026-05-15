"""Vector memory stores for local and PostgreSQL-backed operation."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Iterable, Protocol

from custom_agents.agentic_it_firm.memory.schemas import RichMemoryRecord


class VectorMemoryStore(Protocol):
    def save(self, record: RichMemoryRecord) -> RichMemoryRecord:
        ...

    def list_records(
        self,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: str | None = None,
    ) -> list[RichMemoryRecord]:
        ...

    def search(
        self,
        embedding: list[float],
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: str | None = None,
        limit: int = 5,
    ) -> list[tuple[RichMemoryRecord, float]]:
        ...


class JsonVectorMemoryStore:
    """Durable local vector store for development and tests."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: RichMemoryRecord) -> RichMemoryRecord:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=True) + "\n")
        return record

    def list_records(
        self,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: str | None = None,
    ) -> list[RichMemoryRecord]:
        return [
            record
            for record in self._read_all()
            if self._matches(record, project_id, agent_id, workflow_id, client_id, conversation_id, scope)
        ]

    def search(
        self,
        embedding: list[float],
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        client_id: str | None = None,
        conversation_id: str | None = None,
        scope: str | None = None,
        limit: int = 5,
    ) -> list[tuple[RichMemoryRecord, float]]:
        scored = [
            (record, cosine_similarity(embedding, record.embedding))
            for record in self.list_records(project_id, agent_id, workflow_id, client_id, conversation_id, scope)
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

    def _read_all(self) -> list[RichMemoryRecord]:
        if not self.path.exists():
            return []
        records = []
        for row in self.path.read_text(encoding="utf-8").splitlines():
            if row.strip():
                records.append(RichMemoryRecord.from_dict(json.loads(row)))
        return records

    @staticmethod
    def _matches(
        record: RichMemoryRecord,
        project_id: str | None,
        agent_id: str | None,
        workflow_id: str | None,
        client_id: str | None,
        conversation_id: str | None,
        scope: str | None,
    ) -> bool:
        filters = {
            "project_id": project_id,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "client_id": client_id,
            "conversation_id": conversation_id,
            "scope": scope,
        }
        return all(value is None or getattr(record, key) == value for key, value in filters.items())


class PostgresPgVectorMemoryStore:
    """PostgreSQL pgvector memory store for production deployments."""

    def __init__(self, dsn: str | None = None, table_name: str = "agentic_memories", dimensions: int = 128):
        self.dsn = dsn or os.getenv("AGENTIC_MEMORY_DATABASE_URL", "")
        if not self.dsn:
            raise ValueError("AGENTIC_MEMORY_DATABASE_URL is required for PostgreSQL memory storage.")
        self.table_name = table_name
        self.dimensions = dimensions

    def initialize_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        memory_id TEXT PRIMARY KEY,
                        scope TEXT NOT NULL,
                        text TEXT NOT NULL,
                        embedding vector({self.dimensions}) NOT NULL,
                        project_id TEXT,
                        agent_id TEXT,
                        workflow_id TEXT,
                        client_id TEXT,
                        conversation_id TEXT,
                        session_id TEXT,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute(f"CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS {self.table_name}_project_idx ON {self.table_name} (project_id)")

    def save(self, record: RichMemoryRecord) -> RichMemoryRecord:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (
                        memory_id, scope, text, embedding, project_id, agent_id, workflow_id,
                        client_id, conversation_id, session_id, metadata, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (memory_id) DO NOTHING
                    """,
                    (
                        record.memory_id,
                        record.scope,
                        record.text,
                        self._vector_literal(record.embedding),
                        record.project_id,
                        record.agent_id,
                        record.workflow_id,
                        record.client_id,
                        record.conversation_id,
                        record.session_id,
                        json.dumps(record.metadata),
                        record.created_at,
                    ),
                )
        return record

    def list_records(self, **filters) -> list[RichMemoryRecord]:
        clauses, values = self._where(filters)
        query = f"SELECT * FROM {self.table_name}{clauses} ORDER BY created_at DESC"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                return [self._record_from_row(row) for row in cur.fetchall()]

    def search(self, embedding: list[float], limit: int = 5, **filters) -> list[tuple[RichMemoryRecord, float]]:
        clauses, values = self._where(filters)
        query = f"SELECT *, 1 - (embedding <=> %s::vector) AS score FROM {self.table_name}{clauses} ORDER BY embedding <=> %s::vector LIMIT %s"
        vector = self._vector_literal(embedding)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, [vector, *values, vector, limit])
                rows = cur.fetchall()
        return [(self._record_from_row(row[:-1]), float(row[-1])) for row in rows]

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] to use PostgreSQL pgvector memory storage.") from exc
        return psycopg.connect(self.dsn)

    def _where(self, filters: dict) -> tuple[str, list[str]]:
        clauses = []
        values = []
        for key in ["project_id", "agent_id", "workflow_id", "client_id", "conversation_id", "scope"]:
            value = filters.get(key)
            if value is not None:
                clauses.append(f"{key} = %s")
                values.append(value)
        return (f" WHERE {' AND '.join(clauses)}" if clauses else ""), values

    @staticmethod
    def _record_from_row(row) -> RichMemoryRecord:
        return RichMemoryRecord(
            memory_id=row[0],
            scope=row[1],
            text=row[2],
            embedding=list(row[3]),
            project_id=row[4],
            agent_id=row[5],
            workflow_id=row[6],
            client_id=row[7],
            conversation_id=row[8],
            session_id=row[9],
            metadata=row[10] or {},
            created_at=str(row[11]),
        )

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(str(float(value)) for value in embedding) + "]"


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    numerator = sum(a * b for a, b in zip(left_values, right_values))
    left_mag = math.sqrt(sum(a * a for a in left_values))
    right_mag = math.sqrt(sum(b * b for b in right_values))
    if left_mag == 0 or right_mag == 0:
        return 0.0
    return numerator / (left_mag * right_mag)
