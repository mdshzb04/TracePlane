from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.config import settings
from app.llm.provider import LLMProvider


class NvidiaProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "nvidia"

    @property
    def default_model(self) -> str:
        return settings.NVIDIA_MODEL

    def is_configured(self) -> bool:
        return bool(settings.NVIDIA_API_KEY)

    def get_chat_model(self, *, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        if not settings.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY not configured")
        return ChatNVIDIA(
            model=model or settings.NVIDIA_MODEL,
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
            temperature=temperature,
            max_tokens=4096,
        )
