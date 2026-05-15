class AgentQualityEvaluator:
    REQUIRED_MARKERS = ["findings", "recommendation", "next steps"]

    def evaluate(self, role: str, output: str) -> dict:
        lower = output.lower()
        score = 43
        score += min(len(output) // 40, 20)
        score += 15 if role else 0
        score += sum(10 for marker in self.REQUIRED_MARKERS if marker in lower)
        score = min(score, 100)
        if score >= 90:
            grade = "excellent"
        elif score >= 75:
            grade = "strong"
        elif score >= 60:
            grade = "acceptable"
        else:
            grade = "needs_improvement"
        return {
            "role": role,
            "score": score,
            "grade": grade,
            "missing_markers": [marker for marker in self.REQUIRED_MARKERS if marker not in lower],
        }
