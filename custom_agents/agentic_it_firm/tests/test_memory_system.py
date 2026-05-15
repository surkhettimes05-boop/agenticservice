from pathlib import Path

from custom_agents.agentic_it_firm.memory import (
    AgentLearningHistory,
    DeterministicEmbeddingPipeline,
    JsonVectorMemoryStore,
    MemoryManager,
    MemoryScope,
    ProjectContextLoader,
    RetrievalEngine,
    SessionTracker,
)
from custom_agents.agentic_it_firm.memory.shared_memory import SharedMemory


def test_memory_manager_persists_scoped_memories_and_retrieves_semantic_context(tmp_path: Path):
    manager = MemoryManager.local(tmp_path / "memory_store.jsonl")
    session = manager.sessions.start_session(project_id="portal", client_id="acme", workflow_id="wf-1")

    project_record = manager.remember(
        scope=MemoryScope.PROJECT,
        text="Client portal uses FastAPI, PostgreSQL, Supabase auth, and Next.js dashboard.",
        project_id="portal",
        client_id="acme",
        workflow_id="wf-1",
        agent_id="solution_architect",
        session_id=session.session_id,
        metadata={"source": "architecture"},
    )
    agent_record = manager.remember(
        scope=MemoryScope.AGENT,
        text="Backend engineer learned that auth callbacks require retry handling.",
        project_id="portal",
        agent_id="backend_engineer",
        session_id=session.session_id,
    )

    assert project_record.memory_id.startswith("mem_")
    assert agent_record.scope == MemoryScope.AGENT.value

    results = manager.retrieve("What database does the portal use?", project_id="portal", limit=2)

    assert results[0].record.project_id == "portal"
    assert any("PostgreSQL" in result.record.text for result in results)


def test_session_tracker_supports_long_running_workflows(tmp_path: Path):
    tracker = SessionTracker(tmp_path / "sessions.jsonl")

    session = tracker.start_session(project_id="portal", client_id="acme", workflow_id="wf-99")
    tracker.record_step(session.session_id, "qa_team_leader", "planned regression checks")
    closed = tracker.end_session(session.session_id, status="completed")

    assert closed is not None
    assert closed.status == "completed"
    assert closed.steps[0]["agent_id"] == "qa_team_leader"
    assert tracker.get_session(session.session_id).workflow_id == "wf-99"


def test_project_context_loader_combines_memory_for_cross_agent_context(tmp_path: Path):
    manager = MemoryManager.local(tmp_path / "memory_store.jsonl")
    manager.remember(
        scope=MemoryScope.CLIENT,
        text="ACME requires human approval before production deployment.",
        client_id="acme",
        project_id="portal",
    )
    manager.remember(
        scope=MemoryScope.WORKFLOW,
        text="Workflow wf-1 completed API contract review.",
        workflow_id="wf-1",
        project_id="portal",
    )
    manager.remember(
        scope=MemoryScope.CONVERSATION,
        text="User decided to use Supabase for authentication.",
        project_id="portal",
    )

    context = ProjectContextLoader(manager).load(project_id="portal", query="deployment authentication API", limit=5)

    assert context["project_id"] == "portal"
    assert context["memory_count"] == 3
    assert "human approval" in context["context_text"]
    assert "Supabase" in context["context_text"]


def test_embedding_pipeline_is_deterministic_and_retrieval_orders_relevant_records(tmp_path: Path):
    embeddings = DeterministicEmbeddingPipeline(dimensions=16)
    store = JsonVectorMemoryStore(tmp_path / "vectors.jsonl")
    retrieval = RetrievalEngine(store=store, embeddings=embeddings)
    manager = MemoryManager(store=store, embeddings=embeddings, retrieval=retrieval)

    first_vector = embeddings.embed("FastAPI PostgreSQL backend")
    second_vector = embeddings.embed("FastAPI PostgreSQL backend")
    assert first_vector == second_vector

    manager.remember(scope=MemoryScope.PROJECT, text="FastAPI backend persists invoices in PostgreSQL.", project_id="billing")
    manager.remember(scope=MemoryScope.PROJECT, text="Tailwind components render a landing page.", project_id="billing")

    results = retrieval.search("PostgreSQL API backend", project_id="billing", limit=1)

    assert len(results) == 1
    assert "PostgreSQL" in results[0].record.text


def test_agent_learning_history_filters_agent_memories(tmp_path: Path):
    manager = MemoryManager.local(tmp_path / "memory_store.jsonl")
    manager.remember(scope=MemoryScope.AGENT, text="Reviewer learned to flag broad exception handling.", agent_id="code_review_agent")
    manager.remember(scope=MemoryScope.AGENT, text="QA learned to require regression evidence.", agent_id="qa_validator")

    history = AgentLearningHistory(manager).for_agent("qa_validator")

    assert len(history) == 1
    assert history[0].agent_id == "qa_validator"
    assert "regression evidence" in history[0].text


def test_shared_memory_bridges_agent_events_to_semantic_memory(tmp_path: Path):
    manager = MemoryManager.local(tmp_path / "semantic.jsonl")
    shared = SharedMemory(tmp_path / "shared.jsonl", semantic_memory=manager)

    shared.add(
        event_type="agent_task_execution",
        task="Review release readiness",
        agent_id="qa_team_leader",
        data={"summary": "QA release scored 92 and approved for release.", "project_id": "portal"},
    )

    results = manager.retrieve("release scored approved", project_id="portal")

    assert results
    assert results[0].record.agent_id == "qa_team_leader"
    assert "release scored 92" in results[0].record.text
