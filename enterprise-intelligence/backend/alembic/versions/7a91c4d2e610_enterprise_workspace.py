"""M7 enterprise workspace.

Revision ID: 7a91c4d2e610
Revises: 5c1a9e2d7b41
"""

from alembic import op
import sqlalchemy as sa


revision = "7a91c4d2e610"
down_revision = "5c1a9e2d7b41"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organizations",
        sa.Column("industry", sa.String(120), nullable=True),
    )

    op.add_column(
        "organizations",
        sa.Column(
            "timezone",
            sa.String(80),
            nullable=False,
            server_default="Asia/Kolkata",
        ),
    )

    op.add_column(
        "organizations",
        sa.Column(
            "settings",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )

    op.add_column(
        "users",
        sa.Column("display_name", sa.String(200), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_department_org_name",
        ),
    )

    op.create_index(
        "ix_departments_organization_id",
        "departments",
        ["organization_id"],
    )

    op.add_column(
        "organization_memberships",
        sa.Column(
            "department_id",
            sa.Uuid(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_organization_memberships_department_id",
        "organization_memberships",
        ["department_id"],
    )

    op.create_table(
        "organization_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column(
            "department_id",
            sa.Uuid(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "invited_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "email",
            name="uq_org_invitation_email",
        ),
    )

    op.create_index(
        "ix_organization_invitations_organization_id",
        "organization_invitations",
        ["organization_id"],
    )

    op.create_index(
        "ix_org_invitation_token_hash",
        "organization_invitations",
        ["token_hash"],
        unique=True,
    )

    op.create_table(
        "organization_audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_org_audit_org_created",
        "organization_audit_logs",
        ["organization_id", "created_at"],
    )

        # Tenant isolation for M7 tables.
    op.execute("""
        ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
        ALTER TABLE departments FORCE ROW LEVEL SECURITY;

        CREATE POLICY departments_tenant_policy
        ON departments
        USING (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        );

        ALTER TABLE organization_invitations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE organization_invitations FORCE ROW LEVEL SECURITY;

        CREATE POLICY invitations_tenant_policy
        ON organization_invitations
        USING (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        )
        WITH CHECK (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        );

        ALTER TABLE organization_audit_logs ENABLE ROW LEVEL SECURITY;
        ALTER TABLE organization_audit_logs FORCE ROW LEVEL SECURITY;

        CREATE POLICY audit_logs_select_policy
        ON organization_audit_logs
        FOR SELECT
        USING (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        );

        CREATE POLICY audit_logs_insert_policy
        ON organization_audit_logs
        FOR INSERT
        WITH CHECK (
            organization_id =
            NULLIF(current_setting('app.current_org_id', true), '')::uuid
        );

        -- Allow members to see their own membership.
-- Owners and admins can see all memberships in their workspace.
DROP POLICY IF EXISTS membership_select_policy
ON organization_memberships;

CREATE POLICY membership_select_policy
ON organization_memberships
FOR SELECT
USING (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
    AND (
        user_id =
            NULLIF(current_setting('app.current_user_id', true), '')::uuid
        OR current_setting('app.current_org_role', true)
            IN ('owner', 'admin')
    )
);

-- Organization updates are restricted to owner and admin.
CREATE POLICY organization_update_policy
ON organizations
FOR UPDATE
USING (
    id = NULLIF(current_setting('app.current_org_id', true), '')::uuid
    AND current_setting('app.current_org_role', true)
        IN ('owner', 'admin')
)
WITH CHECK (
    id = NULLIF(current_setting('app.current_org_id', true), '')::uuid
);

-- Membership management is restricted to owner and admin.
CREATE POLICY membership_update_policy
ON organization_memberships
FOR UPDATE
USING (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
    AND current_setting('app.current_org_role', true)
        IN ('owner', 'admin')
)
WITH CHECK (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
);

-- Departments: all CRUD operations inside the active organization.
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments FORCE ROW LEVEL SECURITY;

CREATE POLICY departments_tenant_policy
ON departments
FOR ALL
USING (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
)
WITH CHECK (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
);

-- Invitations: organization-scoped access.
ALTER TABLE organization_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_invitations FORCE ROW LEVEL SECURITY;

CREATE POLICY invitations_tenant_policy
ON organization_invitations
FOR ALL
USING (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
)
WITH CHECK (
    organization_id =
        NULLIF(current_setting('app.current_org_id', true), '')::uuid
);

    """)


def downgrade():
    op.drop_index(
        "ix_org_audit_org_created",
        table_name="organization_audit_logs",
    )

    op.execute("""
        DROP POLICY IF EXISTS audit_logs_insert_policy
        ON organization_audit_logs;

        DROP POLICY IF EXISTS audit_logs_select_policy
        ON organization_audit_logs;

        DROP POLICY IF EXISTS invitations_tenant_policy
        ON organization_invitations;

        DROP POLICY IF EXISTS departments_tenant_policy
        ON departments;
    """)

    op.drop_table("organization_audit_logs")

    op.drop_index(
        "ix_org_invitation_token_hash",
        table_name="organization_invitations",
    )
    op.drop_index(
        "ix_organization_invitations_organization_id",
        table_name="organization_invitations",
    )
    op.drop_table("organization_invitations")

    op.drop_index(
        "ix_organization_memberships_department_id",
        table_name="organization_memberships",
    )
    op.drop_column("organization_memberships", "department_id")

    op.drop_index(
        "ix_departments_organization_id",
        table_name="departments",
    )
    op.drop_table("departments")

    op.drop_column("users", "display_name")
    op.drop_column("users", "email_verified")
    op.drop_column("organizations", "settings")
    op.drop_column("organizations", "timezone")
    op.drop_column("organizations", "industry")