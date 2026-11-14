from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.models.document_version import DocumentVersion

from app.core.security.principal import UserPrincipal
from app.db.dependencies import get_db

from app.modules.search.api_dependencies import (
    get_authorized_search_context,
)
from app.modules.search.dependencies import (
    get_retrieval_service,
)
from app.modules.search.reranking import RerankedResult
from app.modules.search.schemas import (
    EvidenceResponse,
    SearchRequest,
    SearchResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_documents(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    context: dict = Depends(get_authorized_search_context),
    retrieval=Depends(get_retrieval_service),
):
    principal: UserPrincipal = context["principal"]
    allowed_document_ids = context["allowed_document_ids"]

    if payload.document_id is not None:
        if payload.document_id not in allowed_document_ids:
            # Avoid revealing whether another user's document exists.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
    
    
    if payload.version_id is not None:
        if payload.document_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "document_id is required when version_id is supplied"
                ),
            )

        version = db.execute(
            select(DocumentVersion.id).where(
                DocumentVersion.id == payload.version_id,
                DocumentVersion.document_id == payload.document_id,
                DocumentVersion.organization_id == principal.organization_id,
                DocumentVersion.status == "indexed",
            )
        ).scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document version not found",
            )


    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found",
        )

    if payload.version_id is not None and payload.document_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is required when version_id is supplied",
        )

    if payload.candidate_limit < payload.top_k:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="candidate_limit must be greater than or equal to top_k",
        )

    started_at = time.perf_counter()

    try:
        results = retrieval.search(
            db=db,
            organization_id=principal.organization_id,
            query=payload.query,
            allowed_document_ids=allowed_document_ids,
            top_k=payload.top_k,
            candidate_limit=payload.candidate_limit,
            document_id=payload.document_id,
            version_id=payload.version_id,
            use_reranker=payload.use_reranker,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Document retrieval failed",
            extra={
                "organization_id": str(principal.organization_id),
                "user_id": str(principal.user_id),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search could not be completed",
        ) from exc

    elapsed_ms = (time.perf_counter() - started_at) * 1000

    logger.info(
        "Document search completed",
        extra={
            "organization_id": str(principal.organization_id),
            "user_id": str(principal.user_id),
            "result_count": len(results),
            "reranking_enabled": payload.use_reranker,
            "elapsed_ms": round(elapsed_ms, 2),
        },
    )

    evidence = []

    for item in results:
        if isinstance(item, RerankedResult):
            hybrid = item.result
            rerank_score = item.rerank_score
            rerank_position = item.rerank_position
        else:
            hybrid = item
            rerank_score = None
            rerank_position = None

        source = hybrid.result

        evidence.append(
            EvidenceResponse(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                version_id=source.version_id,
                document_title=source.document_title,
                version_number=source.version_number,
                chunk_index=source.chunk_index,
                content=source.content,
                page_start=source.page_start,
                page_end=source.page_end,
                semantic_rank=hybrid.semantic_rank,
                keyword_rank=hybrid.keyword_rank,
                rrf_score=hybrid.rrf_score,
                rerank_score=rerank_score,
                rerank_position=rerank_position,
            )
        )

    return SearchResponse(
        query=payload.query,
        total_results=len(evidence),
        reranking_enabled=(
            payload.use_reranker
            and retrieval.reranker is not None
        ),
        results=evidence,
    )