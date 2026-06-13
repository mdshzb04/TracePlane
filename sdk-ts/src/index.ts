export interface InitOptions {
  apiKey: string
  baseUrl?: string
  timeoutMs?: number
}

export interface TraceOptions {
  agent: string
  model?: string
  framework?: string
  provider?: string
  environment?: string
  owner?: string
  tags?: string[]
}

export type SpanType = "root" | "llm" | "tool" | "error" | "custom"
export type SpanStatus = "success" | "failed" | "running"

export interface SpanRecord {
  span_id: string
  parent_span_id?: string
  name: string
  span_type: SpanType
  status: SpanStatus
  latency_ms?: number
  attributes?: Record<string, unknown>
  token_usage?: Record<string, number>
  estimated_cost?: number
}

let config: Required<InitOptions> | null = null
let spanCounter = 0

export function init(options: InitOptions): void {
  config = {
    apiKey: options.apiKey,
    baseUrl: (options.baseUrl ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, ""),
    timeoutMs: options.timeoutMs ?? 30000,
  }
}

function requireConfig(): Required<InitOptions> {
  if (!config) throw new Error("Call init({ apiKey }) before using the SDK")
  return config
}

function newSpanId(prefix: string): string {
  spanCounter += 1
  return `${prefix}-${spanCounter}`
}

/** Nested span tree — matches Python SDK / ingest IngestSpan schema. */
export class SpanTree {
  private spans: SpanRecord[] = []

  get all(): SpanRecord[] {
    return [...this.spans]
  }

  root(name: string, attrs: Record<string, unknown> = {}): string {
    const id = newSpanId("root")
    this.spans.push({
      span_id: id,
      name,
      span_type: "root",
      status: "success",
      attributes: attrs,
    })
    return id
  }

  child(
    parentId: string,
    name: string,
    spanType: SpanType,
    opts: Partial<SpanRecord> = {},
  ): string {
    const id = newSpanId(spanType)
    this.spans.push({
      span_id: id,
      parent_span_id: parentId,
      name,
      span_type: spanType,
      status: opts.status ?? "success",
      latency_ms: opts.latency_ms,
      attributes: opts.attributes,
      token_usage: opts.token_usage,
      estimated_cost: opts.estimated_cost,
    })
    return id
  }

  llm(
    parentId: string,
    model: string,
    opts: {
      latencyMs?: number
      inputTokens?: number
      outputTokens?: number
      cachedTokens?: number
      estimatedCost?: number
      status?: SpanStatus
    } = {},
  ): string {
    const inTok = opts.inputTokens ?? 0
    const outTok = opts.outputTokens ?? 0
    return this.child(parentId, model, "llm", {
      status: opts.status ?? "success",
      latency_ms: opts.latencyMs,
      token_usage: {
        input_tokens: inTok,
        output_tokens: outTok,
        cached_tokens: opts.cachedTokens ?? 0,
        total_tokens: inTok + outTok,
      },
      estimated_cost: opts.estimatedCost,
      attributes: { model },
    })
  }

  tool(
    parentId: string,
    name: string,
    opts: {
      latencyMs?: number
      status?: SpanStatus
      attributes?: Record<string, unknown>
    } = {},
  ): string {
    return this.child(parentId, name, "tool", {
      status: opts.status ?? "success",
      latency_ms: opts.latencyMs,
      attributes: { tool: name, ...opts.attributes },
    })
  }

  errorSpan(
    parentId: string,
    message: string,
    opts: { latencyMs?: number; code?: string | number } = {},
  ): string {
    return this.child(parentId, message, "error", {
      status: "failed",
      latency_ms: opts.latencyMs,
      attributes: { error: message, code: opts.code },
    })
  }

  /** Parity helper — mirrors demo span tree layout. */
  buildSessionReplayTree(model: string): string {
    const rootId = this.root("agent.run", { replay: true })
    this.tool(rootId, "web_search", { latencyMs: 200, attributes: { tool: "web_search" } })
    this.llm(rootId, model, {
      latencyMs: 900,
      inputTokens: 200,
      outputTokens: 80,
      cachedTokens: 50,
      estimatedCost: 0.0024,
    })
    return rootId
  }
}

export class TraceRun {
  private events: { event_type: string; event_data: Record<string, unknown> }[] = []
  private tokenUsage: Record<string, number> = {}
  private input?: string
  private output?: string
  private status: SpanStatus = "success"
  private start: number
  readonly spans: SpanTree
  readonly rootSpanId: string

  constructor(private opts: TraceOptions) {
    this.start = Date.now()
    this.spans = new SpanTree()
    this.rootSpanId = this.spans.root(opts.agent)
    this.addEvent("execution.started", { agent: opts.agent })
  }

  setInput(value: string): void {
    this.input = value
  }

  setOutput(value: string): void {
    this.output = value
  }

  addEvent(eventType: string, data: Record<string, unknown> = {}): void {
    this.events.push({ event_type: eventType, event_data: data })
  }

  startSpan(name: string, spanType: SpanType = "custom", parentId?: string): string {
    return this.spans.child(parentId ?? this.rootSpanId, name, spanType)
  }

  llmCall(params: {
    model?: string
    inputTokens?: number
    outputTokens?: number
    cachedTokens?: number
    latencyMs?: number
    estimatedCost?: number
    parentSpanId?: string
  }): string {
    const model = params.model ?? this.opts.model ?? "llm"
    this.addEvent("model.call.completed", {
      model,
      input_tokens: params.inputTokens ?? 0,
      output_tokens: params.outputTokens ?? 0,
      latency_ms: params.latencyMs,
    })
    const inTok = (this.tokenUsage.input_tokens ?? 0) + (params.inputTokens ?? 0)
    const outTok = (this.tokenUsage.output_tokens ?? 0) + (params.outputTokens ?? 0)
    this.tokenUsage = {
      input_tokens: inTok,
      output_tokens: outTok,
      cached_tokens: (this.tokenUsage.cached_tokens ?? 0) + (params.cachedTokens ?? 0),
      total_tokens: inTok + outTok,
    }
    return this.spans.llm(params.parentSpanId ?? this.rootSpanId, model, {
      latencyMs: params.latencyMs,
      inputTokens: params.inputTokens,
      outputTokens: params.outputTokens,
      cachedTokens: params.cachedTokens,
      estimatedCost: params.estimatedCost,
    })
  }

  toolCall(
    name: string,
    data: Record<string, unknown> = {},
    opts: { latencyMs?: number; parentSpanId?: string } = {},
  ): string {
    this.addEvent("tool.invoked", { tool: name, latency_ms: opts.latencyMs, ...data })
    return this.spans.tool(opts.parentSpanId ?? this.rootSpanId, name, {
      latencyMs: opts.latencyMs,
      attributes: data,
    })
  }

  error(message: string, data: Record<string, unknown> = {}, parentSpanId?: string): void {
    this.status = "failed"
    this.output = this.output ?? message
    this.addEvent("error.agent", { message, ...data })
    this.spans.errorSpan(parentSpanId ?? this.rootSpanId, message, {
      latencyMs: data.latency_ms as number | undefined,
      code: data.code as string | number | undefined,
    })
  }

  span(name: string, spanType: SpanType = "custom", attrs: Record<string, unknown> = {}): string {
    this.addEvent(`span.${spanType}`, { name, ...attrs })
    return this.spans.child(this.rootSpanId, name, spanType, { attributes: attrs })
  }

  async flush(): Promise<Record<string, unknown>> {
    const cfg = requireConfig()
    const latencyMs = Date.now() - this.start
    const payload = {
      agent: {
        name: this.opts.agent,
        model: this.opts.model,
        framework: this.opts.framework,
        provider: this.opts.provider,
        environment: this.opts.environment ?? "production",
        owner: this.opts.owner,
        tags: this.opts.tags ?? [],
      },
      input: this.input,
      output: this.output,
      status: this.status,
      latency_ms: latencyMs,
      model: this.opts.model,
      token_usage: this.tokenUsage,
      events: this.events,
      spans: this.spans.all,
    }

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), cfg.timeoutMs)
    const res = await fetch(`${cfg.baseUrl}/ingest/trace`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cfg.apiKey },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).finally(() => clearTimeout(timer))

    if (!res.ok) throw new Error(`Ingest failed: ${res.status}`)
    return res.json() as Promise<Record<string, unknown>>
  }
}

export async function trace<T>(
  opts: TraceOptions,
  fn: (run: TraceRun) => Promise<T> | T,
): Promise<{ result: T; ingest: Record<string, unknown> }> {
  const run = new TraceRun(opts)
  try {
    const result = await fn(run)
    const ingest = await run.flush()
    return { result, ingest }
  } catch (err) {
    run.error(err instanceof Error ? err.message : String(err))
    await run.flush()
    throw err
  }
}
