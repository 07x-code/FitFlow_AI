const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? '';

const COACH_SESSION_ID =
  globalThis.crypto?.randomUUID?.() ??
  `coach-${Date.now()}-${Math.random().toString(16).slice(2)}`;

let coachCleanupRegistered = false;

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE';
  userId?: string;
  sessionId?: string;
  body?: unknown;
  keepalive?: boolean;
};

export type KnowledgeSource = {
  title: string;
  category: string;
  summary: string;
};

export type CoachChatResponse = {
  answer: string;
  safety_level: string;
  referenced_plan_id: number | null;
  knowledge_sources: KnowledgeSource[];
  memory_events: MemoryMutationEvent[];
};

export type MemoryMutationEvent = {
  action: 'remembered' | 'forgotten';
  memory_id: number;
  type:
    | 'preferred_equipment'
    | 'disliked_exercise'
    | 'training_time'
    | 'physical_limitation'
    | 'general_note';
  content: string;
};

export type ExercisePrescription = {
  exercise_name: string;
  sets: number;
  reps_min: number;
  reps_max: number;
  target_rpe: number;
};

export type WorkoutDayDraft = {
  scheduled_date: string;
  name: string;
  focus: string;
  estimated_minutes: number;
  exercises: ExercisePrescription[];
};

export type TrainingPlanDraft = {
  week_start: string;
  week_end: string;
  timezone: string;
  goal_summary: string;
  days: WorkoutDayDraft[];
};

export type SafetyCheckResult = {
  valid: boolean;
  violations: Record<string, string>[];
};

export type ProposalDecision = 'approve' | 'reject';

export type ProposalStatus =
  | 'pending'
  | 'approving'
  | 'approved'
  | 'rejected'
  | 'superseded';

export type TrainingPlanProposalResponse = {
  id: number;
  type: 'training_plan';
  operation: 'create' | 'replace' | 'adjust';
  target_week_start: string;
  base_plan_id: number | null;
  parent_proposal_id: number | null;
  revision: number;
  status: ProposalStatus;
  plan: TrainingPlanDraft;
  safety_check: SafetyCheckResult;
  generation_summary: string;
  approved_plan_id: number | null;
  decision_note: string | null;
  created_at: string;
  decided_at: string | null;
};

export type ProposalListResponse = {
  proposals: TrainingPlanProposalResponse[];
};

export type TrainingPlanStatus =
  | 'scheduled'
  | 'active'
  | 'superseded'
  | 'completed';

export type TrainingPlanHistoryItem = {
  id: number;
  version: number;
  status: TrainingPlanStatus;
  source_proposal_id: number;
  plan: TrainingPlanDraft;
  safety_check: SafetyCheckResult;
  created_at: string;
};

export type TrainingPlanHistoryResponse = {
  plans: TrainingPlanHistoryItem[];
};

export type WorkoutSetLog = {
  exercise_id: string | null;
  exercise_name: string;
  set_number: number;
  weight_kg: number;
  reps: number;
  rpe: number;
};

export type WorkoutSafetyAlert = {
  level: string;
  message: string;
};

export type WorkoutSessionResponse = {
  id: number;
  plan_id: number;
  plan_day_index: number;
  plan_day_name: string;
  completed: boolean;
  fatigue_level: number;
  pain_level: number;
  notes: string | null;
  sets: WorkoutSetLog[];
  safety_alert: WorkoutSafetyAlert | null;
  created_at: string;
};

export type WorkoutHistoryResponse = {
  sessions: WorkoutSessionResponse[];
};

export class FitFlowApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: unknown,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  {
    method = 'GET',
    userId,
    sessionId,
    body,
    keepalive = false,
  }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(userId ? { 'X-User-ID': userId } : {}),
      ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    keepalive,
  });

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? payload.detail
        : undefined;
    throw new FitFlowApiError(
      `FitFlow API 请求失败：${response.status}`,
      response.status,
      detail,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * 首次发起教练对话时注册页面结束清理，避免重复监听。
 *
 * @param userId 当前用户标识。
 */
function ensureCoachSessionCleanup(userId: string) {
  if (coachCleanupRegistered || typeof window === 'undefined') {
    return;
  }

  coachCleanupRegistered = true;
  window.addEventListener(
    'pagehide',
    () => {
      void request<void>(
        `/api/memories/working/${COACH_SESSION_ID}`,
        {
          method: 'DELETE',
          userId,
          keepalive: true,
        },
      ).catch(() => undefined);
    },
    { once: true },
  );
}

export const fitFlowApi = {
  health: () => request<{ service: string; status: string }>('/health'),
  getProfile: (userId: string) =>
    request('/api/profiles/me', { userId }),
  createProfile: (userId: string, profile: unknown) =>
    request('/api/profiles', { method: 'POST', userId, body: profile }),
  listTrainingPlans: (userId: string) =>
    request<TrainingPlanHistoryResponse>('/api/training-plans/history', {
      userId,
    }),
  listWorkoutHistory: (userId: string) =>
    request<WorkoutHistoryResponse>('/api/workouts/history', { userId }),
  createTrainingPlanProposal: (userId: string, message?: string) =>
    request<TrainingPlanProposalResponse>('/api/proposals/training-plan', {
      method: 'POST',
      userId,
      body: message ? { message } : undefined,
    }),
  createManualTrainingPlanProposal: (
    userId: string,
    basePlanId: number,
    plan: TrainingPlanDraft,
  ) =>
    request<TrainingPlanProposalResponse>(
      '/api/proposals/training-plan/manual-replacement',
      {
        method: 'POST',
        userId,
        body: { base_plan_id: basePlanId, plan },
      },
    ),
  listTrainingPlanProposals: (userId: string) =>
    request<ProposalListResponse>('/api/proposals', { userId }),
  decideTrainingPlanProposal: (
    userId: string,
    proposalId: number,
    decision: ProposalDecision,
  ) =>
    request<TrainingPlanProposalResponse>(
      `/api/proposals/${proposalId}/decision`,
      {
        method: 'POST',
        userId,
        body: { decision },
      },
    ),
  reviseTrainingPlanProposal: (
    userId: string,
    proposalId: number,
    feedback: string,
  ) =>
    request<TrainingPlanProposalResponse>(
      `/api/proposals/${proposalId}/revisions`,
      {
        method: 'POST',
        userId,
        body: { feedback },
      },
    ),
  chatWithCoach: (userId: string, message: string) => {
    ensureCoachSessionCleanup(userId);
    return request<CoachChatResponse>('/api/coach/chat', {
      method: 'POST',
      userId,
      sessionId: COACH_SESSION_ID,
      body: { message },
    });
  },
  endCoachSession: (userId: string, keepalive = false) =>
    request<void>(`/api/memories/working/${COACH_SESSION_ID}`, {
      method: 'DELETE',
      userId,
      keepalive,
    }),
  deleteMemory: (userId: string, memoryId: number) =>
    request<void>(`/api/memories/${memoryId}`, {
      method: 'DELETE',
      userId,
    }),
  createWeeklyReport: (userId: string) =>
    request('/api/reports/weekly', { method: 'POST', userId }),
};
