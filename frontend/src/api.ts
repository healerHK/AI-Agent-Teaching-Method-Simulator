import type {
  EvaluatorStatusResponse,
  FeedbackItemView,
  LiveSessionStartResponse,
  LiveTeacherTurnResponse,
  Phase3DemoResponse,
  ScenarioListResponse,
  StartSessionResponse,
  TeacherTurnResponse,
  TranscriptBenchmarkRunResponse,
  TranscriptScenario,
  TranscriptScenarioListResponse,
  TranscriptScenarioSaveResponse,
  TranscriptScenarioTestResponse,
  RenderedStudentPrompt,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export function startSession(): Promise<StartSessionResponse> {
  return request<StartSessionResponse>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ scenario_id: 'python_loops_001', max_teacher_turns: 12 }),
  });
}

export function getEvaluatorStatus(): Promise<EvaluatorStatusResponse> {
  return request<EvaluatorStatusResponse>('/api/evaluator/status');
}

export function sendTeacherTurn(sessionId: string, teacherMessage: string): Promise<TeacherTurnResponse> {
  return request<TeacherTurnResponse>(`/api/sessions/${sessionId}/turn`, {
    method: 'POST',
    body: JSON.stringify({ teacher_message: teacherMessage }),
  });
}

export function runPhase3Demo(): Promise<Phase3DemoResponse> {
  return request<Phase3DemoResponse>('/api/phase3/demo', {
    method: 'POST',
    body: JSON.stringify({ transcript_id: 'python_loops_weak_001', reviewer_id: 'researcher_phase3_ui' }),
  });
}

export function getV2Scenarios(): Promise<ScenarioListResponse> {
  return request<ScenarioListResponse>('/api/v2/scenarios');
}

export function listTranscriptScenarios(): Promise<TranscriptScenarioListResponse> {
  return request<TranscriptScenarioListResponse>('/api/v2/transcript-system/scenarios');
}

export function getTranscriptScenario(scenarioId: string): Promise<TranscriptScenario> {
  return request<TranscriptScenario>(`/api/v2/transcript-system/scenarios/${scenarioId}`);
}

export function saveTranscriptScenario(scenario: TranscriptScenario): Promise<TranscriptScenarioSaveResponse> {
  return request<TranscriptScenarioSaveResponse>(`/api/v2/transcript-system/scenarios/${scenario.scenario_id}`, {
    method: 'PUT',
    body: JSON.stringify(scenario),
  });
}

export function renderTranscriptScenarioPrompts(scenarioId: string): Promise<RenderedStudentPrompt[]> {
  return request<RenderedStudentPrompt[]>(`/api/v2/transcript-system/scenarios/${scenarioId}/prompts`);
}

export function testTranscriptScenario(scenarioId: string): Promise<TranscriptScenarioTestResponse> {
  return request<TranscriptScenarioTestResponse>(`/api/v2/transcript-system/scenarios/${scenarioId}/test`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function runTranscriptScenarioTILEvaluation(scenarioId: string, reviewerId?: string): Promise<TranscriptBenchmarkRunResponse> {
  const params = new URLSearchParams({ reviewer_id: reviewerId ?? `expert_reviewer_${scenarioId}` });
  return request<TranscriptBenchmarkRunResponse>(`/api/v2/transcript-system/scenarios/${scenarioId}/til-evaluation?${params.toString()}`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function startV2LiveSession(params?: { scenarioId?: string; maxTeacherTurns?: number }): Promise<LiveSessionStartResponse> {
  return request<LiveSessionStartResponse>('/api/v2/live/sessions', {
    method: 'POST',
    body: JSON.stringify({
      scenario_id: params?.scenarioId ?? 'python_loops_full_lesson_001',
      max_teacher_turns: params?.maxTeacherTurns ?? 8,
    }),
  });
}

export function sendV2LiveTeacherTurn(sessionId: string, teacherMessage: string): Promise<LiveTeacherTurnResponse> {
  return request<LiveTeacherTurnResponse>(`/api/v2/live/sessions/${sessionId}/turn`, {
    method: 'POST',
    body: JSON.stringify({ teacher_message: teacherMessage }),
  });
}

export function runV2TranscriptBenchmark(params?: {
  transcriptId?: string;
  reviewerId?: string;
}): Promise<TranscriptBenchmarkRunResponse> {
  return request<TranscriptBenchmarkRunResponse>('/api/v2/transcript-benchmark/run', {
    method: 'POST',
    body: JSON.stringify({
      transcript_id: params?.transcriptId ?? 'python_loops_weak_001',
      reviewer_id: params?.reviewerId ?? 'expert_reviewer_mvp_ui',
    }),
  });
}

export function saveQuickAnnotation(params: {
  reviewerId: string;
  label: string;
  evaluationId: string;
  item: FeedbackItemView;
  accept: boolean;
}) {
  return request<{ annotation_id: string; saved: boolean }>('/api/annotations', {
    method: 'POST',
    body: JSON.stringify({
      reviewer_id: params.reviewerId,
      evaluation_id: params.evaluationId,
      feedback_item_id: params.item.feedback_item_id,
      blinded_label: params.label,
      criterion: params.item.criterion,
      ai_score: params.item.score,
      human_score: params.item.score,
      accept: params.accept,
      fabricated_evidence: params.item.verification_status !== 'verified',
      unsupported_inference: params.item.verification_status !== 'verified',
      pedagogical_disagreement: !params.accept,
      missed_issue: false,
      usefulness: params.accept ? 4 : 2,
      review_time_seconds: 10,
      comment: params.accept ? 'Quick UI accept annotation.' : 'Quick UI reject annotation.',
    }),
  });
}
