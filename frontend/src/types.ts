export type SpeakerRole = 'teacher' | 'student' | 'controller' | 'evaluator';

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

export interface BenchmarkTurn {
  turn_id: string;
  speaker_role: SpeakerRole;
  speaker_name: string;
  message: string;
}

export interface BenchmarkTranscript {
  transcript_id: string;
  scenario_id: string;
  variant: 'strong' | 'weak';
  domain: string;
  education_level: string;
  learning_objective: string;
  turns: BenchmarkTurn[];
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
  response_source: 'openai' | 'fallback' | string;
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

export interface ThesisPositioning {
  title: string;
  research_gap: string;
  contribution: string;
  safe_claim: string;
}

export interface LessonPhase {
  phase_id: string;
  title: string;
  minute_range: string;
  teacher_goal: string;
  expected_student_behaviours: string[];
  evidence_focus: string[];
}

export interface StudentBehaviourMechanism {
  mechanism: 'memory_stream' | 'retrieval' | 'reflection' | 'planning' | 'state_update';
  source: string;
  implementation_signal: string;
  thesis_claim: string;
}

export interface ScenarioSpec {
  scenario_id: string;
  title: string;
  mode: 'live_micro_lesson_and_transcript_benchmark';
  estimated_duration_minutes: number;
  subject_domain: string;
  education_level: string;
  learning_objective: string;
  core_misconceptions: string[];
  lesson_phases: LessonPhase[];
  virtual_student_behaviour_claim: string;
  student_behaviour_architecture: StudentBehaviourMechanism[];
  planned_benchmark_variants: string[];
  available_transcript_ids: string[];
  claim_guardrails: string[];
}

export interface MetricDefinition {
  metric_id: string;
  label: string;
  formula: string;
  interpretation: string;
}

export interface ReviewProtocol {
  reviewer_role: string;
  blinding: string;
  rating_dimensions: string[];
  metrics: MetricDefinition[];
}

export interface ScenarioListResponse {
  thesis_positioning: ThesisPositioning;
  scenarios: ScenarioSpec[];
  review_protocol: ReviewProtocol;
}

export interface LiveSessionStartResponse {
  scenario: ScenarioSpec;
  session: SessionState;
  personas: StudentPersona[];
  protocol_notes: string[];
}

export interface LiveTeacherTurnResponse extends TeacherTurnResponse {
  current_phase: LessonPhase;
  protocol_notes: string[];
}

export interface ReviewMetricsSummary {
  reviewer_id: string;
  annotations_count: number;
  expert_acceptance_rate: number;
  correction_rate: number;
  rejection_rate: number;
  evidence_validity_rate: number;
  unsupported_inference_rate: number;
  usefulness_mean: number | null;
  metrics_definition: MetricDefinition[];
}

export interface TranscriptBenchmarkRunResponse extends Phase3DemoResponse {
  thesis_positioning: ThesisPositioning;
  transcript: BenchmarkTranscript;
  scenario: ScenarioSpec;
  benchmark_protocol: {
    controlled_comparison: boolean;
    pipeline: string[];
    baseline_condition_hidden_from_reviewer: boolean;
    experiment_id: string;
    main_claim_scope: string;
    [key: string]: unknown;
  };
  review_metrics: ReviewMetricsSummary;
  claim_guardrails: string[];
}
