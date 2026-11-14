from __future__ import annotations

from app.core.config import settings
from app.modules.search.reranking import RerankedResult


class ResearchAgent:

    def __init__(self, retrieval_service):
        self.retrieval_service = retrieval_service

    def run(
        self,
        *,
        db,
        organization_id,
        allowed_document_ids: set,
        selected_document_ids: set,
        tasks: list[dict],
    ) -> list[dict]:

        if selected_document_ids:
            permitted_ids = (
                allowed_document_ids & selected_document_ids
            )
        else:
            permitted_ids = allowed_document_ids

        if not permitted_ids:
            return []

        evidence = []
        seen_chunks = set()

        for task in tasks:
            results = self.retrieval_service.search(
                db=db,
                organization_id=organization_id,
                query=task["query"],
                allowed_document_ids=permitted_ids,
                top_k=settings.investigation_max_evidence_per_task,
                candidate_limit=max(
                    10,
                    settings.investigation_max_evidence_per_task * 4,
                ),
                use_reranker=True,
            )

            for result in results:
                hybrid = (
                    result.result
                    if isinstance(result, RerankedResult)
                    else result
                )

                source = hybrid.result
                chunk_id = str(source.chunk_id)

                if chunk_id in seen_chunks:
                    continue

                seen_chunks.add(chunk_id)

                if len(evidence) >= settings.investigation_max_total_evidence:
                    return evidence

                score = (
                    result.rerank_score
                    if isinstance(result, RerankedResult)
                    else hybrid.rrf_score
                )

                evidence.append(
                    {
                        "evidence_id": f"E{len(evidence) + 1}",
                        "chunk_id": chunk_id,
                        "document_id": str(source.document_id),
                        "version_id": str(source.version_id),
                        "document_title": source.document_title,
                        "version_number": source.version_number,
                        "page_start": source.page_start,
                        "page_end": source.page_end,
                        "content": source.content,
                        "retrieval_score": (
                            float(score)
                            if score is not None
                            else None
                        ),
                        "task_id": task["task_id"],
                    }
                )

        return evidence