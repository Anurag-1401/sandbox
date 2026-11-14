from __future__ import annotations

from app.core.config import settings
from app.modules.ml_intelligence.classification import DocumentClassifier
from app.modules.ml_intelligence.ner import RegulatoryNER
from app.modules.ml_intelligence.nli import NLIService
from app.modules.ml_intelligence.obligations import ObligationExtractor
from app.modules.ml_intelligence.similarity import ClauseSimilarity


class MLIntelligenceService:
    def __init__(self):
        self.ner = RegulatoryNER()
        self.classifier = DocumentClassifier()
        self.obligations = ObligationExtractor()
        self.similarity = ClauseSimilarity()
        self.nli = NLIService()

    def extract_entities(self, text: str) -> dict:
        return self.ner.run(text)

    def classify_document(self, text: str) -> dict:
        return self.classifier.run(text)

    def extract_obligations(self, text: str) -> dict:
        return self.obligations.run(text)

    def compare_clauses(self, text_a: str, text_b: str) -> dict:
        return self.similarity.compare(text_a, text_b)

    def verify_nli(self, premise: str, hypothesis: str) -> dict:
        return self.nli.run(premise, hypothesis)

        def evaluate_claims_with_nli(
        self,
        *,
        claims: list[dict],
        evidence: list[dict],
        max_pairs: int = 100,
    ) -> list[dict]:
            evidence_by_id = {
            str(item.get("evidence_id")): item
            for item in evidence
            if item.get("evidence_id")
        }

        signals = []

        for claim in claims:
            claim_id = str(claim.get("claim_id", ""))
            claim_text = str(claim.get("text", "")).strip()

            if not claim_id or not claim_text:
                continue

            for evidence_id in claim.get("evidence_ids", []):
                if len(signals) >= max_pairs:
                    return signals

                source = evidence_by_id.get(str(evidence_id))
                if source is None:
                    continue

                premise = str(source.get("content", "")).strip()

                if not premise:
                    continue

                result = self.verify_nli(
                    premise=premise,
                    hypothesis=claim_text,
                )

                signals.append({
                    "claim_id": claim_id,
                    "evidence_id": str(evidence_id),
                    "label": result["label"],
                    "scores": result["scores"],
                    "model_status": result["model_status"],
                    "limitations": result["limitations"],
                })

        return signals

    def enrich_investigation(
        self,
        *,
        findings: list[dict],
        evidence: list[dict],
        existing_intelligence: dict | None,
    ) -> dict:
        entities = []
        obligations = []
        limitations = []

        # Evidence is the primary source for extraction. Finding statements
        # are included as additional context but retain their own provenance.
        for item in evidence:
            evidence_id = str(item.get("evidence_id", ""))
            text = str(item.get("content", ""))

            if not text.strip():
                continue

            ner_result = self.extract_entities(text)
            obligation_result = self.extract_obligations(text)

            for entity in ner_result["entities"]:
                entities.append({
                    **entity,
                    "evidence_id": evidence_id,
                    "document_id": item.get("document_id"),
                    "page_start": item.get("page_start"),
                    "page_end": item.get("page_end"),
                })

            for obligation in obligation_result["obligations"]:
                obligations.append({
                    **obligation,
                    "evidence_id": evidence_id,
                    "document_id": item.get("document_id"),
                    "page_start": item.get("page_start"),
                    "page_end": item.get("page_end"),
                })

            limitations.extend(ner_result["limitations"])
            limitations.extend(obligation_result["limitations"])

        # Only compare clauses when they have evidence-backed source text.
        # This first version does not infer that a clause was amended.
        clause_signals = []
        seen_pairs = set()

        for index, left in enumerate(evidence):
            left_text = str(left.get("content", "")).strip()
            if not left_text:
                continue

            for right in evidence[index + 1:]:
                right_text = str(right.get("content", "")).strip()
                if not right_text:
                    continue

                left_id = str(left.get("evidence_id", ""))
                right_id = str(right.get("evidence_id", ""))

                pair = tuple(sorted((left_id, right_id)))
                if not left_id or not right_id or pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                # Avoid quadratic processing of very large evidence sets.
                if len(clause_signals) >= 100:
                    limitations.append(
                        "Clause comparison was capped at 100 pairs."
                    )
                    break

                try:
                    comparison = self.compare_clauses(
                        left_text,
                        right_text,
                    )
                except Exception:
                    continue

                if comparison["relation"] != "low_similarity":
                    clause_signals.append({
                        "evidence_a_id": left_id,
                        "evidence_b_id": right_id,
                        **comparison,
                    })

        if not evidence:
            limitations.append(
                "No evidence records were available for ML enrichment."
            )

        if existing_intelligence is None:
            limitations.append(
                "M5 intelligence was not supplied; M6 enrichment is "
                "not a replacement for M5 verification."
            )

                # Classify each source document using its retrieved evidence text.
        document_texts: dict[str, list[str]] = {}

        for item in evidence:
            document_id = str(item.get("document_id", ""))
            content = str(item.get("content", "")).strip()

            if document_id and content:
                document_texts.setdefault(document_id, []).append(content)

        document_classifications = []

        for document_id, contents in document_texts.items():
            combined_text = "\n\n".join(contents)

            classification = self.classify_document(combined_text)

            document_classifications.append({
                "document_id": document_id,
                **classification,
                "classification_scope": "retrieved_evidence_only",
            })

        nli_signals = self.evaluate_claims_with_nli(
            claims=(
                existing_intelligence.get("claims", [])
                if existing_intelligence
                else []
            ),
            evidence=evidence,
        )

        return {
            "schema_version": "1.0",
            "entities": entities,
            "obligations": obligations,
            "clause_signals": clause_signals,
            "limitations": list(dict.fromkeys(limitations)),
            "human_review_required": bool(
                entities or obligations or clause_signals
            ),
            "source_evidence_count": len(evidence),
            "source_finding_count": len(findings),
            "configuration": {
                "similarity_threshold": settings.ml_similarity_threshold,
                "transformers_enabled": settings.ml_enable_transformers,
            },
            "document_classifications": document_classifications,
            "nli_signals": nli_signals,
        }