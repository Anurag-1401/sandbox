from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal
from app.db.session import get_db
from app.modules.search.dependencies import get_embedding_service
from app.modules.search.reranking import get_reranker
from app.modules.search import RetrievalService
from app.schemas.search import SearchRequest, SearchResponse


router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        service = RetrievalService(
            db=db,
            embedding_service=get_embedding_service(),
            reranker=get_reranker(),
        )

        result = service.search(
            query=request.query,
            organization_id=principal.organization_id,
            user_id=principal.user_id,
            role=principal.organization_role,
            top_k=request.top_k,
            candidate_limit=settings.search_candidate_limit,
        )

        db.commit()
        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc

    except Exception:
        db.rollback()
        raise