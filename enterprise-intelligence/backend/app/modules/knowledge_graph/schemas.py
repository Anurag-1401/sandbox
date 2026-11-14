from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


NODE_TYPES = {
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

RELATION_TYPES = {
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

VERIFICATION_STATUSES = {
    "unverified",
    "reviewed",
    "verified",
    "rejected",
}


class NodeCreate(BaseModel):
    node_type: str
    name: str = Field(min_length=1, max_length=500)
    canonical_key: str | None = Field(
        default=None,
        max_length=700,
    )
    external_identifier: str | None = Field(
        default=None,
        max_length=300,
    )
    description: str | None = None
    jurisdiction: str | None = Field(
        default=None,
        max_length=150,
    )
    aliases: list[str] = Field(default_factory=list)
    properties: dict = Field(default_factory=dict)
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def validate_node(self):
        if self.node_type not in NODE_TYPES:
            raise ValueError("Unsupported node_type")

        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Node name cannot be blank")

        if self.canonical_key is None:
            self.canonical_key = (
                f"{self.node_type}:{self.name.casefold()}"
            )

        self.canonical_key = self.canonical_key.strip().casefold()

        if not self.canonical_key:
            raise ValueError("canonical_key cannot be blank")

        return self


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    node_type: str
    name: str
    canonical_key: str
    external_identifier: str | None
    description: str | None
    jurisdiction: str | None
    aliases: list
    properties: dict
    verification_status: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime


class EdgeCreate(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    relation_type: str
    description: str | None = None
    properties: dict = Field(default_factory=dict)
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def validate_edge(self):
        if self.relation_type not in RELATION_TYPES:
            raise ValueError("Unsupported relation_type")

        if self.source_node_id == self.target_node_id:
            raise ValueError("Self-referencing edges are not allowed")

        return self


class EdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relation_type: str
    description: str | None
    properties: dict
    verification_status: str
    confidence: float | None
    created_at: datetime


class EvidenceCreate(BaseModel):
    node_id: UUID | None = None
    edge_id: UUID | None = None

    document_id: UUID
    version_id: UUID
    chunk_id: UUID | None = None

    page_number: int | None = Field(
        default=None,
        ge=1,
    )

    quote: str = Field(
        min_length=1,
        max_length=12000,
    )

    evidence_role: str = Field(
        default="supports",
        pattern="^(supports|contradicts|contextualizes)$",
        max_length=50,
    )

    metadata_json: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_target(self):
        if (self.node_id is None) == (self.edge_id is None):
            raise ValueError(
                "Provide exactly one of node_id or edge_id"
            )

        self.quote = self.quote.strip()

        if not self.quote:
            raise ValueError("Evidence quote cannot be blank")

        return self


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    node_id: UUID | None
    edge_id: UUID | None
    document_id: UUID
    version_id: UUID
    chunk_id: UUID | None
    page_number: int | None
    quote: str
    evidence_role: str
    metadata_json: dict
    created_at: datetime


class VerificationRequest(BaseModel):
    status: str = Field(
        pattern="^(unverified|reviewed|verified|rejected)$"
    )


class GraphSearchResponse(BaseModel):
    items: list[NodeResponse]
    total: int


class GraphNeighborhoodResponse(BaseModel):
    root: NodeResponse
    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    depth: int