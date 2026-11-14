
from __future__ import annotations

from app.modules.rag.schemas import (
    Citation,
    RAGFinding,
)


class CitationValidationError(ValueError):
    pass


class CitationValidator:
    def build_citations(
        self,
        *,
        findings: list[RAGFinding],
        evidence_items: list,
        require_citations: bool = True,
    ) -> list[Citation]:

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence_items
        }

        used_ids: set[str] = set()

        for finding_index, finding in enumerate(findings):
            if not finding.evidence_ids:
                if require_citations:
                    raise CitationValidationError(
                        f"Finding {finding_index + 1} has no citations."
                    )

                continue

            for evidence_id in finding.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise CitationValidationError(
                        f"Unknown evidence reference: {evidence_id}"
                    )

                used_ids.add(evidence_id)

        citations = []

        # Preserve the retrieval order in the returned citations.
        for item in evidence_items:
            if item.evidence_id not in used_ids:
                continue

            citations.append(
                Citation(
                    evidence_id=item.evidence_id,
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    version_id=item.version_id,
                    document_title=item.document_title,
                    version_number=item.version_number,
                    page_start=item.page_start,
                    page_end=item.page_end,
                    quoted_text=item.content,
                )
            )

        return citations
