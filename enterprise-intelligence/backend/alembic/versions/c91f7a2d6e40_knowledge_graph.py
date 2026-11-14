"""Create tenant-scoped enterprise knowledge graph.

Revision ID: c91f7a2d6e40
Revises: b8e21f6a4c90
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c91f7a2d6e40"
down_revision = "b8e21f6a4c90"
branch_labels = None
depends_on = None


def upgrade():

    # ---------------------------------------------------------
    # NODES
    # ---------------------------------------------------------

    op.create_table(
        "knowledge_graph_nodes",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column("node_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("canonical_key", sa.String(700), nullable=False),
        sa.Column("external_identifier", sa.String(300)),
        sa.Column("description", sa.Text),
        sa.Column("jurisdiction", sa.String(150)),

        sa.Column(
            "aliases",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),

        sa.Column(
            "properties",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column(
            "verification_status",
            sa.String(30),
            nullable=False,
            server_default="unverified",
        ),

        sa.Column("confidence", sa.Numeric(5, 4)),

        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "organization_id",
            "canonical_key",
            name="uq_kg_node_org_canonical_key",
        ),

        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_kg_node_id_organization",
        ),

        sa.CheckConstraint(
            "node_type IN "
            "('regulation','clause','amendment','obligation',"
            "'standard','product','organization','authority','concept')",
            name="ck_kg_node_type",
        ),

        sa.CheckConstraint(
            "verification_status IN "
            "('unverified','reviewed','verified','rejected')",
            name="ck_kg_node_verification_status",
        ),

        sa.CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_kg_node_confidence",
        ),
    )

    op.create_index(
        "ix_kg_nodes_org_type",
        "knowledge_graph_nodes",
        ["organization_id", "node_type"],
    )

    op.create_index(
        "ix_kg_nodes_org_name",
        "knowledge_graph_nodes",
        ["organization_id", "name"],
    )

    # ---------------------------------------------------------
    # EDGES
    # ---------------------------------------------------------

    op.create_table(
        "knowledge_graph_edges",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "source_node_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "target_node_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "relation_type",
            sa.String(50),
            nullable=False,
        ),

        sa.Column("description", sa.Text),

        sa.Column(
            "properties",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column(
            "verification_status",
            sa.String(30),
            nullable=False,
            server_default="unverified",
        ),

        sa.Column("confidence", sa.Numeric(5, 4)),

        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "organization_id",
            "source_node_id",
            "target_node_id",
            "relation_type",
            name="uq_kg_edge_org_source_target_relation",
        ),

        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_kg_edge_id_organization",
        ),

        sa.ForeignKeyConstraint(
            ["source_node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_edge_source_tenant",
        ),

        sa.ForeignKeyConstraint(
            ["target_node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_edge_target_tenant",
        ),

        sa.CheckConstraint(
            "source_node_id <> target_node_id",
            name="ck_kg_edge_no_self_reference",
        ),

        sa.CheckConstraint(
            "relation_type IN "
            "('contains','amends','supersedes','repeals','requires',"
            "'applies_to','references','defines','issued_by','governs',"
            "'implements','conflicts_with','related_to','derived_from')",
            name="ck_kg_edge_relation_type",
        ),

        sa.CheckConstraint(
            "verification_status IN "
            "('unverified','reviewed','verified','rejected')",
            name="ck_kg_edge_verification_status",
        ),

        sa.CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_kg_edge_confidence",
        ),
    )

    op.create_index(
        "ix_kg_edges_org_source",
        "knowledge_graph_edges",
        ["organization_id", "source_node_id"],
    )

    op.create_index(
        "ix_kg_edges_org_target",
        "knowledge_graph_edges",
        ["organization_id", "target_node_id"],
    )

    # ---------------------------------------------------------
    # EVIDENCE
    # ---------------------------------------------------------

    op.create_table(
        "knowledge_graph_evidence",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "node_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        sa.Column(
            "edge_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "document_chunks.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),

        sa.Column("page_number", sa.Integer),
        sa.Column("quote", sa.Text, nullable=False),

        sa.Column(
            "evidence_role",
            sa.String(50),
            nullable=False,
            server_default="supports",
        ),

        sa.Column(
            "metadata_json",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_node_tenant",
        ),

        sa.ForeignKeyConstraint(
            ["edge_id", "organization_id"],
            [
                "knowledge_graph_edges.id",
                "knowledge_graph_edges.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_edge_tenant",
        ),

        sa.ForeignKeyConstraint(
            ["document_id", "organization_id"],
            ["documents.id", "documents.organization_id"],
            ondelete="CASCADE",
            name="fk_kg_evidence_document_tenant",
        ),

        sa.ForeignKeyConstraint(
            ["version_id", "organization_id"],
            [
                "document_versions.id",
                "document_versions.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_version_tenant",
        ),

        sa.CheckConstraint(
            "(node_id IS NOT NULL AND edge_id IS NULL) OR "
            "(node_id IS NULL AND edge_id IS NOT NULL)",
            name="ck_kg_evidence_exactly_one_target",
        ),

        sa.CheckConstraint(
            "evidence_role IN "
            "('supports','contradicts','contextualizes')",
            name="ck_kg_evidence_role",
        ),

        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="ck_kg_evidence_page",
        ),
    )

    op.create_index(
        "ix_kg_evidence_org_document",
        "knowledge_graph_evidence",
        ["organization_id", "document_id"],
    )

    # ---------------------------------------------------------
    # ROW LEVEL SECURITY
    # ---------------------------------------------------------

    for table in (
        "knowledge_graph_nodes",
        "knowledge_graph_edges",
        "knowledge_graph_evidence",
    ):

        op.execute(
            f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'
        )

        op.execute(
            f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'
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
        "knowledge_graph_evidence",
        "knowledge_graph_edges",
        "knowledge_graph_nodes",
    ):
        op.execute(
            f'DROP POLICY IF EXISTS {table}_tenant_policy ON "{table}"'
        )
        op.drop_table(table)