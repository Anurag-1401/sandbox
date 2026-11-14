
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.search.reranking import RerankedResult


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str

    chunk_id: UUID
    document_id: UUID
    version_id: UUID

    document_title: str
    version_number: int

    page_start: int
    page_end: int

    content: str


@dataclass(frozen=True)
class EvidenceContext:
    items: list[EvidenceItem]
    text: str


class EvidenceContextBuilder:
    def __init__(
        self,
        max_context_chars: int = 24000,
    ) -> None:
        if max_context_chars <= 0:
            raise ValueError(
                "max_context_chars must be positive"
            )

        self.max_context_chars = max_context_chars

    @staticmethod
    def _unwrap_result(item):
        """
        Normalize both retrieval return types:

        HybridSearchResult
        RerankedResult
        """

        if isinstance(item, RerankedResult):
            hybrid_result = item.result
        else:
            hybrid_result = item

        return hybrid_result.result

    def build(
        self,
        results: list,
    ) -> EvidenceContext:

        evidence_items: list[EvidenceItem] = []
        context_parts: list[str] = []

        used_chars = 0

        for index, result_item in enumerate(results, start=1):
            source = self._unwrap_result(result_item)

            content = source.content.strip()

            if not content:
                continue

            evidence_id = f"E{len(evidence_items) + 1}"

            header = (
                f"[{evidence_id}]\n"
                f"Document: {source.document_title}\n"
                f"Version: {source.version_number}\n"
                f"Pages: {source.page_start}-{source.page_end}\n"
                f"Passage:\n"
            )

            remaining = (
                self.max_context_chars
                - used_chars
                - len(header)
            )

            if remaining <= 0:
                break

            # Keep the passage inside the configured context budget.
            bounded_content = content[:remaining]

            if not bounded_content.strip():
                break

            block = header + bounded_content

            evidence_items.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    chunk_id=source.chunk_id,
                    document_id=source.document_id,
                    version_id=source.version_id,
                    document_title=source.document_title,
                    version_number=source.version_number,
                    page_start=source.page_start,
                    page_end=source.page_end,
                    content=bounded_content,
                )
            )

            context_parts.append(block)
            used_chars += len(block) + 2

            if len(bounded_content) < len(content):
                break

        return EvidenceContext(
            items=evidence_items,
            text="\n\n".join(context_parts),
        )
