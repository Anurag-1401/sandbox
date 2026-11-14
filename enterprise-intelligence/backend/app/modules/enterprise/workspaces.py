from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import (
    Organization,
    OrganizationMembership,
)


def list_user_workspaces(
    db: Session,
    user_id,
) -> list[dict]:

    rows = db.execute(
        select(
            Organization,
            OrganizationMembership.role,
        )
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == "active",
            Organization.is_active.is_(True),
        )
        .order_by(Organization.name.asc())
    ).all()

    return [
        {
            "organization_id": str(organization.id),
            "name": organization.name,
            "industry": organization.industry,
            "role": role,
        }
        for organization, role in rows
    ]