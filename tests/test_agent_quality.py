from custom_agents.agentic_it_firm.quality import AgentQualityEvaluator


def test_quality_evaluator_scores_structured_complete_outputs():
    evaluator = AgentQualityEvaluator()

    report = evaluator.evaluate(
        role="Code Review Agent",
        output="## Findings\n- Risk identified\n## Recommendation\n- Add tests\n## Next Steps\n- Fix issue",
    )

    assert report["score"] >= 90
    assert report["grade"] == "excellent"
