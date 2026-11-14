from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal
from app.core.security.rbac import (
    Permission,
    require_permission,
)
from app.models.identity import User, Organization
from app.modules.enterprise.schemas import (
    OrganizationUpdate,
    OrganizationResponse,
    MemberRoleUpdate,
    MemberDepartmentUpdate,
    InvitationCreate,
    InvitationAccept,
    InvitationCreated,
    DepartmentCreate,
    ProfileUpdate,
    DashboardResponse,
    AuditLogResponse,
)
from app.modules.enterprise.service import EnterpriseService

from app.modules.enterprise.workspaces import list_user_workspaces

router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise Workspace"],
)


def translate_error(exc: Exception):
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))

    if isinstance(exc, ValueError):
        raise HTTPException(status_code=409, detail=str(exc))

    raise exc


def get_service() -> EnterpriseService:
    return EnterpriseService()


@router.get("/workspaces")
def get_user_workspaces(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return list_user_workspaces(
        db,
        principal.user_id,
    )
    
@router.get(
    "/workspace",
    response_model=OrganizationResponse,
)
def get_workspace(
    principal: UserPrincipal = Depends(
        require_permission(Permission.WORKSPACE_READ)
    ),
    db: Session = Depends(get_db),
):
    organization = db.get(Organization, principal.organization_id)

    if organization is None or not organization.is_active:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return organization


@router.patch(
    "/workspace",
    response_model=OrganizationResponse,
)
def update_workspace(
    payload: OrganizationUpdate,
    principal: UserPrincipal = Depends(
        require_permission(Permission.WORKSPACE_UPDATE)
    ),
    db: Session = Depends(get_db),
):
    try:
        result = EnterpriseService().update_organization(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            changes=payload.model_dump(exclude_unset=True),
        )
        db.commit()
        db.refresh(result)
        return result
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.get("/members")
def list_members(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_READ)
    ),
    db: Session = Depends(get_db),
):
    return EnterpriseService().list_members(
        db,
        principal.organization_id,
        limit=limit,
        offset=offset,
    )


@router.patch("/members/{target_user_id}/role")
def update_member_role(
    target_user_id: UUID,
    payload: MemberRoleUpdate,
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_UPDATE)
    ),
    db: Session = Depends(get_db),
):
    try:
        service = EnterpriseService()
        result = service.update_member_role(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            actor_role=principal.role,
            target_user_id=target_user_id,
            new_role=payload.role,
        )
        db.commit()
        return {
            "user_id": str(target_user_id),
            "role": result.role,
        }
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.patch("/members/{target_user_id}/status")
def update_member_status(
    target_user_id: UUID,
    active: bool,
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_REMOVE)
    ),
    db: Session = Depends(get_db),
):
    try:
        result = EnterpriseService().set_member_status(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            actor_role=principal.role,
            target_user_id=target_user_id,
            new_status="active" if active else "suspended",
        )
        db.commit()
        return {
            "user_id": str(target_user_id),
            "status": result.status,
        }
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.patch("/members/{target_user_id}/department")
def assign_member_department(
    target_user_id: UUID,
    payload: MemberDepartmentUpdate,
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_UPDATE)
    ),
    db: Session = Depends(get_db),
):
    try:
        result = EnterpriseService().assign_department(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            target_user_id=target_user_id,
            department_id=payload.department_id,
        )
        db.commit()
        return {
            "user_id": str(target_user_id),
            "department_id": (
                str(result.department_id)
                if result.department_id else None
            ),
        }
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.post(
    "/invitations",
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    payload: InvitationCreate,
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_INVITE)
    ),
    db: Session = Depends(get_db),
):
    try:
        invitation, token = EnterpriseService().create_invitation(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            actor_role=principal.role,
            email=str(payload.email),
            role=payload.role,
            department_id=payload.department_id,
        )
        db.commit()
        db.refresh(invitation)

        # The raw token is returned only once.
        return {
            "invitation": {
                "id": str(invitation.id),
                "email": invitation.email,
                "role": invitation.role,
                "department_id": (
                    str(invitation.department_id)
                    if invitation.department_id else None
                ),
                "expires_at": invitation.expires_at,
                "created_at": invitation.created_at,
            },
            "token": token,
        }
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.post("/invitations/accept")
def accept_invitation(
    payload: InvitationAccept,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    try:
        invitation = EnterpriseService().accept_invitation(
            db,
            token=payload.token,
            user_id=principal.user_id,
        )
        db.commit()
        return {
            "accepted": True,
            "organization_id": str(invitation.organization_id),
            "role": invitation.role,
        }
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.delete("/invitations/{invitation_id}")
def revoke_invitation(
    invitation_id: UUID,
    principal: UserPrincipal = Depends(
        require_permission(Permission.MEMBERS_INVITE)
    ),
    db: Session = Depends(get_db),
):
    try:
        invitation = EnterpriseService().revoke_invitation(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            invitation_id=invitation_id,
        )
        db.commit()
        return {"revoked": True, "invitation_id": str(invitation.id)}
    except (LookupError, PermissionError, ValueError) as exc:
        db.rollback()
        translate_error(exc)


@router.get("/departments")
def list_departments(
    principal: UserPrincipal = Depends(
        require_permission(Permission.DEPARTMENTS_READ)
    ),
    db: Session = Depends(get_db),
):
    return EnterpriseService().list_departments(
        db,
        principal.organization_id,
    )


@router.post(
    "/departments",
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    payload: DepartmentCreate,
    principal: UserPrincipal = Depends(
        require_permission(Permission.DEPARTMENTS_MANAGE)
    ),
    db: Session = Depends(get_db),
):
    try:
        department = EnterpriseService().create_department(
            db,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            name=payload.name,
            description=payload.description,
        )
        db.commit()
        db.refresh(department)
        return department
    except Exception:
        db.rollback()
        raise


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def get_dashboard(
    principal: UserPrincipal = Depends(
        require_permission(Permission.WORKSPACE_READ)
    ),
    db: Session = Depends(get_db),
):
    return EnterpriseService().dashboard(
        db,
        principal.organization_id,
    )


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    principal: UserPrincipal = Depends(
        require_permission(Permission.AUDIT_READ)
    ),
    db: Session = Depends(get_db),
):
    return EnterpriseService().list_audit_logs(
        db,
        principal.organization_id,
        limit=limit,
        offset=offset,
    )


@router.get("/profile")
def get_profile(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    user = db.get(User, principal.user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "organization_id": str(principal.organization_id),
        "role": principal.role,
    }


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdate,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    user = db.get(User, principal.user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip() or None

    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }