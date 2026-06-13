export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ExecutionListResponse extends PaginatedResponse<Execution> {
  summary: ExecutionSummary
}

export interface User {
  id: string
  email: string
  full_name: string | null
  role: "admin" | "developer" | "viewer"
  is_active: boolean
  provider: "email" | "github"
  github_id: string | null
  avatar_url: string | null
  has_password: boolean
  has_github: boolean
  created_at: string
  updated_at: string
}

export interface SetPasswordRequest {
  password: string
  current_password?: string
}

export interface AgentHealthMetrics {
  health_score: number
  total_executions: number
  success_rate: number
  error_rate: number
  avg_latency_ms: number
  total_cost: number
}

export interface Agent {
  id: string
  name: string
  description: string | null
  owner: string
  model: string | null
  framework: string | null
  environment: string | null
  provider: string | null
  external_name: string | null
  source: string
  status: "active" | "inactive" | "deprecated"
  tags: string[]
  last_seen_at: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface AgentDetail extends Agent {
  health: AgentHealthMetrics
}

export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  workspace_id: string
  is_active: boolean
  last_used_at: string | null
  request_count: number
  total_cost: number
  created_at: string
}

export interface OnboardingStep {
  id: string
  label: string
  complete: boolean
}

export interface WorkspaceUsage {
  total_requests: number
  total_tokens: number
  total_cost: number
  active_agents: number
  success_rate: number
}

export interface OnboardingStatus {
  has_api_key: boolean
  has_first_trace: boolean
  has_agent: boolean
  onboarding_complete: boolean
  execution_count: number
  span_count: number
  agent_count: number
  steps: OnboardingStep[]
  usage: WorkspaceUsage
}

export interface ProductionReadiness {
  overall_score: number
  categories: { id: string; name: string; score: number; status: string; detail: string; missing_work: string[] }[]
  blockers: string[]
}

export interface ApiKeyCreateResponse extends ApiKey {
  key: string
}

export interface IngestDiscoveryInfo {
  framework: string
  model: string
  provider: string | null
}

export interface IngestTraceResponse {
  agent_id: string
  execution_id: string
  trace_id: string
  created_agent: boolean
  health_score: number
  discovery: IngestDiscoveryInfo | null
}

export interface Execution {
  id: string
  agent_id: string
  agent_name?: string | null
  provider?: string | null
  input: string | null
  output: string | null
  status: "running" | "success" | "failed" | "timeout" | "cancelled"
  latency_ms: number | null
  token_usage: Record<string, number> | null
  estimated_cost: number | null
  model: string | null
  replay_of_id: string | null
  is_replay: boolean
  started_at: string
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface ExecutionSummary {
  total_executions: number
  total_cost: number
  total_tokens: number
  avg_latency_ms: number
  success_count: number
  failed_count: number
}

export interface ExecutionDetail extends Execution {
  agent_name: string | null
  spans: TraceSpanNode[]
  timelines: TraceTimelines | null
  retry_count: number
  error_count: number
}

export interface ReplayDiff {
  original: {
    execution_id: string
    output: string | null
    latency_ms: number | null
    total_tokens: number
    estimated_cost: number | null
    status: string
  }
  replay: {
    execution_id: string
    output: string | null
    latency_ms: number | null
    total_tokens: number
    estimated_cost: number | null
    status: string
  }
  output_changed: boolean
  output_diff: string | null
  latency_increased: boolean
  tokens_increased: boolean
  cost_increased: boolean
  quality_dropped: boolean
  regression_warnings: string[]
}

export interface ReplayResponse {
  replay_execution_id: string
  diff: ReplayDiff
}

export interface LeaderboardEntry {
  rank: number
  agent_id: string
  agent_name: string
  health_score: number
  success_rate: number
  cost_efficiency_score: number
  avg_latency_ms: number
  total_cost: number
  evaluation_score: number | null
  composite_score: number
}

export interface ExecutionEvent {
  id: string
  execution_id: string
  event_type: string
  event_data: Record<string, unknown> | null
  timestamp: string
}

export interface Evaluation {
  id: string
  agent_id: string
  test_case: string
  expected_output: string | null
  actual_output: string | null
  score: number | null
  evaluation_date: string
  created_at: string
  updated_at: string
}

export interface OverviewStats {
  total_agents: number
  total_executions: number
  success_rate: number
  error_rate?: number
  avg_latency_ms: number
  total_token_usage: number
  total_estimated_cost: number
  monthly_cost?: number
  degraded?: boolean
}

export interface TimeSeriesPoint {
  date: string
  value: number
}

export interface LatencyTimeSeries {
  points: TimeSeriesPoint[]
}

export interface CostTimeSeries {
  points: TimeSeriesPoint[]
}

export interface TokenUsageTimeSeries {
  points: TimeSeriesPoint[]
}

export interface EvaluationTrend {
  points: TimeSeriesPoint[]
}

export interface CostByAgent {
  agent_id: string
  agent_name: string
  total_cost: number
  execution_count: number
}

export interface CostByModel {
  model: string
  total_cost: number
  execution_count: number
  total_tokens: number
}

export interface CostAnomaly {
  execution_id: string
  agent_id: string
  model: string | null
  estimated_cost: number
  avg_cost: number
  multiplier: number
  started_at: string | null
}

export interface CostByWorkspace {
  workspace_id: string
  workspace_name: string
  total_cost: number
  execution_count: number
}

export interface CostIntelligence {
  total_cost: number
  monthly_cost: number
  cost_per_execution: number
  trends: TimeSeriesPoint[]
  monthly_trends?: TimeSeriesPoint[]
  by_agent: CostByAgent[]
  by_model: CostByModel[]
  by_workspace?: CostByWorkspace[]
  anomalies: CostAnomaly[]
  degraded?: boolean
}

export interface TokenByModel {
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
}

export interface TokenByAgent {
  agent_id: string
  agent_name: string
  total_tokens: number
}

export interface TokenAnomaly {
  execution_id: string
  agent_id: string
  model: string | null
  total_tokens: number
  avg_tokens: number
  multiplier: number
  started_at: string | null
}

export interface TokenIntelligence {
  input_tokens: number
  output_tokens: number
  cached_tokens?: number
  total_tokens: number
  trends: TimeSeriesPoint[]
  by_model: TokenByModel[]
  by_agent: TokenByAgent[]
  anomalies?: TokenAnomaly[]
  degraded?: boolean
}

export interface HealthScoreBreakdown {
  latency_score: number
  cost_efficiency_score: number
  reliability_score: number
}

export interface AgentHealth {
  agent_id: string
  agent_name: string
  total_executions: number
  success_rate: number
  error_rate: number
  avg_latency_ms: number
  total_cost: number
  avg_cost_per_execution: number
  health_score: number
  breakdown?: HealthScoreBreakdown
}

export interface AgentHealthResponse {
  agents: AgentHealth[]
  platform_health_score: number
  degraded?: boolean
}

export interface TraceSummary {
  trace_id: string
  execution_id: string
  agent_id: string
  agent_name?: string | null
  name: string
  model: string | null
  status: string
  timestamp: string
  latency_ms: number | null
  input_tokens: number
  output_tokens: number
  total_tokens: number
  estimated_cost: number
  error?: string | null
  tags?: string[]
  metadata?: Record<string, unknown>
}

export interface TraceListResponse {
  traces: TraceSummary[]
  total: number
  page: number
  page_size: number
  degraded?: boolean
}

export interface TraceEvent {
  id: string
  event_type: string
  timestamp: string
  event_data: Record<string, unknown>
}

export interface TraceSpanNode {
  id: string
  parent_span_id: string | null
  name: string
  span_type: string
  status: string
  started_at: string
  ended_at: string | null
  latency_ms: number | null
  attributes: Record<string, unknown>
  token_usage: Record<string, unknown>
  estimated_cost: number | null
  children: TraceSpanNode[]
}

export interface TraceTimelines {
  llm_calls: TraceEvent[]
  tool_calls: TraceEvent[]
  errors: TraceEvent[]
}

export interface TraceDetail {
  trace: TraceSummary
  input: string | null
  output: string | null
  events: TraceEvent[]
  spans?: TraceSpanNode[]
  timelines?: TraceTimelines
  correlation_id: string | null
}

export interface LiveExecutionSummary {
  execution_id: string
  agent_id: string
  agent_name?: string | null
  status: string
  model: string | null
  latency_ms: number | null
  estimated_cost: number
  started_at: string
}

export interface LiveTopProvider {
  provider: string
  request_count: number
}

export interface LiveTopModel {
  model: string
  request_count: number
}

export interface LiveDashboard {
  recent_executions: LiveExecutionSummary[]
  running_executions: LiveExecutionSummary[]
  failed_executions: LiveExecutionSummary[]
  success_rate: number
  error_rate: number
  avg_latency_ms: number
  executions_today: number
  cost_today: number
  tokens_today: number
  input_tokens_today: number
  output_tokens_today: number
  active_agents: number
  top_providers: LiveTopProvider[]
  top_models: LiveTopModel[]
}

export interface EvaluationDataset {
  id: string
  workspace_id: string
  name: string
  description: string | null
  items: { test_case: string; expected_output?: string }[]
  created_at: string
  updated_at: string
}

export interface EvaluationRun {
  id: string
  dataset_id: string
  agent_id: string
  status: string
  average_score: number | null
  results: { test_case: string; expected_output?: string; actual_output?: string; score: number }[]
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface InvestigationHistoryItem {
  id: string
  query: string
  agent_id: string | null
  summary: string
  confidence_score: number
  investigated_at: string
}

export interface RootCause {
  category: string
  description: string
  evidence: string[]
  severity: "low" | "medium" | "high" | "critical"
}

export interface Recommendation {
  title: string
  description: string
  priority: "low" | "medium" | "high" | "critical"
}

export interface InvestigationReport {
  report_source?: "llm" | "rule_based"
  summary: string
  confidence_score: number
  root_causes: RootCause[]
  recommendations: Recommendation[]
  agent_id: string | null
  query: string
  investigated_at: string
}

export interface InvestigateRequest {
  query: string
  agent_id?: string
  start_date?: string
  end_date?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface SessionReplayStep {
  step_index: number
  step_type: "span" | "llm" | "tool" | "error" | "execution"
  name: string
  status: string
  started_at: string
  ended_at?: string | null
  offset_ms: number
  duration_ms: number
  input_preview?: string | null
  output_preview?: string | null
  prompt?: string | null
  completion?: string | null
  tool_input?: Record<string, unknown> | null
  tool_output?: Record<string, unknown> | null
  token_usage?: Record<string, number>
  estimated_cost?: number | null
  error_message?: string | null
  attributes?: Record<string, unknown>
}

export interface SessionReplayResponse {
  execution_id: string
  total_duration_ms: number
  step_count: number
  error_count: number
  steps: SessionReplayStep[]
}

export interface ExecutionCompareSide {
  execution_id: string
  agent_name?: string | null
  model?: string | null
  input?: string | null
  output?: string | null
  latency_ms?: number | null
  total_tokens: number
  estimated_cost?: number | null
  status: string
}

export interface ExecutionCompareDiff {
  execution_a: ExecutionCompareSide
  execution_b: ExecutionCompareSide
  output_diff?: string | null
  prompt_diff?: string | null
  model_changed: boolean
  latency_delta_ms: number
  token_delta: number
  cost_delta: number
  status_changed: boolean
}

export interface ToolMetric {
  tool_name: string
  invocation_count: number
  success_count: number
  failure_count: number
  success_rate: number
  avg_latency_ms: number
  total_cost: number
  p95_latency_ms: number
}

export interface ToolAnalyticsResponse {
  tools: ToolMetric[]
  total_invocations: number
  total_failures: number
}

export interface IncidentEvent {
  id: string
  event_type: string
  message: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface ObservabilityKpis {
  total_requests: number
  total_cost: number
  total_tokens: number
  success_rate: number
  avg_latency_ms: number
  active_agents: number
}

export interface ObservabilityTimeSeries {
  requests: TimeSeriesPoint[]
  cost: TimeSeriesPoint[]
  tokens: TimeSeriesPoint[]
  latency: TimeSeriesPoint[]
  failure_rate: TimeSeriesPoint[]
  bucket: string
}

export interface TopModelRow {
  model: string
  request_count: number
  total_cost: number
  total_tokens: number
}

export interface TopAgentRow {
  agent_id: string
  agent_name: string
  request_count: number
  total_cost: number
  total_tokens: number
  success_rate: number
}

export interface TopToolRow {
  tool_name: string
  invocation_count: number
  success_rate: number
  avg_latency_ms: number
  total_cost: number
}

export interface ExecutionTableRow {
  execution_id: string
  trace_id: string
  agent_id: string
  agent_name: string
  provider: string | null
  status: string
  model: string | null
  total_tokens: number
  latency_ms: number | null
  estimated_cost: number
  started_at: string
}

export interface ObservabilityBreakdowns {
  top_models: TopModelRow[]
  top_agents: TopAgentRow[]
  top_providers: TopProviderRow[]
}

export interface TopProviderRow {
  provider: string
  request_count: number
  total_cost: number
  total_tokens: number
}

export interface ObservabilityTables {
  recent_executions: ExecutionTableRow[]
}

export interface ObservabilityDashboard {
  kpis: ObservabilityKpis
  timeseries: ObservabilityTimeSeries
  breakdowns: ObservabilityBreakdowns
  tables: ObservabilityTables
  start_date: string
  end_date: string
  bucket: string
  degraded?: boolean
}

export interface ProviderCatalogItem {
  provider_id: string
  name: string
  description: string
  connected: boolean
  status?: string | null
  key_hint?: string | null
  last_validated_at?: string | null
  last_error?: string | null
}

export interface ProviderConnectionRead {
  provider_id: string
  name: string
  status: string
  key_hint: string
  last_validated_at?: string | null
  last_error?: string | null
}

export interface QuickstartTestResponse {
  execution_id: string
  agent_id: string
  trace_id: string
  agent_name: string
  status: string
  model: string
  provider: string
  latency_ms: number
  input_tokens: number
  output_tokens: number
  estimated_cost: number
  output_preview: string
}

export interface ProviderTestResult {
  provider_id: string
  status: "connected" | "error"
  message: string
  latency_ms?: number | null
}

export type AlertMetric = "cost_spike" | "error_rate" | "latency_threshold" | "token_threshold" | "provider_outage"

export interface AlertChannelConfig {
  type: "slack" | "discord" | "webhook" | "email"
  target: string
  name?: string | null
}

export interface AlertRuleCreate {
  name: string
  metric: AlertMetric
  operator?: "gt" | "gte" | "lt" | "lte"
  threshold: number
  window_minutes?: number
  cooldown_minutes?: number
  channels: AlertChannelConfig[]
  is_active?: boolean
}

export interface AlertRule {
  id: string
  name: string
  metric: AlertMetric
  operator: string
  threshold: number
  window_minutes: number
  cooldown_minutes: number
  channels: AlertChannelConfig[]
  is_active: boolean
  trigger_count: number
  last_triggered_at?: string | null
  created_at: string
  updated_at: string
}

export interface AlertDeliveryResult {
  channel_type: string
  target: string
  success: boolean
  error?: string | null
  resend_id?: string | null
  resend_response?: Record<string, unknown> | null
}

export interface AlertEvaluationResult {
  rule_id: string
  triggered: boolean
  current_value: number
  message: string
  deliveries?: AlertDeliveryResult[]
}

export interface AlertTestEmailResponse {
  success: boolean
  recipient: string
  message: string
  resend_id?: string | null
  resend_response?: Record<string, unknown> | null
  error?: string | null
}

export interface AlertEvent {
  id: string
  rule_id: string
  rule_name: string
  metric: string
  operator: string
  threshold: number
  current_value: number
  message: string
  channel_type: string
  channel_target: string
  delivery_success: boolean
  delivery_error?: string | null
  resend_id?: string | null
  severity?: string | null
  agent_name?: string | null
  provider?: string | null
  model?: string | null
  environment?: string | null
  is_test: boolean
  created_at: string
}

export interface Incident {
  id: string
  title: string
  incident_type: string
  severity: string
  status: string
  root_cause?: string | null
  resolution_notes?: string | null
  agent_id?: string | null
  metadata: Record<string, unknown>
  resolved_at?: string | null
  created_at: string
  updated_at: string
  events: IncidentEvent[]
}