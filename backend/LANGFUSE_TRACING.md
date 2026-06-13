# Langfuse Tracing — AgentOps Hub

Tracing follows [Langfuse SDK v4 best practices](https://langfuse.com/docs/observability/sdk/overview) and the official [Langfuse Agent Skill](https://github.com/langfuse/skills).

## Environment Variables

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://jp.cloud.langfuse.com   # or cloud.langfuse.com / us.cloud.langfuse.com
LANGFUSE_ENABLED=true
LANGFUSE_TRACING_ENVIRONMENT=development
```

`LANGFUSE_HOST` is also accepted as an alias for `LANGFUSE_BASE_URL`.

## What Gets Traced

| Feature | Trace Name | Type | Attributes |
|---------|-----------|------|------------|
| Agent execution | `execution:{agent_name}` | span | `user_id`, `session_id=agent_id`, tags |
| Model call | `model:{model}` | generation | tokens, cost, model |
| Tool call | `tool:{name}` | tool | latency |
| Evaluation | `evaluation:{agent_name}` | evaluator | score, test case |
| Failure investigator | `failure-investigation` | agent | user_id, session_id, tags |
| Investigator nodes | `investigator:{node}` | span | latency per pipeline step |
| LangChain LLM calls | auto via CallbackHandler | generation | model, tokens (automatic) |

## Architecture

```
FastAPI Request
  └── LangfuseService (get_client())
        ├── propagate_attributes(user_id, session_id, tags)
        ├── start_as_current_observation() — nested spans/generations
        └── CallbackHandler — LangChain/LangGraph LLM auto-tracing
```

## Key Files

- `app/services/langfuse_service.py` — centralized tracing service (SDK v4)
- `app/agents/graph.py` — investigator with CallbackHandler + node spans
- `app/agents/nodes.py` — LLM calls pass RunnableConfig for callback propagation
- `app/services/execution.py` — execution lifecycle traces
- `app/services/evaluation.py` — evaluation traces
- `app/services/analytics.py` — reads traces/generations via SDK v4 REST API

## Viewing Traces

1. Open your Langfuse project at `LANGFUSE_BASE_URL`
2. Go to **Traces** — filter by tags: `execution`, `investigation`, `evaluation`
3. Go to **Sessions** — grouped by `agent_id` or `investigation-{agent_id}`
4. Go to **Users** — filter by authenticated `user_id`

## Skill Reference

The Langfuse skill is installed at `.cursor/skills/langfuse/` for Cursor agent guidance.
