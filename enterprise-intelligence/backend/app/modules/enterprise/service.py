from __future__ import annotations

import hashlib
import secrets
import uuid

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.identity import (
    User,
    Organization,
    OrganizationMembership,
    Department,
)
from app.models.document import Document
from app.modules.investigations.models import Investigation
from app.models.enterprise import (
    OrganizationInvitation,
    OrganizationAuditLog,
)


VALID_ROLES = {"owner", "admin", "analyst", "reviewer"}


class EnterpriseService:

    @staticmethod
    def audit(
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
    ):
        db.add(
            OrganizationAuditLog(
                organization_id=organization_id,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
            )
        )

    def get_organization(
        self,
        db: Session,
        organization_id: uuid.UUID,
    ):
        return db.execute(
            select(Organization).where(
                Organization.id == organization_id,
                Organization.is_active.is_(True),
            )
        ).scalar_one_or_none()

    def update_organization(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        changes: dict,
    ):
        organization = self.get_organization(db, organization_id)

        if organization is None:
            raise LookupError("Organization not found.")

        for field in ("name", "industry", "timezone"):
            if field in changes and changes[field] is not None:
                setattr(organization, field, changes[field])

        if "settings" in changes:
            # Only explicitly supported settings should be mutable.
            allowed = {
                "default_jurisdiction",
                "default_industry",
                "notification_preferences",
                "report_preferences",
            }
            unknown = set(changes["settings"]) - allowed
            if unknown:
                raise ValueError(
                    f"Unsupported settings: {sorted(unknown)}"
                )

            organization.settings = {
                **(organization.settings or {}),
                **changes["settings"],
            }

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="organization.updated",
            resource_type="organization",
            resource_id=str(organization_id),
            details={"updated_fields": list(changes)},
        )

        db.flush()
        return organization

    def list_members(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ):
        statement = (
            select(
                OrganizationMembership,
                User,
            )
            .join(User, User.id == OrganizationMembership.user_id)
            .where(
                OrganizationMembership.organization_id
                == organization_id
            )
            .order_by(User.email.asc())
            .limit(limit)
            .offset(offset)
        )

        rows = db.execute(statement).all()

        return [
            {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": membership.role,
                "status": membership.status,
                "department_id": membership.department_id,
                "joined_at": membership.created_at,
            }
            for membership, user in rows
        ]

    def _membership(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        lock: bool = False,
    ):
        statement = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        )

        if lock:
            statement = statement.with_for_update()

        return db.execute(statement).scalar_one_or_none()

    def update_member_role(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        target_user_id: uuid.UUID,
        new_role: str,
    ):
        if new_role not in {"admin", "analyst", "reviewer"}:
            raise ValueError("Invalid role.")

        target = self._membership(
            db,
            organization_id,
            target_user_id,
            lock=True,
        )

        if target is None:
            raise LookupError("Member not found.")

        if target.role == "owner":
            raise ValueError("Owner role cannot be changed here.")

        if new_role == "admin" and actor_role != "owner":
            raise PermissionError(
                "Only the owner can grant the admin role."
            )

        if target_user_id == actor_id and target.role == "admin":
            raise ValueError("You cannot change your own admin role.")

        previous_role = target.role
        target.role = new_role

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="member.role_updated",
            resource_type="membership",
            resource_id=str(target.id),
            details={
                "target_user_id": str(target_user_id),
                "previous_role": previous_role,
                "new_role": new_role,
            },
        )

        db.flush()
        return target

    def set_member_status(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        target_user_id: uuid.UUID,
        new_status: str,
    ):
        if new_status not in {"active", "suspended"}:
            raise ValueError("Invalid membership status.")

        if target_user_id == actor_id and new_status == "suspended":
            raise ValueError("You cannot suspend your own membership.")

        target = self._membership(
            db,
            organization_id,
            target_user_id,
            lock=True,
        )

        if target is None:
            raise LookupError("Member not found.")

        if target.role == "owner":
            raise ValueError("Owner membership cannot be suspended here.")

        if target.role == "admin" and actor_role != "owner":
            raise PermissionError(
                "Only the owner can suspend an admin."
            )

        previous_status = target.status
        target.status = new_status

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action=f"member.{new_status}",
            resource_type="membership",
            resource_id=str(target.id),
            details={
                "target_user_id": str(target_user_id),
                "previous_status": previous_status,
            },
        )

        db.flush()
        return target

    def create_department(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        name: str,
        description: str | None,
    ):
        department = Department(
            organization_id=organization_id,
            name=name.strip(),
            description=description,
        )

        db.add(department)
        db.flush()

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="department.created",
            resource_type="department",
            resource_id=str(department.id),
            details={"name": department.name},
        )

        return department

    def list_departments(
        self,
        db: Session,
        organization_id: uuid.UUID,
    ):
        return list(
            db.execute(
                select(Department)
                .where(
                    Department.organization_id == organization_id,
                    Department.is_active.is_(True),
                )
                .order_by(Department.name.asc())
            ).scalars().all()
        )

    def assign_department(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        target_user_id: uuid.UUID,
        department_id: uuid.UUID | None,
    ):
        membership = self._membership(
            db,
            organization_id,
            target_user_id,
            lock=True,
        )

        if membership is None:
            raise LookupError("Member not found.")

        if department_id is not None:
            department = db.execute(
                select(Department).where(
                    Department.id == department_id,
                    Department.organization_id == organization_id,
                    Department.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if department is None:
                raise LookupError("Department not found.")

        previous = membership.department_id
        membership.department_id = department_id

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="member.department_updated",
            resource_type="membership",
            resource_id=str(membership.id),
            details={
                "target_user_id": str(target_user_id),
                "previous_department_id": (
                    str(previous) if previous else None
                ),
                "department_id": (
                    str(department_id) if department_id else None
                ),
            },
        )

        db.flush()
        return membership

    def create_invitation(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        email: str,
        role: str,
        department_id: uuid.UUID | None,
    ):
        email = email.strip().lower()

        if role not in {"admin", "analyst", "reviewer"}:
            raise ValueError("Invalid invitation role.")

        if role == "admin" and actor_role != "owner":
            raise PermissionError(
                "Only the owner can invite administrators."
            )

        if department_id is not None:
            department = db.execute(
                select(Department).where(
                    Department.id == department_id,
                    Department.organization_id == organization_id,
                    Department.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if department is None:
                raise LookupError("Department not found.")

        existing_user = db.execute(
            select(User).where(func.lower(User.email) == email)
        ).scalar_one_or_none()

        if existing_user:
            existing_membership = self._membership(
                db,
                organization_id,
                existing_user.id,
            )
            if existing_membership and existing_membership.status != "suspended":
                raise ValueError(
                    "This user already has an organization membership."
                )

        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)

        invitation = db.execute(
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.organization_id == organization_id,
                func.lower(OrganizationInvitation.email) == email,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if invitation:
            if (
                invitation.accepted_at is None
                and invitation.revoked_at is None
                and invitation.expires_at > now
            ):
                raise ValueError("An active invitation already exists.")

            invitation.role = role
            invitation.department_id = department_id
            invitation.token_hash = token_hash
            invitation.invited_by = actor_id
            invitation.expires_at = expires_at
            invitation.accepted_at = None
            invitation.revoked_at = None
        else:
            invitation = OrganizationInvitation(
                organization_id=organization_id,
                email=email,
                role=role,
                department_id=department_id,
                token_hash=token_hash,
                invited_by=actor_id,
                expires_at=expires_at,
            )
            db.add(invitation)

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="member.invited",
            resource_type="invitation",
            resource_id=str(invitation.id),
            details={"email": email, "role": role},
        )

        db.flush()

        # The raw token is returned once. Persist only its hash.
        return invitation, raw_token

    def accept_invitation(
        self,
        db: Session,
        *,
        token: str,
        user_id: uuid.UUID,
    ):
        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        invitation = db.execute(
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.token_hash == token_hash
            )
            .with_for_update()
        ).scalar_one_or_none()

        if invitation is None:
            raise LookupError("Invitation not found.")

        now = datetime.now(timezone.utc)

        if invitation.accepted_at is not None:
            raise ValueError("Invitation has already been accepted.")

        if invitation.revoked_at is not None:
            raise ValueError("Invitation has been revoked.")

        if invitation.expires_at <= now:
            raise ValueError("Invitation has expired.")

        user = db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if user is None or not user.email:
            raise PermissionError(
                "A verified account email is required."
            )

        if user.email.strip().lower() != invitation.email.lower():
            raise PermissionError(
                "The invitation email does not match your account."
            )

        if (
            user is None
            or not user.email
            or not user.email_verified
        ):
            raise PermissionError(
                "A verified account email is required to accept invitations."
            )

        existing = self._membership(
            db,
            invitation.organization_id,
            user_id,
            lock=True,
        )

        if existing and existing.status != "suspended":
            raise ValueError("Membership already exists.")

        if existing:
            existing.role = invitation.role
            existing.status = "active"
            existing.department_id = invitation.department_id
        else:
            db.add(
                OrganizationMembership(
                    organization_id=invitation.organization_id,
                    user_id=user_id,
                    role=invitation.role,
                    status="active",
                    department_id=invitation.department_id,
                )
            )

        invitation.accepted_at = now

        self.audit(
            db,
            organization_id=invitation.organization_id,
            actor_id=user_id,
            action="invitation.accepted",
            resource_type="invitation",
            resource_id=str(invitation.id),
            details={"email": invitation.email},
        )

        db.flush()
        return invitation

    def revoke_invitation(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        invitation_id: uuid.UUID,
    ):
        invitation = db.execute(
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.id == invitation_id,
                OrganizationInvitation.organization_id == organization_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if invitation is None:
            raise LookupError("Invitation not found.")

        if invitation.accepted_at is not None:
            raise ValueError("Accepted invitations cannot be revoked.")

        if invitation.revoked_at is None:
            invitation.revoked_at = datetime.now(timezone.utc)

        self.audit(
            db,
            organization_id=organization_id,
            actor_id=actor_id,
            action="invitation.revoked",
            resource_type="invitation",
            resource_id=str(invitation.id),
        )

        db.flush()
        return invitation

    def dashboard(
        self,
        db: Session,
        organization_id: uuid.UUID,
    ) -> dict:
        total_members = db.scalar(
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id
            )
        ) or 0

        active_members = db.scalar(
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.status == "active",
            )
        ) or 0

        total_documents = db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.organization_id == organization_id)
        ) or 0

        total_investigations = db.scalar(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.organization_id == organization_id)
        ) or 0

        statuses = db.execute(
            select(
                Investigation.status,
                func.count(),
            )
            .where(
                Investigation.organization_id == organization_id
            )
            .group_by(Investigation.status)
        ).all()

        departments = db.scalar(
            select(func.count())
            .select_from(Department)
            .where(
                Department.organization_id == organization_id,
                Department.is_active.is_(True),
            )
        ) or 0

        pending_invitations = db.scalar(
            select(func.count())
            .select_from(OrganizationInvitation)
            .where(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.accepted_at.is_(None),
                OrganizationInvitation.revoked_at.is_(None),
                OrganizationInvitation.expires_at > datetime.now(timezone.utc),
            )
        ) or 0

        return {
            "organization_id": organization_id,
            "total_members": total_members,
            "active_members": active_members,
            "total_documents": total_documents,
            "total_investigations": total_investigations,
            "investigations_by_status": {
                status: count for status, count in statuses
            },
            "total_departments": departments,
            "pending_invitations": pending_invitations,
        }

    def list_audit_logs(
        self,
        db: Session,
        organization_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ):
        return list(
            db.execute(
                select(OrganizationAuditLog)
                .where(
                    OrganizationAuditLog.organization_id
                    == organization_id
                )
                .order_by(
                    OrganizationAuditLog.created_at.desc()
                )
                .limit(limit)
                .offset(offset)
            ).scalars().all()
        )