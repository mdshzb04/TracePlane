import logging
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.core.exceptions import BadRequestError
from app.core.oauth_state import create_oauth_state, verify_oauth_state
from app.core.security_headers import clear_auth_cookies, get_refresh_from_cookie, set_auth_cookies
from app.schemas.user import (
    LoginRequest,
    RefreshRequest,
    SetPasswordRequest,
    TokenResponse,
    UserAdminUpdate,
    UserCreate,
    UserRead,
    UserRegister,
    UserSelfUpdate,
)
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.github_oauth import build_github_authorize_url, exchange_code_for_token, fetch_github_profile

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

OAUTH_STATE_COOKIE = "tp_oauth_state"


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserRegister, db: DbSession):
    service = AuthService(db)
    user = await service.register(data)
    await AuditService(db).log("user.registered", "user", resource_id=user.id)
    return user


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    current_user: AdminUser,
    db: DbSession,
):
    service = AuthService(db)
    user = await service.create_user(data)
    await AuditService(db).log("user.created", "user", resource_id=user.id, user_id=current_user.id)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: DbSession):
    service = AuthService(db)
    tokens = await service.login(data.email, data.password)
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    await AuditService(db).log("user.login", "auth", details={"email": data.email, "provider": "email"})
    return tokens


@router.get("/github")
async def github_login():
    if not settings.github_oauth_configured:
        raise BadRequestError("GitHub OAuth is not configured")
    state = create_oauth_state()
    secure = settings.ENV == "production"
    redirect = RedirectResponse(url=build_github_authorize_url(state), status_code=302)
    redirect.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=600,
        path="/api/auth",
    )
    return redirect


@router.get("/github/status")
async def github_status():
    return {"enabled": settings.github_oauth_configured}


@router.get("/github/callback")
async def github_callback(
    request: Request,
    response: Response,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={quote(error)}",
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=missing_code",
            status_code=302,
        )

    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not cookie_state or not verify_oauth_state(state) or not verify_oauth_state(cookie_state):
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=invalid_state",
            status_code=302,
        )
    if cookie_state != state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=invalid_state",
            status_code=302,
        )

    service = AuthService(db)
    try:
        github_token = await exchange_code_for_token(code)
        profile = await fetch_github_profile(github_token)
        user, created = await service.login_or_link_github(profile)
        tokens = await service.issue_tokens(user)
    except Exception as exc:
        logger.warning("GitHub OAuth callback failed: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=github_auth_failed",
            status_code=302,
        )

    await AuditService(db).log(
        "user.login",
        "auth",
        resource_id=user.id,
        details={"email": user.email, "provider": "github", "created": created},
    )

    fragment = (
        f"#access_token={quote(tokens.access_token)}"
        f"&refresh_token={quote(tokens.refresh_token)}"
    )
    redirect = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback{fragment}",
        status_code=302,
    )
    set_auth_cookies(redirect, tokens.access_token, tokens.refresh_token)
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path="/api/auth")
    return redirect


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    data: RefreshRequest | None = None,
):
    service = AuthService(db)
    raw = (data.refresh_token if data else None) or get_refresh_from_cookie(request)
    if not raw:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError("Refresh token required")
    tokens = await service.refresh_tokens(raw)
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=204)
async def logout(response: Response):
    clear_auth_cookies(response)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    from app.core.cache import cache_key, cached_async

    key = cache_key("auth_me", str(current_user.id))

    async def _load() -> UserRead:
        return UserRead.model_validate(current_user)

    return await cached_async(key, 60, _load)


@router.put("/me", response_model=UserRead)
async def update_me(
    data: UserSelfUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    from app.core.auth_cache import invalidate_user_cache
    from app.core.cache import clear_cache

    service = AuthService(db)
    user = await service.update_profile(
        user_id=current_user.id,
        full_name=data.full_name,
    )
    invalidate_user_cache(current_user.id)
    clear_cache("auth_me")
    return user


@router.post("/set-password", response_model=UserRead)
async def set_password(
    data: SetPasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = AuthService(db)
    return await service.set_password(
        user_id=current_user.id,
        password=data.password,
        current_password=data.current_password,
    )


@router.put("/users/{user_id}", response_model=UserRead)
async def admin_update_user(
    user_id: uuid.UUID,
    data: UserAdminUpdate,
    current_user: AdminUser,
    db: DbSession,
):
    service = AuthService(db)
    user = await service.admin_update_user(
        user_id=user_id,
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
    )
    await AuditService(db).log("user.updated", "user", resource_id=user_id, user_id=current_user.id)
    return user
