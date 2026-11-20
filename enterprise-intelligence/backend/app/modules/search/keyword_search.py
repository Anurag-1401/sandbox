from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
from app.modules.search.repository import SearchResult


class KeywordSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _literal_pattern(query: str) -> str:
        escaped = (
            query
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )

        return f"%{escaped}%"

    def search(
        self,
        *,
        organization_id: uuid.UUID,
        query: str,
        top_k: int = 20,
        document_id: uuid.UUID | None = None,
        version_id: uuid.UUID | None = None,
        exact_phrase: bool = False,
        allowed_document_ids: set[uuid.UUID],
    ) -> list[SearchResult]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if len(query) > 4000:
            raise ValueError("Search query is too long")

        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        query = query.strip()

        ts_query = func.websearch_to_tsquery(
            "simple",
            query,
        )

        # Normalize whitespace so a phrase can match even when
        # the PDF extraction has line breaks between its words.
        query = " ".join(query.split())

        normalized_content = func.regexp_replace(
            DocumentChunk.content,
            r"\s+",
            " ",
            "g",
        )

        literal_match = normalized_content.ilike(
            self._literal_pattern(query),
            escape="\\",
        )

        ts_query = func.websearch_to_tsquery(
            "simple",
            query,
        )

        rank = func.ts_rank_cd(
            DocumentChunk.search_vector,
            ts_query,
        )

        full_text_match = DocumentChunk.search_vector.op("@@")(
            ts_query
        )

        statement = (
            select(
                DocumentChunk,
                Document.id.label("document_id"),
                Document.title.label("document_title"),
                DocumentVersion.version_number,
                rank.label("rank_score"),
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
                (
    literal_match
    if exact_phrase
    else or_(full_text_match, literal_match)
),
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

        statement = (
            statement
            .order_by(
                rank.desc(),
                DocumentChunk.id.asc(),
            )
            .limit(top_k)
        )

        rows = self.db.execute(statement).all()

        results: list[SearchResult] = []

        for row in rows:
            chunk = row[0]

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
                    # Keyword rank is deliberately not represented
                    # as a cosine similarity or probability.
                    similarity=0.0,
                )
            )

        return results