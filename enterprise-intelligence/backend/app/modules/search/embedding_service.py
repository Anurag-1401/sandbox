from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from app.modules.search.embeddings import EmbeddingService


class DocumentEmbeddingService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

    def embed_chunks(
        self,
        chunks: Sequence[str],
    ) -> np.ndarray:
        return self.embedding_service.encode_documents(chunks)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embedding_service.encode_query(query)