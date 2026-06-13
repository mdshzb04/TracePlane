import uuid
from typing import Literal

from pydantic import BaseModel, Field

QuickstartProviderId = Literal[
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "xai",
    "openrouter",
    "cohere",
    "perplexity",
    "together",
    "mistral",
]

QUICKSTART_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {"name": "OpenAI", "model": "gpt-4o-mini"},
    "anthropic": {"name": "Anthropic", "model": "claude-3-5-haiku-latest"},
    "google": {"name": "Gemini", "model": "gemini-2.0-flash"},
    "deepseek": {"name": "DeepSeek", "model": "deepseek-chat"},
    "xai": {"name": "Grok", "model": "grok-2-1212"},
    "openrouter": {"name": "OpenRouter", "model": "google/gemini-2.0-flash-001"},
    "cohere": {"name": "Cohere", "model": "command-r-plus-08-2024"},
    "perplexity": {"name": "Perplexity", "model": "sonar"},
    "together": {"name": "Together AI", "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"},
    "mistral": {"name": "Mistral", "model": "mistral-small-latest"},
}


class QuickstartTestRequest(BaseModel):
    provider_id: QuickstartProviderId
    provider_api_key: str = Field(min_length=8, max_length=512)
    traceplane_api_key: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=120)
    prompt: str = Field(default="Reply with exactly one word: Traceplane", min_length=1, max_length=4000)
    agent_name: str = Field(default="quickstart-agent", min_length=1, max_length=255)


class QuickstartTestResponse(BaseModel):
    execution_id: uuid.UUID
    agent_id: uuid.UUID
    trace_id: uuid.UUID
    agent_name: str
    status: str
    model: str
    provider: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    output_preview: str
