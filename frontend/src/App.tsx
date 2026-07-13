import { useState } from 'react';
import { sendTeacherTurn, startSession } from './api';
import { ModeSelect } from './components/ModeSelect';
import { PixelClassroom } from './components/PixelClassroom';
import type { SessionState, StudentPersona } from './types';

function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [personas, setPersonas] = useState<StudentPersona[]>([]);
  const [teacherMessage, setTeacherMessage] = useState('Before we run this loop, how many times will print(number) execute?');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseSource, setResponseSource] = useState<string | undefined>();

  async function handleStartDemo() {
    setLoading(true);
    setError(null);
    try {
      const result = await startSession();
      setSession(result.session);
      setPersonas(result.personas);
      setResponseSource('fallback-ready');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start session');
    } finally {
      setLoading(false);
    }
  }

  async function handleSendTeacherMessage() {
    if (!session || !teacherMessage.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await sendTeacherTurn(session.session_id, teacherMessage.trim());
      setSession(result.session_state);
      setResponseSource(result.response_source);
      setTeacherMessage('Can someone trace the next step and explain why?');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send teacher message');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setSession(null);
    setPersonas([]);
    setResponseSource(undefined);
    setTeacherMessage('Before we run this loop, how many times will print(number) execute?');
    setError(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <span className="logo-mark">▣</span>
          <strong>PixelClass TIL</strong>
        </div>
        <span>Teacher-in-the-Loop Classroom Simulation</span>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {!session ? (
        <ModeSelect onStartDemo={handleStartDemo} loading={loading} />
      ) : (
        <PixelClassroom
          session={session}
          personas={personas}
          teacherMessage={teacherMessage}
          onTeacherMessageChange={setTeacherMessage}
          onSendTeacherMessage={handleSendTeacherMessage}
          onReset={handleReset}
          loading={loading}
          responseSource={responseSource}
        />
      )}
    </div>
  );
}

export default App;
