import enum


class Role(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[Role, set[Role]] = {
    Role.ADMIN: {Role.ADMIN, Role.DEVELOPER, Role.VIEWER},
    Role.DEVELOPER: {Role.DEVELOPER, Role.VIEWER},
    Role.VIEWER: {Role.VIEWER},
}


def has_permission(user_role: str, required_role: Role) -> bool:
    try:
        role = Role(user_role)
    except ValueError:
        return False
    return required_role in ROLE_HIERARCHY.get(role, set())


def require_role(required_role: Role):
    from functools import wraps

    from fastapi import Depends

    from app.core.dependencies import CurrentUser
    from app.core.exceptions import ForbiddenError

    async def _check_role(current_user: CurrentUser):
        if not has_permission(current_user.role, required_role):
            raise ForbiddenError(
                f"Role '{required_role.value}' required, but user has '{current_user.role}'"
            )
        return current_user

    return Depends(_check_role)