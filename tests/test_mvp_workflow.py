from pathlib import Path

from custom_agents.agentic_it_firm.workflows.mvp_workflow import MVPWorkflow


def test_mvp_workflow_creates_delivery_package(tmp_path: Path):
    workflow = MVPWorkflow.local(deliveries_root=tmp_path, dry_run=True, auto_approve=True)

    result = workflow.run("Build a client portal for ACME with dashboard, API, QA, and docs.")

    assert result.status == "completed"
    assert result.delivery_dir.exists()
    assert (result.delivery_dir / "project_summary.md").exists()
    assert (result.delivery_dir / "implementation" / "implementation_plan.md").exists()
    assert (result.delivery_dir / "qa_report.md").exists()
    assert (result.delivery_dir / "documentation.md").exists()
    assert (result.delivery_dir / "revenue_package.md").exists()
    assert (result.delivery_dir / "delivery_manifest.json").exists()
    assert result.state.completed_stages[-1] == "final_delivery"


def test_mvp_workflow_resume_skips_completed_stages(tmp_path: Path):
    workflow = MVPWorkflow.local(deliveries_root=tmp_path, dry_run=True, auto_approve=True)
    first = workflow.run("Build an internal ops dashboard.")

    resumed = workflow.resume(first.state_path)

    assert resumed.status == "completed"
    assert resumed.state.completed_stages == first.state.completed_stages
