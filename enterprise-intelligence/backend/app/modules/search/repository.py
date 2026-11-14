from __future__ import annotations

from sqlalchemy.dialects.postgresql import Any

import uuid
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion


EMBEDDING_DIMENSION = 384


@dataclass(frozen=True)
class ChunkRecord:
    chunk_index: int
    content: str
    token_count: int
    page_start: int
    page_end: int
    embedding: Sequence[float]
    section_title: str | None = None
    source_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class SearchResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    version_id: uuid.UUID
    document_title: str
    version_number: int
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    similarity: float


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _validate_embedding(
        embedding: Sequence[float],
    ) -> list[float]:
        vector = np.asarray(embedding, dtype=np.float32)

        if vector.shape != (EMBEDDING_DIMENSION,):
            raise ValueError(
                f"Embedding must contain exactly "
                f"{EMBEDDING_DIMENSION} dimensions"
            )

        if not np.all(np.isfinite(vector)):
            raise ValueError(
                "Embedding contains NaN or infinite values"
            )

        norm = float(np.linalg.norm(vector))

        if norm <= 0:
            raise ValueError("Embedding cannot be a zero vector")

        return vector.tolist()

    def replace_version_chunks(
        self,
        *,
        organization_id: uuid.UUID,
        version_id: uuid.UUID,
        chunks: Sequence[ChunkRecord],
    ) -> int:
        """
        Replace chunks for one document version.

        Caller owns the transaction and must commit or roll back.
        """

        version = self.db.execute(
            select(DocumentVersion)
            .where(
                DocumentVersion.id == version_id,
                DocumentVersion.organization_id == organization_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if version is None:
            raise LookupError(
                "Document version not found in this organization"
            )

        indices = [chunk.chunk_index for chunk in chunks]

        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate chunk indices")

        if sorted(indices) != list(range(len(chunks))):
            raise ValueError(
                "Chunk indices must start at zero and be consecutive"
            )

        prepared = []

        for chunk in chunks:
            if not chunk.content.strip():
                raise ValueError("Chunk content cannot be empty")

            if chunk.token_count <= 0:
                raise ValueError("Chunk token_count must be positive")

            if (
                chunk.page_start < 1
                or chunk.page_end < chunk.page_start
            ):
                raise ValueError("Invalid chunk page range")

            prepared.append(
                DocumentChunk(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    version_id=version_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    section_title=chunk.section_title,
                    source_metadata={},
                    embedding=self._validate_embedding(
                        chunk.embedding
                    ),
                )
            )

        self.db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.version_id == version_id,
                DocumentChunk.organization_id == organization_id,
            )
        )

        self.db.add_all(prepared)

        version.status = "indexed"
        self.db.flush()

        return len(prepared)

    def semantic_search(
        self,
        *,
        organization_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int = 10,
        document_id: uuid.UUID | None = None,
        version_id: uuid.UUID | None = None,
        allowed_document_ids: set[uuid.UUID],
    ) -> list[SearchResult]:
        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        vector = self._validate_embedding(query_embedding)

        distance = DocumentChunk.embedding.cosine_distance(vector)

        statement = (
            select(
                DocumentChunk,
                Document.id.label("document_id"),
                Document.title.label("document_title"),
                DocumentVersion.version_number,
                distance.label("distance"),
            )
            .join(
                DocumentVersion,
                DocumentVersion.id == DocumentChunk.version_id,
            )
            .join(
                Document,
                Document.id == DocumentVersion.document_id,
            )
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentVersion.organization_id == organization_id,
                Document.organization_id == organization_id,
                DocumentVersion.status == "indexed",
            )
        )

        if not allowed_document_ids:
            return []

        statement = statement.where(
            Document.id.in_(allowed_document_ids)
        )

        if document_id is not None:
            statement = statement.where(
                Document.id == document_id
            )

        if version_id is not None:
            statement = statement.where(
                DocumentVersion.id == version_id
            )

        # Distance ascending = nearest vectors first.
        statement = (
            statement
            .order_by(distance.asc(), DocumentChunk.id.asc())
            .limit(top_k)
        )

        rows = self.db.execute(statement).all()

        results: list[SearchResult] = []

        for row in rows:
            chunk = row[0]
            cosine_distance = float(row.distance)

            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=row.document_id,
                    version_id=chunk.version_id,
                    document_title=row.document_title,
                    version_number=row.version_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    similarity=1.0 - cosine_distance,
                )
            )

        return results

    def count_version_chunks(
        self,
        *,
        organization_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(DocumentChunk)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.version_id == version_id,
            )
        )

        return int(self.db.scalar(statement) or 0)