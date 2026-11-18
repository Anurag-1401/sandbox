from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


FINDING_TYPES = {
    "obligation_impact",
    "product_impact",
    "organization_impact",
    "evidence_gap",
    "contradiction",
    "related_entity",
}

FINDING_STATUSES = {
    "open",
    "under_review",
    "confirmed",
    "dismissed",
}

REVIEW_DECISIONS = {
    "applicable",
    "not_applicable",
    "uncertain",
    "insufficient_evidence",
}


VALID_NODE_TYPES = {
    "regulation",
    "clause",
    "amendment",
    "obligation",
    "standard",
    "product",
    "organization",
    "authority",
    "concept",
}

VALID_RELATIONSHIP_TYPES = {
    "contains",
    "amends",
    "supersedes",
    "repeals",
    "requires",
    "applies_to",
    "references",
    "defines",
    "issued_by",
    "governs",
    "implements",
    "conflicts_with",
    "related_to",
    "derived_from",
}

class GraphInvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    root_node_ids: list[UUID] = Field(
        min_length=1,
        max_length=10,
    )

    depth: int = Field(
        default=2,
        ge=1,
        le=3,
    )

    include_unverified: bool = False

    relationship_types: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    node_types: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    include_evidence: bool = True

    
    @model_validator(mode="after")
    def validate_roots(self):
        if len(set(self.root_node_ids)) != len(self.root_node_ids):
            raise ValueError("Duplicate root node IDs are not allowed")

        if not set(self.node_types).issubset(VALID_NODE_TYPES):
            raise ValueError("Unsupported node type filter")

        if not set(self.relationship_types).issubset(
            VALID_RELATIONSHIP_TYPES
        ):
            raise ValueError("Unsupported relationship type filter")

        return self


class GraphInvestigationFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    node_id: UUID | None
    finding_type: str
    priority: str
    priority_score: float
    confidence: float | None
    title: str
    summary: str
    status: str
    path_node_ids: list
    path_edge_ids: list
    evidence_ids: list
    details: dict
    review_decision: str | None
    review_notes: str | None
    created_at: datetime


class GraphInvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: str
    root_node_ids: list
    depth: int
    summary: str | None
    result_metadata: dict
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class GraphInvestigationDetail(BaseModel):
    investigation: GraphInvestigationResponse
    findings: list[GraphInvestigationFindingResponse]


class FindingReviewRequest(BaseModel):
    status: str = Field(
        pattern="^(under_review|confirmed|dismissed)$"
    )

    review_decision: str | None = None

    review_notes: str | None = Field(
        default=None,
        max_length=10000,
    )

    @model_validator(mode="after")
    def validate_decision(self):
        if (
            self.review_decision is not None
            and self.review_decision not in REVIEW_DECISIONS
        ):
            raise ValueError("Invalid review decision")

        if self.status == "confirmed" and not self.review_decision:
            raise ValueError(
                "A review decision is required when confirming a finding"
            )

        return self