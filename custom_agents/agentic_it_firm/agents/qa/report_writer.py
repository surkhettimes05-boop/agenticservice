"""Markdown QA report generation."""

from __future__ import annotations


class QAReportWriter:
    """Render QA workflow output as a human-readable markdown report."""

    def to_markdown(self, report: dict) -> str:
        workflow_name = report.get("workflow_name", "QA Workflow")
        summary = report.get("summary", {})
        readiness = report.get("release_readiness", {})
        lines = [
            f"# QA Report: {workflow_name}",
            "",
            "## Summary",
            f"- Total tests: {summary.get('total', 0)}",
            f"- Passed: {summary.get('passed', 0)}",
            f"- Failed: {summary.get('failed', 0)}",
            f"- Quality score: {summary.get('quality_score', 0)}",
            f"- Release readiness score: {readiness.get('score', 0)}",
            f"- Release recommendation: {readiness.get('recommendation', 'hold')}",
            "",
            "## Pass/Fail Results",
            "| Test Case | Status | Acceptance Criteria |",
            "| --- | --- | --- |",
        ]
        for result in report.get("results", []):
            lines.append(
                f"| {result.get('test_case_id', '')} | {result.get('status', '')} | {result.get('acceptance_criteria', '')} |"
            )
        lines.extend(["", "## Structured Bug Log"])
        bugs = report.get("bug_log", {}).get("bugs", [])
        if not bugs:
            lines.append("No open bugs.")
        for bug in bugs:
            lines.append(f"- {bug.get('id')}: {bug.get('severity')} - {bug.get('title')}")
        lines.extend(
            [
                "",
                "## Release Recommendation",
                f"Release recommendation: {readiness.get('recommendation', 'hold')}",
                "",
            ]
        )
        return "\n".join(lines)
