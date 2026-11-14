from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.modules.ml_intelligence.preprocessing import normalize_text
from app.modules.ml_intelligence.runtime import (
    ModelLoadError,
    load_sentence_model,
)


class ClauseSimilarity:
    def __init__(self):
        self.model_name = settings.ml_sentence_transformer
        self.threshold = settings.ml_similarity_threshold

    @staticmethod
    def _tfidf_similarity(text_a: str, text_b: str) -> float:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        matrix = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        ).fit_transform([text_a, text_b])

        return float(cosine_similarity(matrix[0], matrix[1])[0][0])

    def compare(self, text_a: str, text_b: str) -> dict:
        a = normalize_text(text_a)
        b = normalize_text(text_b)

        if not a or not b:
            raise ValueError("Both clauses must contain text.")

        method = "tfidf"
        status = "lexical_baseline"
        limitations = [
            "Similarity is not a legal-equivalence or amendment verdict.",
            "Thresholds must be calibrated on labelled clause pairs.",
        ]

        try:
            model = load_sentence_model(self.model_name)
            vectors = model.encode(
                [a, b],
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            score = float(np.dot(vectors[0], vectors[1]))
            method = "sentence_transformer"
            status = "semantic_model"
        except (ModelLoadError, ImportError):
            score = self._tfidf_similarity(a, b)
        except Exception:
            score = self._tfidf_similarity(a, b)
            limitations.append(
                "Semantic model failed; TF-IDF fallback was used."
            )

        score = max(-1.0, min(1.0, score))

        if score >= self.threshold:
            relation = "candidate_near_duplicate"
        elif score >= 0.65:
            relation = "related_clause"
        else:
            relation = "low_similarity"

        return {
            "similarity": round(score, 4),
            "relation": relation,
            "method": method,
            "model_status": status,
            "limitations": limitations,
        }

    def compare_many(
        self,
        clauses: list[dict],
    ) -> list[dict]:
        results = []

        for index, left in enumerate(clauses):
            for right in clauses[index + 1:]:
                result = self.compare(
                    str(left["text"]),
                    str(right["text"]),
                )

                results.append({
                    "clause_a_id": left["id"],
                    "clause_b_id": right["id"],
                    **result,
                })

        return results