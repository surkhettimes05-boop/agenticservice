"""Static code review pipeline for coding agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from custom_agents.agentic_it_firm.agents.coding.repository_context import RepositoryContextLoader


class CodeReviewPipeline:
    def review(self, root: str | Path) -> dict[str, Any]:
        context = RepositoryContextLoader(root).load()
        findings = []
        for rel_path, content in context.files.items():
            lowered = content.lower()
            if "password" in lowered or "secret" in lowered or "api_key" in lowered:
                findings.append(self._finding(rel_path, "high", "Possible hardcoded secret or credential."))
            if "eval(" in lowered:
                findings.append(self._finding(rel_path, "high", "Use of eval can execute unsafe code."))
            if "except exception" in lowered and "pass" in lowered:
                findings.append(self._finding(rel_path, "medium", "Broad exception handling hides failures."))
            if len(content.splitlines()) > 400:
                findings.append(self._finding(rel_path, "medium", "Large file may need decomposition."))
        return {
            "summary": {
                "file_count": len(context.files),
                "risk_count": len(findings),
                "detected_stack": context.detected_stack,
            },
            "findings": findings,
            "recommendations": self._recommendations(findings),
        }

    @staticmethod
    def _finding(path: str, severity: str, message: str) -> dict[str, str]:
        return {"path": path, "severity": severity, "message": message}

    @staticmethod
    def _recommendations(findings: list[dict[str, str]]) -> list[str]:
        if not findings:
            return ["No code smells detected by the static review pipeline."]
        recommendations = ["Address high severity findings before release."]
        if any("secret" in item["message"].lower() for item in findings):
            recommendations.append("Move secrets to environment variables or a managed secret store.")
        if any("eval" in item["message"].lower() for item in findings):
            recommendations.append("Replace dynamic evaluation with explicit parsing or whitelisted dispatch.")
        return recommendations
