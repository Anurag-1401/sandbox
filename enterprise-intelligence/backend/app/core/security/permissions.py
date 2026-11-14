from fastapi import Depends, HTTPException, status

from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal


def require_roles(*allowed_roles: str):
    def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
    ) -> UserPrincipal:

        if principal.organization_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return principal

    return dependency