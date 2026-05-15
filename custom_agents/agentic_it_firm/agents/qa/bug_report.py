"""Structured bug reporting for QA Department workflows."""

from __future__ import annotations

from datetime import UTC, datetime


class BugReportBuilder:
    """Create structured bug logs from failed validation results."""

    def from_validation_results(self, results: list[dict], workflow_name: str = "qa_workflow") -> dict:
        failed_results = [result for result in results if result.get("status") == "fail"]
        bugs = [
            {
                "id": f"BUG-{index:03d}",
                "title": f"Failed acceptance criterion: {result.get('acceptance_criteria', 'Unspecified')}",
                "severity": self._severity_for(result),
                "status": "open",
                "source_test_case": result.get("test_case_id"),
                "expected_result": result.get("expected_result", "Acceptance criterion should pass."),
                "actual_result": result.get("actual_result", "Validation failed."),
                "recommended_fix": "Investigate the failing behavior, add a regression test, and verify the acceptance criterion before release.",
            }
            for index, result in enumerate(failed_results, start=1)
        ]
        return {
            "workflow_name": workflow_name,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "open_bugs": len(bugs),
                "critical_bugs": len([bug for bug in bugs if bug["severity"] == "critical"]),
                "high_bugs": len([bug for bug in bugs if bug["severity"] == "high"]),
            },
            "bugs": bugs,
        }

    @staticmethod
    def _severity_for(result: dict) -> str:
        text = " ".join(str(value).lower() for value in result.values())
        if any(keyword in text for keyword in ["security", "payment", "data loss", "credential", "production"]):
            return "critical"
        if any(keyword in text for keyword in ["checkout", "login", "auth", "database", "api"]):
            return "high"
        return "medium"
