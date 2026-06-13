from typing import Literal, Optional

from pydantic import BaseModel, Field

UI_PROVIDER_IDS: tuple[str, ...] = (
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "xai",
    "openrouter",
    "cohere",
    "perplexity",
    "mistral",
    "minimax",
    "cerebras",
    "deepinfra",
    "fireworks",
)

SUPPORTED_PROVIDERS = {pid: {"name": _name, "description": ""} for pid, _name in (
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("google", "Gemini"),
    ("deepseek", "DeepSeek"),
    ("xai", "Grok"),
    ("openrouter", "OpenRouter"),
    ("cohere", "Cohere"),
    ("perplexity", "Perplexity"),
    ("mistral", "Mistral"),
    ("minimax", "MiniMax"),
    ("cerebras", "Cerebras"),
    ("deepinfra", "DeepInfra"),
    ("fireworks", "Fireworks"),
)}


class ProviderCatalogItem(BaseModel):
    provider_id: str
    name: str
    description: str = ""
    connected: bool = False
    status: Optional[str] = None
    key_hint: Optional[str] = None
    last_validated_at: Optional[str] = None
    last_error: Optional[str] = None


class ProviderConnectRequest(BaseModel):
    api_key: str = Field(min_length=8, max_length=512)


class ProviderConnectionRead(BaseModel):
    provider_id: str
    name: str
    status: str
    key_hint: str
    last_validated_at: Optional[str] = None
    last_error: Optional[str] = None

    model_config = {"from_attributes": True}


class ProviderTestResult(BaseModel):
    provider_id: str
    status: Literal["connected", "error"]
    message: str
    latency_ms: Optional[int] = None


class ProviderTestTraceRequest(BaseModel):
    traceplane_api_key: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=120)
    prompt: str = Field(default="Reply with exactly one word: Traceplane", min_length=1, max_length=4000)
    agent_name: str = Field(default="sdk-agent", min_length=1, max_length=255)
