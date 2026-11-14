
import json
import uuid
from unittest.mock import MagicMock

from app.modules.rag.schemas import RAGRequest
from app.modules.rag.service import RAGService
from app.modules.search.hybrid import HybridSearchResult
from app.modules.search.repository import SearchResult


class FakeRetrievalService:
    def __init__(self, results):
        self.results = results
        self.received_arguments = None

    def search(self, **kwargs):
        self.received_arguments = kwargs
        return self.results


class FakeLLMProvider:
    model = "fake-test-model"

    def __init__(self, response):
        self.response = response
        self.received_prompt = None

    def generate_json(self, **kwargs):
        self.received_prompt = kwargs
        return json.dumps(self.response)


def make_result():
    source = SearchResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_title="BIS Electronics Standard",
        version_number=1,
        chunk_index=0,
        content=(
            "The product must comply with the applicable "
            "Indian Standard before sale."
        ),
        page_start=4,
        page_end=5,
        similarity=0.92,
    )

    return HybridSearchResult(
        result=source,
        rrf_score=0.04,
        semantic_rank=1,
        keyword_rank=1,
    )


def test_rag_service_returns_grounded_answer():
    retrieval = FakeRetrievalService([make_result()])

    llm = FakeLLMProvider(
        {
            "answer": "The product must meet the applicable standard.",
            "findings": [
                {
                    "text": (
                        "The product must comply with the applicable "
                        "Indian Standard."
                    ),
                    "evidence_ids": ["E1"],
                }
            ],
            "limitations": [],
            "insufficient_evidence": False,
        }
    )

    service = RAGService(
        retrieval_service=retrieval,
        llm_provider=llm,
    )

    response = service.answer(
        db=MagicMock(),
        organization_id=uuid.uuid4(),
        allowed_document_ids={uuid.uuid4()},
        request=RAGRequest(
            question="What compliance is required?",
        ),
    )

    assert response.insufficient_evidence is False
    assert len(response.findings) == 1
    assert len(response.citations) == 1
    assert response.citations[0].evidence_id == "E1"
    assert response.model == "fake-test-model"


def test_rag_service_returns_insufficient_evidence():
    retrieval = FakeRetrievalService([])

    llm = FakeLLMProvider({})

    service = RAGService(
        retrieval_service=retrieval,
        llm_provider=llm,
    )

    response = service.answer(
        db=MagicMock(),
        organization_id=uuid.uuid4(),
        allowed_document_ids={uuid.uuid4()},
        request=RAGRequest(
            question="What is the applicable deadline?",
        ),
    )

    assert response.insufficient_evidence is True
    assert response.findings == []
    assert response.citations == []
    assert response.retrieval_count == 0


def test_rag_service_rejects_unknown_citation():
    retrieval = FakeRetrievalService([make_result()])

    llm = FakeLLMProvider(
        {
            "answer": "A requirement exists.",
            "findings": [
                {
                    "text": "A requirement exists.",
                    "evidence_ids": ["E999"],
                }
            ],
            "limitations": [],
            "insufficient_evidence": False,
        }
    )

    service = RAGService(
        retrieval_service=retrieval,
        llm_provider=llm,
    )

    import pytest

    from app.modules.rag.citation_validator import (
        CitationValidationError,
    )

    with pytest.raises(CitationValidationError):
        service.answer(
            db=MagicMock(),
            organization_id=uuid.uuid4(),
            allowed_document_ids={uuid.uuid4()},
            request=RAGRequest(
                question="What compliance is required?",
            ),
        )
