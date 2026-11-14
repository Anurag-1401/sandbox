from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.auth import get_current_principal
from app.core.security.permissions import require_roles
from app.core.security.principal import UserPrincipal
from app.db.session import get_db
from app.models.regulatory import (
    RegulatorySource,
    RegulatorySubscription,
    RegulatoryAlert,
    RegulatoryDocumentLink,
    RegulatoryPublication,
    RegulatoryPublicationVersion,
)
from app.modules.regulatory_monitoring.impact import FILTER_KEYS
from app.modules.regulatory_monitoring.schemas import (
    SubscriptionCreate,
    AlertReviewRequest,
)


router = APIRouter(
    prefix="/regulatory",
    tags=["Regulatory Intelligence"],
)


@router.get("/sources")
def list_sources(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    sources = db.execute(
        select(RegulatorySource)
        .where(RegulatorySource.enabled.is_(True))
        .order_by(RegulatorySource.authority, RegulatorySource.name)
    ).scalars().all()

    return [
        {
            "id": str(source.id),
            "code": source.code,
            "name": source.name,
            "authority": source.authority,
            "jurisdiction": source.jurisdiction,
            "source_type": source.source_type,
            "scan_interval_minutes": source.scan_interval_minutes,
        }
        for source in sources
    ]


@router.get("/subscriptions")
def list_subscriptions(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    subscriptions = db.execute(
        select(RegulatorySubscription).where(
            RegulatorySubscription.organization_id
            == principal.organization_id
        )
    ).scalars().all()

    return [
        {
            "id": str(item.id),
            "source_id": str(item.source_id),
            "filters": item.filters,
            "active": item.active,
            "created_at": item.created_at,
        }
        for item in subscriptions
    ]


@router.post("/subscriptions", status_code=201)
def create_subscription(
    payload: SubscriptionCreate,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    unknown = set(payload.filters) - FILTER_KEYS

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported filters: {sorted(unknown)}",
        )

    for key, values in payload.filters.items():
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip()
            for value in values
        ):
            raise HTTPException(
                status_code=422,
                detail=f"Filter '{key}' must be a list of non-empty strings.",
            )

    source = db.execute(
        select(RegulatorySource).where(
            RegulatorySource.id == payload.source_id,
            RegulatorySource.enabled.is_(True),
        )
    ).scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Regulatory source not found.",
        )

    existing = db.execute(
        select(RegulatorySubscription).where(
            RegulatorySubscription.organization_id
            == principal.organization_id,
            RegulatorySubscription.source_id == payload.source_id,
        )
    ).scalar_one_or_none()

    if existing:
        existing.active = True
        existing.filters = payload.filters
        db.commit()
        db.refresh(existing)
        return existing

    subscription = RegulatorySubscription(
        organization_id=principal.organization_id,
        source_id=payload.source_id,
        created_by=principal.user_id,
        filters=payload.filters,
        active=True,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@router.delete("/subscriptions/{subscription_id}")
def deactivate_subscription(
    subscription_id: UUID,
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin")
    ),
    db: Session = Depends(get_db),
):
    subscription = db.execute(
        select(RegulatorySubscription).where(
            RegulatorySubscription.id == subscription_id,
            RegulatorySubscription.organization_id
            == principal.organization_id,
        )
    ).scalar_one_or_none()

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found.",
        )

    subscription.active = False
    db.commit()

    return {
        "subscription_id": str(subscription.id),
        "active": False,
    }


@router.get("/alerts")
def list_alerts(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(pending|reviewed|dismissed)$",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    statement = select(RegulatoryAlert).where(
        RegulatoryAlert.organization_id == principal.organization_id
    )

    if status_filter:
        statement = statement.where(
            RegulatoryAlert.status == status_filter
        )

    alerts = db.execute(
        statement
        .order_by(RegulatoryAlert.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    return alerts


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: UUID,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    alert = db.execute(
        select(RegulatoryAlert).where(
            RegulatoryAlert.id == alert_id,
            RegulatoryAlert.organization_id
            == principal.organization_id,
        )
    ).scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Regulatory alert not found.",
        )

    publication = db.get(
        RegulatoryPublication,
        alert.publication_id,
    )

    version = db.get(
        RegulatoryPublicationVersion,
        alert.publication_version_id,
    )

    return {
        "alert": alert,
        "publication": {
            "id": str(publication.id),
            "title": publication.title,
            "canonical_url": publication.canonical_url,
            "published_at": publication.published_at,
            "effective_at": publication.effective_at,
            "current_version_number": (
                publication.current_version_number
            ),
        },
        "version": {
            "id": str(version.id),
            "version_number": version.version_number,
            "content_hash": version.content_hash,
            "diff_summary": version.diff_summary,
            "observed_at": version.observed_at,
        },
    }


@router.patch(
    "/alerts/{alert_id}",
    dependencies=[
        Depends(require_roles("owner", "admin", "reviewer"))
    ],
)
def review_alert(
    alert_id: UUID,
    payload: AlertReviewRequest,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    alert = db.execute(
        select(RegulatoryAlert).where(
            RegulatoryAlert.id == alert_id,
            RegulatoryAlert.organization_id
            == principal.organization_id,
        )
    ).scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Regulatory alert not found.",
        )

    if payload.applicability_decision:
        alert.relevance_status = payload.applicability_decision

    if payload.effective_at is not None:
        publication = db.get(
            RegulatoryPublication,
            alert.publication_id,
        )

        if publication is not None:
            publication.effective_at = payload.effective_at

    alert.status = payload.status
    alert.reviewed_by = principal.user_id
    alert.reviewed_at = datetime.now(timezone.utc)
    alert.review_notes = payload.notes

    db.commit()

    return {
        "alert_id": str(alert.id),
        "status": alert.status,
        "reviewed_by": str(principal.user_id),
        "reviewed_at": alert.reviewed_at,
    }


@router.get("/publications/{publication_id}/versions")
def publication_versions(
    publication_id: UUID,
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    # The tenant must have a document link to this publication.
    link = db.execute(
        select(RegulatoryDocumentLink).where(
            RegulatoryDocumentLink.organization_id
            == principal.organization_id,
            RegulatoryDocumentLink.publication_id == publication_id,
        )
    ).scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=404,
            detail="Publication not found in this workspace.",
        )

    versions = db.execute(
        select(RegulatoryPublicationVersion)
        .where(
            RegulatoryPublicationVersion.publication_id
            == publication_id
        )
        .order_by(
            RegulatoryPublicationVersion.version_number.desc()
        )
    ).scalars().all()

    return [
        {
            "id": str(version.id),
            "version_number": version.version_number,
            "content_hash": version.content_hash,
            "diff_summary": version.diff_summary,
            "observed_at": version.observed_at,
        }
        for version in versions
    ]