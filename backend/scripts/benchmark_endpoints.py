#!/usr/bin/env python3
"""Benchmark authenticated API endpoints (cold + warm)."""

from __future__ import annotations

import asyncio
import time

from httpx import ASGITransport, AsyncClient

from app.main import app

ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/system/onboarding",
    "/api/v1/agents?page=1&page_size=20",
    "/api/v1/executions?page=1&page_size=20",
    "/api/v1/analytics/overview",
    "/api/v1/analytics/observability",
    "/api/v1/analytics/tools",
    "/api/v1/analytics/traces?page=1&page_size=20",
    "/api/v1/analytics/latency",
    "/api/v1/analytics/costs",
    "/api/v1/api-keys",
]


async def main() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = "bench@gmail.com"
        password = "benchtest12345"
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Bench"},
        )
        if reg.status_code not in (201, 400):
            print("register failed", reg.status_code, reg.text)
            return
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if login.status_code != 200:
            print("login failed", login.status_code, login.text)
            return
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        rows: list[tuple[str, int, float, float]] = []
        for path in ENDPOINTS:
            cold = warm = 0.0
            status = 0
            for i in range(2):
                t0 = time.perf_counter()
                resp = await client.get(path, headers=headers)
                ms = (time.perf_counter() - t0) * 1000
                status = resp.status_code
                if i == 0:
                    cold = ms
                else:
                    warm = ms
            rows.append((path, status, cold, warm))

        rows.sort(key=lambda r: r[3], reverse=True)
        print(f"{'warm_ms':>8} {'cold_ms':>8} {'st':>4}  path")
        for path, status, cold, warm in rows:
            print(f"{warm:8.0f} {cold:8.0f} {status:4d}  {path}")


if __name__ == "__main__":
    asyncio.run(main())
