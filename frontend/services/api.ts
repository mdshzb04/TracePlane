import { API_BASE_URL } from "@/lib/constants"
import { clearSession, getAccessToken, getCsrfToken, getRefreshToken, setSession } from "@/lib/auth"
import {
  Agent,
  AgentDetail,
  ApiKey,
  ApiKeyCreateResponse,
  CostTimeSeries,
  Evaluation,
  AgentHealthResponse,
  CostIntelligence,
  EvaluationTrend,
  LeaderboardEntry,
  ObservabilityDashboard,
  TokenIntelligence,
  TraceDetail,
  TraceListResponse,
  InvestigationReport,
  IngestTraceResponse,
  LatencyTimeSeries,
  LoginRequest,
  OverviewStats,
  TokenUsageTimeSeries,
  PaginatedResponse,
  RegisterRequest,
  TokenResponse,
  User,
  SetPasswordRequest,
} from "@/types"

const REQUEST_TIMEOUT_MS = 30_000
const LLM_REQUEST_TIMEOUT_MS = 120_000

function fetchErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    if (err.name === "AbortError" || err.name === "TimeoutError") {
      return "Request timed out — please try again."
    }
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      return "Cannot reach the API server. Start the backend on port 8000 and try again."
    }
  }
  return "Cannot reach the API server. Start the backend on port 8000 and try again."
}

async function safeFetch(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = REQUEST_TIMEOUT_MS
): Promise<Response> {
  try {
    return await fetch(url, {
      ...options,
      signal: options.signal ?? AbortSignal.timeout(timeoutMs),
    })
  } catch (err) {
    throw new Error(fetchErrorMessage(err))
  }
}

function parseErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: string }).msg)
        }
        return JSON.stringify(item)
      })
      .join("; ")
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail)
  return "Request failed"
}

function buildQuery(params: Record<string, unknown>): string {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.append(key, String(value))
    }
  })
  const qs = query.toString()
  return qs ? `?${qs}` : ""
}

let refreshPromise: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  const csrf = getCsrfToken()
  const refreshToken = getRefreshToken()
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-CSRF-Token": csrf } : {}),
    },
    credentials: "include",
    body: JSON.stringify(refreshToken ? { refresh_token: refreshToken } : {}),
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  })

  if (!response.ok) return false

  const tokens = (await response.json()) as TokenResponse
  setSession(tokens)
  return true
}

function authHeaders(method: string, extra?: Record<string, string>): Record<string, string> {
  const csrf = getCsrfToken()
  const headers: Record<string, string> = { ...(extra || {}) }
  const accessToken = getAccessToken()
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }
  if (method !== "GET" && method !== "HEAD" && csrf) {
    headers["X-CSRF-Token"] = csrf
  }
  return headers
}

async function fetchWithAuth(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = REQUEST_TIMEOUT_MS
): Promise<Response> {
  const method = (options.method || "GET").toUpperCase()
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...authHeaders(method, options.headers as Record<string, string> | undefined),
  }

  const response = await safeFetch(
    `${API_BASE_URL}${url}`,
    { ...options, headers, credentials: "include" },
    timeoutMs
  )

  if (response.status === 401) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null
      })
    }
    const refreshed = await refreshPromise
    if (refreshed) {
      const retryHeaders: Record<string, string> = {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...authHeaders(method, options.headers as Record<string, string> | undefined),
      }
      const retryResponse = await safeFetch(
        `${API_BASE_URL}${url}`,
        { ...options, headers: retryHeaders, credentials: "include" },
        timeoutMs
      )
      if (retryResponse.ok) return retryResponse
    }

    clearSession()
    if (typeof window !== "undefined") {
      window.location.href = "/login"
    }
    throw new Error("Session expired. Please sign in again.")
  }

  if (response.status === 403) {
    const error = await response.json().catch(() => ({ detail: "Insufficient permissions" }))
    const detail = parseErrorDetail(error.detail)
    if (detail.toLowerCase().includes("developer") || detail.toLowerCase().includes("role")) {
      throw new Error(
        `${detail} Traceplane requires a developer account. Sign out and register again, or ask an admin to upgrade your role.`
      )
    }
    throw new Error(detail)
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }))
    const detail = parseErrorDetail(error.detail) || `HTTP ${response.status}`
    if (response.status >= 500) {
      throw new Error("Unable to load data right now. Please try again.")
    }
    throw new Error(detail)
  }

  return response
}

export async function get<T>(url: string, timeoutMs: number = REQUEST_TIMEOUT_MS): Promise<T> {
  const response = await fetchWithAuth(url, {}, timeoutMs)
  return response.json()
}

export async function post<T>(
  url: string,
  data: unknown,
  timeoutMs: number = REQUEST_TIMEOUT_MS
): Promise<T> {
  const response = await fetchWithAuth(
    url,
    { method: "POST", body: JSON.stringify(data) },
    timeoutMs
  )
  return response.json()
}

export async function put<T>(url: string, data: unknown): Promise<T> {
  const response = await fetchWithAuth(url, {
    method: "PUT",
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function patch<T>(url: string, data: unknown): Promise<T> {
  const response = await fetchWithAuth(url, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function del(url: string): Promise<void> {
  await fetchWithAuth(url, { method: "DELETE" })
}

async function postPublic<T>(path: string, data: unknown): Promise<T> {
  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders("POST"),
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(parseErrorDetail(error.detail))
  }

  return response.json()
}

export const authService = {
  async register(data: RegisterRequest): Promise<void> {
    await postPublic("/auth/register", data)
  },
  async login(data: LoginRequest): Promise<TokenResponse> {
    const result = await postPublic<TokenResponse>("/auth/login", data)
    setSession(result)
    return result
  },
  async logout() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: authHeaders("POST"),
      })
    } catch {
      /* ignore */
    }
    clearSession()
    if (typeof window !== "undefined") {
      window.location.href = "/login"
    }
  },
  async me(): Promise<User> {
    return get<User>("/auth/me")
  },
  githubLoginUrl(): string {
    return `${API_BASE_URL}/auth/github`
  },
  async githubOAuthEnabled(): Promise<boolean> {
    return (await authService.githubOAuthStatus()) === "enabled"
  },
  async githubOAuthStatus(): Promise<"enabled" | "disabled" | "unreachable"> {
    try {
      const res = await safeFetch(`${API_BASE_URL}/auth/github/status`)
      if (!res.ok) return "unreachable"
      const data = (await res.json()) as { enabled?: boolean }
      return data.enabled ? "enabled" : "disabled"
    } catch {
      return "unreachable"
    }
  },
  async setPassword(data: SetPasswordRequest): Promise<User> {
    return post<User>("/auth/set-password", data)
  },
}

export const agentsService = {
  async list(
    params: { status?: string; owner?: string; search?: string; tags?: string; page?: number; page_size?: number } = {}
  ): Promise<PaginatedResponse<Agent>> {
    return get<PaginatedResponse<Agent>>(`/agents${buildQuery(params)}`)
  },
  async get(id: string): Promise<Agent> {
    return get<Agent>(`/agents/${id}`)
  },
  async detail(id: string): Promise<AgentDetail> {
    return get<AgentDetail>(`/agents/${id}/detail`)
  },
}

export const ingestService = {
  async sendTrace(apiKey: string, payload: Record<string, unknown>): Promise<IngestTraceResponse> {
    const response = await safeFetch(`${API_BASE_URL}/ingest/trace`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Ingest failed" }))
      throw new Error(parseErrorDetail(error.detail))
    }
    return response.json()
  },
}

export const apiKeysService = {
  async list(): Promise<ApiKey[]> {
    return get<ApiKey[]>("/api-keys")
  },
  async create(name: string): Promise<ApiKeyCreateResponse> {
    return post<ApiKeyCreateResponse>("/api-keys", { name })
  },
  async revoke(id: string): Promise<void> {
    return del(`/api-keys/${id}`)
  },
  async rotate(id: string): Promise<ApiKeyCreateResponse> {
    return post<ApiKeyCreateResponse>(`/api-keys/${id}/rotate`, {})
  },
}

export const analyticsService = {
  async overview(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<OverviewStats> {
    return get<OverviewStats>(`/analytics/overview${buildQuery(params)}`)
  },
  async observability(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<ObservabilityDashboard> {
    return get<ObservabilityDashboard>(`/analytics/observability${buildQuery(params)}`, 60_000)
  },
  async live(params: { agent_id?: string } = {}) {
    return get<import("@/types").LiveDashboard>(`/analytics/live${buildQuery(params)}`)
  },
  async latency(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<LatencyTimeSeries> {
    return get<LatencyTimeSeries>(`/analytics/latency${buildQuery(params)}`)
  },
  async costs(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<CostIntelligence> {
    return get<CostIntelligence>(`/analytics/costs${buildQuery(params)}`)
  },
  async costTimeseries(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<CostTimeSeries> {
    return get<CostTimeSeries>(`/analytics/costs/timeseries${buildQuery(params)}`)
  },
  async tokens(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<TokenIntelligence> {
    return get<TokenIntelligence>(`/analytics/tokens${buildQuery(params)}`)
  },
  async tokenTimeseries(
    params: { agent_id?: string; start_date?: string; end_date?: string } = {}
  ): Promise<TokenUsageTimeSeries> {
    return get<TokenUsageTimeSeries>(`/analytics/tokens/timeseries${buildQuery(params)}`)
  },
  async health(
    params: { start_date?: string; end_date?: string } = {}
  ): Promise<AgentHealthResponse> {
    return get<AgentHealthResponse>(`/analytics/health${buildQuery(params)}`)
  },
  async traces(
    params: {
      page?: number
      page_size?: number
      agent_id?: string
      model?: string
      status?: string
      search?: string
      start_date?: string
      end_date?: string
    } = {}
  ): Promise<TraceListResponse> {
    return get<TraceListResponse>(`/analytics/traces${buildQuery(params)}`)
  },
  async traceDetail(executionId: string): Promise<TraceDetail> {
    return get<TraceDetail>(`/analytics/traces/${executionId}`)
  },
  async tools(params: { agent_id?: string } = {}): Promise<import("@/types").ToolAnalyticsResponse> {
    return get(`/analytics/tools${buildQuery(params)}`)
  },
}

export const evaluationEngineService = {
  async listDatasets() {
    return get<import("@/types").EvaluationDataset[]>("/evaluation-engine/datasets")
  },
  async createDataset(data: { name: string; description?: string; items: { test_case: string; expected_output?: string }[] }) {
    return post<import("@/types").EvaluationDataset>("/evaluation-engine/datasets", data)
  },
  async runEvaluation(data: { dataset_id: string; agent_id: string }) {
    return post<import("@/types").EvaluationRun>("/evaluation-engine/runs", data)
  },
  async listRuns(agentId?: string) {
    return get<import("@/types").EvaluationRun[]>(`/evaluation-engine/runs${buildQuery({ agent_id: agentId })}`)
  },
  async scoreHistory(agentId?: string) {
    return get<{ points: { date: string; average_score: number; run_id: string }[] }>(
      `/evaluation-engine/score-history${buildQuery({ agent_id: agentId })}`
    )
  },
}

export const systemService = {
  async onboarding(): Promise<import("@/types").OnboardingStatus> {
    return get<import("@/types").OnboardingStatus>("/system/onboarding", 60_000)
  },
  async readiness(): Promise<import("@/types").ProductionReadiness> {
    return get<import("@/types").ProductionReadiness>("/system/readiness")
  },
}

export const quickstartService = {
  async sendTestRequest(data: {
    provider_id: string
    provider_api_key: string
    traceplane_api_key?: string
    model?: string
    prompt?: string
    agent_name?: string
  }): Promise<import("@/types").QuickstartTestResponse> {
    return post<import("@/types").QuickstartTestResponse>(
      "/quickstart/test-request",
      data,
      LLM_REQUEST_TIMEOUT_MS
    )
  },
}

const PROVIDERS_LIST_TIMEOUT_MS = 8_000

export const providersService = {
  async list(): Promise<import("@/types").ProviderCatalogItem[]> {
    return get("/providers", PROVIDERS_LIST_TIMEOUT_MS)
  },
  async connect(providerId: string, apiKey: string) {
    return post<import("@/types").ProviderConnectionRead>(`/providers/${providerId}/connect`, { api_key: apiKey })
  },
  async disconnect(providerId: string) {
    return del(`/providers/${providerId}`)
  },
  async test(providerId: string) {
    return post<import("@/types").ProviderTestResult>(`/providers/${providerId}/test`, {})
  },
  async testTrace(
    providerId: string,
    data: {
      traceplane_api_key?: string
      model?: string
      prompt?: string
      agent_name?: string
    }
  ): Promise<import("@/types").QuickstartTestResponse> {
    return post<import("@/types").QuickstartTestResponse>(
      `/providers/${providerId}/test-trace`,
      data,
      LLM_REQUEST_TIMEOUT_MS
    )
  },
}

export const alertsService = {
  async list(): Promise<import("@/types").AlertRule[]> {
    return get("/alerts")
  },
  async create(data: import("@/types").AlertRuleCreate) {
    return post<import("@/types").AlertRule>("/alerts", data)
  },
  async delete(id: string) {
    return del(`/alerts/${id}`)
  },
  async evaluate(id: string) {
    return post<import("@/types").AlertEvaluationResult>(`/alerts/${id}/evaluate`, {})
  },
  async testEmail(recipient: string): Promise<import("@/types").AlertTestEmailResponse> {
    return post<import("@/types").AlertTestEmailResponse>("/alerts/test-email", { recipient })
  },
  async listEvents(ruleId?: string, limit = 50): Promise<import("@/types").AlertEvent[]> {
    const params = new URLSearchParams()
    if (ruleId) params.set("rule_id", ruleId)
    if (limit !== 50) params.set("limit", String(limit))
    const qs = params.toString()
    return get(`/alerts/events${qs ? `?${qs}` : ""}`)
  },
  async listRuleEvents(ruleId: string, limit = 50): Promise<import("@/types").AlertEvent[]> {
    return get(`/alerts/${ruleId}/events?limit=${limit}`)
  },
}
