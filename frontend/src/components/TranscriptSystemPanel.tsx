import { useEffect, useMemo, useState } from 'react';
import {
  getTranscriptScenario,
  listTranscriptScenarios,
  saveTranscriptScenario,
  testTranscriptScenario,
} from '../api';
import type {
  StudentPromptParameters,
  TranscriptScenario,
  TranscriptScenarioListResponse,
  TranscriptScenarioTestResponse,
  TranscriptTurnDraft,
} from '../types';

interface TranscriptSystemPanelProps {
  onReset: () => void;
  onProceedToTILEvaluation: (scenarioId: string) => void;
}

export function TranscriptSystemPanel({ onReset, onProceedToTILEvaluation }: TranscriptSystemPanelProps) {
  const [library, setLibrary] = useState<TranscriptScenarioListResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string>('');
  const [scenario, setScenario] = useState<TranscriptScenario | null>(null);
  const [jsonText, setJsonText] = useState('');
  const [testResult, setTestResult] = useState<TranscriptScenarioTestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [openStudentConfigId, setOpenStudentConfigId] = useState<string | null>(null);

  useEffect(() => {
    loadLibrary();
  }, []);

  async function loadLibrary() {
    setLoading(true);
    setError(null);
    try {
      const data = await listTranscriptScenarios();
      setLibrary(data);
      const firstId = data.scenarios[0]?.scenario_id ?? '';
      setSelectedId(firstId);
      if (firstId) await loadScenario(firstId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load transcript scenario library');
    } finally {
      setLoading(false);
    }
  }

  async function loadScenario(scenarioId: string) {
    setLoading(true);
    setError(null);
    setSaveMessage(null);
    setTestResult(null);
    try {
      const data = await getTranscriptScenario(scenarioId);
      setScenario(data);
      setSelectedId(scenarioId);
      setOpenStudentConfigId(null);
      setJsonText(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load scenario');
    } finally {
      setLoading(false);
    }
  }

  function updateScenario(mutator: (draft: TranscriptScenario) => void) {
    setScenario((current) => {
      if (!current) return current;
      const next = structuredClone(current) as TranscriptScenario;
      mutator(next);
      setJsonText(JSON.stringify(next, null, 2));
      setSaveMessage(null);
      setTestResult(null);
      return next;
    });
  }

  function updateStudentParameter(index: number, field: keyof StudentPromptParameters, value: string | number) {
    updateScenario((draft) => {
      const student = draft.student_profiles[index];
      if (!student) return;
      if (field === 'confidence' || field === 'misconception_strength') {
        student.parameters[field] = Number(value);
      } else if (field === 'response_length') {
        student.parameters[field] = value as StudentPromptParameters['response_length'];
      } else {
        student.parameters[field] = String(value);
      }
    });
  }

  function updateNotes(value: string) {
    updateScenario((draft) => {
      draft.editable_notes = value;
    });
  }

  function applyJson() {
    try {
      const parsed = JSON.parse(jsonText) as TranscriptScenario;
      setScenario(parsed);
      setSelectedId(parsed.scenario_id);
      setOpenStudentConfigId(null);
      setSaveMessage('Applied JSON locally. Click Save Scenario to persist it.');
      setTestResult(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid JSON');
    }
  }

  function updateTranscriptTurn(turnId: string, field: 'name' | 'content', value: string) {
    updateScenario((draft) => {
      const turn = draft.transcript_turns.find((item) => item.turn_id === turnId);
      if (!turn) return;
      if (field === 'name') {
        const inferred = inferSpeaker(draft, value);
        turn.speaker_name = value;
        turn.speaker_role = inferred.role;
        turn.student_id = inferred.studentId;
      } else {
        turn.message = value;
      }
    });
  }

  function scenarioWithTranscriptTable() {
    if (!scenario) return null;
    try {
      validateTranscriptTable(scenario);
      return scenario;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid transcript table');
      return null;
    }
  }

  async function handleSave() {
    if (!scenario) return;
    setSaving(true);
    setError(null);
    try {
      const next = scenarioWithTranscriptTable();
      if (!next) return;
      const saved = await saveTranscriptScenario(next);
      setScenario(next);
      setJsonText(JSON.stringify(next, null, 2));
      setSaveMessage(`Saved to ${saved.path}`);
      const refreshed = await listTranscriptScenarios();
      setLibrary(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save scenario');
    } finally {
      setSaving(false);
    }
  }

  async function handleRunTest() {
    if (!scenario) return;
    setLoading(true);
    setError(null);
    setSaveMessage(null);
    try {
      const next = scenarioWithTranscriptTable();
      if (!next) return;
      await saveTranscriptScenario(next);
      setScenario(next);
      setJsonText(JSON.stringify(next, null, 2));
      const result = await testTranscriptScenario(next.scenario_id);
      setTestResult(result);
      setSaveMessage('Saved and ran readiness test.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not test scenario');
    } finally {
      setLoading(false);
    }
  }

  async function handleProceedToTIL() {
    if (!scenario) return;
    setLoading(true);
    setError(null);
    try {
      const next = scenarioWithTranscriptTable();
      if (!next) return;
      await saveTranscriptScenario(next);
      const result = await testTranscriptScenario(next.scenario_id);
      setTestResult(result);
      if (!result.passed) {
        setError('Scenario is not readiness-pass yet. Fix failed checks before TIL evaluation.');
        return;
      }
      onProceedToTILEvaluation(next.scenario_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not proceed to TIL evaluation');
    } finally {
      setLoading(false);
    }
  }

  const selectedSummary = useMemo(
    () => library?.scenarios.find((item) => item.scenario_id === selectedId),
    [library, selectedId],
  );

  return (
    <main className="transcript-system-shell">
      <section className="review-header pixel-panel">
        <div>
          <p className="eyebrow">Transcript-first system · Live Mode paused</p>
          <h1>Transcript Scenario Builder & Readiness Tester</h1>
          <p>
            Build fixed 30-minute classroom transcript drafts first: choose scenarios, tune student prompt
            parameters, edit one transcript table, then proceed to TIL evaluation.
          </p>
        </div>
        <button className="pixel-button secondary" onClick={onReset}>Back</button>
      </section>

      {error && <div className="error-banner">{error}</div>}
      {saveMessage && <div className="loading-banner pixel-panel">{saveMessage}</div>}

      <section className="transcript-layout">
        <aside className="scenario-sidebar pixel-panel">
          <div className="panel-heading">
            <h2>Scenario library</h2>
            <span>{library?.library_summary.scenario_count ?? 0}</span>
          </div>
          {library && (
            <div className="library-summary">
              <span>{library.library_summary.duration_policy}</span>
              <span>Subjects: {library.library_summary.subjects.join(', ')}</span>
              <span>Levels: {library.library_summary.education_levels.join(', ')}</span>
            </div>
          )}
          <div className="scenario-list">
            {library?.scenarios.map((item) => (
              <button
                key={item.scenario_id}
                className={item.scenario_id === selectedId ? 'scenario-list-item active' : 'scenario-list-item'}
                onClick={() => loadScenario(item.scenario_id)}
                disabled={loading}
              >
                <strong>{item.title}</strong>
                <small>{item.subject} · {item.education_level.replace('_', ' ')} · {item.estimated_duration_minutes}m</small>
                <small>{item.student_count} students · {item.turn_count} turns · {item.misconception_count} misconceptions</small>
              </button>
            ))}
          </div>
        </aside>

        <section className="scenario-editor">
          {scenario ? (
            <>
              <article className="pixel-panel transcript-card scenario-overview-card">
                <div>
                  <p className="eyebrow">Selected scenario</p>
                  <h2>{scenario.title}</h2>
                  <p>{scenario.course_context}</p>
                  <div className="tag-row">
                    <span className="tag">{scenario.subject}</span>
                    <span className="tag">{scenario.education_level.replace('_', ' ')}</span>
                    <span className="tag">{scenario.estimated_duration_minutes} minutes</span>
                    <span className="tag">{selectedSummary?.turn_count ?? scenario.transcript_turns.length} turns</span>
                  </div>
                </div>
                <div className="editor-actions">
                  <button className="pixel-button" onClick={handleSave} disabled={saving || loading}>Save Scenario</button>
                  <button className="pixel-button secondary" onClick={handleRunTest} disabled={saving || loading}>Save + Run Readiness Test</button>
                  <button className="pixel-button accent" onClick={handleProceedToTIL} disabled={saving || loading}>Proceed to TIL Evaluation</button>
                </div>
              </article>

              <section className="transcript-grid two">
                <article className="pixel-panel transcript-card">
                  <h3>Learning objectives</h3>
                  <ul>{scenario.learning_objectives.map((item) => <li key={item}>{item}</li>)}</ul>
                  <h3>Misconceptions to surface</h3>
                  <ul>{scenario.misconception_targets.map((item) => <li key={item}>{item}</li>)}</ul>
                  <label className="field-label">Editable research notes</label>
                  <textarea value={scenario.editable_notes} onChange={(event) => updateNotes(event.target.value)} rows={5} />
                </article>

                <article className="pixel-panel transcript-card">
                  <h3>30-minute lesson phases</h3>
                  <div className="compact-phase-list">
                    {scenario.lesson_phases.map((phase) => (
                      <section key={phase.phase_id} className="compact-phase-card">
                        <strong>{phase.minute_start}-{phase.minute_end} min · {phase.title}</strong>
                        <p>{phase.teacher_goal}</p>
                        <div className="tag-row">{phase.evidence_focus.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>
                      </section>
                    ))}
                  </div>
                </article>
              </section>

              <section className="pixel-panel transcript-card">
                <div className="panel-heading">
                  <div>
                    <h2>Student prompt parameters</h2>
                    <p className="muted">Cards stay compact. Click ⚙ to adjust each student's prompt coefficients.</p>
                  </div>
                  <span>{scenario.student_profiles.length} editable profiles</span>
                </div>
                <div className="student-config-grid compact">
                  {scenario.student_profiles.map((student, index) => {
                    const isOpen = openStudentConfigId === student.student_id;
                    return (
                      <article className={isOpen ? 'student-config-card open' : 'student-config-card'} key={student.student_id}>
                        <div className="student-card-summary">
                          <div>
                            <h3>{student.name}</h3>
                            <span className="student-status">{formatStudentStatus(student.role)}</span>
                          </div>
                          <button
                            className="config-icon-button"
                            type="button"
                            aria-label={`Configure ${student.name}`}
                            aria-expanded={isOpen}
                            onClick={() => setOpenStudentConfigId(isOpen ? null : student.student_id)}
                          >
                            ⚙
                          </button>
                        </div>

                        {isOpen && (
                          <div className="student-parameter-panel">
                            <p className="student-background">{student.background}</p>
                            <table className="student-parameter-table">
                              <tbody>
                                <tr>
                                  <th>Confidence coefficient</th>
                                  <td>
                                    <div className="coefficient-control">
                                      <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.01"
                                        value={student.parameters.confidence}
                                        onChange={(event) => updateStudentParameter(index, 'confidence', event.target.value)}
                                      />
                                      <strong>{student.parameters.confidence.toFixed(2)}</strong>
                                    </div>
                                  </td>
                                </tr>
                                <tr>
                                  <th>Misconception coefficient</th>
                                  <td>
                                    <div className="coefficient-control">
                                      <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.01"
                                        value={student.parameters.misconception_strength}
                                        onChange={(event) => updateStudentParameter(index, 'misconception_strength', event.target.value)}
                                      />
                                      <strong>{student.parameters.misconception_strength.toFixed(2)}</strong>
                                    </div>
                                  </td>
                                </tr>
                                <tr>
                                  <th>Response length</th>
                                  <td>
                                    <select
                                      value={student.parameters.response_length}
                                      onChange={(event) => updateStudentParameter(index, 'response_length', event.target.value)}
                                    >
                                      <option value="short">Short</option>
                                      <option value="medium">Medium</option>
                                      <option value="long">Long</option>
                                    </select>
                                  </td>
                                </tr>
                                <tr>
                                  <th>Prior knowledge</th>
                                  <td>
                                    <input
                                      value={student.parameters.prior_knowledge}
                                      onChange={(event) => updateStudentParameter(index, 'prior_knowledge', event.target.value)}
                                    />
                                  </td>
                                </tr>
                                <tr>
                                  <th>Affect</th>
                                  <td>
                                    <input
                                      value={student.parameters.affect}
                                      onChange={(event) => updateStudentParameter(index, 'affect', event.target.value)}
                                    />
                                  </td>
                                </tr>
                                <tr>
                                  <th>Language level</th>
                                  <td>
                                    <input
                                      value={student.parameters.language_level}
                                      onChange={(event) => updateStudentParameter(index, 'language_level', event.target.value)}
                                    />
                                  </td>
                                </tr>
                                <tr>
                                  <th>Participation style</th>
                                  <td>
                                    <textarea
                                      value={student.parameters.participation_style}
                                      onChange={(event) => updateStudentParameter(index, 'participation_style', event.target.value)}
                                      rows={2}
                                    />
                                  </td>
                                </tr>
                                <tr>
                                  <th>Special prompt instructions</th>
                                  <td>
                                    <textarea
                                      value={student.parameters.prompt_instructions}
                                      onChange={(event) => updateStudentParameter(index, 'prompt_instructions', event.target.value)}
                                      rows={3}
                                    />
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              </section>

              <section className="pixel-panel transcript-card">
                <div className="panel-heading">
                  <div>
                    <h2>Draft transcript table</h2>
                    <p className="muted">One real editable table: <code>Turn | Name | Content</code>. Each row is one classroom turn; keep at least 30 rows for a 30-minute lesson.</p>
                  </div>
                  <span className="badge ok">{scenario.transcript_turns.length} rows</span>
                </div>
                <div className="transcript-table-scroll" aria-label="Editable transcript turn table">
                  <table className="transcript-editor-table">
                    <thead>
                      <tr>
                        <th>Turn</th>
                        <th>Name</th>
                        <th>Content</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedTranscriptTurns(scenario).map((turn) => (
                        <tr key={turn.turn_id}>
                          <td className="turn-cell">
                            <strong>{turn.turn_id.replace('turn_', '#')}</strong>
                            <small>{turn.minute} min</small>
                          </td>
                          <td className="name-cell">
                            <input
                              value={turn.speaker_name}
                              onChange={(event) => updateTranscriptTurn(turn.turn_id, 'name', event.target.value)}
                              aria-label={`Speaker name for ${turn.turn_id}`}
                            />
                          </td>
                          <td className="content-cell">
                            <textarea
                              value={turn.message}
                              onChange={(event) => updateTranscriptTurn(turn.turn_id, 'content', event.target.value)}
                              rows={3}
                              aria-label={`Transcript content for ${turn.turn_id}`}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="pixel-panel transcript-card">
                <div className="panel-heading">
                  <h2>Advanced JSON editor</h2>
                  <button className="pixel-button small secondary" onClick={applyJson}>Apply JSON locally</button>
                </div>
                <p className="muted">Use this only when you want to edit objectives, phases, tags, materials, or add new students quickly before saving.</p>
                <textarea className="json-editor" value={jsonText} onChange={(event) => setJsonText(event.target.value)} rows={16} spellCheck={false} />
              </section>

              {testResult && <ReadinessResult result={testResult} onProceed={() => onProceedToTILEvaluation(testResult.scenario_id)} />}
            </>
          ) : (
            <article className="pixel-panel transcript-card">Loading scenario...</article>
          )}
        </section>
      </section>
    </main>
  );
}

function ReadinessResult({ result, onProceed }: { result: TranscriptScenarioTestResponse; onProceed: () => void }) {
  return (
    <section className="pixel-panel transcript-card readiness-result">
      <div className="panel-heading">
        <h2>Readiness test result</h2>
        <span className={result.passed ? 'badge ok' : 'badge warn'}>{result.passed ? 'PASS' : 'NEEDS FIX'}</span>
      </div>
      <div className="check-grid">
        {result.checks.map((check) => (
          <article key={check.check_id} className={`check-card ${check.status}`}>
            <strong>{check.check_id.replace(/_/g, ' ')}</strong>
            <p>{check.message}</p>
          </article>
        ))}
      </div>
      {result.passed && <button className="pixel-button accent" onClick={onProceed}>Proceed to TIL Evaluation</button>}
      <h3>Rendered student prompts</h3>
      <div className="prompt-preview-grid">
        {result.rendered_student_prompts.map((prompt) => (
          <details key={prompt.student_id} className="prompt-preview-card">
            <summary>{prompt.name} · {prompt.role}</summary>
            <pre>{prompt.prompt}</pre>
          </details>
        ))}
      </div>
      <h3>Transcript preview</h3>
      <pre className="markdown-preview">{result.transcript_preview_markdown}</pre>
      <h3>Next steps</h3>
      <ul>{result.next_steps.map((item) => <li key={item}>{item}</li>)}</ul>
    </section>
  );
}

function sortedTranscriptTurns(scenario: TranscriptScenario) {
  return scenario.transcript_turns
    .slice()
    .sort((a, b) => a.minute - b.minute || a.turn_id.localeCompare(b.turn_id));
}

function validateTranscriptTable(scenario: TranscriptScenario) {
  const turns = sortedTranscriptTurns(scenario);
  if (turns.length < 30) {
    throw new Error(`Transcript table has ${turns.length} rows; at least 30 rows are required for a 30-minute scenario.`);
  }
  const invalidTurn = turns.find((turn) => !turn.speaker_name.trim() || !turn.message.trim());
  if (invalidTurn) {
    throw new Error(`${invalidTurn.turn_id} needs both Name and Content before saving.`);
  }
}

function formatStudentStatus(role: string) {
  return role
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function inferSpeaker(scenario: TranscriptScenario, name: string): { role: TranscriptTurnDraft['speaker_role']; studentId: string | null } {
  if (name.toLowerCase() === 'teacher') return { role: 'teacher', studentId: null };
  const student = scenario.student_profiles.find((profile) => profile.name.toLowerCase() === name.toLowerCase());
  if (student) return { role: 'student', studentId: student.student_id };
  return { role: 'student', studentId: null };
}
