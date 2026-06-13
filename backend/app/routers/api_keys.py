import uuid

from fastapi import APIRouter

from app.core.dependencies import DbSession, DeveloperUser
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyRead
from app.services.api_key_service import ApiKeyService
from app.services.audit import AuditService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys(
    current_user: DeveloperUser,
    db: DbSession,
):
    service = ApiKeyService(db)
    return await service.list_keys(current_user)


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: DeveloperUser,
    db: DbSession,
):
    service = ApiKeyService(db)
    result = await service.create_key(current_user, data)
    await AuditService(db).log(
        "api_key.created", "api_key", resource_id=result.id, user_id=current_user.id
    )
    return result


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: DeveloperUser,
    db: DbSession,
):
    service = ApiKeyService(db)
    await service.revoke_key(current_user, key_id)
    await AuditService(db).log(
        "api_key.revoked", "api_key", resource_id=key_id, user_id=current_user.id
    )


@router.post("/{key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    key_id: uuid.UUID,
    current_user: DeveloperUser,
    db: DbSession,
):
    service = ApiKeyService(db)
    result = await service.rotate_key(current_user, key_id)
    await AuditService(db).log(
        "api_key.rotated", "api_key", resource_id=key_id, user_id=current_user.id
    )
    return result
