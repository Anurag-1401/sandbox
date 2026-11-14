
from alembic import op


revision = "002_search_rls"
down_revision = "8d3f2a1c9b70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector is available.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Enable and force RLS on all tenant-scoped tables.
    op.execute("""
        ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

        ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;
        ALTER TABLE organization_memberships FORCE ROW LEVEL SECURITY;

        ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
        ALTER TABLE documents FORCE ROW LEVEL SECURITY;

        ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE document_versions FORCE ROW LEVEL SECURITY;

        ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
        ALTER TABLE document_chunks FORCE ROW LEVEL SECURITY;

        ALTER TABLE document_permissions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE document_permissions FORCE ROW LEVEL SECURITY;
    """)

    # ---------------------------------------------------------
    # 1. ORGANIZATION SELECT POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY organization_select_policy
        ON organizations
        FOR SELECT
        USING (
            id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            OR EXISTS (
                SELECT 1
                FROM organization_memberships m
                WHERE m.organization_id = organizations.id
                  AND m.user_id = NULLIF(
                      current_setting('app.current_user_id', true),
                      ''
                  )::uuid
                  AND m.status = 'active'
            )
        )
    """)

    # ---------------------------------------------------------
    # 2. ORGANIZATION MEMBERSHIP SELECT POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY membership_select_policy
        ON organization_memberships
        FOR SELECT
        USING (
            user_id = NULLIF(
                current_setting('app.current_user_id', true),
                ''
            )::uuid
            AND status = 'active'
        )
    """)

    # ---------------------------------------------------------
    # 3. DOCUMENT SELECT POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY documents_select_policy
        ON documents
        FOR SELECT
        USING (
            organization_id = NULLIF(
                current_setting('app.current_org_id', true),
                ''
            )::uuid
            AND is_active = true
            AND (
                visibility = 'organization'

                OR owner_user_id = NULLIF(
                    current_setting('app.current_user_id', true),
                    ''
                )::uuid

                OR current_setting('app.current_org_role', true)
                    IN ('owner', 'admin')

                OR EXISTS (
                    SELECT 1
                    FROM document_permissions p
                    WHERE p.organization_id = documents.organization_id
                      AND p.document_id = documents.id
                      AND p.user_id = NULLIF(
                          current_setting('app.current_user_id', true),
                          ''
                      )::uuid
                      AND p.permission IN ('read', 'write', 'manage')
                )
            )
        )
    """)

    # ---------------------------------------------------------
    # 4. DOCUMENT VERSION SELECT POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY versions_select_policy
        ON document_versions
        FOR SELECT
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
            )
        )
    """)

    # ---------------------------------------------------------
    # 5. DOCUMENT CHUNK SELECT POLICY
    #
    # Actual relationship:
    # document_chunks.version_id
    #       -> document_versions.id
    #       -> document_versions.document_id
    #       -> documents.id
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY chunks_select_policy
        ON document_chunks
        FOR SELECT
        USING (
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
            )
        )
    """)

    # ---------------------------------------------------------
    # 6. DOCUMENT PERMISSIONS SELECT POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY permissions_select_policy
        ON document_permissions
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
        )
    """)

    # ---------------------------------------------------------
    # 7. DOCUMENT CHUNK INSERT POLICY
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 8. DOCUMENT CHUNK DELETE POLICY
    # ---------------------------------------------------------
    op.execute("""
        CREATE POLICY chunks_delete_policy
        ON document_chunks
        FOR DELETE
        USING (
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


def downgrade() -> None:
    # Remove policies first.
    op.execute("""
        DROP POLICY IF EXISTS chunks_delete_policy
        ON document_chunks
    """)

    op.execute("""
        DROP POLICY IF EXISTS chunks_insert_policy
        ON document_chunks
    """)

    op.execute("""
        DROP POLICY IF EXISTS permissions_select_policy
        ON document_permissions
    """)

    op.execute("""
        DROP POLICY IF EXISTS chunks_select_policy
        ON document_chunks
    """)

    op.execute("""
        DROP POLICY IF EXISTS versions_select_policy
        ON document_versions
    """)

    op.execute("""
        DROP POLICY IF EXISTS documents_select_policy
        ON documents
    """)

    op.execute("""
        DROP POLICY IF EXISTS membership_select_policy
        ON organization_memberships
    """)

    op.execute("""
        DROP POLICY IF EXISTS organization_select_policy
        ON organizations
    """)

    # Disable RLS.
    op.execute("""
        ALTER TABLE document_permissions DISABLE ROW LEVEL SECURITY;
        ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;
        ALTER TABLE document_versions DISABLE ROW LEVEL SECURITY;
        ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
        ALTER TABLE organization_memberships DISABLE ROW LEVEL SECURITY;
        ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
    """)
