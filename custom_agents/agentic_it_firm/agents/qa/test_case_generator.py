"""Test case generation for QA Department workflows."""

from __future__ import annotations


class TestCaseGenerator:
    """Build structured test cases from acceptance criteria."""

    def generate(self, project_request: str, acceptance_criteria: list[str]) -> list[dict[str, str]]:
        return [
            {
                "id": f"TC-{index:03d}",
                "title": self._title_for(criteria),
                "project_request": project_request,
                "acceptance_criteria": criteria,
                "priority": "high",
                "test_type": "acceptance",
                "steps": f"Validate that: {criteria}",
                "expected_result": f"System behavior satisfies acceptance criterion: {criteria}",
            }
            for index, criteria in enumerate(acceptance_criteria, start=1)
        ]

    @staticmethod
    def _title_for(criteria: str) -> str:
        normalized = " ".join(criteria.strip().split())
        return normalized[:80] or "Acceptance criterion validation"
