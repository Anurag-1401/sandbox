from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Investigation(Base):
    __tablename__ = "investigations"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_investigations_id_organization",
        ),
        CheckConstraint(
            """
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
            """,
            name="ck_investigation_status",
        ),
        Index(
            "ix_investigations_org_created",
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
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    scope: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft",
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


class InvestigationRun(Base):
    __tablename__ = "investigation_runs"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_investigation_runs_id_organization",
        ),
        ForeignKeyConstraint(
            ["investigation_id", "organization_id"],
            [
                "investigations.id",
                "investigations.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_investigation_run_tenant",
        ),
        CheckConstraint(
            """
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
            """,
            name="ck_investigation_run_status",
        ),
        Index(
            "ix_investigation_runs_investigation",
            "investigation_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    started_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="queued",
        server_default="queued",
    )

    state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
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


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    __table_args__ = (
        ForeignKeyConstraint(
            ["run_id", "organization_id"],
            [
                "investigation_runs.id",
                "investigation_runs.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_investigation_event_tenant",
        ),
        Index(
            "ix_investigation_events_run_created",
            "run_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )