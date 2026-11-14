from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Hashable


def _validate_k(k: int) -> None:
    if k <= 0:
        raise ValueError("k must be greater than zero")


def precision_at_k(
    ranked_ids: Sequence[Hashable],
    relevant_ids: set[Hashable],
    k: int,
) -> float:
    _validate_k(k)

    retrieved = ranked_ids[:k]

    if not retrieved:
        return 0.0

    relevant_count = sum(
        1 for item in retrieved if item in relevant_ids
    )

    return relevant_count / k


def recall_at_k(
    ranked_ids: Sequence[Hashable],
    relevant_ids: set[Hashable],
    k: int,
) -> float:
    _validate_k(k)

    if not relevant_ids:
        return 0.0

    retrieved = ranked_ids[:k]

    relevant_count = sum(
        1 for item in retrieved if item in relevant_ids
    )

    return relevant_count / len(relevant_ids)


def reciprocal_rank(
    ranked_ids: Sequence[Hashable],
    relevant_ids: set[Hashable],
) -> float:
    for position, item in enumerate(ranked_ids, start=1):
        if item in relevant_ids:
            return 1.0 / position

    return 0.0


def mean_reciprocal_rank(
    rankings: Sequence[Sequence[Hashable]],
    relevant_sets: Sequence[set[Hashable]],
) -> float:
    if len(rankings) != len(relevant_sets):
        raise ValueError(
            "Each ranking must have a corresponding relevant set"
        )

    if not rankings:
        return 0.0

    scores = [
        reciprocal_rank(ranking, relevant)
        for ranking, relevant in zip(rankings, relevant_sets)
    ]

    return sum(scores) / len(scores)


def dcg_at_k(
    ranked_ids: Sequence[Hashable],
    relevance: Mapping[Hashable, int],
    k: int,
) -> float:
    _validate_k(k)

    score = 0.0

    for position, item in enumerate(ranked_ids[:k], start=1):
        grade = relevance.get(item, 0)

        if grade < 0:
            raise ValueError("Relevance grades cannot be negative")

        gain = (2**grade) - 1
        discount = math.log2(position + 1)

        score += gain / discount

    return score


def ndcg_at_k(
    ranked_ids: Sequence[Hashable],
    relevance: Mapping[Hashable, int],
    k: int,
) -> float:
    actual_dcg = dcg_at_k(
        ranked_ids,
        relevance,
        k,
    )

    ideal_ids = sorted(
        relevance,
        key=lambda item: relevance[item],
        reverse=True,
    )

    ideal_dcg = dcg_at_k(
        ideal_ids,
        relevance,
        k,
    )

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def evaluate_retrieval(
    ranked_ids: Sequence[Hashable],
    relevant_ids: set[Hashable],
    k: int = 10,
) -> dict[str, float]:
    binary_relevance = {
        item: 1
        for item in relevant_ids
    }

    return {
        f"precision@{k}": precision_at_k(
            ranked_ids,
            relevant_ids,
            k,
        ),
        f"recall@{k}": recall_at_k(
            ranked_ids,
            relevant_ids,
            k,
        ),
        "mrr": reciprocal_rank(
            ranked_ids,
            relevant_ids,
        ),
        f"ndcg@{k}": ndcg_at_k(
            ranked_ids,
            binary_relevance,
            k,
        ),
    }