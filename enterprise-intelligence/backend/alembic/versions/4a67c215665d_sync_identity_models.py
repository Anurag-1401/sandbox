
"""sync_identity_models

Revision ID: 4a67c215665d
Revises: 2518674e6b9e
Create Date: 2026-11-08 19:38:48.366486
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4a67c215665d"
down_revision: Union[str, Sequence[str], None] = "2518674e6b9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create application users.
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "external_subject",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_subject"),
    )

    # Create organization memberships.
    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'analyst', 'reviewer')",
            name="ck_organization_membership_role",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_organization_membership_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_membership",
        ),
    )

    op.create_index(
        "ix_organization_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
        unique=False,
    )

    op.create_index(
        "ix_organization_memberships_user_id",
        "organization_memberships",
        ["user_id"],
        unique=False,
    )

    # Add organization status.
    # Existing organizations receive TRUE.
    op.add_column(
        "organizations",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    # Remove only the changes introduced by this revision.
    op.drop_column("organizations", "is_active")

    op.drop_index(
        "ix_organization_memberships_user_id",
        table_name="organization_memberships",
    )

    op.drop_index(
        "ix_organization_memberships_organization_id",
        table_name="organization_memberships",
    )

    op.drop_table("organization_memberships")
    op.drop_table("users")
