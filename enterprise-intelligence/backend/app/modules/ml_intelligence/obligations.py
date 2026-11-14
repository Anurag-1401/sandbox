from __future__ import annotations

import re

from app.modules.ml_intelligence.preprocessing import (
    normalize_text,
    split_sentences,
)


MANDATORY = re.compile(
    r"\b(shall|must|required to|is required to|are required to)\b",
    re.IGNORECASE,
)

PROHIBITION = re.compile(
    r"\b(shall not|must not|prohibited|may not|is forbidden)\b",
    re.IGNORECASE,
)

PERMISSION = re.compile(
    r"\b(may|permitted to|is allowed to)\b",
    re.IGNORECASE,
)

DEADLINE = re.compile(
    r"\b(within\s+\d+\s+(?:days?|weeks?|months?)|"
    r"before\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"on or before\s+[^,.;]+|"
    r"by\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    re.IGNORECASE,
)

PENALTY = re.compile(
    r"\b(fine|penalty|imprisonment|liable to|punishable)\b"
    r"[^.;]{0,180}",
    re.IGNORECASE,
)

PARTY = re.compile(
    r"\b(the manufacturer|manufacturer|importer|producer|"
    r"distributor|licensee|employer|company|occupier|"
    r"applicant|establishment|person)\b",
    re.IGNORECASE,
)


class ObligationExtractor:
    def run(self, text: str) -> dict:
        text = normalize_text(text)
        results = []
        seen = set()

        for sentence in split_sentences(text):
            modality = None
            obligation_type = None

            prohibition = PROHIBITION.search(sentence)
            mandatory = MANDATORY.search(sentence)
            permission = PERMISSION.search(sentence)

            if prohibition:
                modality = prohibition.group(1).lower()
                obligation_type = "prohibition"
            elif mandatory:
                modality = mandatory.group(1).lower()
                obligation_type = "mandatory"
            elif permission:
                modality = permission.group(1).lower()
                obligation_type = "permission"

            deadline_match = DEADLINE.search(sentence)
            penalty_match = PENALTY.search(sentence)
            party_match = PARTY.search(sentence)

            # A sentence with a deadline or penalty is retained as a
            # regulatory signal even when it has no explicit modal verb.
            if not obligation_type and deadline_match:
                obligation_type = "deadline"
                modality = "deadline_reference"
            elif not obligation_type and penalty_match:
                obligation_type = "penalty"
                modality = "penalty_reference"

            if not obligation_type:
                continue

            key = (sentence.lower(), obligation_type)
            if key in seen:
                continue
            seen.add(key)

            start = text.find(sentence)
            end = start + len(sentence)

            results.append({
                "text": sentence,
                "obligation_type": obligation_type,
                "modality": modality or "unknown",
                "start": start,
                "end": end,
                "deadline_text": (
                    deadline_match.group(0)
                    if deadline_match else None
                ),
                "responsible_party": (
                    party_match.group(0)
                    if party_match else None
                ),
                "penalty_text": (
                    penalty_match.group(0)
                    if penalty_match else None
                ),
                "confidence": 0.65 if modality else 0.45,
                "source": "rule",
            })

        return {
            "obligations": results,
            "limitations": [
                "Extracted obligations are candidate signals, not legal advice.",
                "Relative deadlines require a verified triggering event and "
                "effective-date context before calendar-date calculation.",
                "The responsible party is extracted only when an explicit "
                "party pattern is found.",
            ],
        }