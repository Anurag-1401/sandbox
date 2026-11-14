"""Create graph-powered investigation tables.

Revision ID: d72a9c4e1f60
Revises: c91f7a2d6e40
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d72a9c4e1f60"
down_revision = "c91f7a2d6e40"
branch_labels = None
depends_on = None


def upgrade():

    # ---------------------------------------------------------
    # INVESTIGATION RUNS
    # ---------------------------------------------------------

    op.create_table(
        "graph_investigation_runs",

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

        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),

        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="running",
        ),

        sa.Column(
            "root_node_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),

        sa.Column(
            "depth",
            sa.Integer,
            nullable=False,
            server_default="2",
        ),

        sa.Column(
            "filters",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column("summary", sa.Text),

        sa.Column(
            "result_metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column("error_message", sa.Text),

        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_graph_run_id_organization",
        ),

        sa.CheckConstraint(
            "status IN ('running','completed','failed','cancelled')",
            name="ck_graph_run_status",
        ),

        sa.CheckConstraint(
            "depth >= 1 AND depth <= 3",
            name="ck_graph_run_depth",
        ),
    )

    op.create_index(
        "ix_graph_runs_org_created",
        "graph_investigation_runs",
        ["organization_id", "created_at"],
    )

    # ---------------------------------------------------------
    # FINDINGS
    # ---------------------------------------------------------

    op.create_table(
        "graph_investigation_findings",

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
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "node_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        sa.Column(
            "finding_type",
            sa.String(50),
            nullable=False,
        ),

        sa.Column(
            "priority",
            sa.String(30),
            nullable=False,
            server_default="medium",
        ),

        sa.Column(
            "priority_score",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "confidence",
            sa.Numeric(5, 4),
        ),

        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),

        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="open",
        ),

        sa.Column(
            "path_node_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),

        sa.Column(
            "path_edge_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),

        sa.Column(
            "evidence_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),

        sa.Column(
            "details",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),

        sa.Column("review_decision", sa.String(30)),
        sa.Column("review_notes", sa.Text),

        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),

        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["run_id", "organization_id"],
            [
                "graph_investigation_runs.id",
                "graph_investigation_runs.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_graph_finding_run_tenant",
        ),

        # RESTRICT is deliberate: setting a composite FK to NULL
        # would also try to null organization_id.
        sa.ForeignKeyConstraint(
            ["node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_graph_finding_node_tenant",
        ),

        sa.CheckConstraint(
            "finding_type IN "
            "('obligation_impact','product_impact','organization_impact',"
            "'evidence_gap','contradiction','related_entity')",
            name="ck_graph_finding_type",
        ),

        sa.CheckConstraint(
            "priority IN "
            "('critical','high','medium','low','informational')",
            name="ck_graph_finding_priority",
        ),

        sa.CheckConstraint(
            "status IN ('open','under_review','confirmed','dismissed')",
            name="ck_graph_finding_status",
        ),

        sa.CheckConstraint(
            "priority_score >= 0 AND priority_score <= 100",
            name="ck_graph_finding_score",
        ),

        sa.CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_graph_finding_confidence",
        ),
    )

    op.create_index(
        "ix_graph_findings_run",
        "graph_investigation_findings",
        ["organization_id", "run_id"],
    )

    op.create_index(
        "ix_graph_findings_priority",
        "graph_investigation_findings",
        ["organization_id", "priority"],
    )

    # ---------------------------------------------------------
    # ROW LEVEL SECURITY
    # ---------------------------------------------------------

    for table in (
        "graph_investigation_runs",
        "graph_investigation_findings",
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
        "graph_investigation_findings",
        "graph_investigation_runs",
    ):

        op.execute(
            f'DROP POLICY IF EXISTS {table}_tenant_policy ON "{table}"'
        )

        op.drop_table(table)