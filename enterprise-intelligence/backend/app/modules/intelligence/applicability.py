
from __future__ import annotations

from app.modules.intelligence.prompts import (
    APPLICABILITY_PROMPT,
)


class RegulatoryApplicabilityAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def run(
        self,
        *,
        claims: list[dict],
        evidence: list[dict],
        scope: dict,
    ) -> list[dict]:

        if not claims:
            return []

        evidence_by_id = {
            item["evidence_id"]: item
            for item in evidence
        }

        payload = []

        for claim in claims:
            claim_evidence = [
                {
                    "evidence_id": evidence_id,
                    "document_title": evidence_by_id[evidence_id][
                        "document_title"
                    ],
                    "content": evidence_by_id[evidence_id][
                        "content"
                    ][:2500],
                }
                for evidence_id in claim["evidence_ids"]
                if evidence_id in evidence_by_id
            ]

            payload.append({
                "claim_id": claim["claim_id"],
                "claim": claim["text"],
                "entity": claim.get("entity"),
                "jurisdiction": claim.get("jurisdiction"),
                "temporal_scope": claim.get("temporal_scope"),
                "evidence": claim_evidence,
            })

        response = self.llm.generate_json(
            system_prompt=APPLICABILITY_PROMPT,
            user_prompt=(
                f"Investigation scope:\n{scope}\n\n"
                f"Claims and evidence:\n{payload}"
            ),
        )

        raw = response.get("assessments", [])

        if not isinstance(raw, list):
            raw = []

        by_claim = {
            item.get("claim_id"): item
            for item in raw
            if isinstance(item, dict)
        }

        valid_claim_ids = {
            item["claim_id"]
            for item in claims
        }

        results = []

        for claim in claims:
            item = by_claim.get(claim["claim_id"])

            if item is None:
                results.append({
                    "claim_id": claim["claim_id"],
                    "verdict": "uncertain",
                    "rationale": (
                        "No applicability assessment was returned."
                    ),
                    "evidence_ids": [],
                    "missing_scope_information": [
                        "applicability_assessment"
                    ],
                })
                continue

            verdict = str(item.get("verdict", "uncertain"))

            if verdict not in {
                "applicable",
                "not_applicable",
                "uncertain",
            }:
                verdict = "uncertain"

            permitted_ids = set(claim["evidence_ids"])

            raw_ids = item.get("evidence_ids", [])

            if not isinstance(raw_ids, list):
                raw_ids = []

            evidence_ids = [
                str(value)
                for value in raw_ids
                if str(value) in permitted_ids
            ]

            # An affirmative applicability result without supporting
            # source references must remain uncertain.
            if verdict in {"applicable", "not_applicable"} and not evidence_ids:
                verdict = "uncertain"

            missing = item.get(
                "missing_scope_information",
                [],
            )

            if not isinstance(missing, list):
                missing = []

            results.append({
                "claim_id": claim["claim_id"],
                "verdict": verdict,
                "rationale": str(
                    item.get("rationale", "")
                )[:4000],
                "evidence_ids": evidence_ids,
                "missing_scope_information": [
                    str(value)[:200]
                    for value in missing[:20]
                ],
            })

        return results
