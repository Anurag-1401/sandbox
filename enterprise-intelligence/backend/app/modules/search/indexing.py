from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.modules.search.chunking import DocumentChunker
from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)
from app.modules.search.repository import (
    ChunkRecord,
    SearchRepository,
)


@dataclass(frozen=True)
class IndexingResult:
    organization_id: uuid.UUID
    version_id: uuid.UUID
    chunks_indexed: int
    embedding_dimension: int


class DocumentIndexingService:
    def __init__(
        self,
        *,
        chunker: DocumentChunker,
        embedding_service: DocumentEmbeddingService,
    ) -> None:
        self.chunker = chunker
        self.embedding_service = embedding_service

    def index_pages(
        self,
        *,
        db: Session,
        organization_id: uuid.UUID,
        version_id: uuid.UUID,
        pages: list[dict[str, Any]],
    ) -> IndexingResult:
        """
        Index parsed pages for an existing document version.

        The caller must provide a database session with appropriate
        organization authorization already established.
        """

        if not pages:
            raise ValueError("Cannot index a document without pages")

        chunks = self.chunker.chunk_pages(pages)

        if not chunks:
            raise ValueError(
                "No searchable text was extracted from the document"
            )

        texts = [chunk.content for chunk in chunks]

        embeddings = self.embedding_service.embed_chunks(texts)

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "Embedding count does not match chunk count"
            )

        records = []

        for chunk, vector in zip(chunks, embeddings):
            records.append(
    ChunkRecord(
        chunk_index=chunk.index,
        content=chunk.content,
        token_count=chunk.token_count,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        section_title=None,
        source_metadata={
            "source_type": "pdf",
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
        },
        embedding=vector.tolist(),
    )
)

        repository = SearchRepository(db)

        count = repository.replace_version_chunks(
    organization_id=organization_id,
    version_id=version_id,
    chunks=records,
)

        return IndexingResult(
            organization_id=organization_id,
            version_id=version_id,
            chunks_indexed=count,
            embedding_dimension=embeddings.shape[1],
        )