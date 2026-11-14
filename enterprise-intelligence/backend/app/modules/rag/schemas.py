
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RAGRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=5,
        max_length=4000,
    )

    top_k: int = Field(
        default=8,
        ge=1,
        le=20,
    )

    candidate_limit: int = Field(
        default=40,
        ge=10,
        le=100,
    )

    document_id: UUID | None = None

    version_id: UUID | None = None

    use_reranker: bool = True


class Citation(BaseModel):
    evidence_id: str

    chunk_id: UUID
    document_id: UUID
    version_id: UUID

    document_title: str
    version_number: int

    page_start: int
    page_end: int

    quoted_text: str


class RAGFinding(BaseModel):
    text: str

    evidence_ids: list[str] = Field(
        default_factory=list,
    )


class RAGResponse(BaseModel):
    question: str

    answer: str

    findings: list[RAGFinding]

    citations: list[Citation]

    limitations: list[str] = Field(
        default_factory=list,
    )

    insufficient_evidence: bool

    retrieval_count: int

    model: str
