import { useEffect, useState } from 'react';
import {
  getEvaluatorStatus,
  getV2Scenarios,
  runV2TranscriptBenchmark,
  saveQuickAnnotation,
  sendV2LiveTeacherTurn,
  startV2LiveSession,
} from './api';
import { BenchmarkModePanel } from './components/BenchmarkModePanel';
import { ModeSelect } from './components/ModeSelect';
import { PixelClassroom } from './components/PixelClassroom';
import { ScenarioBlueprintPanel } from './components/ScenarioBlueprintPanel';
import type {
  EvaluatorStatusResponse,
  FeedbackItemView,
  LessonPhase,
  ScenarioListResponse,
  SessionState,
  StudentPersona,
  TranscriptBenchmarkRunResponse,
} from './types';

type ActiveView = 'home' | 'scenario' | 'live' | 'benchmark';

function App() {
  const [activeView, setActiveView] = useState<ActiveView>('home');
  const [scenarioData, setScenarioData] = useState<ScenarioListResponse | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);
  const [benchmark, setBenchmark] = useState<TranscriptBenchmarkRunResponse | null>(null);
  const [personas, setPersonas] = useState<StudentPersona[]>([]);
  const [currentPhase, setCurrentPhase] = useState<LessonPhase | null>(null);
  const [protocolNotes, setProtocolNotes] = useState<string[]>([]);
  const [teacherMessage, setTeacherMessage] = useState('Before we run this loop, how many times will print(number) execute?');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseSource, setResponseSource] = useState<string | undefined>();
  const [savedAnnotations, setSavedAnnotations] = useState<string[]>([]);
  const [evaluatorStatus, setEvaluatorStatus] = useState<EvaluatorStatusResponse | null>(null);

  useEffect(() => {
    getEvaluatorStatus()
      .then(setEvaluatorStatus)
      .catch(() => setEvaluatorStatus(null));
    getV2Scenarios()
      .then(setScenarioData)
      .catch(() => undefined);
  }, []);

  async function ensureScenarioData() {
    if (scenarioData) return scenarioData;
    const result = await getV2Scenarios();
    setScenarioData(result);
    return result;
  }

  async function handleShowScenario() {
    setLoading(true);
    setError(null);
    try {
      await ensureScenarioData();
      setSession(null);
      setBenchmark(null);
      setActiveView('scenario');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load scenario blueprint');
    } finally {
      setLoading(false);
    }
  }

  async function handleStartLive() {
    setLoading(true);
    setError(null);
    setBenchmark(null);
    setSavedAnnotations([]);
    try {
      const result = await startV2LiveSession({ maxTeacherTurns: 8 });
      setSession(result.session);
      setPersonas(result.personas);
      setScenarioData((current) => current ?? {
        thesis_positioning: {
          title: 'PixelClass TIL',
          research_gap: '',
          contribution: '',
          safe_claim: '',
        },
        scenarios: [result.scenario],
        review_protocol: { reviewer_role: '', blinding: '', rating_dimensions: [], metrics: [] },
      });
      setCurrentPhase(result.scenario.lesson_phases[0]);
      setProtocolNotes(result.protocol_notes);
      setResponseSource('fallback-ready');
      setActiveView('live');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start live mode');
    } finally {
      setLoading(false);
    }
  }

  async function handleRunBenchmark() {
    setLoading(true);
    setError(null);
    setSession(null);
    setSavedAnnotations([]);
    try {
      const result = await runV2TranscriptBenchmark({ transcriptId: 'python_loops_weak_001' });
      setBenchmark(result);
      setActiveView('benchmark');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not run transcript benchmark');
    } finally {
      setLoading(false);
    }
  }

  async function handleSendTeacherMessage() {
    if (!session || !teacherMessage.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await sendV2LiveTeacherTurn(session.session_id, teacherMessage.trim());
      setSession(result.session_state);
      setResponseSource(result.response_source);
      setCurrentPhase(result.current_phase);
      setProtocolNotes(result.protocol_notes);
      setTeacherMessage(nextTeacherPrompt(result.current_phase.phase_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send teacher message');
    } finally {
      setLoading(false);
    }
  }

  async function handleAnnotate(label: string, evaluationId: string, item: FeedbackItemView, accept: boolean) {
    try {
      await saveQuickAnnotation({
        reviewerId: benchmark?.blinded_review.reviewer_id ?? 'expert_reviewer_mvp_ui',
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
    setActiveView('home');
    setSession(null);
    setBenchmark(null);
    setPersonas([]);
    setCurrentPhase(null);
    setProtocolNotes([]);
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
        <span>Teacher-in-the-Loop evidence-grounded pedagogical evaluation benchmark</span>
      </header>

      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="loading-banner pixel-panel">Working...</div>}

      {activeView === 'home' ? (
        <ModeSelect
          onShowScenario={handleShowScenario}
          onStartLive={handleStartLive}
          onRunBenchmark={handleRunBenchmark}
          loading={loading}
          evaluatorStatus={evaluatorStatus}
        />
      ) : activeView === 'scenario' && scenarioData ? (
        <ScenarioBlueprintPanel
          data={scenarioData}
          onStartLive={handleStartLive}
          onRunBenchmark={handleRunBenchmark}
          onReset={handleReset}
          loading={loading}
        />
      ) : activeView === 'benchmark' && benchmark ? (
        <BenchmarkModePanel
          benchmark={benchmark}
          savedAnnotations={savedAnnotations}
          onAnnotate={handleAnnotate}
          onReset={handleReset}
        />
      ) : activeView === 'live' && session ? (
        <>
          <section className="live-protocol pixel-panel">
            <div>
              <p className="eyebrow">Live Mode · 15-30 minute micro-lesson proxy</p>
              <h1>{session.lesson_title}</h1>
              <p>{session.learning_objective}</p>
            </div>
            {currentPhase && (
              <article className="phase-chip">
                <span className="label">Current phase</span>
                <strong>{currentPhase.title}</strong>
                <small>{currentPhase.minute_range} min · {currentPhase.evidence_focus.join(', ')}</small>
              </article>
            )}
            <button className="pixel-button secondary" onClick={handleReset}>Back</button>
          </section>
          {protocolNotes.length > 0 && (
            <section className="note-strip">
              {protocolNotes.map((note) => <span key={note}>{note}</span>)}
            </section>
          )}
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
        </>
      ) : null}
    </div>
  );
}

function nextTeacherPrompt(phaseId: string) {
  if (phaseId.includes('misconception')) return 'Mia thinks one print line means one output. How should we test that idea?';
  if (phaseId.includes('formative')) return 'Write the output and explain why each value appears.';
  if (phaseId.includes('reflection')) return 'What rule should we remember about for-loops before next lesson?';
  return 'Can someone trace the next step and explain why?';
}

export default App;
