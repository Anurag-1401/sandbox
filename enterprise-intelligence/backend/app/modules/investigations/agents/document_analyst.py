from __future__ import annotations

import json

from app.core.config import settings
from app.modules.investigations.llm import InvestigationLLM
from app.modules.investigations.prompts import ANALYST_PROMPT


class DocumentAnalystAgent:

    def __init__(self, llm: InvestigationLLM):
        self.llm = llm

    def run(
        self,
        *,
        question: str,
        evidence: list[dict],
    ) -> dict:

        if not evidence:
            return {
                "findings": [],
                "summary": (
                    "No relevant evidence was retrieved. "
                    "The investigation cannot establish a supported conclusion."
                ),
                "limitations": [
                    "No relevant indexed passages were found."
                ],
            }

        evidence_payload = []

        remaining = settings.investigation_max_context_chars

        for item in evidence:
            serialized = json.dumps(
                {
                    "evidence_id": item["evidence_id"],
                    "document_title": item["document_title"],
                    "version_number": item["version_number"],
                    "page_start": item["page_start"],
                    "page_end": item["page_end"],
                    "content": item["content"],
                },
                ensure_ascii=False,
            )

            if len(serialized) > remaining:
                break

            evidence_payload.append(serialized)
            remaining -= len(serialized)

        response = self.llm.generate_json(
            system_prompt=ANALYST_PROMPT,
            user_prompt=(
                f"Question:\n{question}\n\n"
                "Evidence passages:\n"
                + "\n".join(evidence_payload)
            ),
        )

        findings = response.get("findings", [])

        if not isinstance(findings, list):
            findings = []

        valid_evidence_ids = {
            item["evidence_id"]
            for item in evidence
        }

        normalized_findings = []

        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                continue

            statement = str(finding.get("statement", "")).strip()

            if not statement:
                continue

            evidence_ids = finding.get("evidence_ids", [])

            if not isinstance(evidence_ids, list):
                evidence_ids = []

            evidence_ids = [
                str(item)
                for item in evidence_ids
                if str(item) in valid_evidence_ids
            ]

            confidence = str(
                finding.get("confidence_label", "low")
            ).lower()

            if confidence not in {"high", "medium", "low"}:
                confidence = "low"

            normalized_findings.append(
                {
                    "finding_id": f"F{index}",
                    "category": str(
                        finding.get("category", "observation")
                    )[:100],
                    "statement": statement[:4000],
                    "evidence_ids": evidence_ids,
                    "confidence_label": confidence,
                    "review_required": (
                        bool(finding.get("review_required", False))
                        or not evidence_ids
                        or confidence != "high"
                    ),
                }
            )

        limitations = response.get("limitations", [])

        if not isinstance(limitations, list):
            limitations = []

        return {
            "findings": normalized_findings,
            "summary": str(response.get("summary", ""))[:8000],
            "limitations": [
                str(item)[:1000]
                for item in limitations[:20]
            ],
        }