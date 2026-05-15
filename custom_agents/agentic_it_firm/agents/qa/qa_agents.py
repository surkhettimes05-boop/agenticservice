"""Specialized QA Department agents."""

from __future__ import annotations

from typing import Any

from custom_agents.agentic_it_firm.agents.base import BaseFirmAgent
from custom_agents.agentic_it_firm.agents.qa.bug_report import BugReportBuilder
from custom_agents.agentic_it_firm.agents.qa.regression_workflow import QARegressionWorkflow
from custom_agents.agentic_it_firm.agents.qa.release_readiness import QAReleaseReadinessScorer
from custom_agents.agentic_it_firm.agents.qa.report_writer import QAReportWriter
from custom_agents.agentic_it_firm.agents.qa.test_case_generator import TestCaseGenerator
from custom_agents.agentic_it_firm.agents.qa.validation import AcceptanceCriteriaValidator


class QATeamLeaderAgent(BaseFirmAgent):
    def plan_quality_workflow(self, project_request: str, acceptance_criteria: list[str]) -> dict[str, Any]:
        return {
            "agent_id": self.id,
            "department": "QA",
            "workflow": "qa_department_validation",
            "project_request": project_request,
            "acceptance_criteria": acceptance_criteria,
            "steps": [
                {"agent_id": "test_case_agent", "responsibility": "Generate acceptance and regression test cases."},
                {"agent_id": "qa_validator", "responsibility": "Validate pass/fail evidence against criteria."},
                {"agent_id": "bug_detection_agent", "responsibility": "Convert failures into structured bug logs."},
                {"agent_id": "regression_testing_agent", "responsibility": "Run baseline regression workflow."},
                {"agent_id": "qa_team_leader", "responsibility": "Score release readiness and issue recommendation."},
            ],
            "outputs": ["markdown QA report", "structured bug log", "release recommendation"],
        }


class TestCaseAgent(BaseFirmAgent):
    def generate_test_cases(self, project_request: str, acceptance_criteria: list[str]) -> list[dict[str, str]]:
        return TestCaseGenerator().generate(project_request, acceptance_criteria)


class QAValidatorAgent(BaseFirmAgent):
    def validate_acceptance_criteria(self, test_cases: list[dict], evidence: dict[str, bool | str]) -> dict:
        return AcceptanceCriteriaValidator().validate(test_cases, evidence)


class BugDetectionAgent(BaseFirmAgent):
    def detect_bugs(self, validation_results: list[dict], workflow_name: str = "qa_workflow") -> dict:
        return BugReportBuilder().from_validation_results(validation_results, workflow_name=workflow_name)


class RegressionTestingAgent(BaseFirmAgent):
    def run_regression(
        self,
        workflow_name: str,
        baseline_criteria: list[str],
        current_evidence: dict[str, bool | str],
    ) -> dict:
        return QARegressionWorkflow().run(workflow_name, baseline_criteria, current_evidence)


class QAReportAgent(BaseFirmAgent):
    def render_markdown(self, qa_report: dict) -> str:
        return QAReportWriter().to_markdown(qa_report)


class QAReadinessAgent(BaseFirmAgent):
    def score_release(self, summary: dict[str, int], bug_log: dict | None = None) -> dict[str, int | str]:
        return QAReleaseReadinessScorer().score(summary, bug_log)
