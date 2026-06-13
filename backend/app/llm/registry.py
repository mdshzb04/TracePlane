from functools import lru_cache

from app.core.config import settings
from app.llm.nvidia_provider import NvidiaProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import LLMProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "nvidia": NvidiaProvider,
}


@lru_cache
def get_llm_provider(name: str | None = None) -> LLMProvider:
    provider_name = (name or settings.LLM_PROVIDER).lower().strip()
    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. Supported: {', '.join(_PROVIDERS)}"
        )
    return _PROVIDERS[provider_name]()
