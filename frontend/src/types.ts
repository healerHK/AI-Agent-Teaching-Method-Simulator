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

export interface EvaluatorConditionStatus {
  condition: string;
  provider: string;
  model: string;
  model_label: string;
  api_key_configured: boolean;
  base_url_configured: boolean;
  temperature: number;
}

export interface EvaluatorStatusResponse {
  conditions: EvaluatorConditionStatus[];
  secrets_redacted: boolean;
  fallback_policy: string;
}

export interface TeacherTurnResponse {
  teacher_turn: ClassroomTurn;
  student_turns: ClassroomTurn[];
  session_state: SessionState;
  response_source: 'openai' | 'fallback';
}

export interface EvidenceLinkView {
  turn_id: string;
  evidence_quote: string;
}

export interface FeedbackItemView {
  feedback_item_id: string;
  criterion: string;
  claim: string;
  score?: number | null;
  suggested_action?: string | null;
  confidence?: number | null;
  verification_status?: string | null;
  evidence: EvidenceLinkView[];
}

export interface BlindedEvaluationView {
  display_label: 'Evaluation A' | 'Evaluation B';
  evaluation_id: string;
  feedback_items: FeedbackItemView[];
}

export interface VerificationRunResponse {
  evaluation_id: string;
  verifier_version: string;
  overall_status: string;
  items: Array<{ criterion: string; claim: string; status: string; problems: string[] }>;
}

export interface Phase3DemoResponse {
  transcript_id: string;
  baseline_evaluation_id: string;
  til_evaluation_id: string;
  baseline_verification: VerificationRunResponse;
  til_verification: VerificationRunResponse;
  blinded_review: {
    transcript_id: string;
    reviewer_id: string;
    blinded_evaluations: BlindedEvaluationView[];
  };
}
