import uuid

import pytest

from app.modules.search.hybrid import reciprocal_rank_fusion
from app.modules.search.repository import SearchResult


def make_result(chunk_id):
    return SearchResult(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_title="Regulatory document",
        version_number=1,
        chunk_index=0,
        content="Certification requirements",
        page_start=1,
        page_end=1,
        similarity=0.8,
    )


def test_rrf_combines_two_rankings():
    a, b, c, d = [make_result(uuid.uuid4()) for _ in range(4)]

    fused = reciprocal_rank_fusion(
        [a, b, c],
        [b, c, d],
    )

    assert [item.result.chunk_id for item in fused] == [
        b.chunk_id,
        c.chunk_id,
        a.chunk_id,
        d.chunk_id,
    ]


def test_rrf_score_for_first_rank():
    a = make_result(uuid.uuid4())

    fused = reciprocal_rank_fusion(
        [a],
        [],
        k=60,
    )

    assert fused[0].rrf_score == pytest.approx(1 / 61)


def test_rrf_preserves_source_ranks():
    a, b = [make_result(uuid.uuid4()) for _ in range(2)]

    fused = reciprocal_rank_fusion(
        [a, b],
        [b, a],
    )

    by_id = {
        item.result.chunk_id: item
        for item in fused
    }

    assert by_id[a.chunk_id].semantic_rank == 1
    assert by_id[a.chunk_id].keyword_rank == 2

    assert by_id[b.chunk_id].semantic_rank == 2
    assert by_id[b.chunk_id].keyword_rank == 1


def test_rrf_handles_one_empty_ranking():
    a, b = [make_result(uuid.uuid4()) for _ in range(2)]

    fused = reciprocal_rank_fusion(
        [a, b],
        [],
    )

    assert len(fused) == 2


def test_rrf_deduplicates_same_chunk():
    a = make_result(uuid.uuid4())

    fused = reciprocal_rank_fusion(
        [a, a],
        [a],
    )

    assert len(fused) == 1


def test_rrf_rejects_invalid_k():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([], [], k=0)


def test_rrf_rejects_negative_weights():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            [],
            [],
            semantic_weight=-1,
        )


def test_rrf_rejects_both_weights_zero():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            [],
            [],
            semantic_weight=0,
            keyword_weight=0,
        )