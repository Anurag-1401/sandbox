
from __future__ import annotations


class ConfidenceScorer:
    GROUNDEDNESS = {
        "supported": 1.0,
        "insufficient": 0.35,
        "contradicted": 0.0,
    }

    APPLICABILITY = {
        "applicable": 1.0,
        "not_applicable": 1.0,
        "uncertain": 0.35,
    }

    def score(
        self,
        *,
        claims: list[dict],
        verifications: list[dict],
        source_quality: list[dict],
        applicability: list[dict],
        contradictions: list[dict],
    ) -> list[dict]:

        verification_by_id = {
            item["claim_id"]: item
            for item in verifications
        }

        applicability_by_id = {
            item["claim_id"]: item
            for item in applicability
        }

        source_by_id = {
            item["document_id"]: item
            for item in source_quality
        }

        contradiction_claim_ids = {
            claim_id
            for item in contradictions
            for claim_id in (
                item["claim_a_id"],
                item["claim_b_id"],
            )
        }

        evidence_to_document = {}

        # Evidence IDs are attached to claims by the extractor.
        for claim in claims:
            for evidence_id in claim["evidence_ids"]:
                evidence_to_document.setdefault(
                    evidence_id,
                    set(),
                )

        # Source scores are document-level. We map them to claims
        # through evidence document IDs in the service layer.
        results = []

        for claim in claims:
            claim_id = claim["claim_id"]

            verification = verification_by_id.get(
                claim_id,
                {"verdict": "insufficient"},
            )

            applicability_item = applicability_by_id.get(
                claim_id,
                {"verdict": "uncertain"},
            )

            groundedness_score = self.GROUNDEDNESS[
                verification["verdict"]
            ]

            applicability_score = self.APPLICABILITY[
                applicability_item["verdict"]
            ]

            # Claim-level source quality is supplied by the caller
            # through the temporary field.
            source_score = claim.get(
                "_source_quality_score"
            )

            components = [
                (groundedness_score, 0.60),
                (source_score, 0.25),
                (applicability_score, 0.15),
            ]

            available = [
                (value, weight)
                for value, weight in components
                if value is not None
            ]

            denominator = sum(
                weight for _, weight in available
            )

            score = (
                sum(
                    value * weight
                    for value, weight in available
                ) / denominator
                if denominator
                else None
            )

            has_contradiction = (
                claim_id in contradiction_claim_ids
            )

            if score is not None and has_contradiction:
                score *= 0.5

            if score is None:
                label = "unrated"
            elif (
                verification["verdict"] != "supported"
                or applicability_item["verdict"] == "uncertain"
                or has_contradiction
            ):
                label = "requires_review"
            elif score >= 0.85:
                label = "high"
            elif score >= 0.65:
                label = "moderate"
            else:
                label = "low"

            results.append({
                "claim_id": claim_id,
                "score": (
                    round(score, 4)
                    if score is not None
                    else None
                ),
                "label": label,
                "components": {
                    "groundedness": groundedness_score,
                    "source_quality": source_score,
                    "applicability": applicability_score,
                    "contradiction_detected": has_contradiction,
                },
                "explanation": (
                    "Heuristic evidence-confidence indicator; "
                    "not a calibrated probability of truth."
                ),
            })

        return results
