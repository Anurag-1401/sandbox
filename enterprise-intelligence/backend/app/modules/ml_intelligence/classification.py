from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.modules.ml_intelligence.preprocessing import normalize_text
from app.modules.ml_intelligence.runtime import (
    ModelLoadError,
    load_text_classifier,
)


DOCUMENT_LABELS = [
    "act",
    "rule",
    "notification",
    "circular",
    "standard",
    "amendment",
    "policy",
    "audit_report",
    "contract",
    "other",
]

KEYWORDS = {
    "act": ["an act to", "be it enacted", "act, 20"],
    "rule": ["in exercise of the powers", "these rules may be called"],
    "notification": ["notification", "notifies the following"],
    "circular": ["circular", "all concerned are hereby informed"],
    "standard": ["indian standard", "is/iec", "iso standard", "bis standard"],
    "amendment": ["amendment", "substitution", "insertion", "omission"],
    "policy": ["policy document", "policy objectives", "scope of this policy"],
    "audit_report": ["audit findings", "audit observation", "non-conformity"],
    "contract": ["agreement is made", "hereinafter referred", "terms and conditions"],
}


class DocumentClassifier:
    def __init__(self):
        self.model_path = settings.ml_document_classifier_path

    def _baseline(self, text: str) -> dict:
        lower = text.lower()
        scores = {}

        for label, terms in KEYWORDS.items():
            scores[label] = float(
                sum(1 for term in terms if term in lower)
            )

        if not any(scores.values()):
            scores["other"] = 1.0

        total = sum(scores.values()) or 1.0
        normalized = {
            label: round(score / total, 4)
            for label, score in scores.items()
        }

        best = max(normalized, key=normalized.get)

        # The baseline is deliberately low-confidence.
        return {
            "label": best,
            "scores": normalized,
            "model_status": "keyword_baseline",
            "limitations": [
                "This is a keyword baseline, not a trained classifier.",
                "Documents may contain multiple legal instrument types. "
                "Human confirmation is recommended.",
            ],
        }

    def run(self, text: str) -> dict:
        text = normalize_text(text)[:settings.ml_max_text_chars]

        if not text:
            return {
                "label": "other",
                "scores": {"other": 1.0},
                "model_status": "empty_input",
                "limitations": ["No text was supplied."],
            }

        model_path = Path(self.model_path)

        if model_path.exists():
            try:
                model = load_text_classifier(str(model_path))
                probabilities = model.predict_proba([text])[0]
                labels = model.classes_

                scores = {
                    str(label): round(float(score), 4)
                    for label, score in zip(labels, probabilities)
                }

                return {
                    "label": max(scores, key=scores.get),
                    "scores": scores,
                    "model_status": "trained_classifier",
                    "limitations": [
                        "Prediction confidence is not guaranteed to be "
                        "calibrated. Review low-confidence classifications."
                    ],
                }
            except ModelLoadError as exc:
                baseline = self._baseline(text)
                baseline["limitations"].append(str(exc))
                return baseline
            except Exception:
                baseline = self._baseline(text)
                baseline["limitations"].append(
                    "Trained classifier failed; keyword baseline used."
                )
                return baseline

        return self._baseline(text)