"""Regression workflow support for QA Department agents."""

from __future__ import annotations

from custom_agents.agentic_it_firm.agents.qa.bug_report import BugReportBuilder
from custom_agents.agentic_it_firm.agents.qa.release_readiness import QAReleaseReadinessScorer
from custom_agents.agentic_it_firm.agents.qa.test_case_generator import TestCaseGenerator
from custom_agents.agentic_it_firm.agents.qa.validation import AcceptanceCriteriaValidator


class QARegressionWorkflow:
    """Run a baseline regression check and produce release guidance."""

    def __init__(
        self,
        test_case_generator: TestCaseGenerator | None = None,
        validator: AcceptanceCriteriaValidator | None = None,
        bug_report_builder: BugReportBuilder | None = None,
        readiness_scorer: QAReleaseReadinessScorer | None = None,
    ):
        self.test_case_generator = test_case_generator or TestCaseGenerator()
        self.validator = validator or AcceptanceCriteriaValidator()
        self.bug_report_builder = bug_report_builder or BugReportBuilder()
        self.readiness_scorer = readiness_scorer or QAReleaseReadinessScorer()

    def run(self, workflow_name: str, baseline_criteria: list[str], current_evidence: dict[str, bool | str]) -> dict:
        test_cases = self.test_case_generator.generate(workflow_name, baseline_criteria)
        validation = self.validator.validate(test_cases, current_evidence)
        bug_log = self.bug_report_builder.from_validation_results(validation["results"], workflow_name=workflow_name)
        release_readiness = self.readiness_scorer.score(validation["summary"], bug_log)
        return {
            "workflow_name": workflow_name,
            "test_cases": test_cases,
            "summary": validation["summary"],
            "results": validation["results"],
            "bug_log": bug_log,
            "release_readiness": release_readiness,
        }
