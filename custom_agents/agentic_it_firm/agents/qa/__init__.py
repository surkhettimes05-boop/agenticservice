"""QA Department agents and workflows."""

from .bug_report import BugReportBuilder
from .qa_agents import (
    BugDetectionAgent,
    QAReadinessAgent,
    QAReportAgent,
    QATeamLeaderAgent,
    QAValidatorAgent,
    RegressionTestingAgent,
    TestCaseAgent,
)
from .regression_workflow import QARegressionWorkflow
from .release_readiness import QAReleaseReadinessScorer
from .report_writer import QAReportWriter
from .test_case_generator import TestCaseGenerator
from .validation import AcceptanceCriteriaValidator

QA_AGENT_CLASSES = {
    "qa_team_leader": QATeamLeaderAgent,
    "test_case_agent": TestCaseAgent,
    "qa_validator": QAValidatorAgent,
    "bug_detection_agent": BugDetectionAgent,
    "regression_testing_agent": RegressionTestingAgent,
}
QAAgent_CLASSES = QA_AGENT_CLASSES

__all__ = [
    "AcceptanceCriteriaValidator",
    "BugDetectionAgent",
    "BugReportBuilder",
    "QAAgent_CLASSES",
    "QAReadinessAgent",
    "QAReportAgent",
    "QARegressionWorkflow",
    "QAReleaseReadinessScorer",
    "QAReportWriter",
    "QA_AGENT_CLASSES",
    "QATeamLeaderAgent",
    "QAValidatorAgent",
    "RegressionTestingAgent",
    "TestCaseAgent",
    "TestCaseGenerator",
]
