import uuid
from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_one(self, statement: Select) -> Optional[ModelType]:
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_many(self, statement: Select) -> list[ModelType]:
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: ModelType, data: dict[str, Any]) -> ModelType:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        # Reload server-side defaults (e.g. updated_at onupdate) before async serialization.
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def count(self, statement: Optional[Select] = None) -> int:
        if statement is None:
            statement = select(func.count()).select_from(self.model)
        result = await self.session.execute(statement)
        return result.scalar() or 0