import type { ClassroomTurn, SessionState, StudentPersona } from '../types';
import { fallbackPersonas, teacherAvatar } from '../data/uiCharacterPresets';
import { DialogueBubble } from './DialogueBubble';
import { PixelCharacter } from './PixelCharacter';
import { SessionControls } from './SessionControls';
import { TeacherInputPanel } from './TeacherInputPanel';
import { TranscriptPanel } from './TranscriptPanel';

interface PixelClassroomProps {
  session: SessionState;
  personas: StudentPersona[];
  teacherMessage: string;
  onTeacherMessageChange: (value: string) => void;
  onSendTeacherMessage: () => void;
  onReset: () => void;
  loading: boolean;
  responseSource?: string;
}

export function PixelClassroom({
  session,
  personas,
  teacherMessage,
  onTeacherMessageChange,
  onSendTeacherMessage,
  onReset,
  loading,
  responseSource,
}: PixelClassroomProps) {
  const displayPersonas = personas.length ? personas : fallbackPersonas;
  const latestTurn = session.turns.length ? session.turns[session.turns.length - 1] : undefined;
  const activeStudent = latestTurn?.speaker_role === 'student' ? latestTurn.persona_id : undefined;

  return (
    <main className="classroom-shell">
      <section className="classroom-stage pixel-panel">
        <div className="classroom-board">
          <span>Learning objective</span>
          <strong>{session.learning_objective}</strong>
          <code>for number in [1, 2, 3]: print(number)</code>
        </div>

        <div className="teacher-row">
          <PixelCharacter
            name={teacherAvatar.name}
            role={teacherAvatar.display_role}
            variant={teacherAvatar.avatar_variant}
            active={latestTurn?.speaker_role === 'teacher'}
          />
          <DialogueBubble turn={latestTurn} />
        </div>

        <div className="student-grid">
          {displayPersonas.map((persona) => (
            <PixelCharacter
              key={persona.persona_id}
              name={persona.name}
              role={persona.display_role}
              variant={persona.avatar_variant}
              active={activeStudent === persona.persona_id}
            />
          ))}
        </div>
      </section>

      <section className="right-rail">
        <SessionControls sessionId={session.session_id} source={responseSource} onReset={onReset} />
        <TeacherInputPanel
          value={teacherMessage}
          onChange={onTeacherMessageChange}
          onSubmit={onSendTeacherMessage}
          disabled={loading || session.status === 'completed'}
        />
        <TranscriptPanel turns={session.turns} />
      </section>
    </main>
  );
}
