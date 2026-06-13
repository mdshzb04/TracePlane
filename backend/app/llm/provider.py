"""Multi-provider LLM abstraction layer.

Switch providers via LLM_PROVIDER environment variable: openai | nvidia
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[float] = None
    raw: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract LLM provider contract for AgentOps Hub."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...

    @abstractmethod
    def get_chat_model(self, *, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        ...

    async def invoke(
        self,
        messages: list[BaseMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.1,
        config: Optional[dict] = None,
    ) -> LLMResponse:
        import time

        llm = self.get_chat_model(model=model, temperature=temperature)
        start = time.perf_counter()
        result = await llm.ainvoke(messages, config=config)
        latency_ms = (time.perf_counter() - start) * 1000

        usage = getattr(result, "usage_metadata", None) or {}
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", 0) or input_tokens + output_tokens)

        return LLMResponse(
            content=str(result.content),
            model=model or self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            raw=result,
        )

    def is_configured(self) -> bool:
        return True
