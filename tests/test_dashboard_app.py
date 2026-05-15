from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app


def test_dashboard_lists_agents_and_creates_task_run(tmp_path: Path):
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'dashboard.db'}",
        dry_run_default=True,
    )
    client = TestClient(app)

    agents = client.get("/api/agents")
    assert agents.status_code == 200
    assert any(agent["id"] == "chief_orchestrator" for agent in agents.json())

    response = client.post(
        "/api/tasks",
        json={"prompt": "Plan a QA dashboard workflow", "auto_approve": True, "dry_run": True},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["agent_id"]
    assert payload["output"]

    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert runs.json()[0]["id"] == payload["id"]


def test_dashboard_home_renders_monitoring_ui(tmp_path: Path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'dashboard.db'}", dry_run_default=True)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Agentic IT Firm Console" in response.text
    assert "Submit Task" in response.text
    assert "Recent Runs" in response.text


def test_dashboard_run_detail_returns_saved_output(tmp_path: Path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'dashboard.db'}", dry_run_default=True)
    client = TestClient(app)
    created = client.post("/api/tasks", json={"prompt": "Review API design", "auto_approve": True, "dry_run": True}).json()

    detail = client.get(f"/api/runs/{created['id']}")

    assert detail.status_code == 200
    assert detail.json()["output"] == created["output"]
