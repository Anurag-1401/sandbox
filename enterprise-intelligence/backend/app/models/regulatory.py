from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegulatorySource(Base):
    """Platform-managed official regulatory source."""

    __tablename__ = "regulatory_sources"

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('rss', 'atom', 'html')",
            name="ck_regulatory_source_type",
        ),
        UniqueConstraint(
            "code",
            name="uq_regulatory_source_code",
        ),
        Index(
            "ix_regulatory_sources_enabled",
            "enabled",
            "last_scanned_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    authority: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    jurisdiction: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="India",
    )

    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    listing_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    allowed_hosts: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        default=list,
    )

    selectors: Mapped[dict] = mapped_column(
        sa.JSON,
        nullable=False,
        default=dict,
    )

    scan_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.true(),
    )

    last_scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RegulatoryPublication(Base):
    """A discovered external publication, independent of tenant."""

    __tablename__ = "regulatory_publications"

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "canonical_url",
            name="uq_regulatory_publication_source_url",
        ),
        Index(
            "ix_regulatory_publications_source_seen",
            "source_id",
            "last_seen_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    canonical_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    current_version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="discovered",
    )

    metadata_json: Mapped[dict] = mapped_column(
        sa.JSON,
        nullable=False,
        default=dict,
    )

    effective_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class RegulatoryPublicationVersion(Base):
    """Immutable observation of a publication's content."""

    __tablename__ = "regulatory_publication_versions"

    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "version_number",
            name="uq_regulatory_publication_version",
        ),
        UniqueConstraint(
            "publication_id",
            "content_hash",
            name="uq_regulatory_publication_content_hash",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    publication_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_publications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    snapshot_storage_key: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    extracted_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    diff_summary: Mapped[dict] = mapped_column(
        sa.JSON,
        nullable=False,
        default=dict,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RegulatorySubscription(Base):
    """Organization subscription to a platform-managed source."""

    __tablename__ = "regulatory_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_id",
            name="uq_regulatory_subscription",
        ),
        Index(
            "ix_regulatory_subscriptions_org_active",
            "organization_id",
            "active",
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

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    filters: Mapped[dict] = mapped_column(
        sa.JSON,
        nullable=False,
        default=dict,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RegulatoryDocumentLink(Base):
    """Connect a global publication to a tenant's indexed document."""

    __tablename__ = "regulatory_document_links"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "publication_id",
            name="uq_regulatory_document_link",
        ),
        ForeignKeyConstraint(
            ["document_id", "organization_id"],
            [
                "documents.id",
                "documents.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_regulatory_document_link_tenant",
        ),
        Index(
            "ix_regulatory_document_links_publication",
            "publication_id",
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

    publication_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_publications.id", ondelete="CASCADE"),
        nullable=False,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RegulatoryAlert(Base):
    """Tenant-scoped alert requiring review."""

    __tablename__ = "regulatory_alerts"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'reviewed', 'dismissed')",
            name="ck_regulatory_alert_status",
        ),
        CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high')",
            name="ck_regulatory_alert_severity",
        ),
        UniqueConstraint(
            "organization_id",
            "publication_version_id",
            "alert_type",
            name="uq_regulatory_alert_version",
        ),
        Index(
            "ix_regulatory_alerts_org_status_created",
            "organization_id",
            "status",
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

    publication_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_publications.id", ondelete="CASCADE"),
        nullable=False,
    )

    publication_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "regulatory_publication_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
    )

    relevance_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="untriaged",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    title: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    matched_terms: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        default=list,
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )