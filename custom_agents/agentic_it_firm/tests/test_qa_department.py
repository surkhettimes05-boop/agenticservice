from custom_agents.agentic_it_firm.agents.qa import (
    BugDetectionAgent,
    BugReportBuilder,
    QAAgent_CLASSES,
    QAReportWriter,
    QARegressionWorkflow,
    QAReleaseReadinessScorer,
    QATeamLeaderAgent,
    QAValidatorAgent,
    RegressionTestingAgent,
    TestCaseAgent,
    TestCaseGenerator,
)
from custom_agents.agentic_it_firm.agents.registry import AgentRegistry
from custom_agents.agentic_it_firm.configs.loader import AgentDefinition, FirmConfig, NvidiaConfig, RouteDefinition, SystemConfig
from custom_agents.agentic_it_firm.llm_config import LLMResult, TokenUsage


class FakeModelManager:
    def agent_model_config(self, model=None):
        return {
            "model": model or "nvidia_nim/meta/llama3-70b-instruct",
            "api_key": "nvapi-test",
            "base_url": "https://integrate.api.nvidia.com/v1",
        }

    def complete(self, request):
        return LLMResult(
            content="Generated QA department output.",
            model="nvidia_nim/meta/llama3-70b-instruct",
            usage=TokenUsage(total_tokens=10),
            latency_ms=1,
            estimated_cost=None,
            attempts=1,
        )


def agent_definition(agent_id: str, name: str, role: str) -> AgentDefinition:
    return AgentDefinition(
        id=agent_id,
        name=name,
        role=role,
        department="QA",
        expertise=["test planning", "validation", "bug reporting", "regression testing"],
        years_of_experience=7,
        goal=f"Handle {role} responsibilities.",
        instructions=f"You are the {role} for the QA department.",
        capabilities=["qa"],
        allowed_actions=["plan", "validate", "test", "review", "report"],
        restricted_actions=["delete", "deploy"],
        memory_enabled=True,
    )


def test_test_case_generator_creates_acceptance_criteria_cases():
    generator = TestCaseGenerator()

    cases = generator.generate(
        "User can log in and view dashboard",
        ["valid user reaches dashboard", "invalid password shows error"],
    )

    assert len(cases) == 2
    assert cases[0]["id"] == "TC-001"
    assert cases[0]["acceptance_criteria"] == "valid user reaches dashboard"
    assert cases[0]["expected_result"]
    assert cases[1]["priority"] == "high"


def test_validator_returns_pass_fail_summary_and_quality_score():
    validator = QAValidatorAgent(agent_definition("qa_validator", "QA Validator", "QA Validator"), FakeModelManager(), dry_run=True)
    cases = TestCaseGenerator().generate("Checkout", ["cart total is correct", "receipt email is sent"])
    evidence = {"cart total is correct": True, "receipt email is sent": False}

    report = validator.validate_acceptance_criteria(cases, evidence)

    assert report["summary"]["total"] == 2
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 1
    assert report["summary"]["quality_score"] == 50
    assert report["results"][1]["status"] == "fail"


def test_bug_report_builder_creates_structured_bug_log():
    builder = BugReportBuilder()

    bug_log = builder.from_validation_results(
        [
            {
                "test_case_id": "TC-002",
                "status": "fail",
                "acceptance_criteria": "receipt email is sent",
                "actual_result": "No evidence provided.",
            }
        ],
        workflow_name="checkout_release",
    )

    assert bug_log["workflow_name"] == "checkout_release"
    assert bug_log["summary"]["open_bugs"] == 1
    assert bug_log["bugs"][0]["severity"] == "medium"
    assert bug_log["bugs"][0]["status"] == "open"


def test_regression_workflow_scores_release_readiness():
    workflow = QARegressionWorkflow()
    baseline = ["login works", "dashboard loads"]
    current = {"login works": True, "dashboard loads": True}

    report = workflow.run("portal release", baseline, current)

    assert report["workflow_name"] == "portal release"
    assert report["summary"]["failed"] == 0
    assert report["release_readiness"]["recommendation"] == "ready"


def test_qa_report_writer_outputs_markdown_release_recommendation():
    report = {
        "workflow_name": "portal release",
        "summary": {"total": 2, "passed": 1, "failed": 1, "quality_score": 50},
        "results": [{"test_case_id": "TC-001", "status": "pass", "acceptance_criteria": "login works"}],
        "bug_log": {"bugs": [{"id": "BUG-001", "severity": "medium", "title": "Missing expected behavior"}]},
        "release_readiness": {"score": 50, "recommendation": "hold"},
    }

    markdown = QAReportWriter().to_markdown(report)

    assert "# QA Report: portal release" in markdown
    assert "Release recommendation: hold" in markdown
    assert "| TC-001 | pass | login works |" in markdown
    assert "BUG-001" in markdown


def test_qa_agents_generate_structured_outputs():
    leader = QATeamLeaderAgent(agent_definition("qa_team_leader", "QA Team Leader", "QA Team Leader"), FakeModelManager(), dry_run=True)
    test_case_agent = TestCaseAgent(agent_definition("test_case_agent", "Test Case Agent", "Test Case Agent"), FakeModelManager(), dry_run=True)
    bug_agent = BugDetectionAgent(agent_definition("bug_detection_agent", "Bug Detection Agent", "Bug Detection Agent"), FakeModelManager(), dry_run=True)
    regression_agent = RegressionTestingAgent(agent_definition("regression_testing_agent", "Regression Testing Agent", "Regression Testing Agent"), FakeModelManager(), dry_run=True)

    qa_plan = leader.plan_quality_workflow("Release client portal", ["login works"])
    cases = test_case_agent.generate_test_cases("Release client portal", ["login works"])
    bug_log = bug_agent.detect_bugs([{"test_case_id": "TC-001", "status": "fail", "acceptance_criteria": "login works"}])
    regression = regression_agent.run_regression("portal release", ["login works"], {"login works": True})

    assert qa_plan["department"] == "QA"
    assert cases[0]["id"] == "TC-001"
    assert bug_log["summary"]["open_bugs"] == 1
    assert regression["release_readiness"]["recommendation"] == "ready"


def test_registry_instantiates_qa_specialists(tmp_path):
    config = FirmConfig(
        system=SystemConfig(name="Agentic IT Firm", default_model="nvidia_nim/meta/llama3-70b-instruct"),
        agents=[
            agent_definition("qa_team_leader", "QA Team Leader", "QA Team Leader"),
            agent_definition("test_case_agent", "Test Case Agent", "Test Case Agent"),
            agent_definition("qa_validator", "QA Validator", "QA Validator"),
            agent_definition("bug_detection_agent", "Bug Detection Agent", "Bug Detection Agent"),
            agent_definition("regression_testing_agent", "Regression Testing Agent", "Regression Testing Agent"),
        ],
        routes=[RouteDefinition(keywords=["qa"], agent_id="qa_team_leader")],
        nvidia=NvidiaConfig(api_key="nvapi-test"),
        root_dir=tmp_path,
    )

    registry = AgentRegistry.from_config(config, dry_run=True, model_manager=FakeModelManager())

    assert isinstance(registry.get("qa_team_leader"), QATeamLeaderAgent)
    assert isinstance(registry.get("test_case_agent"), TestCaseAgent)
    assert isinstance(registry.get("qa_validator"), QAValidatorAgent)
    assert isinstance(registry.get("bug_detection_agent"), BugDetectionAgent)
    assert isinstance(registry.get("regression_testing_agent"), RegressionTestingAgent)
    assert "qa_team_leader" in QAAgent_CLASSES
