import type { ClassroomTurn } from '../types';

interface DialogueBubbleProps {
  turn?: ClassroomTurn;
}

export function DialogueBubble({ turn }: DialogueBubbleProps) {
  if (!turn) {
    return (
      <div className="dialogue-bubble empty">
        Start the lesson by asking students to predict the loop output.
      </div>
    );
  }

  return (
    <div className={`dialogue-bubble ${turn.speaker_role}`}>
      <strong>{turn.speaker_name}</strong>
      <p>{turn.message}</p>
    </div>
  );
}
