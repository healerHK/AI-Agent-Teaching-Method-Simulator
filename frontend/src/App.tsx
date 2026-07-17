import { useState } from 'react';
import { runPhase3Demo, saveQuickAnnotation, sendTeacherTurn, startSession } from './api';
import { BlindedReviewPanel } from './components/BlindedReviewPanel';
import { ModeSelect } from './components/ModeSelect';
import { PixelClassroom } from './components/PixelClassroom';
import type { FeedbackItemView, Phase3DemoResponse, SessionState, StudentPersona } from './types';

function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [phase3Demo, setPhase3Demo] = useState<Phase3DemoResponse | null>(null);
  const [personas, setPersonas] = useState<StudentPersona[]>([]);
  const [teacherMessage, setTeacherMessage] = useState('Before we run this loop, how many times will print(number) execute?');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseSource, setResponseSource] = useState<string | undefined>();
  const [savedAnnotations, setSavedAnnotations] = useState<string[]>([]);

  async function handleStartDemo() {
    setLoading(true);
    setError(null);
    setPhase3Demo(null);
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

  async function handleStartReview() {
    setLoading(true);
    setError(null);
    setSession(null);
    setSavedAnnotations([]);
    try {
      const result = await runPhase3Demo();
      setPhase3Demo(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not run Phase 3 demo');
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

  async function handleAnnotate(label: string, evaluationId: string, item: FeedbackItemView, accept: boolean) {
    try {
      await saveQuickAnnotation({
        reviewerId: 'researcher_phase3_ui',
        label,
        evaluationId,
        item,
        accept,
      });
      setSavedAnnotations((current) => [...current, item.feedback_item_id]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save annotation');
    }
  }

  function handleReset() {
    setSession(null);
    setPhase3Demo(null);
    setPersonas([]);
    setResponseSource(undefined);
    setTeacherMessage('Before we run this loop, how many times will print(number) execute?');
    setSavedAnnotations([]);
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
      {loading && <div className="loading-banner pixel-panel">Working...</div>}

      {!session && !phase3Demo ? (
        <ModeSelect onStartDemo={handleStartDemo} onStartReview={handleStartReview} loading={loading} />
      ) : phase3Demo ? (
        <BlindedReviewPanel
          demo={phase3Demo}
          savedAnnotations={savedAnnotations}
          onAnnotate={handleAnnotate}
          onReset={handleReset}
        />
      ) : session ? (
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
      ) : null}
    </div>
  );
}

export default App;
