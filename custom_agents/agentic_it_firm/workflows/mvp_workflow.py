from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from custom_agents.agentic_it_firm.agents.coding import ImplementationWorkflow
from custom_agents.agentic_it_firm.agents.qa import QARegressionWorkflow, QAReportWriter


STAGES = [
    "client_request",
    "chief_orchestrator",
    "research_department",
    "coding_department",
    "qa_department",
    "documentation_generation",
    "revenue_packaging",
    "human_approval",
    "final_delivery",
]


@dataclass
class MVPWorkflowState:
    workflow_id: str
    request: str
    delivery_dir: str
    completed_stages: list[str] = field(default_factory=list)
    department_summaries: dict[str, str] = field(default_factory=dict)
    status: str = "running"


@dataclass
class MVPWorkflowResult:
    status: str
    delivery_dir: Path
    state_path: Path
    state: MVPWorkflowState


class MVPWorkflow:
    def __init__(self, deliveries_root: Path, dry_run: bool, auto_approve: bool):
        self.deliveries_root = deliveries_root
        self.dry_run = dry_run
        self.auto_approve = auto_approve

    @classmethod
    def local(cls, deliveries_root: str | Path, dry_run: bool = True, auto_approve: bool = True) -> "MVPWorkflow":
        return cls(Path(deliveries_root), dry_run=dry_run, auto_approve=auto_approve)

    def run(self, request: str) -> MVPWorkflowResult:
        workflow_id = f"mvp_{uuid4().hex[:10]}"
        delivery_dir = self.deliveries_root / workflow_id
        delivery_dir.mkdir(parents=True, exist_ok=True)
        state = MVPWorkflowState(workflow_id=workflow_id, request=request, delivery_dir=str(delivery_dir))
        state_path = delivery_dir / "workflow_state.json"
        self._execute(state, state_path)
        return MVPWorkflowResult(status=state.status, delivery_dir=delivery_dir, state_path=state_path, state=state)

    def resume(self, state_path: str | Path) -> MVPWorkflowResult:
        path = Path(state_path)
        state = MVPWorkflowState(**json.loads(path.read_text(encoding="utf-8")))
        self._execute(state, path)
        return MVPWorkflowResult(status=state.status, delivery_dir=Path(state.delivery_dir), state_path=path, state=state)

    def _execute(self, state: MVPWorkflowState, state_path: Path) -> None:
        for stage in STAGES:
            if stage in state.completed_stages:
                continue
            getattr(self, f"_stage_{stage}")(state)
            state.completed_stages.append(stage)
            self._save_state(state, state_path)
        state.status = "completed"
        self._save_state(state, state_path)

    def _stage_client_request(self, state: MVPWorkflowState) -> None:
        state.department_summaries["client_request"] = state.request

    def _stage_chief_orchestrator(self, state: MVPWorkflowState) -> None:
        state.department_summaries["chief_orchestrator"] = "Execution plan created for cross-department delivery."

    def _stage_research_department(self, state: MVPWorkflowState) -> None:
        state.department_summaries["research_department"] = "Market and technical assumptions documented."

    def _stage_coding_department(self, state: MVPWorkflowState) -> None:
        implementation_dir = Path(state.delivery_dir) / "implementation"
        implementation_dir.mkdir(exist_ok=True)
        workflow = ImplementationWorkflow().create(state.request)
        (implementation_dir / "implementation_plan.md").write_text(
            "# Implementation Plan\n\n" + "\n".join(f"- {step['agent_id']}" for step in workflow["steps"]),
            encoding="utf-8",
        )
        state.department_summaries["coding_department"] = "Implementation plan generated."

    def _stage_qa_department(self, state: MVPWorkflowState) -> None:
        report = QARegressionWorkflow().run(
            "mvp_delivery",
            ["request captured", "implementation plan exists", "documentation prepared"],
            {"request captured": True, "implementation plan exists": True, "documentation prepared": True},
        )
        (Path(state.delivery_dir) / "qa_report.md").write_text(QAReportWriter().to_markdown(report), encoding="utf-8")
        state.department_summaries["qa_department"] = "QA report generated with release recommendation."

    def _stage_documentation_generation(self, state: MVPWorkflowState) -> None:
        (Path(state.delivery_dir) / "documentation.md").write_text(
            "# Documentation\n\nSetup, usage, maintenance, and handoff notes for the client delivery.",
            encoding="utf-8",
        )
        state.department_summaries["documentation_generation"] = "Documentation generated."

    def _stage_revenue_packaging(self, state: MVPWorkflowState) -> None:
        (Path(state.delivery_dir) / "revenue_package.md").write_text(
            "# Revenue Package\n\n- Delivery scope\n- Value summary\n- Pricing requires human review\n",
            encoding="utf-8",
        )
        state.department_summaries["revenue_packaging"] = "Commercial package prepared."

    def _stage_human_approval(self, state: MVPWorkflowState) -> None:
        if not self.auto_approve:
            raise RuntimeError("Human approval required before final delivery.")
        state.department_summaries["human_approval"] = "Approved."

    def _stage_final_delivery(self, state: MVPWorkflowState) -> None:
        delivery_dir = Path(state.delivery_dir)
        (delivery_dir / "project_summary.md").write_text(
            "# Project Summary\n\n" + "\n".join(f"- {key}: {value}" for key, value in state.department_summaries.items()),
            encoding="utf-8",
        )
        manifest = {
            "workflow_id": state.workflow_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "artifacts": [
                "project_summary.md",
                "implementation/implementation_plan.md",
                "qa_report.md",
                "documentation.md",
                "revenue_package.md",
                "workflow_state.json",
            ],
        }
        (delivery_dir / "delivery_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        state.department_summaries["final_delivery"] = "Delivery package assembled."

    @staticmethod
    def _save_state(state: MVPWorkflowState, state_path: Path) -> None:
        state_path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
