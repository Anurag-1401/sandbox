
from __future__ import annotations

from typing import Literal, TypedDict


VerificationLabel = Literal[
    "supported",
    "contradicted",
    "insufficient",
]

ApplicabilityLabel = Literal[
    "applicable",
    "not_applicable",
    "uncertain",
]

ContradictionSeverity = Literal[
    "high",
    "medium",
    "low",
]


class AtomicClaim(TypedDict):
    claim_id: str
    text: str
    claim_type: str
    source_finding_ids: list[str]
    evidence_ids: list[str]
    entity: str | None
    jurisdiction: str | None
    temporal_scope: str | None


class ClaimVerification(TypedDict):
    claim_id: str
    verdict: VerificationLabel
    rationale: str
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    limitations: list[str]


class Contradiction(TypedDict):
    contradiction_id: str
    claim_a_id: str
    claim_b_id: str
    description: str
    severity: ContradictionSeverity
    evidence_ids: list[str]
    temporal_conflict: bool
    resolution_status: str


class SourceQuality(TypedDict):
    document_id: str
    document_title: str
    authority_level: str
    authority_score: float | None
    provenance_score: float
    freshness_score: float | None
    quality_score: float
    assessment_notes: list[str]


class ApplicabilityAssessment(TypedDict):
    claim_id: str
    verdict: ApplicabilityLabel
    rationale: str
    evidence_ids: list[str]
    missing_scope_information: list[str]


class ClaimConfidence(TypedDict):
    claim_id: str
    score: float | None
    label: str
    components: dict
    explanation: str


class IntelligenceResult(TypedDict):
    schema_version: str
    claims: list[AtomicClaim]
    verifications: list[ClaimVerification]
    contradictions: list[Contradiction]
    source_quality: list[SourceQuality]
    applicability: list[ApplicabilityAssessment]
    confidence: list[ClaimConfidence]
    summary: dict
    limitations: list[str]
    human_review_required: bool
