import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationRead,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "org"


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(self, user: User, data: OrganizationCreate) -> OrganizationRead:
        slug_base = _slugify(data.name)
        slug = slug_base
        counter = 1
        while await self._slug_exists(slug):
            slug = f"{slug_base}-{counter}"
            counter += 1

        org = Organization(name=data.name, slug=slug)
        self.session.add(org)
        await self.session.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="admin",
        )
        self.session.add(member)

        if user.workspace_id:
            ws = await self.session.get(Workspace, user.workspace_id)
            if ws:
                ws.organization_id = org.id
        await self.session.flush()
        return OrganizationRead.model_validate(org)

    async def list_for_user(self, user_id: uuid.UUID) -> list[OrganizationRead]:
        stmt = (
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return [OrganizationRead.model_validate(o) for o in result.scalars().all()]

    async def list_members(self, user_id: uuid.UUID, org_id: uuid.UUID) -> list[OrganizationMemberRead]:
        await self._require_member(user_id, org_id)
        stmt = (
            select(OrganizationMember, User.email, User.full_name)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == org_id)
        )
        result = await self.session.execute(stmt)
        members = []
        for row in result:
            member, email, full_name = row
            data = OrganizationMemberRead.model_validate(member)
            members.append(
                OrganizationMemberRead(
                    **data.model_dump(),
                    email=email,
                    full_name=full_name,
                )
            )
        return members

    async def add_member(
        self, actor_id: uuid.UUID, org_id: uuid.UUID, data: OrganizationMemberCreate
    ) -> OrganizationMemberRead:
        actor = await self._require_admin(actor_id, org_id)
        user = await self.session.get(User, data.user_id)
        if user is None:
            raise NotFoundError("User", str(data.user_id))

        member = OrganizationMember(
            organization_id=org_id,
            user_id=data.user_id,
            role=data.role,
        )
        self.session.add(member)
        await self.session.flush()
        return OrganizationMemberRead.model_validate(member)

    async def _slug_exists(self, slug: str) -> bool:
        result = await self.session.execute(
            select(Organization.id).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none() is not None

    async def _require_member(self, user_id: uuid.UUID, org_id: uuid.UUID) -> OrganizationMember:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError("Organization", str(org_id))
        return member

    async def _require_admin(self, user_id: uuid.UUID, org_id: uuid.UUID) -> OrganizationMember:
        member = await self._require_member(user_id, org_id)
        if member.role != "admin":
            raise NotFoundError("Organization", "admin required")
        return member
