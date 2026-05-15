from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app
from custom_agents.agentic_it_firm.agents.leads import LeadQualificationPipeline


def test_dashboard_requires_auth_for_task_creation(tmp_path: Path):
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'dashboard.db'}",
        dry_run_default=True,
        auth_secret="test-secret-value-with-more-than-32-characters",
        bootstrap_admin_password="admin-pass",
    )
    client = TestClient(app)

    unauthorized = client.post("/api/tasks", json={"prompt": "Plan project"})
    assert unauthorized.status_code == 401

    token = client.post("/api/auth/login", json={"username": "admin", "password": "admin-pass"}).json()["access_token"]
    authorized = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Plan project", "dry_run": True},
    )
    assert authorized.status_code == 201


def test_lead_pipeline_scores_compliant_public_sources():
    pipeline = LeadQualificationPipeline()
    report = pipeline.qualify(
        [
            {
                "company_name": "Acme Health",
                "website": "https://acme.example",
                "industry": "healthcare",
                "employee_count": 120,
                "signals": ["hiring developers", "mentions automation"],
                "source": "public_company_website",
            }
        ],
        ideal_industries=["healthcare"],
        min_employees=50,
    )

    assert report["qualified_leads"][0]["score"] >= 80
    assert report["qualified_leads"][0]["recommended_action"] == "human_review_before_outreach"
