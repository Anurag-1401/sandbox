from enum import StrEnum

from fastapi import Depends, HTTPException, status

from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal


class Permission(StrEnum):
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"

    MEMBERS_READ = "members:read"
    MEMBERS_INVITE = "members:invite"
    MEMBERS_UPDATE = "members:update"
    MEMBERS_REMOVE = "members:remove"

    DEPARTMENTS_READ = "departments:read"
    DEPARTMENTS_MANAGE = "departments:manage"

    AUDIT_READ = "audit:read"

    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_MANAGE = "documents:manage"

    INVESTIGATIONS_CREATE = "investigations:create"
    INVESTIGATIONS_REVIEW = "investigations:review"


ROLE_PERMISSIONS = {
    "owner": set(Permission),

    "admin": {
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_UPDATE,
        Permission.MEMBERS_READ,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_UPDATE,
        Permission.MEMBERS_REMOVE,
        Permission.DEPARTMENTS_READ,
        Permission.DEPARTMENTS_MANAGE,
        Permission.AUDIT_READ,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_MANAGE,
        Permission.INVESTIGATIONS_CREATE,
        Permission.INVESTIGATIONS_REVIEW,
    },

    "analyst": {
        Permission.WORKSPACE_READ,
        Permission.MEMBERS_READ,
        Permission.DEPARTMENTS_READ,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_MANAGE,
        Permission.INVESTIGATIONS_CREATE,
    },

    "reviewer": {
        Permission.WORKSPACE_READ,
        Permission.MEMBERS_READ,
        Permission.DEPARTMENTS_READ,
        Permission.DOCUMENTS_READ,
        Permission.INVESTIGATIONS_REVIEW,
    },
}


def has_permission(
    principal: UserPrincipal,
    permission: Permission,
) -> bool:
    return permission in ROLE_PERMISSIONS.get(
        principal.role,
        set(),
    )


def require_permission(permission: Permission):
    def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
    ) -> UserPrincipal:

        if not principal.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user.",
            )

        if not has_permission(principal, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return principal

    return dependency