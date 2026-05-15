from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app


def auth_headers(client: TestClient) -> dict[str, str]:
    token = client.post("/api/auth/login", json={"username": "admin", "password": "admin-pass"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_runs_mvp_workflow_and_lists_delivery(tmp_path: Path):
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'dashboard.db'}",
        dry_run_default=True,
        auth_secret="this-is-a-secure-auth-secret-value-123456",
        bootstrap_admin_password="admin-pass",
        deliveries_root=tmp_path / "deliveries",
    )
    client = TestClient(app)

    response = client.post(
        "/api/workflows/mvp",
        headers=auth_headers(client),
        json={"request": "Build an ACME client portal"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["delivery_dir"]


def test_dashboard_qualifies_leads_and_exports_csv(tmp_path: Path):
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'dashboard.db'}",
        dry_run_default=True,
        auth_secret="this-is-a-secure-auth-secret-value-123456",
        bootstrap_admin_password="admin-pass",
        deliveries_root=tmp_path / "deliveries",
    )
    client = TestClient(app)
    headers = auth_headers(client)

    response = client.post(
        "/api/leads/qualify",
        headers=headers,
        json={
            "ideal_industries": ["healthcare"],
            "min_employees": 50,
            "leads": [
                {
                    "company_name": "Acme Health",
                    "website": "https://acme.example",
                    "industry": "healthcare",
                    "employee_count": 120,
                    "signals": ["hiring developers", "mentions automation"],
                    "source": "public_company_website",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["qualified_leads"][0]["company_name"] == "Acme Health"

    export = client.post("/api/leads/export", headers=headers, json=response.json())
    assert export.status_code == 200
    assert "company_name" in export.text
