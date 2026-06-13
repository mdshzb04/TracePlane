import logging
import time
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.llm.pricing import estimate_cost
from app.schemas.ingest import IngestAgentMeta, IngestTraceRequest
from app.schemas.quickstart import QUICKSTART_PROVIDERS, QuickstartTestResponse
from app.services.api_key_service import ApiKeyService
from app.services.ingest import IngestService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderCallResult:
    output: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _extract_openai_usage(data: dict) -> tuple[int, int]:
    usage = data.get("usage") or {}
    return int(usage.get("prompt_tokens", 0) or 0), int(usage.get("completion_tokens", 0) or 0)


def _extract_openai_output(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("Provider returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [p.get("text", "") for p in content if isinstance(p, dict)]
        return "".join(parts).strip()
    raise ValueError("Provider returned empty content")


def _provider_error_message(_provider_id: str, response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            err = payload.get("error")
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
            if payload.get("message"):
                return str(payload["message"])
    except Exception:
        pass
    if response.status_code == 401:
        return "Invalid provider API key"
    if response.status_code == 403:
        return "Provider API key lacks required permissions"
    return f"Provider returned HTTP {response.status_code}"


def _max_output_tokens(prompt: str) -> int:
    return min(512, max(64, len(prompt) // 2 + 64))


async def _call_openai_compatible(
    *,
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    extra_headers: dict[str, str] | None = None,
) -> ProviderCallResult:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": _max_output_tokens(prompt),
    }
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=body)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        raise ValueError(_provider_error_message("openai", response))
    data = response.json()
    input_tokens, output_tokens = _extract_openai_usage(data)
    return ProviderCallResult(
        output=_extract_openai_output(data),
        model=str(data.get("model") or model),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )


async def _call_anthropic(api_key: str, model: str, prompt: str) -> ProviderCallResult:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": _max_output_tokens(prompt),
        "messages": [{"role": "user", "content": prompt}],
    }
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        raise ValueError(_provider_error_message("anthropic", response))
    data = response.json()
    usage = data.get("usage") or {}
    content = data.get("content") or []
    text_parts = [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"]
    output = "".join(text_parts).strip()
    if not output:
        raise ValueError("Provider returned empty content")
    return ProviderCallResult(
        output=output,
        model=str(data.get("model") or model),
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        latency_ms=latency_ms,
    )


async def _call_gemini(api_key: str, model: str, prompt: str) -> ProviderCallResult:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": _max_output_tokens(prompt)},
    }
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=body)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        raise ValueError(_provider_error_message("google", response))
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Provider returned no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text_parts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    output = "".join(text_parts).strip()
    if not output:
        raise ValueError("Provider returned empty content")
    usage = data.get("usageMetadata") or {}
    return ProviderCallResult(
        output=output,
        model=model,
        input_tokens=int(usage.get("promptTokenCount", 0) or 0),
        output_tokens=int(usage.get("candidatesTokenCount", 0) or 0),
        latency_ms=latency_ms,
    )


async def _call_cohere(api_key: str, model: str, prompt: str) -> ProviderCallResult:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("https://api.cohere.com/v2/chat", headers=headers, json=body)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        raise ValueError(_provider_error_message("cohere", response))
    data = response.json()
    message = data.get("message") or {}
    content = message.get("content") or []
    text_parts = [p.get("text", "") for p in content if isinstance(p, dict)]
    output = "".join(text_parts).strip()
    if not output:
        raise ValueError("Provider returned empty content")
    usage = data.get("usage") or {}
    tokens = usage.get("tokens") or {}
    return ProviderCallResult(
        output=output,
        model=str(data.get("model") or model),
        input_tokens=int(tokens.get("input_tokens", 0) or 0),
        output_tokens=int(tokens.get("output_tokens", 0) or 0),
        latency_ms=latency_ms,
    )


async def call_provider(provider_id: str, api_key: str, *, model: str, prompt: str) -> ProviderCallResult:
    if provider_id == "openai":
        return await _call_openai_compatible(
            url="https://api.openai.com/v1/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "deepseek":
        return await _call_openai_compatible(
            url="https://api.deepseek.com/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "xai":
        return await _call_openai_compatible(
            url="https://api.x.ai/v1/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "openrouter":
        return await _call_openai_compatible(
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
            extra_headers={"HTTP-Referer": "https://traceplane.dev", "X-Title": "Traceplane Quickstart"},
        )
    if provider_id == "anthropic":
        return await _call_anthropic(api_key, model, prompt)
    if provider_id == "google":
        return await _call_gemini(api_key, model, prompt)
    if provider_id == "mistral":
        return await _call_openai_compatible(
            url="https://api.mistral.ai/v1/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "together":
        return await _call_openai_compatible(
            url="https://api.together.xyz/v1/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "perplexity":
        return await _call_openai_compatible(
            url="https://api.perplexity.ai/chat/completions",
            api_key=api_key,
            model=model,
            prompt=prompt,
        )
    if provider_id == "cohere":
        return await _call_cohere(api_key, model, prompt)
    raise ValueError(f"Unsupported provider: {provider_id}")


class QuickstartService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_test_request(
        self,
        *,
        workspace_id: uuid.UUID,
        provider_id: str,
        provider_api_key: str,
        traceplane_api_key: str | None = None,
        model: str | None = None,
        prompt: str,
        agent_name: str,
    ) -> QuickstartTestResponse:
        if provider_id not in QUICKSTART_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_id}")

        resolved_model = model or QUICKSTART_PROVIDERS[provider_id]["model"]
        agent_name = agent_name.strip() or "quickstart-agent"

        api_key_id: uuid.UUID | None = None
        if traceplane_api_key:
            key_service = ApiKeyService(self.session)
            try:
                api_key = await key_service.authenticate(traceplane_api_key)
            except NotFoundError as exc:
                raise ValueError("Invalid Traceplane API key") from exc
            if api_key.workspace_id != workspace_id:
                raise ValueError("Traceplane API key does not belong to this workspace")
            api_key_id = api_key.id

        try:
            call = await call_provider(
                provider_id,
                provider_api_key,
                model=resolved_model,
                prompt=prompt,
            )
        except httpx.TimeoutException as exc:
            raise ValueError("Provider request timed out") from exc
        except httpx.HTTPError as exc:
            logger.warning("Quickstart provider call failed for %s: %s", provider_id, exc)
            raise ValueError("Unable to reach provider API") from exc

        model_used = call.model
        cost = estimate_cost(model_used, call.input_tokens, call.output_tokens) or 0.0

        ingest = IngestTraceRequest(
            agent=IngestAgentMeta(
                name=agent_name,
                framework="quickstart",
                model=model_used,
                provider=provider_id,
                environment="development",
                tags=["quickstart", "test-request"],
            ),
            input=prompt,
            output=call.output,
            status="success",
            latency_ms=call.latency_ms,
            model=model_used,
            token_usage={
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "total_tokens": call.input_tokens + call.output_tokens,
            },
            estimated_cost=cost,
        )

        result = await IngestService(self.session).ingest_trace(
            ingest,
            workspace_id=workspace_id,
            api_key_id=api_key_id,
        )

        if traceplane_api_key and api_key_id:
            key_service = ApiKeyService(self.session)
            api_key = await key_service.authenticate(traceplane_api_key)
            await key_service.record_usage(api_key, cost)

        return QuickstartTestResponse(
            execution_id=result.execution_id,
            agent_id=result.agent_id,
            trace_id=result.trace_id,
            agent_name=agent_name,
            status="success",
            model=model_used,
            provider=provider_id,
            latency_ms=call.latency_ms,
            input_tokens=call.input_tokens,
            output_tokens=call.output_tokens,
            estimated_cost=float(cost),
            output_preview=call.output[:500],
        )
