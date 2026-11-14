import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.modules.search.semantic_search import (
    SemanticSearchService,
)


@pytest.fixture
def organization_id():
    return uuid.uuid4()


@pytest.fixture
def embedding_service():
    service = MagicMock()
    service.embed_query.return_value = np.ones(
        384,
        dtype=np.float32,
    ) / np.sqrt(384)
    return service


@pytest.fixture
def search_service(embedding_service):
    return SemanticSearchService(
        embedding_service=embedding_service,
    )


def test_empty_query_rejected(
    search_service,
    organization_id,
):
    with pytest.raises(ValueError):
        search_service.search(
            db=MagicMock(),
            organization_id=organization_id,
            query="   ",
        )


def test_invalid_top_k_rejected(
    search_service,
    organization_id,
):
    with pytest.raises(ValueError):
        search_service.search(
            db=MagicMock(),
            organization_id=organization_id,
            query="certification",
            top_k=0,
        )


def test_query_length_limit(
    search_service,
    organization_id,
):
    with pytest.raises(ValueError):
        search_service.search(
            db=MagicMock(),
            organization_id=organization_id,
            query="a" * 4001,
        )


@patch(
    "app.modules.search.semantic_search.SearchRepository"
)
def test_search_calls_repository(
    repository_class,
    search_service,
    embedding_service,
    organization_id,
):
    repository = repository_class.return_value
    repository.semantic_search.return_value = []

    db = MagicMock()

    results = search_service.search(
        db=db,
        organization_id=organization_id,
        query="What are the BIS certification requirements?",
        top_k=5,
    )

    assert results == []

    embedding_service.embed_query.assert_called_once_with(
        "What are the BIS certification requirements?"
    )

    repository.semantic_search.assert_called_once()

    kwargs = repository.semantic_search.call_args.kwargs

    assert kwargs["organization_id"] == organization_id
    assert kwargs["top_k"] == 5
    assert len(kwargs["query_embedding"]) == 384


@patch(
    "app.modules.search.semantic_search.SearchRepository"
)
def test_document_filter_is_forwarded(
    repository_class,
    search_service,
    organization_id,
):
    document_id = uuid.uuid4()

    repository_class.return_value.semantic_search.return_value = []

    search_service.search(
        db=MagicMock(),
        organization_id=organization_id,
        query="annual certification",
        document_id=document_id,
    )

    kwargs = (
        repository_class.return_value
        .semantic_search.call_args.kwargs
    )

    assert kwargs["document_id"] == document_id