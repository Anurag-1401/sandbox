from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)
from app.modules.search.repository import (
    SearchRepository,
    SearchResult,
)


class SemanticSearchService:
    def __init__(
        self,
        embedding_service: DocumentEmbeddingService,
    ) -> None:
        self.embedding_service = embedding_service

    def search(
        self,
        *,
        db: Session,
        organization_id: uuid.UUID,
        query: str,
        top_k: int = 10,
        document_id: uuid.UUID | None = None,
        version_id: uuid.UUID | None = None,
    ) -> list[SearchResult]:
        if not isinstance(query, str):
            raise TypeError("Query must be a string")

        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty")

        if len(query) > 4000:
            raise ValueError(
                "Search query exceeds the 4000-character limit"
            )

        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        query_vector = self.embedding_service.embed_query(query)

        repository = SearchRepository(db)

        return repository.semantic_search(
            organization_id=organization_id,
            query_embedding=query_vector.tolist(),
            top_k=top_k,
            document_id=document_id,
            version_id=version_id,
        )