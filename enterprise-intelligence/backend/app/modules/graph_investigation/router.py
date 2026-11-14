from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security.auth import (
    get_current_principal,
    UserPrincipal,
)
from app.core.security.permissions import require_roles

from app.modules.graph_investigation.schemas import (
    GraphInvestigationCreate,
    GraphInvestigationResponse,
    GraphInvestigationDetail,
    GraphInvestigationFindingResponse,
    FindingReviewRequest,
)

from app.modules.graph_investigation.service import (
    GraphInvestigationService,
)


router = APIRouter(
    prefix="/graph-investigations",
    tags=["Graph-Powered Investigations"],
)


def get_service(
    db: Session,
    principal: UserPrincipal,
):

    return GraphInvestigationService(
        db=db,
        organization_id=principal.organization_id,
        user_id=principal.user_id,
    )


# ---------------------------------------------------------
# CREATE INVESTIGATION
# ---------------------------------------------------------

@router.post(
    "",
    response_model=GraphInvestigationDetail,
    status_code=201,
)
def create_investigation(
    payload: GraphInvestigationCreate,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "analyst")
    ),
):

    service = get_service(db, principal)

    try:

        run, findings = service.create_investigation(payload)

        db.commit()

        db.refresh(run)

        for finding in findings:
            db.refresh(finding)

        return {
            "investigation": run,
            "findings": findings,
        }

    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------
# LIST INVESTIGATIONS
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[GraphInvestigationResponse],
)
def list_investigations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    return get_service(
        db,
        principal,
    ).list_investigations(
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------
# GET INVESTIGATION AND FINDINGS
# ---------------------------------------------------------

@router.get(
    "/{run_id}",
    response_model=GraphInvestigationDetail,
)
def get_investigation(
    run_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    run, findings = get_service(
        db,
        principal,
    ).get_investigation(run_id)

    return {
        "investigation": run,
        "findings": findings,
    }


# ---------------------------------------------------------
# REVIEW A FINDING
# ---------------------------------------------------------

@router.patch(
    "/findings/{finding_id}",
    response_model=GraphInvestigationFindingResponse,
)
def review_finding(
    finding_id: UUID,
    payload: FindingReviewRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "reviewer")
    ),
):

    service = get_service(db, principal)

    try:

        finding = service.review_finding(
            finding_id,
            payload,
        )

        db.commit()
        db.refresh(finding)

        return finding

    except Exception:
        db.rollback()
        raise