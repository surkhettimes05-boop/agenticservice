"""Release readiness scoring for QA workflows."""

from __future__ import annotations


class QAReleaseReadinessScorer:
    """Convert validation and bug state into release guidance."""

    def score(self, summary: dict[str, int], bug_log: dict | None = None) -> dict[str, int | str]:
        total = int(summary.get("total", 0))
        passed = int(summary.get("passed", 0))
        failed = int(summary.get("failed", 0))
        open_bugs = 0
        if bug_log:
            open_bugs = int(bug_log.get("summary", {}).get("open_bugs", 0))
        quality_score = int(round((passed / total) * 100)) if total else 0
        penalty = min(open_bugs * 10, 40)
        readiness_score = max(0, quality_score - penalty)
        recommendation = "ready" if failed == 0 and open_bugs == 0 and readiness_score >= 90 else "hold"
        if recommendation == "hold" and readiness_score >= 75 and failed <= 1:
            recommendation = "conditional"
        return {
            "score": readiness_score,
            "quality_score": quality_score,
            "open_bugs": open_bugs,
            "recommendation": recommendation,
        }
