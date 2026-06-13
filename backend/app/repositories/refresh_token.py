import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return await self.get_one(stmt)

    async def revoke_family(self, family_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(revoked=True)
        )

    async def revoke_jti(self, jti: str) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True)
        )

    async def purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(RefreshToken.expires_at < now)
        rows = await self.get_many(stmt)
        for row in rows:
            await self.session.delete(row)
