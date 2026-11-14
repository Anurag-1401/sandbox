from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from app.modules.search.hybrid import HybridSearchResult


class CrossEncoderProtocol(Protocol):
    def predict(
        self,
        sentences: list[tuple[str, str]],
        **kwargs: Any,
    ) -> Any:
        ...


class RerankingError(RuntimeError):
    """Raised when cross-encoder reranking fails."""


@dataclass(frozen=True)
class RerankedResult:
    result: HybridSearchResult
    rerank_score: float
    rerank_position: int


class CrossEncoderReranker:
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        model: CrossEncoderProtocol | None = None,
        batch_size: int = 16,
        max_length: int = 512,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        if max_length <= 0:
            raise ValueError("max_length must be positive")

        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self._model = model

    def _load_model(self) -> CrossEncoderProtocol:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RerankingError(
                "Install sentence-transformers to use the reranker"
            ) from exc

        try:
            return CrossEncoder(
                self.model_name,
                max_length=self.max_length,
            )
        except Exception as exc:
            raise RerankingError(
                f"Could not load reranker model: {self.model_name}"
            ) from exc

    @property
    def model(self) -> CrossEncoderProtocol:
        if self._model is None:
            self._model = self._load_model()

        return self._model

    def rerank(
        self,
        *,
        query: str,
        candidates: list[HybridSearchResult],
        top_k: int = 10,
    ) -> list[RerankedResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty")

        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        if not candidates:
            return []

        if len(candidates) > 200:
            raise ValueError(
                "Reranking is limited to 200 candidates per request"
            )

        # Keep only the first occurrence of each chunk.
        unique_candidates = []
        seen = set()

        for candidate in candidates:
            chunk_id = candidate.result.chunk_id

            if chunk_id in seen:
                continue

            seen.add(chunk_id)
            unique_candidates.append(candidate)

        pairs = [
            (query.strip(), item.result.content)
            for item in unique_candidates
        ]

        try:
            raw_scores = self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise RerankingError(
                "Cross-encoder prediction failed"
            ) from exc

        scores = np.asarray(raw_scores)

        # A ranking model should produce one scalar per query/passage pair.
        if scores.shape == (len(unique_candidates), 1):
            scores = scores.reshape(-1)

        if scores.shape != (len(unique_candidates),):
            raise RerankingError(
                "Unexpected reranker output shape: "
                f"{scores.shape}"
            )

        if not np.all(np.isfinite(scores)):
            raise RerankingError(
                "Reranker returned NaN or infinite scores"
            )

        ranked = [
            (candidate, float(score))
            for candidate, score in zip(
                unique_candidates,
                scores,
            )
        ]

        # Higher relevance logit is better.
        ranked.sort(
            key=lambda item: (
                -item[1],
                str(item[0].result.result.chunk_id),
            )
        )

        return [
            RerankedResult(
                result=candidate,
                rerank_score=score,
                rerank_position=position,
            )
            for position, (candidate, score) in enumerate(
                ranked[:top_k],
                start=1,
            )
        ]