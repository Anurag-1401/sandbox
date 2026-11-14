import numpy as np
import pytest

from app.modules.search.embeddings import (
    EmbeddingError,
    EmbeddingService,
)


class FakeEncoder:
    def __init__(self, dimension=384):
        self.dimension = dimension

    def get_sentence_embedding_dimension(self):
        return self.dimension

    def encode(
        self,
        sentences,
        **kwargs,
    ):
        vectors = []

        for sentence in sentences:
            seed = sum(ord(char) for char in sentence)
            vector = np.full(
                self.dimension,
                float(seed % 100 + 1),
                dtype=np.float32,
            )
            vectors.append(vector)

        return np.vstack(vectors)


@pytest.fixture
def service():
    return EmbeddingService(
        model=FakeEncoder(),
        expected_dimension=384,
    )


def test_document_embedding_shape(service):
    vectors = service.encode_documents(
        ["Regulatory compliance requirements"]
    )

    assert vectors.shape == (1, 384)


def test_multiple_document_embeddings(service):
    vectors = service.encode_documents(
        [
            "Certification requirements",
            "Annual renewal requirements",
        ]
    )

    assert vectors.shape == (2, 384)


def test_query_embedding_shape(service):
    vector = service.encode_query(
        "What are the certification requirements?"
    )

    assert vector.shape == (384,)


def test_embeddings_are_normalized(service):
    vectors = service.encode_documents(
        ["A regulatory document"]
    )

    norm = np.linalg.norm(vectors[0])

    assert norm == pytest.approx(1.0, abs=1e-5)


def test_empty_document_list_returns_empty_matrix(service):
    vectors = service.encode_documents([])

    assert vectors.shape == (0, 384)


def test_empty_query_is_rejected(service):
    with pytest.raises(ValueError):
        service.encode_query("   ")


def test_empty_document_is_rejected(service):
    with pytest.raises(ValueError):
        service.encode_documents(["valid text", ""])


def test_non_string_input_is_rejected(service):
    with pytest.raises(TypeError):
        service.encode_documents(["valid text", 123])


def test_dimension_mismatch_is_rejected():
    with pytest.raises(ValueError):
        EmbeddingService(
            model=FakeEncoder(dimension=128),
            expected_dimension=384,
        )


def test_non_finite_output_is_rejected():
    class InvalidEncoder(FakeEncoder):
        def encode(self, sentences, **kwargs):
            return np.full(
                (len(sentences), 384),
                np.nan,
                dtype=np.float32,
            )

    service = EmbeddingService(model=InvalidEncoder())

    with pytest.raises(EmbeddingError):
        service.encode_documents(["test document"])