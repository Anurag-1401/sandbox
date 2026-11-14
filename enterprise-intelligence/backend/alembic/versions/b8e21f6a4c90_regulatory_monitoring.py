"""M8 regulatory monitoring.

Revision ID: b8e21f6a4c90
Revises: 5c1a9e2d7b41
"""

from alembic import op
import sqlalchemy as sa


revision = "b8e21f6a4c90"
down_revision = "7a91c4d2e610"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "regulatory_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("authority", sa.String(255), nullable=False),
        sa.Column(
            "jurisdiction",
            sa.String(120),
            nullable=False,
            server_default="India",
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("listing_url", sa.String(2000), nullable=False),
        sa.Column("allowed_hosts", sa.JSON(), nullable=False),
        sa.Column("selectors", sa.JSON(), nullable=False),
        sa.Column(
            "scan_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "last_scanned_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "code",
            name="uq_regulatory_source_code",
        ),
        sa.CheckConstraint(
            "source_type IN ('rss', 'atom', 'html')",
            name="ck_regulatory_source_type",
        ),
    )

    op.create_index(
        "ix_regulatory_sources_enabled",
        "regulatory_sources",
        ["enabled", "last_scanned_at"],
    )

    op.create_table(
        "regulatory_publications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("regulatory_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("canonical_url", sa.String(2000), nullable=False),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=True),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "effective_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "current_version_number",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="discovered",
        ),
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.UniqueConstraint(
            "source_id",
            "canonical_url",
            name="uq_regulatory_publication_source_url",
        ),
    )

    op.create_index(
        "ix_regulatory_publications_source_id",
        "regulatory_publications",
        ["source_id"],
    )

    op.create_index(
        "ix_regulatory_publications_source_seen",
        "regulatory_publications",
        ["source_id", "last_seen_at"],
    )

    op.create_table(
        "regulatory_publication_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "publication_id",
            sa.Uuid(),
            sa.ForeignKey(
                "regulatory_publications.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("snapshot_storage_key", sa.String(2000), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column(
            "diff_summary",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "publication_id",
            "version_number",
            name="uq_regulatory_publication_version",
        ),
        sa.UniqueConstraint(
            "publication_id",
            "content_hash",
            name="uq_regulatory_publication_content_hash",
        ),
    )

    op.create_index(
        "ix_regulatory_publication_versions_publication_id",
        "regulatory_publication_versions",
        ["publication_id"],
    )

    op.create_table(
        "regulatory_subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("regulatory_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "filters",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "active",
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
            "source_id",
            name="uq_regulatory_subscription",
        ),
    )

    op.create_index(
        "ix_regulatory_subscriptions_org_active",
        "regulatory_subscriptions",
        ["organization_id", "active"],
    )

    op.create_table(
        "regulatory_document_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "publication_id",
            sa.Uuid(),
            sa.ForeignKey(
                "regulatory_publications.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "organization_id"],
            ["documents.id", "documents.organization_id"],
            ondelete="CASCADE",
            name="fk_regulatory_document_link_tenant",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "publication_id",
            name="uq_regulatory_document_link",
        ),
    )

    op.create_index(
        "ix_regulatory_document_links_publication",
        "regulatory_document_links",
        ["publication_id"],
    )

    op.create_table(
        "regulatory_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "publication_id",
            sa.Uuid(),
            sa.ForeignKey(
                "regulatory_publications.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "publication_version_id",
            sa.Uuid(),
            sa.ForeignKey(
                "regulatory_publication_versions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("alert_type", sa.String(40), nullable=False),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default="info",
        ),
        sa.Column(
            "relevance_status",
            sa.String(30),
            nullable=False,
            server_default="untriaged",
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "matched_terms",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "reviewed_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'reviewed', 'dismissed')",
            name="ck_regulatory_alert_status",
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high')",
            name="ck_regulatory_alert_severity",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "publication_version_id",
            "alert_type",
            name="uq_regulatory_alert_version",
        ),
    )

    op.create_index(
        "ix_regulatory_alerts_org_status_created",
        "regulatory_alerts",
        ["organization_id", "status", "created_at"],
    )

    # Organization-scoped tables.
    for table in (
        "regulatory_subscriptions",
        "regulatory_document_links",
        "regulatory_alerts",
    ):
        op.execute(
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"
        )
        op.execute(
            f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"
        )
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_policy
            ON {table}
            USING (
                organization_id =
                NULLIF(
                    current_setting('app.current_org_id', true),
                    ''
                )::uuid
            )
            WITH CHECK (
                organization_id =
                NULLIF(
                    current_setting('app.current_org_id', true),
                    ''
                )::uuid
            )
            """
        )


def downgrade():
    for table in (
        "regulatory_alerts",
        "regulatory_document_links",
        "regulatory_subscriptions",
    ):
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_policy ON {table}"
        )

    op.drop_index(
        "ix_regulatory_alerts_org_status_created",
        table_name="regulatory_alerts",
    )
    op.drop_table("regulatory_alerts")

    op.drop_index(
        "ix_regulatory_document_links_publication",
        table_name="regulatory_document_links",
    )
    op.drop_table("regulatory_document_links")

    op.drop_index(
        "ix_regulatory_subscriptions_org_active",
        table_name="regulatory_subscriptions",
    )
    op.drop_table("regulatory_subscriptions")

    op.drop_index(
        "ix_regulatory_publication_versions_publication_id",
        table_name="regulatory_publication_versions",
    )
    op.drop_table("regulatory_publication_versions")

    op.drop_index(
        "ix_regulatory_publications_source_seen",
        table_name="regulatory_publications",
    )
    op.drop_index(
        "ix_regulatory_publications_source_id",
        table_name="regulatory_publications",
    )
    op.drop_table("regulatory_publications")

    op.drop_index(
        "ix_regulatory_sources_enabled",
        table_name="regulatory_sources",
    )
    op.drop_table("regulatory_sources")