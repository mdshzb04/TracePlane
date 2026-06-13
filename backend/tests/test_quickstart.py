from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.quickstart_service import (
    _extract_openai_output,
    _extract_openai_usage,
    call_provider,
)

TEST_PROMPT = "Reply with exactly one word: Traceplane"


def test_extract_openai_usage_and_output():
    data = {
        "choices": [{"message": {"content": "Traceplane"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 3},
    }
    assert _extract_openai_usage(data) == (12, 3)
    assert _extract_openai_output(data) == "Traceplane"


@pytest.mark.asyncio
async def test_call_provider_openai():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "Traceplane"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
    }

    with patch("app.services.quickstart_service.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.post.return_value = mock_response
        client_cls.return_value = client

        result = await call_provider(
            "openai",
            "sk-test-key",
            model="gpt-4o-mini",
            prompt=TEST_PROMPT,
        )

    assert result.output == "Traceplane"
    assert result.input_tokens == 10
    assert result.output_tokens == 2
    assert result.latency_ms >= 0
    posted = client.post.call_args
    assert posted.kwargs["json"]["messages"][0]["content"] == TEST_PROMPT


@pytest.mark.asyncio
async def test_quickstart_route_requires_auth(client):
    response = await client.post(
        "/api/v1/quickstart/test-request",
        json={
            "provider_id": "openai",
            "provider_api_key": "sk-test-key-12345",
        },
    )
    assert response.status_code == 401
