
from __future__ import annotations

from app.modules.intelligence.prompts import (
    CLAIM_EXTRACTION_PROMPT,
)


class ClaimExtractionError(RuntimeError):
    pass


class ClaimExtractor:
    def __init__(self, llm):
        self.llm = llm

    def run(
        self,
        *,
        findings: list[dict],
        evidence: list[dict],
    ) -> tuple[list[dict], list[str]]:

        if not findings:
            return [], ["No findings were available for claim extraction."]

        evidence_by_id = {
            item["evidence_id"]: item
            for item in evidence
        }

        finding_by_id = {
            item["finding_id"]: item
            for item in findings
        }

        payload = []

        for finding in findings:
            valid_ids = [
                item
                for item in finding.get("evidence_ids", [])
                if item in evidence_by_id
            ]

            payload.append({
                "finding_id": finding["finding_id"],
                "statement": finding["statement"],
                "evidence_ids": valid_ids,
            })

        response = self.llm.generate_json(
            system_prompt=CLAIM_EXTRACTION_PROMPT,
            user_prompt=(
                "Investigation findings:\n"
                f"{payload}\n\n"
                "Extract independently verifiable claims."
            ),
        )

        raw_claims = response.get("claims", [])

        if not isinstance(raw_claims, list):
            raise ClaimExtractionError(
                "Claim extraction returned an invalid claims collection."
            )

        normalized = []

        for index, item in enumerate(raw_claims[:100], start=1):
            if not isinstance(item, dict):
                continue

            text = str(item.get("text", "")).strip()

            if not text:
                continue

            raw_finding_ids = item.get("source_finding_ids", [])
            raw_evidence_ids = item.get("evidence_ids", [])

            if not isinstance(raw_finding_ids, list):
                raw_finding_ids = []

            if not isinstance(raw_evidence_ids, list):
                raw_evidence_ids = []

            source_finding_ids = [
                str(value)
                for value in raw_finding_ids
                if str(value) in finding_by_id
            ]

            # A claim can cite only evidence already cited by
            # one of its source findings.
            permitted_evidence = set()

            for finding_id in source_finding_ids:
                permitted_evidence.update(
                    finding_by_id[finding_id].get(
                        "evidence_ids", []
                    )
                )

            evidence_ids = [
                str(value)
                for value in raw_evidence_ids
                if (
                    str(value) in evidence_by_id
                    and str(value) in permitted_evidence
                )
            ]

            normalized.append({
                "claim_id": f"C{len(normalized) + 1}",
                "text": text[:4000],
                "claim_type": str(
                    item.get("claim_type", "observation")
                )[:100],
                "source_finding_ids": source_finding_ids,
                "evidence_ids": evidence_ids,
                "entity": self._optional_text(item.get("entity")),
                "jurisdiction": self._optional_text(
                    item.get("jurisdiction")
                ),
                "temporal_scope": self._optional_text(
                    item.get("temporal_scope")
                ),
            })

        limitations = response.get("limitations", [])

        if not isinstance(limitations, list):
            limitations = []

        if not normalized:
            limitations.append(
                "No valid atomic claims were extracted."
            )

        return normalized, [
            str(item)[:1000]
            for item in limitations[:20]
        ]

    @staticmethod
    def _optional_text(value):
        if value is None:
            return None

        value = str(value).strip()

        return value[:500] if value else None
