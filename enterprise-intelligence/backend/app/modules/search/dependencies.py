from functools import lru_cache

from app.modules.search.chunking import DocumentChunker
from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)
from app.modules.search.embeddings import EmbeddingService
from app.modules.search.indexing import DocumentIndexingService
from app.modules.search.semantic_search import SemanticSearchService
from app.modules.search.hybrid_search import HybridSearchService
from app.modules.search.reranking import CrossEncoderReranker
from app.modules.search.retrieval_service import RetrievalService


@lru_cache(maxsize=1)
def get_embedding_service() -> DocumentEmbeddingService:
    return DocumentEmbeddingService(
        embedding_service=EmbeddingService(
            model_name=(
                "sentence-transformers/all-MiniLM-L6-v2"
            ),
            expected_dimension=384,
            batch_size=32,
            normalize=True,
        )
    )


@lru_cache(maxsize=1)
def get_chunker() -> DocumentChunker:
    return DocumentChunker(
        chunk_size=220,
        overlap=40,
    )

@lru_cache(maxsize=1)
def get_hybrid_search_service() -> HybridSearchService:
    return HybridSearchService(
        embedding_service=get_embedding_service(),
        rrf_k=60,
        semantic_weight=1.0,
        keyword_weight=1.0,
    )


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoderReranker:
    return CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size=16,
        max_length=512,
    )


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(
        hybrid_search=get_hybrid_search_service(),
        reranker=get_reranker(),
    )

def get_indexing_service() -> DocumentIndexingService:
    return DocumentIndexingService(
        chunker=get_chunker(),
        embedding_service=get_embedding_service(),
    )


def get_semantic_search_service() -> SemanticSearchService:
    return SemanticSearchService(
        embedding_service=get_embedding_service(),
    )