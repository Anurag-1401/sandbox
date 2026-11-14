from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID

    document_title: str
    filename: str

    chunk_index: int
    page_start: int | None
    page_end: int | None

    content: str

    rrf_score: float
    rerank_score: float


class SearchResponse(BaseModel):
    query: str
    retrieval_method: str
    total_candidates: int
    results: list[SearchResult]