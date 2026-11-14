
from __future__ import annotations

from app.modules.intelligence.applicability import (
    RegulatoryApplicabilityAnalyzer,
)
from app.modules.intelligence.claim_extractor import (
    ClaimExtractor,
)
from app.modules.intelligence.contradiction import (
    ContradictionDetector,
)
from app.modules.intelligence.groundedness import (
    GroundednessVerifier,
)
from app.modules.intelligence.report import (
    IntelligenceReportBuilder,
)
from app.modules.intelligence.scoring import (
    ConfidenceScorer,
)
from app.modules.intelligence.source_reliability import (
    SourceReliabilityScorer,
)

class IntelligenceService:
    def __init__(self, llm):
        self.claim_extractor = ClaimExtractor(llm)
        self.groundedness = GroundednessVerifier(llm)
        self.contradiction_detector = ContradictionDetector(llm)
        self.source_scorer = SourceReliabilityScorer()
        self.applicability = RegulatoryApplicabilityAnalyzer(llm)
        self.confidence_scorer = ConfidenceScorer()
        self.report_builder = IntelligenceReportBuilder()

    def run(
        self,
        *,
        question: str,
        findings: list[dict],
        evidence: list[dict],
        comparisons: list[dict],
        scope: dict,
    ) -> dict:

        limitations = []

        # 1. Atomic claim extraction
        claims, extraction_limitations = self.claim_extractor.run(
            findings=findings,
            evidence=evidence,
        )
        limitations.extend(extraction_limitations)

        if not claims:
            return self.report_builder.build(
                claims=[],
                verifications=[],
                contradictions=[],
                source_quality=[],
                applicability=[],
                confidence=[],
                limitations=limitations + [
                    "No claims could be extracted for verification."
                ],
            )

        # 2. Claim-to-evidence groundedness verification
        verifications = self.groundedness.run(
            claims=claims,
            evidence=evidence,
        )

        # 3. Contradiction detection
        contradictions, contradiction_limitations = (
            self.contradiction_detector.run(
                claims=claims,
                evidence=evidence,
                existing_comparisons=comparisons,
            )
        )
        limitations.extend(contradiction_limitations)

        # 4. Source reliability and provenance
        # Source registry is server-controlled. Do not accept
        # authority ratings from ordinary investigation input.
        source_registry = {}

        source_quality = self.source_scorer.score(
            evidence=evidence,
            source_registry=source_registry,
        )

        source_by_document = {
            item["document_id"]: item
            for item in source_quality
        }

        evidence_by_id = {
            item["evidence_id"]: item
            for item in evidence
        }

        # 5. Regulatory applicability
        applicability = self.applicability.run(
            claims=claims,
            evidence=evidence,
            scope=scope,
        )

        # 6. Map document quality to each claim.
        for claim in claims:
            scores = []

            for evidence_id in claim["evidence_ids"]:
                source = evidence_by_id.get(evidence_id)

                if source is None:
                    continue

                document_quality = source_by_document.get(
                    source["document_id"]
                )

                if document_quality is not None:
                    scores.append(
                        document_quality["quality_score"]
                    )

            claim["_source_quality_score"] = (
                sum(scores) / len(scores)
                if scores
                else None
            )

        confidence = self.confidence_scorer.score(
            claims=claims,
            verifications=verifications,
            source_quality=source_quality,
            applicability=applicability,
            contradictions=contradictions,
        )

        # Remove internal-only scoring fields from public claims.
        public_claims = [
            {
                key: value
                for key, value in claim.items()
                if not key.startswith("_")
            }
            for claim in claims
        ]

        return self.report_builder.build(
            claims=public_claims,
            verifications=verifications,
            contradictions=contradictions,
            source_quality=source_quality,
            applicability=applicability,
            confidence=confidence,
            limitations=limitations,
        )
