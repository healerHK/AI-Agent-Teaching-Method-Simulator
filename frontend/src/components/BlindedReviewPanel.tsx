import type { BlindedEvaluationView, Phase3DemoResponse, FeedbackItemView } from '../types';

interface BlindedReviewPanelProps {
  demo: Phase3DemoResponse;
  savedAnnotations: string[];
  onAnnotate: (label: string, evaluationId: string, item: FeedbackItemView, accept: boolean) => void;
  onReset: () => void;
}

export function BlindedReviewPanel({ demo, savedAnnotations, onAnnotate, onReset }: BlindedReviewPanelProps) {
  return (
    <main className="review-shell">
      <section className="review-header pixel-panel">
        <div>
          <p className="eyebrow">Golden benchmark review</p>
          <h1>Blinded Evaluation A/B</h1>
          <p>
            Transcript: <strong>{demo.transcript_id}</strong>. Conditions are hidden from the reviewer.
          </p>
        </div>
        <button className="pixel-button secondary" onClick={onReset}>Back</button>
      </section>

      <section className="verification-strip">
        <StatusCard title="Baseline verification" status={demo.baseline_verification.overall_status} />
        <StatusCard title="TIL verification" status={demo.til_verification.overall_status} />
        <StatusCard title="Saved annotations" status={`${savedAnnotations.length}`} />
      </section>

      <section className="blind-grid">
        {demo.blinded_review.blinded_evaluations.map((evaluation) => (
          <EvaluationColumn
            key={evaluation.display_label}
            evaluation={evaluation}
            savedAnnotations={savedAnnotations}
            onAnnotate={onAnnotate}
          />
        ))}
      </section>
    </main>
  );
}

function StatusCard({ title, status }: { title: string; status: string }) {
  return (
    <article className="status-card pixel-panel">
      <span className="label">{title}</span>
      <strong className={status === 'verified' ? 'ok' : 'warn'}>{status}</strong>
    </article>
  );
}

function EvaluationColumn({
  evaluation,
  savedAnnotations,
  onAnnotate,
}: {
  evaluation: BlindedEvaluationView;
  savedAnnotations: string[];
  onAnnotate: (label: string, evaluationId: string, item: FeedbackItemView, accept: boolean) => void;
}) {
  return (
    <article className="evaluation-column pixel-panel">
      <div className="panel-heading">
        <h2>{evaluation.display_label}</h2>
        <span>{evaluation.feedback_items.length} items</span>
      </div>
      <div className="feedback-list">
        {evaluation.feedback_items.map((item) => {
          const saved = savedAnnotations.includes(item.feedback_item_id);
          return (
            <section className="feedback-card" key={item.feedback_item_id}>
              <div className="feedback-topline">
                <strong>{item.criterion.replace(/_/g, ' ')}</strong>
                <span className={item.verification_status === 'verified' ? 'badge ok' : 'badge warn'}>
                  {item.verification_status ?? 'unverified'}
                </span>
              </div>
              <p>{item.claim}</p>
              <div className="score-row">
                <span>Score: {item.score ?? 'n/a'}</span>
                <span>Confidence: {item.confidence ?? 'n/a'}</span>
              </div>
              {item.evidence.length > 0 ? (
                <ul className="evidence-list">
                  {item.evidence.map((evidence) => (
                    <li key={`${item.feedback_item_id}-${evidence.turn_id}`}>
                      <code>{evidence.turn_id}</code> {evidence.evidence_quote}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">No evidence supplied.</p>
              )}
              {item.suggested_action && <p className="suggestion">Action: {item.suggested_action}</p>}
              <div className="annotation-actions">
                <button
                  className="pixel-button small"
                  disabled={saved}
                  onClick={() => onAnnotate(evaluation.display_label, evaluation.evaluation_id, item, true)}
                >
                  {saved ? 'Saved' : 'Accept'}
                </button>
                <button
                  className="pixel-button small secondary"
                  disabled={saved}
                  onClick={() => onAnnotate(evaluation.display_label, evaluation.evaluation_id, item, false)}
                >
                  Reject
                </button>
              </div>
            </section>
          );
        })}
      </div>
    </article>
  );
}
