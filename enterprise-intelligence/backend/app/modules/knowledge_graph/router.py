from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security.auth import get_current_principal
from app.core.security.permissions import require_roles
from app.core.security.principal import UserPrincipal

from app.modules.knowledge_graph.schemas import (
    NodeCreate,
    NodeResponse,
    EdgeCreate,
    EdgeResponse,
    EvidenceCreate,
    EvidenceResponse,
    VerificationRequest,
    GraphNeighborhoodResponse,
    GraphSearchResponse,
)

from app.modules.knowledge_graph.service import (
    KnowledgeGraphService,
)


router = APIRouter(
    prefix="/knowledge-graph",
    tags=["Enterprise Knowledge Graph"],
)


def get_service(
    db: Session,
    principal: UserPrincipal,
) -> KnowledgeGraphService:

    return KnowledgeGraphService(
        db=db,
        organization_id=principal.organization_id,
        user_id=principal.user_id,
    )


# -------------------------------------------------------------
# NODES
# -------------------------------------------------------------

@router.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=201,
)
def create_node(
    payload: NodeCreate,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "analyst")
    ),
):

    service = get_service(db, principal)

    try:
        node = service.create_node(payload)
        db.commit()
        db.refresh(node)
        return node

    except Exception:
        db.rollback()
        raise


@router.get(
    "/nodes",
    response_model=GraphSearchResponse,
)
def search_nodes(
    q: str | None = Query(default=None, max_length=300),
    node_type: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    service = get_service(db, principal)

    if node_type:
        from app.modules.knowledge_graph.schemas import NODE_TYPES

        if node_type not in NODE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported node_type",
            )

    items, total = service.search_nodes(
        query=q,
        node_type=node_type,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
    }


@router.get(
    "/nodes/{node_id}",
    response_model=NodeResponse,
)
def get_node(
    node_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    return get_service(db, principal).get_node(node_id)


# -------------------------------------------------------------
# EDGES
# -------------------------------------------------------------

@router.post(
    "/edges",
    response_model=EdgeResponse,
    status_code=201,
)
def create_edge(
    payload: EdgeCreate,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "analyst")
    ),
):

    service = get_service(db, principal)

    try:
        edge = service.create_edge(payload)
        db.commit()
        db.refresh(edge)
        return edge

    except Exception:
        db.rollback()
        raise


# -------------------------------------------------------------
# EVIDENCE
# -------------------------------------------------------------

@router.post(
    "/evidence",
    response_model=EvidenceResponse,
    status_code=201,
)
def add_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "analyst")
    ),
):

    service = get_service(db, principal)

    try:
        evidence = service.add_evidence(payload)
        db.commit()
        db.refresh(evidence)
        return evidence

    except Exception:
        db.rollback()
        raise


@router.get(
    "/nodes/{node_id}/evidence",
    response_model=list[EvidenceResponse],
)
def get_node_evidence(
    node_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    return get_service(
        db,
        principal,
    ).get_node_evidence(node_id)


# -------------------------------------------------------------
# VERIFICATION
# -------------------------------------------------------------

@router.patch(
    "/nodes/{node_id}/verification",
    response_model=NodeResponse,
)
def verify_node(
    node_id: UUID,
    payload: VerificationRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "reviewer")
    ),
):

    service = get_service(db, principal)

    try:
        node = service.verify_node(
            node_id,
            payload.status,
        )
        db.commit()
        db.refresh(node)
        return node

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/edges/{edge_id}/verification",
    response_model=EdgeResponse,
)
def verify_edge(
    edge_id: UUID,
    payload: VerificationRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_roles("owner", "admin", "reviewer")
    ),
):

    service = get_service(db, principal)

    try:
        edge = service.verify_edge(
            edge_id,
            payload.status,
        )
        db.commit()
        db.refresh(edge)
        return edge

    except Exception:
        db.rollback()
        raise


# -------------------------------------------------------------
# GRAPH EXPLORATION
# -------------------------------------------------------------

@router.get(
    "/nodes/{node_id}/neighborhood",
    response_model=GraphNeighborhoodResponse,
)
def get_neighborhood(
    node_id: UUID,
    depth: int = Query(default=1, ge=1, le=3),
    include_unverified: bool = Query(default=True),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):

    return get_service(
        db,
        principal,
    ).get_neighborhood(
        root_id=node_id,
        depth=depth,
        include_unverified=include_unverified,
    )