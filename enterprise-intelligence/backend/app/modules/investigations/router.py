from __future__ import annotations

import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal
from app.db.dependencies import get_db

from app.modules.investigations.dependencies import (
    get_investigation_service,
)
from app.modules.investigations.repository import (
    InvestigationRepository,
)
from app.modules.investigations.schemas import (
    InvestigationCreate,
    InvestigationStartRequest,
    InvestigationReviewRequest,
    InvestigationResponse,
    InvestigationRunResponse,
    InvestigationEventResponse,
    InvestigationDetailResponse,
)
from app.modules.investigations.service import (
    InvestigationService,
)

from app.modules.search.authorization import (
    DatabaseDocumentAuthorizationService,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


def require_role(
    principal: UserPrincipal,
    allowed_roles: set[str],
):
    if principal.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )


def get_allowed_document_ids(
    db: Session,
    principal: UserPrincipal,
) -> set[UUID]:

    return DatabaseDocumentAuthorizationService().get_searchable_document_ids(
        db=db,
        principal=principal,
    )


@router.post(
    "/",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation(
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
    service: InvestigationService = Depends(
        get_investigation_service
    ),
):
    require_role(
        principal,
        {"owner", "admin", "analyst"},
    )

    allowed_ids = get_allowed_document_ids(db, principal)

    requested_ids = set(payload.document_ids)

    if requested_ids and not requested_ids.issubset(allowed_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more selected documents were not found.",
        )

    scope = dict(payload.scope)
    scope["document_ids"] = [
        str(item)
        for item in payload.document_ids
    ]

    investigation = service.create(
        db,
        organization_id=principal.organization_id,
        user_id=principal.user_id,
        title=payload.title,
        question=payload.question,
        scope=scope,
    )

    db.commit()
    db.refresh(investigation)

    return investigation


@router.get(
    "/",
    response_model=list[InvestigationResponse],
)
def list_investigations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):
    repository = InvestigationRepository()

    return repository.list_investigations(
        db,
        organization_id=principal.organization_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{investigation_id}",
    response_model=InvestigationDetailResponse,
)
def get_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):
    repository = InvestigationRepository()

    investigation = repository.get_investigation(
        db,
        investigation_id=investigation_id,
        organization_id=principal.organization_id,
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    latest_run = repository.get_latest_run(
        db,
        investigation_id=investigation.id,
        organization_id=principal.organization_id,
    )

    events = []

    if latest_run:
        events = repository.list_events(
            db,
            run_id=latest_run.id,
            organization_id=principal.organization_id,
        )

    return {
        "investigation": investigation,
        "latest_run": latest_run,
        "events": events,
    }


@router.post(
    "/{investigation_id}/execute",
    response_model=InvestigationRunResponse,
)
def execute_investigation(
    investigation_id: UUID,
    payload: InvestigationStartRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
    service: InvestigationService = Depends(
        get_investigation_service
    ),
):
    require_role(
        principal,
        {"owner", "admin", "analyst"},
    )

    repository = InvestigationRepository()

    investigation = repository.get_investigation(
        db,
        investigation_id=investigation_id,
        organization_id=principal.organization_id,
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    if investigation.status in {
        "queued",
        "planning",
        "researching",
        "analyzing",
        "comparing",
        "verifying",
    }:
        raise HTTPException(
            status_code=409,
            detail="Investigation is already executing.",
        )

    latest = repository.get_latest_run(
        db,
        investigation_id=investigation.id,
        organization_id=principal.organization_id,
    )

    if (
    latest
    and latest.status == "review_required"
    and investigation.status == "review_required"
):
        raise HTTPException(
            status_code=409,
            detail="The previous run is awaiting human review.",
        )

    allowed_ids = get_allowed_document_ids(db, principal)

    selected_ids = {
        UUID(str(item))
        for item in investigation.scope.get("document_ids", [])
    }

    if selected_ids and not selected_ids.issubset(allowed_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more selected documents were not found.",
        )

    run = repository.create_run(
        db,
        investigation=investigation,
        user_id=principal.user_id,
    )

    repository.add_event(
        db,
        run=run,
        event_type="run_started",
        description="Investigation execution started.",
        actor_id=principal.user_id,
    )

    db.commit()
    db.refresh(run)

    try:
        service.execute(
            db,
            investigation=investigation,
            run=run,
            user_id=principal.user_id,
            allowed_document_ids=allowed_ids,
        )

    except Exception as exc:
        logger.exception(
            "Investigation failed",
            extra={
                "investigation_id": str(investigation_id),
                "organization_id": str(principal.organization_id),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Investigation execution failed. "
                "Inspect the investigation run for its failure status."
            ),
        ) from exc

    db.refresh(run)

    return run


@router.get(
    "/{investigation_id}/runs/{run_id}",
    response_model=InvestigationRunResponse,
)
def get_investigation_run(
    investigation_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):
    repository = InvestigationRepository()

    investigation = repository.get_investigation(
        db,
        investigation_id=investigation_id,
        organization_id=principal.organization_id,
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    run = repository.get_run(
        db,
        run_id=run_id,
        organization_id=principal.organization_id,
    )

    if run is None or run.investigation_id != investigation.id:
        raise HTTPException(
            status_code=404,
            detail="Investigation run not found.",
        )

    return run


@router.post(
    "/{investigation_id}/runs/{run_id}/review",
)
def review_investigation(
    investigation_id: UUID,
    run_id: UUID,
    payload: InvestigationReviewRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
    service: InvestigationService = Depends(
        get_investigation_service
    ),
):
    require_role(
        principal,
        {"owner", "admin", "reviewer"},
    )

    repository = InvestigationRepository()

    investigation = repository.get_investigation(
        db,
        investigation_id=investigation_id,
        organization_id=principal.organization_id,
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    run = repository.get_run(
        db,
        run_id=run_id,
        organization_id=principal.organization_id,
    )

    if run is None or run.investigation_id != investigation.id:
        raise HTTPException(
            status_code=404,
            detail="Investigation run not found.",
        )

    try:
        service.review(
            db,
            investigation=investigation,
            run=run,
            reviewer_id=principal.user_id,
            decision=payload.decision,
            comments=payload.comments,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "investigation_id": str(investigation.id),
        "run_id": str(run.id),
        "decision": payload.decision,
        "status": investigation.status,
    }