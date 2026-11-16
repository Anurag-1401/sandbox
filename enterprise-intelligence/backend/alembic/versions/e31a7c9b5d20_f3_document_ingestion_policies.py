
"""F3 document ingestion RLS policies.

Revision ID: e31a7c9b5d20
Revises: d72a9c4e1f60
"""

from alembic import op

revision = "e31a7c9b5d20"
down_revision = "d72a9c4e1f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A document can be inserted only into the authenticated
    # organization and must be owned by its authenticated user,
    # unless the user is an organization owner or admin.
    op.execute("""
        CREATE POLICY documents_insert_policy
        ON documents
        FOR INSERT
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND is_active = true
            AND (
                owner_user_id = NULLIF(
                    current_setting('app.current_user_id', true),
                    ''
                )::uuid
                OR current_setting('app.current_org_role', true)
                    IN ('owner', 'admin','analyst')
            )
        )
    """)

    op.execute("""
        CREATE POLICY documents_update_policy
        ON documents
        FOR UPDATE
        USING (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND (
                owner_user_id = NULLIF(
                    current_setting('app.current_user_id', true),
                    ''
                )::uuid
                OR current_setting('app.current_org_role', true)
                    IN ('owner', 'admin','analyst')
            )
        )
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
        )
    """)

    op.execute("""
        CREATE POLICY document_versions_insert_policy
        ON document_versions
        FOR INSERT
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND EXISTS (
                SELECT 1
                FROM documents d
                WHERE d.id = document_versions.document_id
                  AND d.organization_id =
                      document_versions.organization_id
                  AND d.is_active = true
                  AND (
                      d.owner_user_id = NULLIF(
                          current_setting('app.current_user_id', true),
                          ''
                      )::uuid
                      OR current_setting('app.current_org_role', true)
                          IN ('owner', 'admin','analyst')
                  )
            )
        )
    """)

    op.execute("""
        CREATE POLICY document_versions_update_policy
        ON document_versions
        FOR UPDATE
        USING (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND EXISTS (
                SELECT 1
                FROM documents d
                WHERE d.id = document_versions.document_id
                  AND d.organization_id =
                      document_versions.organization_id
                  AND (
                      d.owner_user_id = NULLIF(
                          current_setting('app.current_user_id', true),
                          ''
                      )::uuid
                      OR current_setting('app.current_org_role', true)
                          IN ('owner', 'admin','analyst')
                  )
            )
        )
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
        )
    """)


    # The backend RBAC matrix grants analysts documents:manage.
    # Keep the database policy consistent with that permission.
    op.execute("""
        DROP POLICY IF EXISTS chunks_insert_policy
        ON document_chunks
    """)

    op.execute("""
        CREATE POLICY chunks_insert_policy
        ON document_chunks
        FOR INSERT
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND EXISTS (
                SELECT 1
                FROM document_versions v
                JOIN documents d
                  ON d.id = v.document_id
                 AND d.organization_id = v.organization_id
                WHERE v.id = document_chunks.version_id
                  AND v.organization_id =
                      document_chunks.organization_id
                  AND (
                      d.owner_user_id = NULLIF(
                          current_setting('app.current_user_id', true),
                          ''
                      )::uuid
                      OR current_setting('app.current_org_role', true)
                          IN ('owner', 'admin', 'analyst')
                  )
            )
        )
    """)



def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS document_versions_update_policy
        ON document_versions
    """)

    op.execute("""
        DROP POLICY IF EXISTS document_versions_insert_policy
        ON document_versions
    """)

    op.execute("""
        DROP POLICY IF EXISTS documents_update_policy
        ON documents
    """)

    op.execute("""
        DROP POLICY IF EXISTS documents_insert_policy
        ON documents
    """)

    op.execute("""
        DROP POLICY IF EXISTS chunks_insert_policy
        ON document_chunks
    """)

    op.execute("""
        CREATE POLICY chunks_insert_policy
        ON document_chunks
        FOR INSERT
        WITH CHECK (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND EXISTS (
                SELECT 1
                FROM document_versions v
                JOIN documents d
                  ON d.id = v.document_id
                 AND d.organization_id = v.organization_id
                WHERE v.id = document_chunks.version_id
                  AND v.organization_id =
                      document_chunks.organization_id
                  AND (
                      d.owner_user_id = NULLIF(
                          current_setting('app.current_user_id', true),
                          ''
                      )::uuid
                      OR current_setting('app.current_org_role', true)
                          IN ('owner', 'admin')
                      OR EXISTS (
                          SELECT 1
                          FROM document_permissions p
                          WHERE p.organization_id = d.organization_id
                            AND p.document_id = d.id
                            AND p.user_id = NULLIF(
                                current_setting('app.current_user_id', true),
                                ''
                            )::uuid
                            AND p.permission IN ('write', 'manage')
                      )
                  )
            )
        )
    """)

