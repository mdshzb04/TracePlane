import uuid

from fastapi import APIRouter

from app.core.dependencies import AdminUser, CurrentUser, DbSession, DeveloperUser
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationRead,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(user: CurrentUser, db: DbSession):
    return await OrganizationService(db).list_for_user(user.id)


@router.post("", response_model=OrganizationRead, status_code=201)
async def create_organization(user: DeveloperUser, db: DbSession, data: OrganizationCreate):
    return await OrganizationService(db).create_organization(user, data)


@router.get("/{org_id}/members", response_model=list[OrganizationMemberRead])
async def list_members(org_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return await OrganizationService(db).list_members(user.id, org_id)


@router.post("/{org_id}/members", response_model=OrganizationMemberRead, status_code=201)
async def add_member(
    org_id: uuid.UUID,
    user: AdminUser,
    db: DbSession,
    data: OrganizationMemberCreate,
):
    return await OrganizationService(db).add_member(user.id, org_id, data)
