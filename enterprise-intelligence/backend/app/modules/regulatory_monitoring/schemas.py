from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    source_id: UUID
    filters: dict = Field(default_factory=dict)


class SubscriptionResponse(BaseModel):
    id: UUID
    source_id: UUID
    filters: dict
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceResponse(BaseModel):
    id: UUID
    code: str
    name: str
    authority: str
    jurisdiction: str
    source_type: str
    enabled: bool
    scan_interval_minutes: int

    model_config = ConfigDict(from_attributes=True)


class AlertReviewRequest(BaseModel):
    status: str = Field(pattern="^(reviewed|dismissed)$")
    notes: str | None = Field(default=None, max_length=5000)

    applicability_decision: str | None = Field(
        default=None,
        pattern="^(applicable|not_applicable|uncertain)$",
    )

    effective_at: datetime | None = None


class AlertResponse(BaseModel):
    id: UUID
    publication_id: UUID
    publication_version_id: UUID
    document_id: UUID | None
    alert_type: str
    severity: str
    relevance_status: str
    status: str
    title: str
    summary: str
    matched_terms: list
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationVersionResponse(BaseModel):
    id: UUID
    version_number: int
    content_hash: str
    diff_summary: dict
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)