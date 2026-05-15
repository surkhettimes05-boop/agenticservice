"""Acceptance criteria validation for QA workflows."""

from __future__ import annotations


class AcceptanceCriteriaValidator:
    """Produce pass/fail reports from test cases and execution evidence."""

    def validate(self, test_cases: list[dict], evidence: dict[str, bool | str]) -> dict:
        results = []
        for test_case in test_cases:
            criteria = test_case["acceptance_criteria"]
            raw_status = evidence.get(criteria, False)
            passed = raw_status is True or str(raw_status).lower() in {"pass", "passed", "true", "ok"}
            results.append(
                {
                    "test_case_id": test_case["id"],
                    "title": test_case["title"],
                    "acceptance_criteria": criteria,
                    "expected_result": test_case["expected_result"],
                    "actual_result": "Evidence confirms expected behavior." if passed else "No passing evidence provided.",
                    "status": "pass" if passed else "fail",
                }
            )
        total = len(results)
        passed_count = len([result for result in results if result["status"] == "pass"])
        failed_count = total - passed_count
        quality_score = int(round((passed_count / total) * 100)) if total else 0
        return {
            "summary": {
                "total": total,
                "passed": passed_count,
                "failed": failed_count,
                "quality_score": quality_score,
            },
            "results": results,
        }
