from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        min_length=2,
        max_length=4000,
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
    )

    candidate_limit: int = Field(
        default=40,
        ge=10,
        le=100,
    )

    document_id: UUID | None = None
    version_id: UUID | None = None

    use_reranker: bool = True


class EvidenceResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    version_id: UUID

    document_title: str
    version_number: int

    chunk_index: int
    content: str

    page_start: int
    page_end: int

    semantic_rank: int | None
    keyword_rank: int | None

    rrf_score: float
    rerank_score: float | None = None
    rerank_position: int | None = None


class SearchResponse(BaseModel):
    query: str
    total_results: int
    reranking_enabled: bool
    results: list[EvidenceResponse]