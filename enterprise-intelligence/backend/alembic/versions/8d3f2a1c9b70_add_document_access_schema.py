"""Add document ownership, visibility and permissions.

Revision ID: 8d3f2a1c9b70
Revises: 4a67c215665d
"""

from alembic import op
import sqlalchemy as sa

revision = "8d3f2a1c9b70"
down_revision = "4a67c215665d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add document-level access control fields.
    op.add_column(
        "documents",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "visibility",
            sa.String(30),
            nullable=False,
            server_default="organization",
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "owner_user_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_documents_owner_user",
        "documents",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_check_constraint(
        "ck_documents_visibility",
        "documents",
        "visibility IN ('organization', 'private')",
    )

    # Create document-level permissions.
    op.create_table(
        "document_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission", sa.String(30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "organization_id"],
            ["documents.id", "documents.organization_id"],
            ondelete="CASCADE",
            name="fk_document_permissions_document_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_document_permissions_user",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
            name="fk_document_permissions_organization",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "document_id",
            "user_id",
            name="uq_document_permission_user",
        ),
        sa.CheckConstraint(
            "permission IN ('read', 'write', 'manage')",
            name="ck_document_permission_type",
        ),
    )

    op.create_index(
        "ix_document_permissions_organization_id",
        "document_permissions",
        ["organization_id"],
    )

    op.create_index(
        "ix_document_permissions_document_id",
        "document_permissions",
        ["document_id"],
    )

    op.create_index(
        "ix_document_permissions_user_id",
        "document_permissions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_permissions_user_id",
        table_name="document_permissions",
    )
    op.drop_index(
        "ix_document_permissions_document_id",
        table_name="document_permissions",
    )
    op.drop_index(
        "ix_document_permissions_organization_id",
        table_name="document_permissions",
    )

    op.drop_table("document_permissions")

    op.drop_constraint(
        "ck_documents_visibility",
        "documents",
        type_="check",
    )

    op.drop_constraint(
        "fk_documents_owner_user",
        "documents",
        type_="foreignkey",
    )

    op.drop_column("documents", "owner_user_id")
    op.drop_column("documents", "visibility")
    op.drop_column("documents", "is_active")