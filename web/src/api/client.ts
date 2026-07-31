const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? '';

type RequestOptions = {
  method?: 'GET' | 'POST' | 'DELETE';
  userId?: string;
  body?: unknown;
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
  { method = 'GET', userId, body }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(userId ? { 'X-User-ID': userId } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
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

export const fitFlowApi = {
  health: () => request<{ service: string; status: string }>('/health'),
  getProfile: (userId: string) =>
    request('/api/profiles/me', { userId }),
  createProfile: (userId: string, profile: unknown) =>
    request('/api/profiles', { method: 'POST', userId, body: profile }),
  listTrainingPlans: (userId: string) =>
    request('/api/training-plans/history', { userId }),
  createTrainingPlan: (userId: string) =>
    request('/api/training-plans/draft', { method: 'POST', userId }),
  chatWithCoach: (userId: string, message: string) =>
    request<CoachChatResponse>('/api/coach/chat', {
      method: 'POST',
      userId,
      body: { message },
    }),
  createWeeklyReport: (userId: string) =>
    request('/api/reports/weekly', { method: 'POST', userId }),
};

