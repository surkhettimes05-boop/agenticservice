# Agentic Service

Standalone hostable project for the custom Agentic IT Firm OS and its monitoring dashboard.

## Run Locally

```powershell
python -m pip install -r requirements.txt
python run_dashboard.py
```

Open:

```text
http://127.0.0.1:8000
```

## Environment

Create `custom_agents/agentic_it_firm/.env` with:

```env
NVIDIA_NIM_API_KEY=your-key
NVIDIA_NIM_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct
DASHBOARD_DATABASE_URL=sqlite:///./agentic_dashboard.db
```

For hosted PostgreSQL:

```env
DASHBOARD_DATABASE_URL=postgresql+psycopg://user:password@host:5432/agenticservice
```

## Dashboard

The FastAPI dashboard provides:

- live agent directory
- task submission
- task-run history
- saved outputs
- SQLite for local development
- PostgreSQL-compatible persistence for hosting
- optional JWT authentication for hosted deployments

The database tables are created automatically by SQLModel at startup. A PostgreSQL reference schema is also available at `dashboard/schema.sql`.

## MVP Workflow

Run the first complete delivery workflow:

```powershell
python run_mvp_workflow.py --request "Build a client portal for ACME" --deliveries-root "D:\agentic services\deliveries"
```

The command prints terminal progress and creates a packaged delivery folder with:

- project summary
- implementation plan
- QA report
- documentation
- revenue package
- delivery manifest
- workflow state

## Hosted Deployment

Set these environment variables in production:

```env
DASHBOARD_AUTH_SECRET=use-a-random-secret-at-least-32-characters
DASHBOARD_ADMIN_PASSWORD=change-this-password
DASHBOARD_DATABASE_URL=postgresql+psycopg://user:password@host:5432/agenticservice
NVIDIA_NIM_API_KEY=your-key
NVIDIA_NIM_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct
```

`Dockerfile` and `render.yaml` are included for backend hosting.

## Lead Generation Department

The growth layer now includes:

- Lead Research Agent
- Lead Enrichment Agent
- Lead Qualification Agent

The department is intentionally compliance-first: it accepts public or licensed sources, rejects `linkedin_scrape`, and keeps outreach behind human review.
