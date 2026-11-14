from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)
from app.modules.search.hybrid import (
    HybridSearchResult,
    reciprocal_rank_fusion,
)
from app.modules.search.keyword_search import KeywordSearchService
from app.modules.search.repository import SearchRepository


class HybridSearchService:
    def __init__(
        self,
        embedding_service: DocumentEmbeddingService,
        *,
        rrf_k: int = 60,
        semantic_weight: float = 1.0,
        keyword_weight: float = 1.0,
    ) -> None:
        self.embedding_service = embedding_service
        self.rrf_k = rrf_k
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

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
        allowed_document_ids: set[uuid.UUID],
    ) -> list[HybridSearchResult]:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        if not top_k <= candidate_limit <= 200:
            raise ValueError(
                "candidate_limit must be between top_k and 200"
            )

        query = query.strip()

        if not allowed_document_ids:
            return []

        query_vector = self.embedding_service.embed_query(query)

        semantic_repository = SearchRepository(db)

        semantic_results = (
            semantic_repository.semantic_search(
                organization_id=organization_id,
                query_embedding=query_vector.tolist(),
                allowed_document_ids=allowed_document_ids,
                top_k=candidate_limit,
                document_id=document_id,
                version_id=version_id,
                
            )
        )

        keyword_service = KeywordSearchService(db)

        keyword_results = keyword_service.search(
            organization_id=organization_id,
            query=query,
             allowed_document_ids=allowed_document_ids,
            top_k=candidate_limit,
            document_id=document_id,
            version_id=version_id,
        )

        fused = reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            k=self.rrf_k,
            semantic_weight=self.semantic_weight,
            keyword_weight=self.keyword_weight,
        )

        return fused[:top_k]