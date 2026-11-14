from __future__ import annotations

import re


FILTER_KEYS = {
    "industries",
    "products",
    "jurisdictions",
    "keywords",
}


def normalize(value: str) -> str:
    value = (value or "").casefold()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def evaluate_subscription_impact(
    *,
    filters: dict,
    title: str,
    extracted_text: str,
    authority: str,
    jurisdiction: str,
) -> dict:
    """
    Return a candidate relevance signal.

    A match means only that a human should inspect the publication.
    It does not establish regulatory applicability.
    """

    filters = filters or {}

    unknown = set(filters) - FILTER_KEYS
    if unknown:
        raise ValueError(
            f"Unsupported subscription filters: {sorted(unknown)}"
        )

    searchable = normalize(
        " ".join([
            title,
            extracted_text[:100000],
            authority,
            jurisdiction,
        ])
    )

    matched = []

    for key in FILTER_KEYS:
        terms = filters.get(key, [])

        if not isinstance(terms, list):
            raise ValueError(
                f"Filter '{key}' must be a list of strings."
            )

        for term in terms:
            if not isinstance(term, str) or not term.strip():
                continue

            normalized_term = normalize(term)

            if normalized_term and normalized_term in searchable:
                matched.append({
                    "filter": key,
                    "term": term,
                })

    configured = any(filters.get(key) for key in FILTER_KEYS)

    if not configured:
        return {
            "relevance_status": "untriaged",
            "potentially_relevant": True,
            "matched_terms": [],
            "reason": (
                "No organization relevance filters are configured. "
                "Manual triage is required."
            ),
        }

    if matched:
        return {
            "relevance_status": "candidate_relevant",
            "potentially_relevant": True,
            "matched_terms": matched,
            "reason": (
                "One or more organization filters matched the publication. "
                "This is a screening signal, not a legal applicability finding."
            ),
        }

    return {
        "relevance_status": "no_filter_match",
        "potentially_relevant": False,
        "matched_terms": [],
        "reason": (
            "No configured organization filters matched. "
            "This does not prove the publication is inapplicable."
        ),
    }