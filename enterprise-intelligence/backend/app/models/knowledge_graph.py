import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


NODE_TYPES = (
    "regulation",
    "clause",
    "amendment",
    "obligation",
    "standard",
    "product",
    "organization",
    "authority",
    "concept",
)

RELATION_TYPES = (
    "contains",
    "amends",
    "supersedes",
    "repeals",
    "requires",
    "applies_to",
    "references",
    "defines",
    "issued_by",
    "governs",
    "implements",
    "conflicts_with",
    "related_to",
    "derived_from",
)

VERIFICATION_STATUSES = (
    "unverified",
    "reviewed",
    "verified",
    "rejected",
)


class KnowledgeGraphNode(Base):
    __tablename__ = "knowledge_graph_nodes"

    __table_args__ = (
        UniqueConstraint(
    "id",
    "organization_id",
    name="uq_kg_node_id_organization",
),
        UniqueConstraint(
            "organization_id",
            "canonical_key",
            name="uq_kg_node_org_canonical_key",
        ),
        CheckConstraint(
            "node_type IN "
            "('regulation','clause','amendment','obligation',"
            "'standard','product','organization','authority','concept')",
            name="ck_kg_node_type",
        ),
        CheckConstraint(
            "verification_status IN "
            "('unverified','reviewed','verified','rejected')",
            name="ck_kg_node_verification_status",
        ),
        Index(
            "ix_kg_nodes_org_type",
            "organization_id",
            "node_type",
        ),
        Index(
            "ix_kg_nodes_org_name",
            "organization_id",
            "name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    node_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    canonical_key: Mapped[str] = mapped_column(
        String(700),
        nullable=False,
    )

    external_identifier: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    jurisdiction: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    aliases: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    properties: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unverified",
        server_default="unverified",
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class KnowledgeGraphEdge(Base):
    __tablename__ = "knowledge_graph_edges"

    __table_args__ = (
        UniqueConstraint(
    "id",
    "organization_id",
    name="uq_kg_edge_id_organization",
),
        CheckConstraint(
            "relation_type IN "
            "('contains','amends','supersedes','repeals','requires',"
            "'applies_to','references','defines','issued_by','governs',"
            "'implements','conflicts_with','related_to','derived_from')",
            name="ck_kg_edge_relation_type",
        ),
        CheckConstraint(
            "source_node_id <> target_node_id",
            name="ck_kg_edge_no_self_reference",
        ),
        CheckConstraint(
            "verification_status IN "
            "('unverified','reviewed','verified','rejected')",
            name="ck_kg_edge_verification_status",
        ),
        UniqueConstraint(
            "organization_id",
            "source_node_id",
            "target_node_id",
            "relation_type",
            name="uq_kg_edge_org_source_target_relation",
        ),
        ForeignKeyConstraint(
            ["source_node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_edge_source_tenant",
        ),
        ForeignKeyConstraint(
            ["target_node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_edge_target_tenant",
        ),
        Index(
            "ix_kg_edges_org_source",
            "organization_id",
            "source_node_id",
        ),
        Index(
            "ix_kg_edges_org_target",
            "organization_id",
            "target_node_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    target_node_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    relation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    properties: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unverified",
        server_default="unverified",
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class KnowledgeGraphEvidence(Base):
    __tablename__ = "knowledge_graph_evidence"

    __table_args__ = (
        UniqueConstraint(
    "id",
    "organization_id",
    name="uq_kg_node_id_organization",
),
        CheckConstraint(
            "(node_id IS NOT NULL AND edge_id IS NULL) OR "
            "(node_id IS NULL AND edge_id IS NOT NULL)",
            name="ck_kg_evidence_exactly_one_target",
        ),
        ForeignKeyConstraint(
            ["edge_id", "organization_id"],
            [
                "knowledge_graph_edges.id",
                "knowledge_graph_edges.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_edge_tenant",
        ),
        ForeignKeyConstraint(
            ["node_id", "organization_id"],
            [
                "knowledge_graph_nodes.id",
                "knowledge_graph_nodes.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_node_tenant",
        ),
        ForeignKeyConstraint(
            ["document_id", "organization_id"],
            [
                "documents.id",
                "documents.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_document_tenant",
        ),
        ForeignKeyConstraint(
            ["version_id", "organization_id"],
            [
                "document_versions.id",
                "document_versions.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_kg_evidence_version_tenant",
        ),
        Index(
            "ix_kg_evidence_org_document",
            "organization_id",
            "document_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    node_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )

    edge_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    quote: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="supports",
        server_default="supports",
    )

    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )