import type { EvaluatorStatusResponse } from '../types';

interface ModeSelectProps {
  onShowScenario: () => void;
  onStartLive: () => void;
  onRunBenchmark: () => void;
  loading: boolean;
  evaluatorStatus: EvaluatorStatusResponse | null;
}

export function ModeSelect({ onShowScenario, onStartLive, onRunBenchmark, loading, evaluatorStatus }: ModeSelectProps) {
  return (
    <section className="mode-select pixel-panel">
      <div className="mode-copy">
        <p className="eyebrow">PixelClass TIL · v2 Honours MVP</p>
        <h1>Teacher-in-the-Loop Evaluation Benchmark</h1>
        <p>
          Live micro-lesson simulation is the testbed. Fixed transcript benchmark,
          evidence verification, and blinded expert review are the research contribution.
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
        <button className="mode-card primary" onClick={onShowScenario} disabled={loading}>
          <span className="mode-icon">▤</span>
          <strong>Scenario Builder / Thesis Blueprint</strong>
          <small>15-30 min lesson phases, student behaviour layer, claim guardrails</small>
        </button>
        <button className="mode-card" onClick={onStartLive} disabled={loading}>
          <span className="mode-icon">▣</span>
          <strong>Live Mode: Micro-lesson Simulation</strong>
          <small>Teacher input + literature-informed virtual student behaviour</small>
        </button>
        <button className="mode-card accent" onClick={onRunBenchmark} disabled={loading}>
          <span className="mode-icon">◇</span>
          <strong>Transcript Benchmark Mode</strong>
          <small>Fixed transcript → baseline vs TIL → verifier → blinded review</small>
        </button>
      </div>
    </section>
  );
}
