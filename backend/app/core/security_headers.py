"""CSRF protection and secure cookie helpers."""

from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

ACCESS_COOKIE = "tp_access_token"
REFRESH_COOKIE = "tp_refresh_token"
CSRF_COOKIE = "tp_csrf_token"
CSRF_HEADER = "X-CSRF-Token"

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> str:
    secure = settings.ENV == "production"
    csrf = new_csrf_token()
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )
    return csrf


def clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


def get_access_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get(ACCESS_COOKIE)


def get_refresh_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get(REFRESH_COOKIE)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Validate CSRF header on mutating requests when session cookie auth is used."""

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            return await call_next(request)
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)
        if request.url.path.startswith("/api/v1/ingest"):
            return await call_next(request)
        if request.url.path.startswith("/api/v1/auth/github"):
            return await call_next(request)
        if request.url.path in ("/api/v1/auth/login", "/api/v1/auth/register"):
            return await call_next(request)
        if request.headers.get("X-API-Key"):
            return await call_next(request)
        if request.headers.get("Authorization"):
            return await call_next(request)

        cookie_csrf = request.cookies.get(CSRF_COOKIE)
        header_csrf = request.headers.get(CSRF_HEADER)
        if cookie_csrf and header_csrf and secrets.compare_digest(cookie_csrf, header_csrf):
            return await call_next(request)
        if settings.ENV == "development" and not cookie_csrf:
            return await call_next(request)

        from starlette.responses import JSONResponse

        return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})
