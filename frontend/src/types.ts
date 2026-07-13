export type SpeakerRole = 'teacher' | 'student' | 'controller';

export interface StudentPersona {
  persona_id: string;
  name: string;
  display_role: string;
  learning_profile: string;
  misconception_bias: string;
  avatar_variant: string;
}

export interface ClassroomTurn {
  turn_id: string;
  speaker_role: SpeakerRole;
  speaker_name: string;
  persona_id?: string | null;
  message: string;
  turn_index: number;
}

export interface SessionState {
  session_id: string;
  scenario_id: string;
  lesson_title: string;
  learning_objective: string;
  current_teacher_turn: number;
  max_teacher_turns: number;
  status: 'active' | 'completed';
  turns: ClassroomTurn[];
}

export interface StartSessionResponse {
  session: SessionState;
  personas: StudentPersona[];
}

export interface TeacherTurnResponse {
  teacher_turn: ClassroomTurn;
  student_turns: ClassroomTurn[];
  session_state: SessionState;
  response_source: 'openai' | 'fallback';
}
