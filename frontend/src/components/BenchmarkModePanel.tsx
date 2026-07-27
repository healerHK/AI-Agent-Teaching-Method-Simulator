import type { FeedbackItemView, TranscriptBenchmarkRunResponse } from '../types';
import { BlindedReviewPanel } from './BlindedReviewPanel';

interface BenchmarkModePanelProps {
  benchmark: TranscriptBenchmarkRunResponse;
  savedAnnotations: string[];
  onAnnotate: (label: string, evaluationId: string, item: FeedbackItemView, accept: boolean) => void;
  onReset: () => void;
}

export function BenchmarkModePanel({ benchmark, savedAnnotations, onAnnotate, onReset }: BenchmarkModePanelProps) {
  return (
    <main className="benchmark-shell">
      <section className="review-header pixel-panel">
        <div>
          <p className="eyebrow">Transcript Benchmark Mode</p>
          <h1>Controlled Baseline vs TIL Evaluation</h1>
          <p>{benchmark.benchmark_protocol.main_claim_scope}</p>
        </div>
        <button className="pixel-button secondary" onClick={onReset}>Back</button>
      </section>

      <section className="verification-strip four">
        <StatusCard title="Transcript" status={benchmark.transcript_id} />
        <StatusCard title="Baseline verifier" status={benchmark.baseline_verification.overall_status} />
        <StatusCard title="TIL verifier" status={benchmark.til_verification.overall_status} />
        <StatusCard title="Annotations" status={`${benchmark.review_metrics.annotations_count + savedAnnotations.length}`} />
      </section>

      <section className="blueprint-grid">
        <article className="pixel-panel blueprint-card wide">
          <span className="label">Controlled pipeline</span>
          <ol className="pipeline-list">
            {benchmark.benchmark_protocol.pipeline.map((step) => <li key={step}>{step}</li>)}
          </ol>
          <p className="suggestion">Claim: {benchmark.thesis_positioning.safe_claim}</p>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Expert review metrics</span>
          <MetricLine label="Acceptance" value={benchmark.review_metrics.expert_acceptance_rate} />
          <MetricLine label="Correction" value={benchmark.review_metrics.correction_rate} />
          <MetricLine label="Rejection" value={benchmark.review_metrics.rejection_rate} />
          <MetricLine label="Evidence validity" value={benchmark.review_metrics.evidence_validity_rate} />
          <MetricLine label="Unsupported inference" value={benchmark.review_metrics.unsupported_inference_rate} />
          <small className="muted">Rates update after expert annotations are saved.</small>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Transcript sample</span>
          <div className="mini-transcript">
            {benchmark.transcript.turns.slice(0, 6).map((turn) => (
              <p key={turn.turn_id}><code>{turn.turn_id}</code> <strong>{turn.speaker_name}</strong>: {turn.message}</p>
            ))}
          </div>
        </article>
      </section>

      <BlindedReviewPanel
        demo={benchmark}
        savedAnnotations={savedAnnotations}
        onAnnotate={onAnnotate}
        onReset={onReset}
      />
    </main>
  );
}

function StatusCard({ title, status }: { title: string; status: string }) {
  const className = status === 'verified' ? 'ok' : status === 'unsupported' ? 'warn' : '';
  return (
    <article className="status-card pixel-panel">
      <span className="label">{title}</span>
      <strong className={className}>{status}</strong>
    </article>
  );
}

function MetricLine({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-line">
      <span>{label}</span>
      <strong>{Math.round(value * 100)}%</strong>
    </div>
  );
}
