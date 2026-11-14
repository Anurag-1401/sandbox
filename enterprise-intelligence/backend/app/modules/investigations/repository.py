from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.investigations.models import (
    Investigation,
    InvestigationRun,
    InvestigationEvent,
)


class InvestigationRepository:

    def create_investigation(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        question: str,
        scope: dict,
    ) -> Investigation:

        item = Investigation(
            organization_id=organization_id,
            created_by=user_id,
            title=title,
            question=question,
            scope=scope,
            status="draft",
        )

        db.add(item)
        db.flush()

        return item

    def get_investigation(
        self,
        db: Session,
        *,
        investigation_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> Investigation | None:

        return db.execute(
            select(Investigation).where(
                Investigation.id == investigation_id,
                Investigation.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def list_investigations(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Investigation]:

        statement = (
            select(Investigation)
            .where(
                Investigation.organization_id == organization_id
            )
            .order_by(Investigation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(db.execute(statement).scalars().all())

    def create_run(
        self,
        db: Session,
        *,
        investigation: Investigation,
        user_id: uuid.UUID,
    ) -> InvestigationRun:

        run = InvestigationRun(
            investigation_id=investigation.id,
            organization_id=investigation.organization_id,
            started_by=user_id,
            status="queued",
            state={},
            result={},
        )

        db.add(run)
        db.flush()

        investigation.status = "queued"

        return run

    def get_run(
        self,
        db: Session,
        *,
        run_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> InvestigationRun | None:

        return db.execute(
            select(InvestigationRun).where(
                InvestigationRun.id == run_id,
                InvestigationRun.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def get_latest_run(
        self,
        db: Session,
        *,
        investigation_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> InvestigationRun | None:

        statement = (
            select(InvestigationRun)
            .where(
                InvestigationRun.investigation_id == investigation_id,
                InvestigationRun.organization_id == organization_id,
            )
            .order_by(InvestigationRun.created_at.desc())
            .limit(1)
        )

        return db.execute(statement).scalar_one_or_none()

    def update_run(
        self,
        db: Session,
        *,
        run: InvestigationRun,
        status: str,
        state: dict | None = None,
        result: dict | None = None,
        error_message: str | None = None,
        completed: bool = False,
    ) -> None:

        run.status = status

        if state is not None:
            run.state = state

        if result is not None:
            run.result = result

        run.error_message = error_message

        if run.started_at is None:
            run.started_at = datetime.now(timezone.utc)

        if completed:
            run.completed_at = datetime.now(timezone.utc)

    def add_event(
        self,
        db: Session,
        *,
        run: InvestigationRun,
        event_type: str,
        description: str,
        payload: dict | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> InvestigationEvent:

        event = InvestigationEvent(
            run_id=run.id,
            organization_id=run.organization_id,
            actor_id=actor_id,
            event_type=event_type,
            description=description,
            payload=payload or {},
        )

        db.add(event)
        db.flush()

        return event

    def list_events(
        self,
        db: Session,
        *,
        run_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> list[InvestigationEvent]:

        statement = (
            select(InvestigationEvent)
            .where(
                InvestigationEvent.run_id == run_id,
                InvestigationEvent.organization_id == organization_id,
            )
            .order_by(InvestigationEvent.created_at.asc())
        )

        return list(db.execute(statement).scalars().all())