from __future__ import annotations

from app.core.config import settings
from app.modules.ml_intelligence.preprocessing import normalize_text
from app.modules.ml_intelligence.runtime import (
    ModelLoadError,
    load_nli_pipeline,
)


class NLIService:
    LABEL_ALIASES = {
        "entailment": "entailment",
        "contradiction": "contradiction",
        "neutral": "neutral",
        "label_0": "contradiction",
        "label_1": "neutral",
        "label_2": "entailment",
    }

    def run(self, premise: str, hypothesis: str) -> dict:
        premise = normalize_text(premise)
        hypothesis = normalize_text(hypothesis)

        if not premise or not hypothesis:
            raise ValueError("Premise and hypothesis are required.")

        if not settings.ml_nli_model_path:
            return {
                "label": "unavailable",
                "scores": {},
                "model_status": "not_configured",
                "limitations": [
                    "No NLI model is configured. No NLI verdict was produced."
                ],
            }

        try:
            classifier = load_nli_pipeline(
                settings.ml_nli_model_path
            )

            raw = classifier({
                "text": premise,
                "text_pair": hypothesis,
            })

            # Transformers versions may return either a list of
            # dictionaries or a nested list.
            if raw and isinstance(raw[0], list):
                raw = raw[0]

            scores = {}
            for item in raw:
                original = str(item["label"]).lower()
                label = self.LABEL_ALIASES.get(original)

                if label:
                    scores[label] = float(item["score"])

            if not scores:
                raise ValueError(
                    "Configured NLI model returned unknown labels."
                )

            label = max(scores, key=scores.get)

            return {
                "label": label,
                "scores": scores,
                "model_status": "configured_nli_model",
                "limitations": [
                    "Scores are model outputs and may not be calibrated "
                    "probabilities.",
                    "NLI output is a review signal, not a legal conclusion.",
                ],
            }

        except ModelLoadError as exc:
            return {
                "label": "unavailable",
                "scores": {},
                "model_status": "load_error",
                "limitations": [str(exc)],
            }
        except Exception:
            return {
                "label": "unavailable",
                "scores": {},
                "model_status": "inference_error",
                "limitations": [
                    "NLI inference failed. No verdict should be inferred."
                ],
            }