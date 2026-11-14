from __future__ import annotations

import re

from app.core.config import settings
from app.modules.ml_intelligence.preprocessing import normalize_text
from app.modules.ml_intelligence.runtime import (
    ModelLoadError,
    load_token_classifier,
)
from app.modules.ml_intelligence.schemas import EntityResult


PATTERNS: dict[str, list[str]] = {
    "DATE": [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
    ],
    "STANDARD": [
        r"\bIS\s*[:\-]?\s*\d{3,6}(?:\s*:\s*\d{4})?\b",
        r"\bISO\s*\d{3,6}(?:-\d+)*\b",
        r"\bIEC\s*\d{3,6}(?:-\d+)*\b",
        r"\bBIS\s+(?:standard|certification)\b",
    ],
    "REGULATION": [
        r"\b(?:Act|Rules|Regulations|Notification|Circular)\s*,?\s*\d{4}\b",
        r"\b(?:Companies Act|Consumer Protection Act|Environment Protection Act)\s*,?\s*\d{4}\b",
        r"\bG\.S\.R\.\s*\d+(?:\(E\))?\b",
        r"\bS\.O\.\s*\d+(?:\(E\))?\b",
    ],
    "CLAUSE": [
        r"\b(?:Section|Rule|Regulation|Clause|Article)\s+\d+[A-Za-z]?(?:\([0-9A-Za-z]+\))*\b",
    ],
    "JURISDICTION": [
        r"\b(?:India|Maharashtra|Karnataka|Delhi|Tamil Nadu|"
        r"United States|European Union|United Kingdom)\b",
    ],
    "AUTHORITY": [
        r"\b(?:Bureau of Indian Standards|BIS|Ministry of Corporate Affairs|"
        r"MCA|Central Pollution Control Board|CPCB|"
        r"Ministry of Environment|MoEFCC|FSSAI|RBI|SEBI)\b",
    ],
    "PENALTY": [
        r"\b(?:fine|penalty|imprisonment|imprisonable)\b"
        r".{0,100}?(?:Rs\.?|INR|rupees)?\s*[\d,]+(?:\.\d+)?",
        r"\b(?:Rs\.?|INR)\s*[\d,]+(?:\.\d+)?\b",
    ],
    "PRODUCT": [
        r"\b(?:electronic|electrical|industrial|consumer)\s+"
        r"(?:equipment|product|appliance|device)s?\b",
    ],
}


class RegulatoryNER:
    def __init__(self):
        self.model_path = settings.ml_ner_model_path

    def _rule_entities(self, text: str) -> list[EntityResult]:
        found: dict[tuple[int, int, str], EntityResult] = {}

        for label, patterns in PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    key = (match.start(), match.end(), label)
                    found[key] = EntityResult(
                        text=match.group(0),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        score=None,
                        source="rule",
                    )

        return sorted(
            found.values(),
            key=lambda item: (item.start, item.end),
        )

    def run(self, text: str) -> dict:
        text = normalize_text(text)[:settings.ml_max_text_chars]

        if not text:
            return {
                "entities": [],
                "model_status": "empty_input",
                "limitations": ["No text was supplied."],
            }

        entities = self._rule_entities(text)
        limitations = [
            "Rule-based entity patterns are a baseline and may miss "
            "entities or incorrectly classify ambiguous text.",
            "Product and organization recognition requires domain-labelled "
            "training data for reliable results.",
        ]
        status = "rule_baseline"

        if self.model_path and settings.ml_enable_transformers:
            try:
                classifier = load_token_classifier(self.model_path)
                predictions = classifier(text)

                for item in predictions:
                    start = int(item["start"])
                    end = int(item["end"])
                    if start < 0 or end > len(text) or end <= start:
                        continue

                    entities.append(
                        EntityResult(
                            text=text[start:end],
                            label=str(item["entity_group"]).upper(),
                            start=start,
                            end=end,
                            score=float(item["score"]),
                            source="model",
                        )
                    )

                status = "transformer_plus_rules"
            except ModelLoadError as exc:
                limitations.append(str(exc))
            except Exception:
                limitations.append(
                    "Transformer inference failed; rule-based output retained."
                )

        # Remove exact duplicate spans while preserving model predictions.
        unique = {}
        for item in entities:
            key = (item.start, item.end, item.label)
            previous = unique.get(key)
            if previous is None or (
                item.source == "model" and previous.source == "rule"
            ):
                unique[key] = item

        return {
            "entities": [
                item.model_dump()
                for item in sorted(
                    unique.values(),
                    key=lambda value: (value.start, value.end),
                )
            ],
            "model_status": status,
            "limitations": limitations,
        }