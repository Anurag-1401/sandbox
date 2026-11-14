from __future__ import annotations

from app.modules.search.hybrid import HybridSearchResult
from app.modules.search.reranking import (
    CrossEncoderReranker,
    RerankedResult,
)


class RerankingService:
    def __init__(
        self,
        reranker: CrossEncoderReranker,
    ) -> None:
        self.reranker = reranker

    def rerank_candidates(
        self,
        *,
        query: str,
        candidates: list[HybridSearchResult],
        top_k: int = 10,
    ) -> list[RerankedResult]:

        return self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )