from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TextInput(BaseModel):
    text: str = Field(min_length=1, max_length=200000)


class EntityResult(BaseModel):
    text: str
    label: str
    start: int
    end: int
    score: float | None = None
    source: Literal["rule", "model"]


class NERResponse(BaseModel):
    entities: list[EntityResult]
    model_status: str
    limitations: list[str] = Field(default_factory=list)


class ClassificationResponse(BaseModel):
    label: str
    scores: dict[str, float] = Field(default_factory=dict)
    model_status: str
    limitations: list[str] = Field(default_factory=list)


class ObligationResult(BaseModel):
    text: str
    obligation_type: str
    modality: str
    start: int
    end: int
    deadline_text: str | None = None
    responsible_party: str | None = None
    penalty_text: str | None = None
    confidence: float
    source: Literal["rule", "model"] = "rule"


class ObligationResponse(BaseModel):
    obligations: list[ObligationResult]
    limitations: list[str] = Field(default_factory=list)


class SimilarityInput(BaseModel):
    text_a: str = Field(min_length=1, max_length=200000)
    text_b: str = Field(min_length=1, max_length=200000)


class SimilarityResponse(BaseModel):
    similarity: float
    relation: str
    method: str
    model_status: str
    limitations: list[str] = Field(default_factory=list)


class NLIInput(BaseModel):
    premise: str = Field(min_length=1, max_length=200000)
    hypothesis: str = Field(min_length=1, max_length=200000)


class NLIResponse(BaseModel):
    label: Literal["entailment", "contradiction", "neutral", "unavailable"]
    scores: dict[str, float] = Field(default_factory=dict)
    model_status: str
    limitations: list[str] = Field(default_factory=list)


class MLEnrichment(BaseModel):
    document_classification: dict[str, Any] | None = None
    entities: list[dict[str, Any]] = Field(default_factory=list)
    obligations: list[dict[str, Any]] = Field(default_factory=list)
    clause_signals: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)