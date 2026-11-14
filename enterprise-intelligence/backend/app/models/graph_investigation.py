import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GraphInvestigationRun(Base):
    __tablename__ = "graph_investigation_runs"

    __table_args__ = (
        UniqueConstraint(
    "id",
    "organization_id",
    name="uq_graph_run_id_organization",
),
        CheckConstraint(
            "status IN ('running','completed','failed','cancelled')",
            name="ck_graph_run_status",
        ),
        CheckConstraint(
            "depth >= 1 AND depth <= 3",
            name="ck_graph_run_depth",
        ),
        Index(
            "ix_graph_runs_org_created",
            "organization_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="running",
        server_default="running",
    )

    root_node_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    depth: Mapped[int] = mapped_column(
        nullable=False,
        default=2,
    )

    filters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result_metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class GraphInvestigationFinding(Base):
    __tablename__ = "graph_investigation_findings"

    __table_args__ = (
        CheckConstraint(
            "finding_type IN "
            "('obligation_impact','product_impact','organization_impact',"
            "'evidence_gap','contradiction','related_entity')",
            name="ck_graph_finding_type",
        ),
        CheckConstraint(
            "priority IN ('critical','high','medium','low','informational')",
            name="ck_graph_finding_priority",
        ),
        CheckConstraint(
            "status IN ('open','under_review','confirmed','dismissed')",
            name="ck_graph_finding_status",
        ),
        CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_graph_finding_confidence",
        ),
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 100",
            name="ck_graph_finding_score",
        ),
        ForeignKeyConstraint(
            ["run_id", "organization_id"],
            [
                "graph_investigation_runs.id",
                "graph_investigation_runs.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_graph_finding_run_tenant",
        ),
        ForeignKeyConstraint(
            ["node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_graph_finding_node_tenant",
        ),
        Index(
            "ix_graph_findings_run",
            "organization_id",
            "run_id",
        ),
        Index(
            "ix_graph_findings_priority",
            "organization_id",
            "priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    node_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )

    finding_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="medium",
    )

    priority_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        server_default="open",
    )

    path_node_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    path_edge_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    evidence_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    review_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# Composite references above require these unique keys on their
# referenced tables. Add these constraints to the respective
# models and migration if they are not already present:
#
# GraphInvestigationRun:
# UniqueConstraint("id", "organization_id",
#                 name="uq_graph_run_id_organization")
#
# KnowledgeGraphNode:
# UniqueConstraint("id", "organization_id",
#                 name="uq_kg_node_id_organization")