from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal
from app.modules.ml_intelligence.schemas import (
    NERResponse,
    TextInput,
    NLIInput,
    NLIResponse,
    SimilarityInput,
    SimilarityResponse,
    ObligationResponse,
    ClassificationResponse,
)
from app.modules.ml_intelligence.service import MLIntelligenceService


router = APIRouter(
    prefix="/ml",
    tags=["Model Intelligence"],
)


def get_service() -> MLIntelligenceService:
    return MLIntelligenceService()


@router.post("/ner", response_model=NERResponse)
def extract_entities(
    payload: TextInput,
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        return get_service().extract_entities(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Entity extraction failed.",
        ) from exc


@router.post("/classify", response_model=ClassificationResponse)
def classify_document(
    payload: TextInput,
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        return get_service().classify_document(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Document classification failed.",
        ) from exc


@router.post("/obligations", response_model=ObligationResponse)
def extract_obligations(
    payload: TextInput,
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        return get_service().extract_obligations(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Obligation extraction failed.",
        ) from exc


@router.post("/similarity", response_model=SimilarityResponse)
def compare_clauses(
    payload: SimilarityInput,
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        return get_service().compare_clauses(
            payload.text_a,
            payload.text_b,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Clause comparison failed.",
        ) from exc


@router.post("/nli", response_model=NLIResponse)
def verify_nli(
    payload: NLIInput,
    principal: UserPrincipal = Depends(get_current_principal),
):
    try:
        return get_service().verify_nli(
            payload.premise,
            payload.hypothesis,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="NLI inference failed.",
        ) from exc