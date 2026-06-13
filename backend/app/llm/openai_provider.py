from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return settings.OPENAI_MODEL

    def is_configured(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    def get_chat_model(self, *, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=4096,
        )
