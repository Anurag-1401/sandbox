
from __future__ import annotations

from datetime import datetime, timezone


AUTHORITY_SCORES = {
    "official_regulator": 1.00,
    "legislation": 1.00,
    "court": 1.00,
    "official_government": 0.95,
    "internal_approved": 0.85,
    "internal_unverified": 0.55,
    "industry_association": 0.70,
    "secondary": 0.50,
    "unknown": None,
}


class SourceReliabilityScorer:
    def score(
        self,
        *,
        evidence: list[dict],
        source_registry: dict | None = None,
        freshness_window_days: int = 1095,
    ) -> list[dict]:

        source_registry = source_registry or {}

        documents = {}

        for item in evidence:
            document_id = item["document_id"]

            if document_id not in documents:
                documents[document_id] = item

        results = []

        for document_id, item in documents.items():
            metadata = source_registry.get(document_id, {})

            if not isinstance(metadata, dict):
                metadata = {}

            authority_level = str(
                metadata.get("authority_level", "unknown")
            ).lower()

            if authority_level not in AUTHORITY_SCORES:
                authority_level = "unknown"

            authority_score = AUTHORITY_SCORES[authority_level]

            provenance_score = self._provenance_score(item)

            freshness_score = self._freshness_score(
                metadata.get("published_at"),
                freshness_window_days,
            )

            components = [
                (authority_score, 0.50),
                (provenance_score, 0.30),
                (freshness_score, 0.20),
            ]

            available = [
                (score, weight)
                for score, weight in components
                if score is not None
            ]

            total_weight = sum(
                weight for _, weight in available
            )

            quality_score = (
                sum(
                    score * weight
                    for score, weight in available
                ) / total_weight
                if total_weight
                else 0.0
            )

            notes = []

            if authority_score is None:
                notes.append(
                    "Issuing authority has not been verified."
                )

            if freshness_score is None:
                notes.append(
                    "Publication date is unavailable."
                )

            if provenance_score < 1.0:
                notes.append(
                    "Document provenance metadata is incomplete."
                )

            results.append({
                "document_id": document_id,
                "document_title": item["document_title"],
                "authority_level": authority_level,
                "authority_score": authority_score,
                "provenance_score": round(provenance_score, 4),
                "freshness_score": (
                    round(freshness_score, 4)
                    if freshness_score is not None
                    else None
                ),
                "quality_score": round(quality_score, 4),
                "assessment_notes": notes,
            })

        return results

    @staticmethod
    def _provenance_score(item: dict) -> float:
        checks = [
            bool(item.get("document_id")),
            bool(item.get("version_id")),
            bool(item.get("chunk_id")),
            bool(item.get("document_title")),
            isinstance(item.get("page_start"), int),
            isinstance(item.get("page_end"), int),
        ]

        return sum(checks) / len(checks)

    @staticmethod
    def _freshness_score(
        published_at,
        freshness_window_days: int,
    ) -> float | None:

        if not published_at:
            return None

        try:
            published = datetime.fromisoformat(
                str(published_at).replace("Z", "+00:00")
            )

            if published.tzinfo is None:
                published = published.replace(
                    tzinfo=timezone.utc
                )

            age_days = max(
                0,
                (
                    datetime.now(timezone.utc) - published
                ).days,
            )

            if freshness_window_days <= 0:
                return None

            return max(
                0.0,
                1.0 - age_days / freshness_window_days,
            )

        except (ValueError, TypeError):
            return None
