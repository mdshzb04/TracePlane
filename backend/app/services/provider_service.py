import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_secret_with_migration, encrypt_secret
from app.models.provider_connection import ProviderConnection
from app.schemas.provider import (
    ProviderCatalogItem,
    ProviderConnectionRead,
    ProviderTestResult,
    SUPPORTED_PROVIDERS,
    UI_PROVIDER_IDS,
)
from app.schemas.quickstart import QuickstartTestResponse
from app.services.quickstart_service import QuickstartService
from app.services.provider_validation import validate_provider_key


class ProviderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _load_connection(
        self, workspace_id: uuid.UUID, provider_id: str
    ) -> ProviderConnection | None:
        result = await self.session.execute(
            select(ProviderConnection).where(
                ProviderConnection.workspace_id == workspace_id,
                ProviderConnection.provider_id == provider_id,
            )
        )
        return result.scalar_one_or_none()

    async def _provider_api_key(self, row: ProviderConnection) -> str:
        """Decrypt stored provider key and migrate ciphertext to the primary encryption key."""
        await self.session.refresh(row, attribute_names=["api_key_encrypted"])
        plaintext, needs_reencrypt = decrypt_secret_with_migration(row.api_key_encrypted)
        if needs_reencrypt:
            row.api_key_encrypted = encrypt_secret(plaintext)
            await self.session.flush()
        return plaintext

    async def list_catalog(self, workspace_id: uuid.UUID) -> list[ProviderCatalogItem]:
        result = await self.session.execute(
            select(ProviderConnection).where(ProviderConnection.workspace_id == workspace_id)
        )
        connected = {row.provider_id: row for row in result.scalars().all()}
        catalog: list[ProviderCatalogItem] = []
        for provider_id in UI_PROVIDER_IDS:
            meta = SUPPORTED_PROVIDERS[provider_id]
            row = connected.get(provider_id)
            catalog.append(
                ProviderCatalogItem(
                    provider_id=provider_id,
                    name=meta["name"],
                    description=meta["description"],
                    connected=row is not None,
                    status=row.status if row else None,
                    key_hint=row.key_hint if row else None,
                    last_validated_at=row.last_validated_at.isoformat() if row and row.last_validated_at else None,
                    last_error=row.last_error if row else None,
                )
            )
        return catalog

    async def connect(
        self, workspace_id: uuid.UUID, provider_id: str, api_key: str
    ) -> ProviderConnectionRead:
        if provider_id not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_id}")

        status, message, _ = await validate_provider_key(provider_id, api_key)
        now = datetime.now(timezone.utc)

        result = await self.session.execute(
            select(ProviderConnection).where(
                ProviderConnection.workspace_id == workspace_id,
                ProviderConnection.provider_id == provider_id,
            )
        )
        row = result.scalar_one_or_none()
        hint = api_key[-4:] if len(api_key) >= 4 else "****"

        if row:
            row.api_key_encrypted = encrypt_secret(api_key)
            row.key_hint = f"…{hint}"
            row.status = status
            row.last_validated_at = now if status == "connected" else row.last_validated_at
            row.last_error = None if status == "connected" else message
        else:
            row = ProviderConnection(
                workspace_id=workspace_id,
                provider_id=provider_id,
                api_key_encrypted=encrypt_secret(api_key),
                key_hint=f"…{hint}",
                status=status,
                last_validated_at=now if status == "connected" else None,
                last_error=None if status == "connected" else message,
            )
            self.session.add(row)

        await self.session.flush()
        meta = SUPPORTED_PROVIDERS[provider_id]
        return ProviderConnectionRead(
            provider_id=provider_id,
            name=meta["name"],
            status=row.status,
            key_hint=row.key_hint,
            last_validated_at=row.last_validated_at.isoformat() if row.last_validated_at else None,
            last_error=row.last_error,
        )

    async def disconnect(self, workspace_id: uuid.UUID, provider_id: str) -> None:
        row = await self._load_connection(workspace_id, provider_id)
        if row:
            await self.session.delete(row)

    async def test(self, workspace_id: uuid.UUID, provider_id: str) -> ProviderTestResult:
        row = await self._load_connection(workspace_id, provider_id)
        if not row:
            return ProviderTestResult(
                provider_id=provider_id, status="error", message="Provider not connected"
            )

        try:
            api_key = await self._provider_api_key(row)
        except ValueError as exc:
            row.status = "error"
            row.last_error = str(exc)
            await self.session.flush()
            return ProviderTestResult(provider_id=provider_id, status="error", message=str(exc))
        status, message, latency_ms = await validate_provider_key(provider_id, api_key)
        now = datetime.now(timezone.utc)
        row.status = status
        row.last_validated_at = now if status == "connected" else row.last_validated_at
        row.last_error = None if status == "connected" else message
        await self.session.flush()

        return ProviderTestResult(
            provider_id=provider_id,
            status=status,  # type: ignore[arg-type]
            message=message,
            latency_ms=latency_ms,
        )

    async def send_test_trace(
        self,
        workspace_id: uuid.UUID,
        provider_id: str,
        *,
        traceplane_api_key: str | None,
        model: str | None,
        prompt: str,
        agent_name: str,
    ) -> QuickstartTestResponse:
        if provider_id not in UI_PROVIDER_IDS:
            raise ValueError(f"Unsupported provider: {provider_id}")

        row = await self._load_connection(workspace_id, provider_id)
        if not row or row.status != "connected":
            raise ValueError("Connect this provider before sending a test request")

        try:
            api_key = await self._provider_api_key(row)
        except ValueError as exc:
            row.status = "error"
            row.last_error = str(exc)
            await self.session.flush()
            raise
        return await QuickstartService(self.session).send_test_request(
            workspace_id=workspace_id,
            provider_id=provider_id,
            provider_api_key=api_key,
            traceplane_api_key=traceplane_api_key,
            model=model,
            prompt=prompt,
            agent_name=agent_name,
        )
