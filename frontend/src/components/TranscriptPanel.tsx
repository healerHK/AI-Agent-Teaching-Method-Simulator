import type { ClassroomTurn } from '../types';

interface TranscriptPanelProps {
  turns: ClassroomTurn[];
}

export function TranscriptPanel({ turns }: TranscriptPanelProps) {
  return (
    <aside className="transcript pixel-panel">
      <div className="panel-heading">
        <h2>Transcript</h2>
        <span>{turns.length} turns</span>
      </div>
      <div className="transcript-list">
        {turns.length === 0 ? (
          <p className="muted">No turns yet.</p>
        ) : (
          turns.map((turn) => (
            <div className={`transcript-row ${turn.speaker_role}`} key={turn.turn_id}>
              <span>#{turn.turn_index}</span>
              <strong>{turn.speaker_name}</strong>
              <p>{turn.message}</p>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
