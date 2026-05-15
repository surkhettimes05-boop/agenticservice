from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dashboard.database import create_db_engine, init_db
from dashboard.schemas import AgentRead, TaskCreate, TaskRunRead
from dashboard.service import DashboardService


BASE_DIR = Path(__file__).resolve().parent


def create_app(database_url: str | None = None, dry_run_default: bool = True) -> FastAPI:
    app = FastAPI(title="Agentic IT Firm Console")
    engine = create_db_engine(database_url)
    init_db(engine)
    service = DashboardService(engine=engine, dry_run_default=dry_run_default)
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    app.state.service = service
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    def get_service() -> DashboardService:
        return app.state.service

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, dashboard: DashboardService = Depends(get_service)):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"agents": dashboard.list_agents(), "runs": dashboard.list_runs()[:12]},
        )

    @app.get("/api/agents", response_model=list[AgentRead])
    def list_agents(dashboard: DashboardService = Depends(get_service)):
        return dashboard.list_agents()

    @app.get("/api/runs", response_model=list[TaskRunRead])
    def list_runs(dashboard: DashboardService = Depends(get_service)):
        return dashboard.list_runs()

    @app.get("/api/runs/{run_id}", response_model=TaskRunRead)
    def get_run(run_id: int, dashboard: DashboardService = Depends(get_service)):
        run = dashboard.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.post("/api/tasks", response_model=TaskRunRead, status_code=status.HTTP_201_CREATED)
    def create_task(payload: TaskCreate, dashboard: DashboardService = Depends(get_service)):
        return dashboard.run_task(payload.prompt, auto_approve=payload.auto_approve, dry_run=payload.dry_run)

    return app


app = create_app()
