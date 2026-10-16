from app.evaluator_runner import EvaluatorRunner
from app.evidence_verifier import EvidenceVerifier


def test_til_evaluator_fallback_produces_verified_evidence(monkeypatch):
    monkeypatch.delenv("EVALUATOR_API_KEY", raising=False)
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    runner = EvaluatorRunner()
    verifier = EvidenceVerifier()

    evaluation_id, experiment_id, output = runner.run(
        transcript_id="python_loops_weak_001",
        condition="til",
    )
    verification = verifier.verify_evaluation(evaluation_id)

    assert experiment_id.startswith("exp_")
    assert output.condition == "til"
    assert output.feedback_items
    assert verification.overall_status == "verified"


def test_baseline_evaluator_missing_evidence_is_detected(monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    runner = EvaluatorRunner()
    verifier = EvidenceVerifier()

    evaluation_id, _, output = runner.run(
        transcript_id="python_loops_weak_001",
        condition="baseline",
    )
    verification = verifier.verify_evaluation(evaluation_id)

    assert output.condition == "baseline"
    assert verification.overall_status == "unsupported"
    assert any(item.status == "missing_evidence" for item in verification.items)
