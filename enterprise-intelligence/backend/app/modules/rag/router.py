
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.document_version import DocumentVersion
from app.modules.rag.dependencies import get_rag_service
from app.modules.rag.provider import (
    LLMConfigurationError,
    LLMGenerationError,
    LLMRateLimitError,
)
from app.modules.rag.schemas import (
    RAGRequest,
    RAGResponse,
)
from app.modules.rag.service import RAGGenerationError
from app.modules.search.api_dependencies import (
    get_authorized_search_context,
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


@router.post(
    "/answer",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
)
def answer_question(
    request: RAGRequest,
    db: Session = Depends(get_db),
    context: dict = Depends(get_authorized_search_context),
    rag_service=Depends(get_rag_service),
):
    principal = context["principal"]
    allowed_document_ids = context["allowed_document_ids"]

    if request.version_id is not None:
        if request.document_id is None:
            raise HTTPException(
                status_code=400,
                detail="document_id is required when version_id is supplied.",
            )

        version = db.execute(
            select(DocumentVersion.id).where(
                DocumentVersion.id == request.version_id,
                DocumentVersion.document_id == request.document_id,
                DocumentVersion.organization_id == principal.organization_id,
                DocumentVersion.status == "indexed",
            )
        ).scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Document version not found.",
            )

    try:
        return rag_service.answer(
            db=db,
            organization_id=principal.organization_id,
            allowed_document_ids=allowed_document_ids,
            request=request,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="The Groq provider is not configured correctly.",
        ) from exc

    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="The AI provider is temporarily rate limited. Retry later.",
        ) from exc

    except LLMGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail="Groq could not generate a reliable research response.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The RAG request could not be completed.",
        ) from exc
