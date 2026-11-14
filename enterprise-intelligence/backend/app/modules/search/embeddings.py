from __future__ import annotations

from typing import Any, Protocol, Sequence

import numpy as np


class EncoderProtocol(Protocol):
    def get_sentence_embedding_dimension(self) -> int:
        ...

    def encode(
        self,
        sentences: list[str],
        **kwargs: Any,
    ) -> Any:
        ...


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""


class EmbeddingService:
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        expected_dimension: int = DEFAULT_DIMENSION,
        batch_size: int = 32,
        normalize: bool = True,
        model: EncoderProtocol | None = None,
        max_sequence_length: int | None = 256,
    ) -> None:
        if expected_dimension <= 0:
            raise ValueError("expected_dimension must be positive")

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        if max_sequence_length is not None and max_sequence_length <= 0:
            raise ValueError("max_sequence_length must be positive")

        self.model_name = model_name
        self.expected_dimension = expected_dimension
        self.batch_size = batch_size
        self.normalize = normalize
        self.max_sequence_length = max_sequence_length

        self._model = model
        self._validate_model_if_loaded()

    def _load_model(self) -> EncoderProtocol:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers is required. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        try:
            model = SentenceTransformer(self.model_name)

            if self.max_sequence_length is not None:
                model.max_seq_length = min(
                    self.max_sequence_length,
                    model.max_seq_length,
                )

            return model
        except Exception as exc:
            raise EmbeddingError(
                f"Could not load embedding model: {self.model_name}"
            ) from exc

    @property
    def model(self) -> EncoderProtocol:
        if self._model is None:
            self._model = self._load_model()
            self._validate_model_if_loaded()

        return self._model

    def _validate_model_if_loaded(self) -> None:
        if self._model is None:
            return

        actual_dimension = (
            self._model.get_sentence_embedding_dimension()
        )

        if actual_dimension != self.expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected "
                f"{self.expected_dimension}, got {actual_dimension}"
            )

    @staticmethod
    def _validate_texts(texts: Sequence[str]) -> None:
        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise TypeError(
                    f"Input at index {index} must be a string"
                )

            if not text.strip():
                raise ValueError(
                    f"Input at index {index} cannot be empty"
                )

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)

        if np.any(norms == 0):
            raise EmbeddingError(
                "The embedding model returned a zero-length vector"
            )

        return vectors / norms

    def encode_documents(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        return self._encode(texts)

    def encode_query(self, query: str) -> np.ndarray:
        if not isinstance(query, str):
            raise TypeError("Query must be a string")

        if not query.strip():
            raise ValueError("Query cannot be empty")

        vectors = self._encode([query])
        return vectors[0]

    def _encode(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        if not texts:
            return np.empty(
                (0, self.expected_dimension),
                dtype=np.float32,
            )

        self._validate_texts(texts)

        try:
            vectors = self.model.encode(
                list(texts),
                batch_size=self.batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=False,
            )
        except Exception as exc:
            raise EmbeddingError(
                "Embedding generation failed"
            ) from exc

        vectors = np.asarray(vectors, dtype=np.float32)

        expected_shape = (
            len(texts),
            self.expected_dimension,
        )

        if vectors.shape != expected_shape:
            raise EmbeddingError(
                f"Invalid embedding shape: expected {expected_shape}, "
                f"received {vectors.shape}"
            )

        if not np.all(np.isfinite(vectors)):
            raise EmbeddingError(
                "Embedding output contains NaN or infinite values"
            )

        if self.normalize:
            vectors = self._normalize_vectors(vectors)

        return vectors.astype(np.float32, copy=False)