from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=80)
    settings: dict = Field(default_factory=dict)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    industry: str | None
    timezone: str
    settings: dict
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberResponse(BaseModel):
    user_id: UUID
    email: str | None
    display_name: str | None
    role: str
    status: str
    department_id: UUID | None
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberRoleUpdate(BaseModel):
    role: str = Field(
        pattern="^(admin|analyst|reviewer)$"
    )


class MemberDepartmentUpdate(BaseModel):
    department_id: UUID | None


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(
        pattern="^(admin|analyst|reviewer)$"
    )
    department_id: UUID | None = None


class InvitationResponse(BaseModel):
    id: UUID
    email: str
    role: str
    department_id: UUID | None
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitationCreated(BaseModel):
    invitation: InvitationResponse
    token: str


class InvitationAccept(BaseModel):
    token: str = Field(min_length=30, max_length=200)


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)


class ProfileResponse(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    organization_id: UUID
    total_members: int
    active_members: int
    total_documents: int
    total_investigations: int
    investigations_by_status: dict[str, int]
    total_departments: int
    pending_invitations: int


class AuditLogResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)