from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def set_current_user_context(db: Session, user_id: UUID) -> None:
    db.execute(
        text(
            "SELECT set_config('app.current_user_id', :user_id, true)"
        ),
        {"user_id": str(user_id)},
    )


def set_current_organization_context(
    db: Session,
    organization_id: UUID,
) -> None:
    db.execute(
        text(
            "SELECT set_config('app.current_org_id', :org_id, true)"
        ),
        {"org_id": str(organization_id)},
    )


def set_security_context(
    db: Session,
    *,
    user_id: UUID,
    organization_id: UUID,
) -> None:
    set_current_user_context(db, user_id)
    set_current_organization_context(db, organization_id)