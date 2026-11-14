"""Create investigation workflow tables.

Revision ID: 5c1a9e2d7b41
Revises: 4a67c215665d
""" 

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "5c1a9e2d7b41"
down_revision = "002_search_rls"
branch_labels = None
depends_on = None


INVESTIGATION_STATUSES = """
    status IN (
        'draft',
        'queued',
        'planning',
        'researching',
        'analyzing',
        'comparing',
        'verifying',
        'review_required',
        'approved',
        'rejected',
        'failed'
    )
"""


RUN_STATUSES = """
    status IN (
        'queued',
        'planning',
        'researching',
        'analyzing',
        'comparing',
        'verifying',
        'review_required',
        'approved',
        'rejected',
        'failed'
    )
"""


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column(
            "scope",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="draft",
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_investigations_id_organization",
        ),
        sa.CheckConstraint(
            INVESTIGATION_STATUSES,
            name="ck_investigation_status",
        ),
    )

    op.create_index(
        "ix_investigations_organization_id",
        "investigations",
        ["organization_id"],
    )

    op.create_index(
        "ix_investigations_org_created",
        "investigations",
        ["organization_id", "created_at"],
    )

    op.create_table(
        "investigation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("started_by", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="queued",
        ),
        sa.Column(
            "state",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "result",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["investigation_id", "organization_id"],
            [
                "investigations.id",
                "investigations.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_investigation_run_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["started_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_investigation_runs_id_organization",
        ),
        sa.CheckConstraint(
            RUN_STATUSES,
            name="ck_investigation_run_status",
        ),
    )

    op.create_index(
        "ix_investigation_runs_investigation",
        "investigation_runs",
        ["investigation_id", "created_at"],
    )

    op.create_table(
        "investigation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "payload",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["run_id", "organization_id"],
            [
                "investigation_runs.id",
                "investigation_runs.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_investigation_event_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_investigation_events_run_created",
        "investigation_events",
        ["run_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_investigation_events_run_created",
        table_name="investigation_events",
    )
    op.drop_table("investigation_events")

    op.drop_index(
        "ix_investigation_runs_investigation",
        table_name="investigation_runs",
    )
    op.drop_table("investigation_runs")

    op.drop_index(
        "ix_investigations_org_created",
        table_name="investigations",
    )
    op.drop_index(
        "ix_investigations_organization_id",
        table_name="investigations",
    )
    op.drop_table("investigations")