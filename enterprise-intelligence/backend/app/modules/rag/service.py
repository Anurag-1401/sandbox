
from __future__ import annotations

import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.rag.citation_validator import (
    CitationValidator,
)
from app.modules.rag.citation_validator import (
    CitationValidationError,
    CitationValidator,
)
from app.modules.rag.context_builder import (
    EvidenceContextBuilder,
)
from app.modules.rag.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.modules.rag.provider import (
    GroqLLMProvider,
    LLMGenerationError,
)
from app.modules.rag.schemas import (
    RAGFinding,
    RAGRequest,
    RAGResponse,
)
from app.modules.search.retrieval_service import RetrievalService


class RAGGenerationError(RuntimeError):
    pass


class RAGService:
    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        llm_provider: GroqLLMProvider,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.llm_provider = llm_provider

        self.context_builder = EvidenceContextBuilder(
            max_context_chars=settings.rag_max_context_chars,
        )

        self.citation_validator = CitationValidator()

    def answer(
        self,
        *,
        db: Session,
        organization_id,
        allowed_document_ids: set,
        request: RAGRequest,
    ) -> RAGResponse:

        question = request.question.strip()

        if len(question) > settings.rag_max_question_chars:
            raise ValueError("Question exceeds the configured limit.")

        if request.candidate_limit < request.top_k:
            raise ValueError(
                "candidate_limit must be greater than or equal to top_k."
            )

        if request.version_id is not None and request.document_id is None:
            raise ValueError(
                "document_id is required when version_id is supplied."
            )

        if request.document_id is not None:
            if request.document_id not in allowed_document_ids:
                raise LookupError("Document not found.")

        if not allowed_document_ids:
            return RAGResponse(
                question=question,
                answer=(
                    "No accessible indexed documents were found "
                    "for this organization."
                ),
                findings=[],
                citations=[],
                limitations=[
                    "The organization has no accessible indexed evidence."
                ],
                insufficient_evidence=True,
                retrieval_count=0,
                model=self.llm_provider.model,
            )

        # -----------------------------------------------------
        # 1. Retrieve evidence using the existing M2 pipeline.
        # -----------------------------------------------------

        results = self.retrieval_service.search(
            db=db,
            organization_id=organization_id,
            query=question,
            top_k=request.top_k,
            candidate_limit=request.candidate_limit,
            document_id=request.document_id,
            version_id=request.version_id,
            use_reranker=request.use_reranker,
            allowed_document_ids=allowed_document_ids,
        )

        # -----------------------------------------------------
        # 2. Build bounded evidence context.
        # -----------------------------------------------------

        evidence_context = self.context_builder.build(results)

        if not evidence_context.items:
            return RAGResponse(
                question=question,
                answer=(
                    "I could not find sufficient supporting passages "
                    "in the accessible documents to answer this question."
                ),
                findings=[],
                citations=[],
                limitations=[
                    "No relevant evidence passages were retrieved."
                ],
                insufficient_evidence=True,
                retrieval_count=0,
                model=self.llm_provider.model,
            )

        # -----------------------------------------------------
        # 3. Ask the model for structured, evidence-backed output.
        # -----------------------------------------------------

        user_prompt = build_user_prompt(
            question=question,
            evidence_context=evidence_context.text,
        )

        raw_response = self.llm_provider.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # -----------------------------------------------------
        # 4. Parse and validate model JSON.
        # -----------------------------------------------------

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise RAGGenerationError(
                "The model returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise RAGGenerationError(
                "The model response must be a JSON object."
            )

        answer = payload.get("answer")
        raw_findings = payload.get("findings", [])
        limitations = payload.get("limitations", [])
        insufficient_evidence = payload.get(
            "insufficient_evidence",
            False,
        )

        if not isinstance(answer, str) or not answer.strip():
            raise RAGGenerationError(
                "The model did not provide a valid answer."
            )

        if not isinstance(raw_findings, list):
            raise RAGGenerationError(
                "The model returned invalid findings."
            )

        if not isinstance(limitations, list) or not all(
            isinstance(item, str) for item in limitations
        ):
            raise RAGGenerationError(
                "The model returned invalid limitations."
            )

        if not isinstance(insufficient_evidence, bool):
            raise RAGGenerationError(
                "The model returned an invalid evidence status."
            )

        try:
            findings = [
                RAGFinding.model_validate(item)
                for item in raw_findings
            ]
        except ValidationError as exc:
            raise RAGGenerationError(
                "The model returned malformed findings."
            ) from exc
        
        # -----------------------------------------------------
        # 5. Validate all evidence references.
        # -----------------------------------------------------

        if insufficient_evidence and findings:
            raise RAGGenerationError(
                "An insufficient-evidence response must not "
                "contain factual findings."
            )

        if not insufficient_evidence and not findings:
            raise RAGGenerationError(
                "The model returned no cited findings for an answer "
                "that claims to have sufficient evidence."
            )

        try:
            citations = self.citation_validator.build_citations(
                findings=findings,
                evidence_items=evidence_context.items,
                require_citations=(
                    settings.rag_require_citations
                    and not insufficient_evidence
                ),
            )
        except CitationValidationError as exc:
            raise RAGGenerationError(
                "The model returned invalid evidence references."
            ) from exc

        # -----------------------------------------------------
        # 6. Compose the factual answer from cited findings.
        # -----------------------------------------------------

        if insufficient_evidence:
            final_answer = answer.strip()
        else:
            final_answer = "\n\n".join(
                (
                    f"{finding.text} "
                    f"[{', '.join(finding.evidence_ids)}]"
                )
                for finding in findings
            )

        return RAGResponse(
            question=question,
            answer=final_answer,
            findings=findings,
            citations=citations,
            limitations=limitations,
            insufficient_evidence=insufficient_evidence,
            retrieval_count=len(results),
            model=self.llm_provider.model,
        )

