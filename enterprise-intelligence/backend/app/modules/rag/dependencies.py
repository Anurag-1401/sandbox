
from functools import lru_cache

from fastapi import HTTPException

from app.modules.rag.provider import (
    GroqLLMProvider,
    LLMConfigurationError,
)
from app.modules.rag.service import RAGService
from app.modules.search.dependencies import (
    get_retrieval_service,
)


@lru_cache(maxsize=1)
def get_llm_provider() -> GroqLLMProvider:
    try:
        return GroqLLMProvider()

    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="The Groq LLM provider is not configured.",
        ) from exc


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService(
        retrieval_service=get_retrieval_service(),
        llm_provider=get_llm_provider(),
    )
