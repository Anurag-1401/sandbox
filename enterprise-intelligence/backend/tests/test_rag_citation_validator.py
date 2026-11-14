
import uuid

import pytest

from app.modules.rag.citation_validator import (
    CitationValidationError,
    CitationValidator,
)
from app.modules.rag.context_builder import EvidenceItem
from app.modules.rag.schemas import RAGFinding


def make_evidence():
    return EvidenceItem(
        evidence_id="E1",
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_title="BIS Standard",
        version_number=1,
        page_start=5,
        page_end=6,
        content="Certification is required for the product.",
    )


def test_valid_citation_is_resolved():
    evidence = make_evidence()

    citations = CitationValidator().build_citations(
        findings=[
            RAGFinding(
                text="The product requires certification.",
                evidence_ids=["E1"],
            )
        ],
        evidence_items=[evidence],
    )

    assert len(citations) == 1
    assert citations[0].evidence_id == "E1"
    assert citations[0].page_start == 5


def test_unknown_evidence_id_is_rejected():
    evidence = make_evidence()

    with pytest.raises(CitationValidationError):
        CitationValidator().build_citations(
            findings=[
                RAGFinding(
                    text="Unsupported statement.",
                    evidence_ids=["E99"],
                )
            ],
            evidence_items=[evidence],
        )


def test_uncited_finding_is_rejected():
    evidence = make_evidence()

    with pytest.raises(CitationValidationError):
        CitationValidator().build_citations(
            findings=[
                RAGFinding(
                    text="A factual statement without a citation.",
                    evidence_ids=[],
                )
            ],
            evidence_items=[evidence],
        )


def test_only_used_citations_are_returned():
    first = make_evidence()
    second = make_evidence()
    second = EvidenceItem(
        evidence_id="E2",
        chunk_id=second.chunk_id,
        document_id=second.document_id,
        version_id=second.version_id,
        document_title=second.document_title,
        version_number=second.version_number,
        page_start=7,
        page_end=7,
        content="An unrelated passage.",
    )

    citations = CitationValidator().build_citations(
        findings=[
            RAGFinding(
                text="The product requires certification.",
                evidence_ids=["E1"],
            )
        ],
        evidence_items=[first, second],
    )

    assert [item.evidence_id for item in citations] == ["E1"]
