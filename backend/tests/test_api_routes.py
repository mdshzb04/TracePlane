"""Smoke tests — protected routes exist and return 401 without auth."""

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/system/onboarding"),
        ("GET", "/api/v1/system/readiness"),
        ("GET", "/api/v1/executions"),
        ("GET", "/api/v1/analytics/overview"),
        ("GET", "/api/v1/analytics/observability"),
        ("POST", "/api/v1/quickstart/test-request"),
    ],
)
async def test_protected_routes_require_auth(client, method, path):
    response = await client.request(method, path, json={} if method == "POST" else None)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_requires_api_key(client):
    response = await client.post("/api/v1/ingest/trace", json={"agent": {"name": "Test"}})
    assert response.status_code == 401
