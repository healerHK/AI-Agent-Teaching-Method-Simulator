from app.blinding import AnnotationService, BlindedReviewService
from app.evaluator_models import AnnotationRequest
from app.evaluator_runner import EvaluatorRunner
from app.evidence_verifier import EvidenceVerifier


def test_blinded_review_hides_actual_conditions_and_annotation_saves(monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    runner = EvaluatorRunner()
    verifier = EvidenceVerifier()
    review_service = BlindedReviewService(runner)
    annotation_service = AnnotationService()

    baseline_id, experiment_id, _ = runner.run(transcript_id="python_loops_weak_001", condition="baseline")
    til_id, _, _ = runner.run(transcript_id="python_loops_weak_001", condition="til", experiment_id=experiment_id)
    verifier.verify_evaluation(baseline_id)
    verifier.verify_evaluation(til_id)

    review = review_service.create_review(
        transcript_id="python_loops_weak_001",
        reviewer_id="test_reviewer",
        evaluation_ids=[baseline_id, til_id],
    )

    assert [item.display_label for item in review.blinded_evaluations] == ["Evaluation A", "Evaluation B"]
    assert all(item.feedback_items for item in review.blinded_evaluations)
    labels_text = str(review.model_dump())
    assert "actual_condition" not in labels_text
    assert "evaluator_condition" not in labels_text

    first_eval = review.blinded_evaluations[0]
    first_item = first_eval.feedback_items[0]
    saved = annotation_service.save_annotation(
        AnnotationRequest(
            reviewer_id="test_reviewer",
            evaluation_id=first_eval.evaluation_id,
            feedback_item_id=first_item.feedback_item_id,
            blinded_label=first_eval.display_label,
            criterion=first_item.criterion,
            ai_score=first_item.score,
            human_score=first_item.score,
            accept=True,
            usefulness=4,
        )
    )
    assert saved.saved is True
    assert saved.annotation_id.startswith("ann_")
