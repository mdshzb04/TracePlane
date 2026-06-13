# agentops-hub

Python SDK for **Traceplane Hub** — production-ready telemetry ingestion.

## Publish structure

```
sdk/
├── agentops_hub/       # Package source
├── pyproject.toml      # PEP 621 metadata (v0.1.0)
├── README.md
└── LICENSE
```

Target: `pip install agentops-hub` via PyPI (CI publish pending).

## Install

```bash
pip install -e ./sdk
```

## Usage

```python
from agentops_hub import AgentOps

client = AgentOps(api_key="aoh_...", base_url="http://localhost:8000/api/v1")

with client.trace(agent="ResearchAgent", model="gpt-4o", framework="langgraph") as span:
    span.set_input("Summarize latest funding news")
    result = my_agent.run("Summarize latest funding news")
    span.set_output(result)
    span.set_tokens(input_tokens=120, output_tokens=340)

print(span.result)  # {'agent_id': '...', 'execution_id': '...', 'trace_id': '...'}
```

Agents are auto-discovered in the registry when telemetry is ingested.
