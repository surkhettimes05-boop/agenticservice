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

The database tables are created automatically by SQLModel at startup. A PostgreSQL reference schema is also available at `dashboard/schema.sql`.
