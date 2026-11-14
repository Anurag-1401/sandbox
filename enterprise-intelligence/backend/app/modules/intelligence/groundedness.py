
from __future__ import annotations

from app.modules.intelligence.prompts import GROUNDEDNESS_PROMPT


class GroundednessVerifier:
    def __init__(self, llm):
        self.llm = llm

    def run(
        self,
        *,
        claims: list[dict],
        evidence: list[dict],
    ) -> list[dict]:

        if not claims:
            return []

        evidence_by_id = {
            item["evidence_id"]: item
            for item in evidence
        }

        payload = []

        for claim in claims:
            passages = [
                {
                    "evidence_id": evidence_id,
                    "document_title": evidence_by_id[evidence_id][
                        "document_title"
                    ],
                    "page_start": evidence_by_id[evidence_id][
                        "page_start"
                    ],
                    "page_end": evidence_by_id[evidence_id][
                        "page_end"
                    ],
                    "content": evidence_by_id[evidence_id][
                        "content"
                    ][:3000],
                }
                for evidence_id in claim["evidence_ids"]
                if evidence_id in evidence_by_id
            ]

            payload.append({
                "claim_id": claim["claim_id"],
                "claim": claim["text"],
                "evidence": passages,
            })

        response = self.llm.generate_json(
            system_prompt=GROUNDEDNESS_PROMPT,
            user_prompt=(
                "Verify these claims:\n"
                f"{payload}"
            ),
        )

        raw = response.get("verifications", [])

        if not isinstance(raw, list):
            raw = []

        by_claim = {
            item.get("claim_id"): item
            for item in raw
            if isinstance(item, dict)
        }

        results = []

        for claim in claims:
            item = by_claim.get(claim["claim_id"])

            if item is None:
                results.append(self._insufficient(
                    claim,
                    "The verifier did not return an assessment.",
                ))
                continue

            verdict = str(item.get("verdict", "insufficient"))

            if verdict not in {
                "supported",
                "contradicted",
                "insufficient",
            }:
                verdict = "insufficient"

            permitted_ids = set(claim["evidence_ids"])

            supporting = self._valid_ids(
                item.get("supporting_evidence_ids", []),
                permitted_ids,
            )

            contradicting = self._valid_ids(
                item.get("contradicting_evidence_ids", []),
                permitted_ids,
            )

            if verdict == "supported" and not supporting:
                verdict = "insufficient"

            if verdict == "contradicted" and not contradicting:
                verdict = "insufficient"

            limitations = item.get("limitations", [])

            if not isinstance(limitations, list):
                limitations = []

            results.append({
                "claim_id": claim["claim_id"],
                "verdict": verdict,
                "rationale": str(
                    item.get("rationale", "")
                )[:4000],
                "supporting_evidence_ids": supporting,
                "contradicting_evidence_ids": contradicting,
                "limitations": [
                    str(value)[:1000]
                    for value in limitations[:10]
                ],
            })

        return results

    @staticmethod
    def _valid_ids(values, permitted):
        if not isinstance(values, list):
            return []

        return list(dict.fromkeys(
            str(value)
            for value in values
            if str(value) in permitted
        ))

    @staticmethod
    def _insufficient(claim, reason):
        return {
            "claim_id": claim["claim_id"],
            "verdict": "insufficient",
            "rationale": reason,
            "supporting_evidence_ids": [],
            "contradicting_evidence_ids": [],
            "limitations": [reason],
        }
