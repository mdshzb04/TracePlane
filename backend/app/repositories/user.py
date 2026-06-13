import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == normalized)
        )
        return result.scalars().first()

    async def get_by_id(self, id: uuid.UUID) -> Optional[User]:
        return await super().get_by_id(id)

    async def get_by_github_id(self, github_id: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.github_id == github_id)
        )
        return result.scalars().first()