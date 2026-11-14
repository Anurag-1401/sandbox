from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=300)

    question: str = Field(min_length=10, max_length=4000)

    scope: dict[str, Any] = Field(default_factory=dict)

    document_ids: list[UUID] = Field(
        default_factory=list,
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_scope(self):
        allowed_keys = {
            "jurisdiction",
            "industry",
            "effective_date",
            "regulatory_area",
            "additional_context",
        }

        unknown = set(self.scope) - allowed_keys

        if unknown:
            raise ValueError(
                f"Unsupported scope fields: {sorted(unknown)}"
            )

        return self


class InvestigationStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_new_run: bool = False


class InvestigationReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(
        pattern="^(approve|reject|request_changes)$"
    )

    comments: str = Field(
        default="",
        max_length=5000,
    )


class InvestigationResponse(BaseModel):
    id: UUID
    title: str
    question: str
    scope: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationRunResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    status: str
    state: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationEventResponse(BaseModel):
    id: UUID
    event_type: str
    description: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationDetailResponse(BaseModel):
    investigation: InvestigationResponse
    latest_run: InvestigationRunResponse | None
    events: list[InvestigationEventResponse]