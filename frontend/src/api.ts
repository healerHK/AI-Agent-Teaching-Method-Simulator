import type { FeedbackItemView, Phase3DemoResponse, StartSessionResponse, TeacherTurnResponse } from './types';

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
      unsupported_inference: false,
      pedagogical_disagreement: false,
      missed_issue: false,
      usefulness: params.accept ? 4 : 2,
      review_time_seconds: 10,
      comment: params.accept ? 'Quick UI accept annotation.' : 'Quick UI reject annotation.',
    }),
  });
}
