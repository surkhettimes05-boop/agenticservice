from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from sqlmodel import Session, select

from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.startup import build_orchestrator
from dashboard.models import AgentSnapshot, TaskRun, utc_now


class DashboardService:
    def __init__(self, engine, dry_run_default: bool = True):
        self.engine = engine
        self.dry_run_default = dry_run_default

    def sync_agents(self) -> list[AgentSnapshot]:
        config = load_firm_config()
        with Session(self.engine) as session:
            for definition in config.agents:
                snapshot = session.get(AgentSnapshot, definition.id)
                if snapshot is None:
                    snapshot = AgentSnapshot(
                        id=definition.id,
                        name=definition.name,
                        role=definition.role,
                        department=definition.department,
                        goal=definition.goal,
                    )
                    session.add(snapshot)
                else:
                    snapshot.name = definition.name
                    snapshot.role = definition.role
                    snapshot.department = definition.department
                    snapshot.goal = definition.goal
                    snapshot.updated_at = utc_now()
            session.commit()
            return list(session.exec(select(AgentSnapshot).order_by(AgentSnapshot.department, AgentSnapshot.name)))

    def list_agents(self) -> list[AgentSnapshot]:
        return self.sync_agents()

    def list_runs(self) -> list[TaskRun]:
        with Session(self.engine) as session:
            return list(session.exec(select(TaskRun).order_by(TaskRun.created_at.desc())))

    def get_run(self, run_id: int) -> TaskRun | None:
        with Session(self.engine) as session:
            return session.get(TaskRun, run_id)

    def run_task(self, prompt: str, auto_approve: bool, dry_run: bool | None = None) -> TaskRun:
        selected_dry_run = self.dry_run_default if dry_run is None else dry_run
        with Session(self.engine) as session:
            run = TaskRun(prompt=prompt, status="running", agent_id="", dry_run=selected_dry_run)
            session.add(run)
            session.commit()
            session.refresh(run)

        args = Namespace(
            config=str(Path("custom_agents/agentic_it_firm/configs/agents.json")),
            env=str(Path("custom_agents/agentic_it_firm/.env")),
            auto_approve=auto_approve,
            dry_run=selected_dry_run,
        )
        orchestrator = build_orchestrator(args)
        result = orchestrator.execute(prompt)
        output = Path(result.output_file).read_text(encoding="utf-8")

        with Session(self.engine) as session:
            run = session.get(TaskRun, run.id)
            assert run is not None
            run.status = result.status
            run.agent_id = result.agent_id
            run.approval_requested = result.approval.requested
            run.approval_approved = result.approval.approved
            run.output = output
            run.output_file = str(result.output_file)
            run.completed_at = utc_now()
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
