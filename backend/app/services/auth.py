import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token, decode_refresh_token
from app.core.config import settings
from app.core.email_policy import validate_allowed_email_domain
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.core.security_headers import hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserRead, UserRegister
from app.services.api_key_service import ApiKeyService
from app.services.github_oauth import GitHubProfile

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    async def register(self, data: UserRegister) -> UserRead:
        if not settings.ALLOW_REGISTRATION:
            raise BadRequestError("Registration is disabled")

        email = validate_allowed_email_domain(data.email)
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        default_role = "developer" if settings.ENV == "development" else "viewer"
        user = User(
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=default_role,
            provider="email",
        )
        user = await self.user_repo.create(user)
        await self.session.flush()
        await ApiKeyService(self.session).ensure_user_workspace(user)
        logger.info("User registered: %s", user.email)
        return UserRead.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserRead:
        email = validate_allowed_email_domain(data.email)
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError(f"User with email '{email}' already exists")

        user = User(
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            provider="email",
        )
        user = await self.user_repo.create(user)
        await self.session.flush()
        logger.info("User created by admin: %s (role=%s)", user.email, user.role)
        return UserRead.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        normalized_email = validate_allowed_email_domain(email)
        user = await self.user_repo.get_by_email(normalized_email)
        if user is None:
            raise UnauthorizedError("Invalid email or password")
        if user.password_hash is None:
            if user.github_id:
                raise UnauthorizedError(
                    "This account uses GitHub sign-in. Continue with GitHub or set a password in Settings."
                )
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        return await self.issue_tokens(user)

    async def issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id), user.role)
        refresh_token, jti, family_id = create_refresh_token(str(user.id))
        await self._persist_refresh(user.id, refresh_token, jti, family_id)
        logger.info("Session issued for user: %s", user.email)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login_or_link_github(self, profile: GitHubProfile) -> tuple[User, bool]:
        """Return (user, created). Links by github_id or verified email."""
        existing_github = await self.user_repo.get_by_github_id(profile.github_id)
        if existing_github:
            if not existing_github.is_active:
                raise UnauthorizedError("Account is deactivated")
            updates: dict = {}
            if profile.avatar_url and existing_github.avatar_url != profile.avatar_url:
                updates["avatar_url"] = profile.avatar_url
            if profile.full_name and not existing_github.full_name:
                updates["full_name"] = profile.full_name
            if updates:
                existing_github = await self.user_repo.update(existing_github, updates)
            await ApiKeyService(self.session).ensure_user_workspace(existing_github)
            return existing_github, False

        by_email = await self.user_repo.get_by_email(profile.email)
        if by_email:
            if by_email.github_id and by_email.github_id != profile.github_id:
                raise ConflictError("Email is linked to a different GitHub account")
            updates = {
                "github_id": profile.github_id,
                "avatar_url": profile.avatar_url or by_email.avatar_url,
            }
            if profile.full_name and not by_email.full_name:
                updates["full_name"] = profile.full_name
            user = await self.user_repo.update(by_email, updates)
            await ApiKeyService(self.session).ensure_user_workspace(user)
            logger.info("Linked GitHub to existing user: %s", user.email)
            return user, False

        default_role = "developer" if settings.ENV == "development" else "viewer"
        user = User(
            email=profile.email,
            password_hash=None,
            full_name=profile.full_name,
            role=default_role,
            provider="github",
            github_id=profile.github_id,
            avatar_url=profile.avatar_url,
        )
        user = await self.user_repo.create(user)
        await self.session.flush()
        await ApiKeyService(self.session).ensure_user_workspace(user)
        logger.info("GitHub user created: %s", user.email)
        return user, True

    async def set_password(
        self,
        user_id: uuid.UUID,
        password: str,
        current_password: Optional[str] = None,
    ) -> UserRead:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")

        if user.password_hash is not None:
            if not current_password or not verify_password(current_password, user.password_hash):
                raise UnauthorizedError("Current password is incorrect")

        user = await self.user_repo.update(user, {"password_hash": hash_password(password)})
        logger.info("Password set for user: %s", user.email)
        return UserRead.model_validate(user)

    async def _persist_refresh(
        self, user_id: uuid.UUID, token: str, jti: str, family_id: str
    ) -> None:
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        row = RefreshToken(
            user_id=user_id,
            jti=jti,
            family_id=uuid.UUID(family_id),
            token_hash=hash_refresh_token(token),
            expires_at=expires,
        )
        await self.refresh_repo.create(row)
        await self.session.flush()

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        family_id = payload.get("family_id")
        if not user_id_str or not jti or not family_id:
            raise UnauthorizedError("Invalid refresh token payload")

        stored = await self.refresh_repo.get_by_jti(jti)
        if stored is None or stored.revoked:
            if family_id:
                await self.refresh_repo.revoke_family(uuid.UUID(family_id))
            raise UnauthorizedError("Refresh token revoked or reused")

        if stored.token_hash != hash_refresh_token(refresh_token):
            await self.refresh_repo.revoke_family(uuid.UUID(family_id))
            raise UnauthorizedError("Refresh token invalid")

        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError) as exc:
            raise UnauthorizedError("Invalid refresh token payload") from exc

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        await self.refresh_repo.revoke_jti(jti)
        new_access = create_access_token(str(user.id), user.role)
        new_refresh, new_jti, new_family = create_refresh_token(
            str(user.id), family_id=family_id
        )
        await self._persist_refresh(user.id, new_refresh, new_jti, new_family)
        return TokenResponse(access_token=new_access, refresh_token=new_refresh)

    async def update_profile(
        self, user_id: uuid.UUID, full_name: Optional[str]
    ) -> UserRead:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")

        updates: dict = {}
        if full_name is not None:
            updates["full_name"] = full_name

        if updates:
            user = await self.user_repo.update(user, updates)
            logger.info("User profile updated: %s", user.email)
        return UserRead.model_validate(user)

    async def admin_update_user(
        self,
        user_id: uuid.UUID,
        full_name: Optional[str],
        role: Optional[str],
        is_active: Optional[bool],
    ) -> UserRead:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")

        updates: dict = {}
        if full_name is not None:
            updates["full_name"] = full_name
        if role is not None:
            updates["role"] = role
        if is_active is not None:
            updates["is_active"] = is_active

        if updates:
            user = await self.user_repo.update(user, updates)
            logger.info("User updated by admin: %s", user.email)
        return UserRead.model_validate(user)
