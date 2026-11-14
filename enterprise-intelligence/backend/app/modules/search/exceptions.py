class SearchError(Exception):
    """Base exception for search and retrieval operations."""


class ChunkingError(SearchError):
    """Raised when document text cannot be chunked."""


class EmbeddingError(SearchError):
    """Raised when embedding generation fails."""


class EmbeddingDimensionError(EmbeddingError):
    """Raised when an embedding has an unexpected dimension."""


class IndexingError(SearchError):
    """Raised when document indexing fails."""


class RetrievalError(SearchError):
    """Raised when retrieval fails."""