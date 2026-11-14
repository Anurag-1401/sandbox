
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserPrincipal:
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool = True

    @property
    def organization_role(self) -> str:
        """Compatibility alias for organization-scoped role checks."""
        return self.role
