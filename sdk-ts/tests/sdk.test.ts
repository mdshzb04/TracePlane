import { describe, expect, it, vi, beforeEach } from "vitest"
import { SpanTree, init, trace } from "../src/index"

describe("Traceplane TypeScript SDK", () => {
  beforeEach(() => {
    init({ apiKey: "aoh_test_key", baseUrl: "http://example/api/v1" })
  })

  it("builds ingest payload with agent metadata", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ execution_id: "abc", status: "created" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    const { ingest } = await trace({ agent: "ResearchAgent", model: "gpt-4o" }, (run) => {
      run.setInput("hello")
      run.setOutput("world")
      run.llmCall({ inputTokens: 10, outputTokens: 5 })
      return "done"
    })

    expect(ingest.execution_id).toBe("abc")
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string)
    expect(body.agent.name).toBe("ResearchAgent")
    expect(body.input).toBe("hello")
    expect(body.token_usage.total_tokens).toBe(15)
    expect(body.spans.length).toBeGreaterThanOrEqual(2)
  })

  it("builds session replay span tree matching Python explicit_spans", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ execution_id: "replay-1" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    const tree = new SpanTree()
    tree.buildSessionReplayTree("gpt-4o")
    const spans = tree.all

    expect(spans).toHaveLength(3)
    expect(spans[0].span_type).toBe("root")
    expect(spans[1].span_type).toBe("tool")
    expect(spans[1].parent_span_id).toBe(spans[0].span_id)
    expect(spans[2].span_type).toBe("llm")
    expect(spans[2].parent_span_id).toBe(spans[0].span_id)
    expect(spans[2].token_usage?.total_tokens).toBe(280)
  })

  it("records tool, llm, and error spans", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ execution_id: "x" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    await trace({ agent: "SupportAgent", model: "claude-sonnet-4" }, (run) => {
      const toolId = run.toolCall("billing_lookup", { query: "inv-1" }, { latencyMs: 120 })
      run.llmCall({ parentSpanId: toolId, inputTokens: 1, outputTokens: 0 })
      run.error("timeout", { code: 504 })
      return null
    })

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string)
    const types = body.spans.map((s: { span_type: string }) => s.span_type)
    expect(types).toContain("root")
    expect(types).toContain("tool")
    expect(types).toContain("error")
    expect(body.status).toBe("failed")
  })

  it("requires init before trace", async () => {
    vi.resetModules()
    const mod = await import("../src/index")
    await expect(mod.trace({ agent: "Bot" }, () => "x")).rejects.toThrow(/init/)
  })
})
