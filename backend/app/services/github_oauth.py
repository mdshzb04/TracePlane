"""GitHub OAuth token exchange and profile fetch."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestError, UnauthorizedError

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API = "https://api.github.com"


@dataclass
class GitHubProfile:
    github_id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    login: str


def build_github_authorize_url(state: str) -> str:
    if not settings.github_oauth_configured:
        raise BadRequestError("GitHub OAuth is not configured")
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.github_callback_url,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.github_callback_url,
            },
        )
    if response.status_code != 200:
        logger.warning("GitHub token exchange failed: %s", response.text)
        raise UnauthorizedError("GitHub authorization failed")
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise UnauthorizedError("GitHub did not return an access token")
    return token


async def _github_get(client: httpx.AsyncClient, path: str, token: str) -> dict[str, Any]:
    response = await client.get(
        f"{GITHUB_API}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    if response.status_code != 200:
        raise UnauthorizedError("Failed to fetch GitHub profile")
    return response.json()


async def fetch_github_profile(access_token: str) -> GitHubProfile:
    async with httpx.AsyncClient(timeout=15) as client:
        user = await _github_get(client, "/user", access_token)
        emails = await _github_get(client, "/user/emails", access_token)

    primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
    if primary is None:
        primary = next((e for e in emails if e.get("verified")), None)
    email = (primary or {}).get("email") or user.get("email")
    if not email:
        raise UnauthorizedError("GitHub account has no verified email")

    return GitHubProfile(
        github_id=str(user["id"]),
        email=email.strip().lower(),
        full_name=user.get("name") or user.get("login"),
        avatar_url=user.get("avatar_url"),
        login=user.get("login", ""),
    )
