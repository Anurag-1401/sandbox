from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.search.repository import SearchResult


@dataclass(frozen=True)
class HybridSearchResult:
    result: SearchResult
    rrf_score: float
    semantic_rank: int | None
    keyword_rank: int | None


def reciprocal_rank_fusion(
    semantic_results: list[SearchResult],
    keyword_results: list[SearchResult],
    *,
    k: int = 60,
    semantic_weight: float = 1.0,
    keyword_weight: float = 1.0,
) -> list[HybridSearchResult]:

    if k <= 0:
        raise ValueError("k must be positive")

    if semantic_weight < 0 or keyword_weight < 0:
        raise ValueError("RRF weights cannot be negative")

    if semantic_weight == 0 and keyword_weight == 0:
        raise ValueError("At least one RRF weight must be positive")

    scores: dict[UUID, float] = {}
    representatives: dict[UUID, SearchResult] = {}
    semantic_ranks: dict[UUID, int] = {}
    keyword_ranks: dict[UUID, int] = {}

    def process(
        results: list[SearchResult],
        weight: float,
        ranks: dict[UUID, int],
    ) -> None:
        seen: set[UUID] = set()

        for position, result in enumerate(results, start=1):
            chunk_id = result.chunk_id

            # One result per chunk per ranking list.
            if chunk_id in seen:
                continue

            seen.add(chunk_id)
            ranks[chunk_id] = position
            representatives.setdefault(chunk_id, result)

            scores[chunk_id] = (
                scores.get(chunk_id, 0.0)
                + weight / (k + position)
            )

    process(
        semantic_results,
        semantic_weight,
        semantic_ranks,
    )

    process(
        keyword_results,
        keyword_weight,
        keyword_ranks,
    )

    fused = [
        HybridSearchResult(
            result=representatives[chunk_id],
            rrf_score=score,
            semantic_rank=semantic_ranks.get(chunk_id),
            keyword_rank=keyword_ranks.get(chunk_id),
        )
        for chunk_id, score in scores.items()
    ]

    fused.sort(
        key=lambda item: (
            -item.rrf_score,
            str(item.result.chunk_id),
        )
    )

    return fused