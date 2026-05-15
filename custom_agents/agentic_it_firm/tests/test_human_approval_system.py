import json
from pathlib import Path

from custom_agents.agentic_it_firm.agents.orchestrator.human_approval_agent import HumanApprovalAgent
from custom_agents.agentic_it_firm.approvals.approval_logger import ApprovalAuditLogger
from custom_agents.agentic_it_firm.approvals.approval_manager import ApprovalManager, RiskScorer
from custom_agents.agentic_it_firm.approvals.approval_queue import ApprovalQueue, ApprovalRequest
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition
from custom_agents.agentic_it_firm.llm_config import LLMResult, TokenUsage
from custom_agents.agentic_it_firm.tools.approvals import ApprovalCheckpoint


class FakeModelManager:
    def agent_model_config(self, model=None):
        return {
            "model": model or "nvidia_nim/meta/llama3-70b-instruct",
            "api_key": "nvapi-test",
            "base_url": "https://integrate.api.nvidia.com/v1",
        }

    def complete(self, request):
        return LLMResult(
            content="Approval analysis generated.",
            model="nvidia_nim/meta/llama3-70b-instruct",
            usage=TokenUsage(total_tokens=10),
            latency_ms=5,
            estimated_cost=None,
            attempts=1,
        )


def human_approval_definition():
    return AgentDefinition(
        id="human_approval_agent",
        name="Human Approval Agent",
        role="Human Approval Coordinator",
        department="Executive Operations",
        expertise=["risk review", "approval workflows", "audit logging"],
        years_of_experience=10,
        goal="Summarize risky actions for human decision makers.",
        instructions="Create approval summaries with risks, rollback considerations, and recommended action.",
        capabilities=["approval", "risk_scoring", "audit"],
        allowed_actions=["approve", "reject", "summarize", "audit"],
        restricted_actions=["auto approve high risk"],
        memory_enabled=True,
    )


def test_risk_scorer_detects_required_approval_actions():
    scorer = RiskScorer()

    score = scorer.score("Deploy to production and update database credentials")

    assert score.score >= 90
    assert "production deployment" in score.triggers
    assert "changing credentials" in score.triggers
    assert score.requires_approval is True


def test_approval_queue_persists_pending_and_history(tmp_path: Path):
    queue = ApprovalQueue(tmp_path / "approvals.json")
    request = ApprovalRequest.create(
        action="production deployment",
        requested_by="devops_engineer",
        summary="Deploy client portal",
        risk_score=95,
        risks=["downtime"],
        rollback_considerations=["rollback previous release"],
        recommended_action="approve with maintenance window",
    )

    queue.enqueue(request)
    queue.decide(request.request_id, approved=False, decided_by="human", reason="Need rollback plan")

    reloaded = ApprovalQueue(tmp_path / "approvals.json")
    assert reloaded.pending() == []
    assert reloaded.history()[0].decision == "rejected"
    assert json.loads((tmp_path / "approvals.json").read_text(encoding="utf-8"))["history"]


def test_approval_logger_writes_audit_jsonl(tmp_path: Path):
    logger = ApprovalAuditLogger(tmp_path / "approval_audit.jsonl")
    request = ApprovalRequest.create(
        action="deleting files",
        requested_by="backend_engineer",
        summary="Delete generated cache",
        risk_score=80,
        risks=["data loss"],
        rollback_considerations=["restore from backup"],
        recommended_action="reject until backup is confirmed",
    )

    logger.log_request(request)
    logger.log_decision(request, "approved", "human", "Backup confirmed")

    contents = (tmp_path / "approval_audit.jsonl").read_text(encoding="utf-8")
    assert "approval_requested" in contents
    assert "approval_decided" in contents


def test_approval_manager_creates_summary_and_handles_rejection(tmp_path: Path):
    manager = ApprovalManager(
        queue=ApprovalQueue(tmp_path / "approvals.json"),
        audit_logger=ApprovalAuditLogger(tmp_path / "approval_audit.jsonl"),
        prompt=lambda _: "n",
    )

    decision = manager.request_approval(
        action="spending money on a cloud upgrade",
        requested_by="project_manager",
        why_needed="Increase capacity for launch",
    )

    assert decision.approved is False
    assert decision.requested is True
    assert "Human rejected" in decision.reason
    assert manager.queue.history()[0].decision == "rejected"


def test_approval_checkpoint_uses_manager_for_required_actions(tmp_path: Path):
    manager = ApprovalManager(
        queue=ApprovalQueue(tmp_path / "approvals.json"),
        audit_logger=ApprovalAuditLogger(tmp_path / "approval_audit.jsonl"),
        prompt=lambda _: "y",
    )
    checkpoint = ApprovalCheckpoint(manager=manager)

    decision = checkpoint.request(
        "Modify secrets for production deployment",
        "task contains approval-controlled term 'secret'",
        required=True,
    )

    assert decision.approved is True
    assert manager.queue.history()[0].decision == "approved"


def test_human_approval_agent_summarizes_risky_action():
    agent = HumanApprovalAgent(human_approval_definition(), FakeModelManager(), dry_run=True)

    summary = agent.summarize_request(
        action="Change database credentials",
        why_needed="Rotate compromised password",
        requested_by="security_reviewer",
    )

    assert summary["what_action_is_requested"] == "Change database credentials"
    assert summary["why_it_is_needed"] == "Rotate compromised password"
    assert summary["possible_risks"]
    assert summary["rollback_considerations"]
    assert summary["recommended_action"]
