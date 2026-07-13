import type { StartSessionResponse, TeacherTurnResponse } from './types';

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
