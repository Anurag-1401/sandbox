
from __future__ import annotations

from datetime import datetime, timezone


class IntelligenceReportBuilder:
    def build(
        self,
        *,
        claims: list[dict],
        verifications: list[dict],
        contradictions: list[dict],
        source_quality: list[dict],
        applicability: list[dict],
        confidence: list[dict],
        limitations: list[str],
    ) -> dict:

        verdict_counts = {
            "supported": 0,
            "contradicted": 0,
            "insufficient": 0,
        }

        for item in verifications:
            verdict_counts[item["verdict"]] += 1

        applicability_counts = {
            "applicable": 0,
            "not_applicable": 0,
            "uncertain": 0,
        }

        for item in applicability:
            applicability_counts[item["verdict"]] += 1

        review_required = (
    not claims
    or bool(contradictions)
    or verdict_counts["contradicted"] > 0
    or verdict_counts["insufficient"] > 0
    or applicability_counts["uncertain"] > 0
    or any(
        item["label"] in {
            "low",
            "requires_review",
            "unrated",
        }
        for item in confidence
    )
)

        return {
            "schema_version": "1.0",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "summary": {
                "total_claims": len(claims),
                "supported_claims": verdict_counts["supported"],
                "contradicted_claims": verdict_counts["contradicted"],
                "insufficient_claims": verdict_counts["insufficient"],
                "contradictions_detected": len(contradictions),
                "applicable_claims": applicability_counts["applicable"],
                "not_applicable_claims": applicability_counts[
                    "not_applicable"
                ],
                "uncertain_applicability": applicability_counts[
                    "uncertain"
                ],
                "human_review_required": review_required,
            },
            "claims": claims,
            "verifications": verifications,
            "contradictions": contradictions,
            "source_quality": source_quality,
            "applicability": applicability,
            "confidence": confidence,
            "limitations": list(dict.fromkeys(limitations)),
            "human_review_required": review_required,
        }
