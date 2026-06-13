import logging
import time
from typing import Optional

import httpx

from app.schemas.provider import SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)

_VALIDATION_ENDPOINTS: dict[str, dict] = {
    "openai": {
        "url": "https://api.openai.com/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/models",
        "headers": lambda key: {"x-api-key": key, "anthropic-version": "2023-06-01"},
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "headers": lambda key: {"x-goog-api-key": key},
    },
    "deepseek": {
        "url": "https://api.deepseek.com/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "xai": {
        "url": "https://api.x.ai/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "cohere": {
        "url": "https://api.cohere.com/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "perplexity": {
        "url": "https://api.perplexity.ai/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "minimax": {
        "url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
        "method": "POST",
        "json": {"model": "abab6.5-chat", "messages": [{"role": "user", "content": "ping"}]},
        "accept_status": {200, 400, 401, 403},
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "deepinfra": {
        "url": "https://api.deepinfra.com/v1/openai/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    "fireworks": {
        "url": "https://api.fireworks.ai/inference/v1/models",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
}


async def validate_provider_key(provider_id: str, api_key: str) -> tuple[str, str, Optional[int]]:
    """Return (status, message, latency_ms). status is 'connected' or 'error'."""
    if provider_id not in SUPPORTED_PROVIDERS:
        return "error", f"Unsupported provider: {provider_id}", None

    config = _VALIDATION_ENDPOINTS.get(provider_id)
    if not config:
        return "error", "No validation endpoint configured", None

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            method = config.get("method", "GET").upper()
            kwargs = {
                "url": config["url"],
                "headers": config["headers"](api_key),
            }
            if method == "POST":
                kwargs["json"] = config.get("json", {})
            response = await client.request(method, **kwargs)

        latency_ms = int((time.perf_counter() - started) * 1000)
        accept = config.get("accept_status", {200})
        if response.status_code in accept:
            if response.status_code == 401:
                return "error", "Invalid API key", latency_ms
            if response.status_code == 403:
                return "error", "API key lacks required permissions", latency_ms
            return "connected", "Connection verified", latency_ms
        if response.status_code == 401:
            return "error", "Invalid API key", latency_ms
        return "error", f"Provider returned HTTP {response.status_code}", latency_ms
    except httpx.TimeoutException:
        return "error", "Connection timed out", None
    except httpx.HTTPError as exc:
        logger.warning("Provider validation failed for %s: %s", provider_id, exc)
        return "error", "Unable to reach provider API", None
