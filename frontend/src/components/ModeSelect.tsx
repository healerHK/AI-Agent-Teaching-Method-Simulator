interface ModeSelectProps {
  onStartDemo: () => void;
  onStartReview: () => void;
  loading: boolean;
}

export function ModeSelect({ onStartDemo, onStartReview, loading }: ModeSelectProps) {
  return (
    <section className="mode-select pixel-panel">
      <div className="mode-copy">
        <p className="eyebrow">PixelClass TIL · Phase 3/4 MVP</p>
        <h1>2D Pixel Classroom + Evaluation Pipeline</h1>
        <p>
          Human teacher input, virtual student characters, golden benchmark evaluation,
          evidence verification, and blinded A/B review.
        </p>
      </div>

      <div className="mode-grid">
        <button className="mode-card primary" onClick={onStartDemo} disabled={loading}>
          <span className="mode-icon">▣</span>
          <strong>Run Live Pixel Classroom Demo</strong>
          <small>Teacher + provider/fallback student simulation</small>
        </button>
        <button className="mode-card" onClick={onStartReview} disabled={loading}>
          <span className="mode-icon">◇</span>
          <strong>Evaluate Golden Benchmark</strong>
          <small>Baseline vs TIL + verifier + blinded review</small>
        </button>
        <button className="mode-card disabled" disabled>
          <span className="mode-icon">▤</span>
          <strong>View Previous Runs</strong>
          <small>Phase 4 CSV/charts/results are exported locally</small>
        </button>
      </div>
    </section>
  );
}
