from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)
from app.modules.search.hybrid import HybridSearchResult
from app.modules.search.hybrid_search import HybridSearchService
from app.modules.search.reranking import (
    CrossEncoderReranker,
    RerankedResult,
)


class RetrievalService:
    def __init__(
        self,
        *,
        hybrid_search: HybridSearchService,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self.hybrid_search = hybrid_search
        self.reranker = reranker

    def search(
        self,
        *,
        db: Session,
        organization_id: uuid.UUID,
        query: str,
        top_k: int = 10,
        candidate_limit: int = 40,
        document_id: uuid.UUID | None = None,
        version_id: uuid.UUID | None = None,
        use_reranker: bool = True,
        allowed_document_ids: set[uuid.UUID],
        match_mode: str = "hybrid",
    ) -> list[RerankedResult] | list[HybridSearchResult]:

        candidates = self.hybrid_search.search(
            db=db,
            organization_id=organization_id,
            query=query,
            allowed_document_ids=allowed_document_ids,
            top_k=candidate_limit,
            candidate_limit=candidate_limit,
            document_id=document_id,
            version_id=version_id,
            match_mode=match_mode,
        )

        if not use_reranker or self.reranker is None:
            return candidates[:top_k]

        return self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )