from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID


class ResearchTask(TypedDict):
    task_id: str
    objective: str
    query: str
    reason: str


class EvidenceRecord(TypedDict):
    evidence_id: str
    chunk_id: str
    document_id: str
    version_id: str
    document_title: str
    version_number: int
    page_start: int
    page_end: int
    content: str
    retrieval_score: float | None
    task_id: str


class Finding(TypedDict):
    finding_id: str
    category: str
    statement: str
    evidence_ids: list[str]
    confidence_label: str
    review_required: bool


class VerificationIssue(TypedDict):
    issue_type: str
    description: str
    finding_id: str | None
    evidence_ids: list[str]


class InvestigationState(TypedDict, total=False):
    investigation_id: str
    run_id: str
    organization_id: str
    user_id: str

    title: str
    question: str
    scope: dict[str, Any]

    allowed_document_ids: list[str]
    selected_document_ids: list[str]

    status: str
    tasks: list[ResearchTask]
    evidence: list[EvidenceRecord]
    findings: list[Finding]
    comparisons: list[dict[str, Any]]
    verification_issues: list[VerificationIssue]

    summary: str
    limitations: list[str]
    final_report: dict[str, Any]

    events: list[dict[str, Any]]
    errors: list[str]
    retry_count: int