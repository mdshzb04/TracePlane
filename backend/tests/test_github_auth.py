import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.models.user import User
from app.services.auth import AuthService
from app.services.github_oauth import GitHubProfile, build_github_authorize_url


@pytest.fixture
def github_profile():
    return GitHubProfile(
        github_id="12345",
        email="dev@gmail.com",
        full_name="Dev User",
        avatar_url="https://avatars.githubusercontent.com/u/1",
        login="devuser",
    )


def _service_with_mocks():
    session = AsyncMock()
    session.flush = AsyncMock()
    return AuthService(session), session


@pytest.mark.asyncio
async def test_login_or_link_github_creates_user(github_profile):
    service, session = _service_with_mocks()
    workspace_id = uuid.uuid4()
    created = User(
        id=uuid.uuid4(),
        email=github_profile.email,
        password_hash=None,
        role="developer",
        provider="github",
        github_id=github_profile.github_id,
        avatar_url=github_profile.avatar_url,
        workspace_id=workspace_id,
    )
    service.user_repo.get_by_github_id = AsyncMock(return_value=None)
    service.user_repo.get_by_email = AsyncMock(return_value=None)
    service.user_repo.create = AsyncMock(return_value=created)

    with patch(
        "app.services.auth.ApiKeyService.ensure_user_workspace",
        new_callable=AsyncMock,
        return_value=workspace_id,
    ):
        user, is_new = await service.login_or_link_github(github_profile)

    assert is_new is True
    assert user.provider == "github"
    assert user.github_id == "12345"
    service.user_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_or_link_github_links_existing_email(github_profile):
    service, _ = _service_with_mocks()
    existing = User(
        id=uuid.uuid4(),
        email=github_profile.email,
        password_hash="hashed",
        role="developer",
        provider="email",
    )
    linked = User(
        id=existing.id,
        email=existing.email,
        password_hash=existing.password_hash,
        role="developer",
        provider="email",
        github_id=github_profile.github_id,
    )
    service.user_repo.get_by_github_id = AsyncMock(return_value=None)
    service.user_repo.get_by_email = AsyncMock(return_value=existing)
    service.user_repo.update = AsyncMock(return_value=linked)

    with patch(
        "app.services.auth.ApiKeyService.ensure_user_workspace",
        new_callable=AsyncMock,
        return_value=uuid.uuid4(),
    ):
        user, is_new = await service.login_or_link_github(github_profile)

    assert is_new is False
    assert user.github_id == "12345"
    service.user_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_rejects_oauth_only_without_password():
    service, _ = _service_with_mocks()
    user = User(
        id=uuid.uuid4(),
        email="dev@gmail.com",
        password_hash=None,
        role="developer",
        provider="github",
        github_id="99",
    )
    service.user_repo.get_by_email = AsyncMock(return_value=user)

    with pytest.raises(UnauthorizedError, match="GitHub"):
        await service.login("dev@gmail.com", "password123")


@pytest.mark.asyncio
async def test_set_password_for_github_user():
    service, _ = _service_with_mocks()
    user = User(
        id=uuid.uuid4(),
        email="dev@gmail.com",
        password_hash=None,
        role="developer",
        provider="github",
        github_id="99",
    )
    now = datetime.now(timezone.utc)
    updated = User(
        id=user.id,
        email=user.email,
        password_hash="newhash",
        role="developer",
        provider="github",
        github_id="99",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    service.user_repo.get_by_id = AsyncMock(return_value=user)
    service.user_repo.update = AsyncMock(return_value=updated)

    result = await service.set_password(user.id, "newpassword123")
    assert result.has_password is True


def test_github_authorize_requires_config(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GITHUB_OAUTH_ENABLED", False)
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "")
    with pytest.raises(BadRequestError):
        build_github_authorize_url("state123")


@pytest.mark.asyncio
async def test_github_route_disabled(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GITHUB_OAUTH_ENABLED", False)
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "")
    response = await client.get("/api/v1/auth/github", follow_redirects=False)
    assert response.status_code == 400
