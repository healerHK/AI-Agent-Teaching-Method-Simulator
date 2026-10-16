interface SessionControlsProps {
  sessionId?: string;
  source?: string;
  onReset: () => void;
}

export function SessionControls({ sessionId, source, onReset }: SessionControlsProps) {
  return (
    <div className="session-controls pixel-panel">
      <div>
        <span className="label">Session</span>
        <strong>{sessionId ?? 'not started'}</strong>
      </div>
      <div>
        <span className="label">Student source</span>
        <strong>{source ?? 'fallback-ready'}</strong>
      </div>
      <button className="pixel-button secondary" onClick={onReset}>Reset</button>
    </div>
  );
}
