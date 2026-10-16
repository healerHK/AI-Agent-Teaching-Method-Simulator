import type { ScenarioListResponse } from '../types';

interface ScenarioBlueprintPanelProps {
  data: ScenarioListResponse;
  onOpenTranscriptSystem: () => void;
  onRunBenchmark: () => void;
  onReset: () => void;
  loading: boolean;
}

export function ScenarioBlueprintPanel({
  data,
  onOpenTranscriptSystem,
  onRunBenchmark,
  onReset,
  loading,
}: ScenarioBlueprintPanelProps) {
  const scenario = data.scenarios[0];

  return (
    <main className="blueprint-shell">
      <section className="review-header pixel-panel">
        <div>
          <p className="eyebrow">Scenario Builder / Research Blueprint</p>
          <h1>{scenario.title}</h1>
          <p>{data.thesis_positioning.safe_claim}</p>
        </div>
        <button className="pixel-button secondary" onClick={onReset}>Back</button>
      </section>

      <section className="blueprint-grid">
        <article className="pixel-panel blueprint-card wide">
          <span className="label">Research gap</span>
          <p>{data.thesis_positioning.research_gap}</p>
          <span className="label">Main contribution</span>
          <p>{data.thesis_positioning.contribution}</p>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Live micro-lesson</span>
          <strong>{scenario.estimated_duration_minutes} minutes · {scenario.education_level}</strong>
          <p>{scenario.learning_objective}</p>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Student behaviour claim</span>
          <strong>{scenario.virtual_student_behaviour_claim}</strong>
          <p>Generative Agents concepts support behaviour design; they do not become the main research claim.</p>
        </article>
      </section>

      <section className="phase-timeline pixel-panel">
        <div className="panel-heading">
          <h2>Lesson phases</h2>
          <span>{scenario.lesson_phases.length} phases</span>
        </div>
        <div className="phase-list">
          {scenario.lesson_phases.map((phase) => (
            <article className="phase-card" key={phase.phase_id}>
              <span className="badge">{phase.minute_range} min</span>
              <h3>{phase.title}</h3>
              <p>{phase.teacher_goal}</p>
              <strong>Expected student behaviour</strong>
              <ul>
                {phase.expected_student_behaviours.map((item) => <li key={item}>{item}</li>)}
              </ul>
              <strong>Evaluator evidence focus</strong>
              <div className="tag-row">
                {phase.evidence_focus.map((item) => <span className="tag" key={item}>{item}</span>)}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="blueprint-grid">
        <article className="pixel-panel blueprint-card wide">
          <span className="label">Student-agent architecture layer</span>
          <div className="mechanism-list">
            {scenario.student_behaviour_architecture.map((mechanism) => (
              <section className="mechanism-card" key={mechanism.mechanism}>
                <strong>{mechanism.mechanism.replace(/_/g, ' ')}</strong>
                <p>{mechanism.implementation_signal}</p>
                <small>{mechanism.thesis_claim}</small>
              </section>
            ))}
          </div>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Benchmark variants</span>
          <ul>
            {scenario.planned_benchmark_variants.map((item) => <li key={item}>{item}</li>)}
          </ul>
          <p className="muted">Available now: {scenario.available_transcript_ids.join(', ')}</p>
        </article>

        <article className="pixel-panel blueprint-card">
          <span className="label">Claim guardrails</span>
          <ul>
            {scenario.claim_guardrails.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </article>
      </section>

      <section className="action-strip pixel-panel">
        <button className="pixel-button" onClick={onOpenTranscriptSystem} disabled={loading}>Open Transcript System</button>
        <button className="pixel-button secondary" onClick={onRunBenchmark} disabled={loading}>Run Existing Benchmark</button>
      </section>
    </main>
  );
}
