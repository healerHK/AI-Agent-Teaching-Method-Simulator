import type { EvaluatorStatusResponse } from '../types';

interface ModeSelectProps {
  onOpenTranscriptSystem: () => void;
  onShowScenario: () => void;
  onRunBenchmark: () => void;
  loading: boolean;
  evaluatorStatus: EvaluatorStatusResponse | null;
}

export function ModeSelect({ onOpenTranscriptSystem, onShowScenario, onRunBenchmark, loading, evaluatorStatus }: ModeSelectProps) {
  return (
    <section className="mode-select pixel-panel transcript-first-home">
      <div className="mode-copy">
        <p className="eyebrow">PixelClass TIL · Transcript-first build</p>
        <h1>Build Fixed Classroom Transcripts Before Live Mode</h1>
        <p>
          Current priority: create editable 30-minute classroom scenarios across subjects and levels,
          tune student prompt parameters, and run transcript readiness checks before evaluator testing.
        </p>
        <div className="provider-status-card">
          <span className="label">Evaluator runtime status</span>
          {evaluatorStatus ? (
            <>
              <div className="provider-status-list">
                {evaluatorStatus.conditions.map((condition) => (
                  <span key={condition.condition} className="provider-pill">
                    {condition.condition.toUpperCase()} · {condition.provider}:{condition.model}
                    {condition.api_key_configured ? ' · key configured' : ' · fallback only'}
                  </span>
                ))}
              </div>
              <small>{evaluatorStatus.fallback_policy}</small>
            </>
          ) : (
            <small>Provider status loading; deterministic fallback remains available.</small>
          )}
        </div>
      </div>

      <div className="mode-grid">
        <button className="mode-card primary" onClick={onOpenTranscriptSystem} disabled={loading}>
          <span className="mode-icon">▥</span>
          <strong>Transcript Scenario System</strong>
          <small>Pick/edit 30-minute scenarios, tune student prompts, save, and run readiness tests</small>
        </button>
        <button className="mode-card" onClick={onShowScenario} disabled={loading}>
          <span className="mode-icon">▤</span>
          <strong>Thesis Blueprint</strong>
          <small>Research gap, contribution, benchmark framing, and claim guardrails</small>
        </button>
        <button className="mode-card accent" onClick={onRunBenchmark} disabled={loading}>
          <span className="mode-icon">◇</span>
          <strong>Existing Benchmark A/B Review</strong>
          <small>Use current golden transcript baseline vs TIL path after transcripts are ready</small>
        </button>
        <button className="mode-card disabled" disabled>
          <span className="mode-icon">▣</span>
          <strong>Live Mode paused</strong>
          <small>Per current plan, live classroom mode will be rebuilt after transcript system is stable</small>
        </button>
      </div>
    </section>
  );
}
