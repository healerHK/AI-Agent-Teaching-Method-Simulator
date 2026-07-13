interface ModeSelectProps {
  onStartDemo: () => void;
  loading: boolean;
}

export function ModeSelect({ onStartDemo, loading }: ModeSelectProps) {
  return (
    <section className="mode-select pixel-panel">
      <div className="mode-copy">
        <p className="eyebrow">PixelClass TIL · Phase 2 MVP</p>
        <h1>2D Pixel Classroom Simulation</h1>
        <p>
          Human teacher input, virtual student characters, transcript capture, and a research
          path toward golden-benchmark evaluation.
        </p>
      </div>

      <div className="mode-grid">
        <button className="mode-card primary" onClick={onStartDemo} disabled={loading}>
          <span className="mode-icon">▣</span>
          <strong>Run Live Pixel Classroom Demo</strong>
          <small>Teacher + OpenAI/fallback student simulation</small>
        </button>
        <button className="mode-card disabled" disabled>
          <span className="mode-icon">◇</span>
          <strong>Evaluate Golden Benchmark</strong>
          <small>Phase 3/4 pipeline placeholder</small>
        </button>
        <button className="mode-card disabled" disabled>
          <span className="mode-icon">▤</span>
          <strong>View Previous Runs</strong>
          <small>CSV/charts/results placeholder</small>
        </button>
      </div>
    </section>
  );
}
