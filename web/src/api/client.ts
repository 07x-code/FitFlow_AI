const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? '';

const COACH_SESSION_ID =
  globalThis.crypto?.randomUUID?.() ??
  `coach-${Date.now()}-${Math.random().toString(16).slice(2)}`;

let coachCleanupRegistered = false;

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE';
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

export type UserAccount = {
  id: string;
  email: string;
  display_name: string;
  status: 'active' | 'disabled';
  email_verified_at: string | null;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
};

export type AuthenticationResponse = {
  user: UserAccount;
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
    sessionId,
    body,
    keepalive = false,
  }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    keepalive,
  });

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/api/auth/')) {
      window.dispatchEvent(new Event('fitflow:unauthorized'));
    }
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
 */
function ensureCoachSessionCleanup() {
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
          keepalive: true,
        },
      ).catch(() => undefined);
    },
    { once: true },
  );
}

export const fitFlowApi = {
  health: () => request<{ service: string; status: string }>('/health'),
  register: (email: string, password: string, displayName: string) =>
    request<AuthenticationResponse>('/api/auth/register', {
      method: 'POST',
      body: { email, password, display_name: displayName },
    }),
  login: (email: string, password: string) =>
    request<AuthenticationResponse>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    }),
  logout: () => request<void>('/api/auth/logout', { method: 'POST' }),
  getCurrentUser: () => request<UserAccount>('/api/auth/me'),
  getProfile: () => request('/api/profiles/me'),
  createProfile: (profile: unknown) =>
    request('/api/profiles', { method: 'POST', body: profile }),
  listTrainingPlans: () =>
    request<TrainingPlanHistoryResponse>('/api/training-plans/history'),
  listWorkoutHistory: () =>
    request<WorkoutHistoryResponse>('/api/workouts/history'),
  createTrainingPlanProposal: (message?: string) =>
    request<TrainingPlanProposalResponse>('/api/proposals/training-plan', {
      method: 'POST',
      body: message ? { message } : undefined,
    }),
  createManualTrainingPlanProposal: (
    basePlanId: number,
    plan: TrainingPlanDraft,
  ) =>
    request<TrainingPlanProposalResponse>(
      '/api/proposals/training-plan/manual-replacement',
      {
        method: 'POST',
        body: { base_plan_id: basePlanId, plan },
      },
    ),
  listTrainingPlanProposals: () =>
    request<ProposalListResponse>('/api/proposals'),
  decideTrainingPlanProposal: (
    proposalId: number,
    decision: ProposalDecision,
  ) =>
    request<TrainingPlanProposalResponse>(
      `/api/proposals/${proposalId}/decision`,
      {
        method: 'POST',
        body: { decision },
      },
    ),
  reviseTrainingPlanProposal: (
    proposalId: number,
    feedback: string,
  ) =>
    request<TrainingPlanProposalResponse>(
      `/api/proposals/${proposalId}/revisions`,
      {
        method: 'POST',
        body: { feedback },
      },
    ),
  chatWithCoach: (message: string) => {
    ensureCoachSessionCleanup();
    return request<CoachChatResponse>('/api/coach/chat', {
      method: 'POST',
      sessionId: COACH_SESSION_ID,
      body: { message },
    });
  },
  endCoachSession: (keepalive = false) =>
    request<void>(`/api/memories/working/${COACH_SESSION_ID}`, {
      method: 'DELETE',
      keepalive,
    }),
  deleteMemory: (memoryId: number) =>
    request<void>(`/api/memories/${memoryId}`, {
      method: 'DELETE',
    }),
  createWeeklyReport: () =>
    request('/api/reports/weekly', { method: 'POST' }),
};
