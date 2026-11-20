"""support self service organization onboarding

Revision ID: 4f3f878b8e79
Revises: e31a7c9b5d20
Create Date: 2026-11-19 19:27:00.850619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f3f878b8e79'
down_revision: Union[str, Sequence[str], None] = 'e31a7c9b5d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Users must be able to list their own active memberships
    # before an organization has been selected.
    op.execute("""
        DROP POLICY IF EXISTS membership_select_policy
        ON organization_memberships;

        CREATE POLICY membership_select_policy
        ON organization_memberships
        FOR SELECT
        USING (
            (
                user_id = NULLIF(
                    current_setting('app.current_user_id', true),
                    ''
                )::uuid
                AND status = 'active'
            )
            OR
            (
                organization_id = NULLIF(
                    current_setting('app.current_org_id', true),
                    ''
                )::uuid
                AND current_setting('app.current_org_role', true)
                    IN ('owner', 'admin')
            )
        );
    """)

    # Only authenticated application requests that explicitly enable
    # organization creation may insert an organization.
    op.execute("""
        CREATE POLICY organization_self_service_insert
        ON organizations
        FOR INSERT
        WITH CHECK (
            NULLIF(
                current_setting('app.current_user_id', true),
                ''
            ) IS NOT NULL
            AND current_setting(
                'app.allow_org_create',
                true
            ) = 'true'
        );
    """)

    # A user can create their own initial owner membership only through
    # the authenticated organization-creation workflow.
    op.execute("""
        CREATE POLICY membership_self_service_insert
        ON organization_memberships
        FOR INSERT
        WITH CHECK (
            user_id = NULLIF(
                current_setting('app.current_user_id', true),
                ''
            )::uuid
            AND status = 'active'
            AND (
                (
                    role = 'owner'
                    AND current_setting(
                        'app.allow_org_create',
                        true
                    ) = 'true'
                )
                OR
                (
                    current_setting(
                        'app.allow_invitation_accept',
                        true
                    ) = 'true'
                )
            )
        );
    """)


def downgrade() -> None:

    op.execute("""
        DROP POLICY IF EXISTS membership_self_service_insert
        ON organization_memberships;

        DROP POLICY IF EXISTS organization_self_service_insert
        ON organizations;
    """)

    # Restore the previous organization-scoped membership policy.
    op.execute("""
        DROP POLICY IF EXISTS membership_select_policy
        ON organization_memberships;

        CREATE POLICY membership_select_policy
        ON organization_memberships
        FOR SELECT
        USING (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND (
                user_id = NULLIF(
                    current_setting('app.current_user_id', true),
                    ''
                )::uuid
                OR current_setting('app.current_org_role', true)
                    IN ('owner', 'admin')
            )
        );
    """)
