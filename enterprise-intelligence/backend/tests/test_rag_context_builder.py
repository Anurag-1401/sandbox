
import uuid

from app.modules.rag.context_builder import EvidenceContextBuilder
from app.modules.search.repository import SearchResult
from app.modules.search.hybrid import HybridSearchResult


def make_hybrid_result():
    source = SearchResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_title="BIS Electronics Standard",
        version_number=1,
        chunk_index=0,
        content="The product must comply with the applicable standard.",
        page_start=4,
        page_end=5,
        similarity=0.91,
    )

    return HybridSearchResult(
        result=source,
        rrf_score=0.03,
        semantic_rank=1,
        keyword_rank=2,
    )


def test_context_builder_assigns_evidence_ids():
    builder = EvidenceContextBuilder()

    context = builder.build([make_hybrid_result()])

    assert len(context.items) == 1
    assert context.items[0].evidence_id == "E1"
    assert "BIS Electronics Standard" in context.text
    assert "Pages: 4-5" in context.text


def test_context_builder_respects_context_limit():
    builder = EvidenceContextBuilder(
        max_context_chars=100,
    )

    context = builder.build([make_hybrid_result()])

    assert len(context.text) <= 100


def test_context_builder_handles_empty_results():
    builder = EvidenceContextBuilder()

    context = builder.build([])

    assert context.items == []
    assert context.text == ""
