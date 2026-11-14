import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.modules.search.hybrid_search import HybridSearchService
from app.modules.search.repository import SearchResult


def make_result(chunk_id):
    return SearchResult(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_title="BIS Regulation",
        version_number=1,
        chunk_index=0,
        content="Electronics certification requirements",
        page_start=3,
        page_end=3,
        similarity=0.9,
    )


def test_hybrid_search_fuses_semantic_and_keyword_results():
    org_id = uuid.uuid4()

    a = make_result(uuid.uuid4())
    b = make_result(uuid.uuid4())

    embeddings = MagicMock()
    embeddings.embed_query.return_value = np.ones(
        384,
        dtype=np.float32,
    )

    service = HybridSearchService(embeddings)

    db = MagicMock()

    from unittest.mock import patch

    with (
        patch(
            "app.modules.search.hybrid_search.SearchRepository"
        ) as repo_class,
        patch(
            "app.modules.search.hybrid_search.KeywordSearchService"
        ) as keyword_class,
    ):
        repo_class.return_value.semantic_search.return_value = [
            a,
            b,
        ]

        keyword_class.return_value.search.return_value = [
            b,
            a,
        ]

        results = service.search(
            db=db,
            organization_id=org_id,
            query="BIS certification",
            top_k=2,
            candidate_limit=10,
        )

    assert len(results) == 2
    assert results[0].result.chunk_id == b.chunk_id
    assert results[1].result.chunk_id == a.chunk_id
    assert results[0].semantic_rank == 2
    assert results[0].keyword_rank == 1


def test_hybrid_search_rejects_invalid_candidate_limit():
    service = HybridSearchService(MagicMock())

    with pytest.raises(ValueError):
        service.search(
            db=MagicMock(),
            organization_id=uuid.uuid4(),
            query="certification",
            top_k=10,
            candidate_limit=5,
        )