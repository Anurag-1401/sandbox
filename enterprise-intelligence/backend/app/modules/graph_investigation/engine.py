from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraversalResult:
    nodes: dict[str, Any] = field(default_factory=dict)
    edges: dict[str, Any] = field(default_factory=dict)

    # Node ID -> shortest path information
    paths: dict[str, dict] = field(default_factory=dict)


def calculate_priority(
    node_type: str,
    path_depth: int,
    evidence_count: int,
    contradiction_count: int,
    evidence_gap: bool,
) -> float:
    """
    Deterministic triage score.

    This is NOT a legal applicability probability.
    """

    type_weights = {
        "obligation": 35,
        "regulation": 25,
        "amendment": 35,
        "clause": 30,
        "standard": 25,
        "product": 20,
        "organization": 20,
        "authority": 10,
        "concept": 5,
    }

    score = type_weights.get(node_type, 5)

    # Nearer entities receive higher priority.
    score += max(0, 3 - path_depth) * 8

    # Contradicting evidence increases review urgency.
    score += min(contradiction_count * 12, 24)

    # Missing evidence is a review gap, not proof of non-compliance.
    if evidence_gap:
        score += 12

    # Supporting evidence improves traceability.
    if evidence_count:
        score += min(evidence_count * 3, 9)

    return round(min(max(score, 0), 100), 2)


def priority_label(score: float) -> str:

    if score >= 80:
        return "critical"

    if score >= 60:
        return "high"

    if score >= 35:
        return "medium"

    if score >= 15:
        return "low"

    return "informational"


def traverse_graph(
    root_nodes,
    edges,
    depth: int,
) -> TraversalResult:

    result = TraversalResult()

    adjacency = {}

    for edge in edges:

        adjacency.setdefault(
            str(edge.source_node_id),
            [],
        ).append(edge)

        adjacency.setdefault(
            str(edge.target_node_id),
            [],
        ).append(edge)

    queue = deque()

    for root in root_nodes:

        root_id = str(root.id)

        result.nodes[root_id] = root

        result.paths[root_id] = {
            "node_ids": [root_id],
            "edge_ids": [],
            "depth": 0,
        }

        queue.append((root_id, 0))

    while queue:

        current_id, current_depth = queue.popleft()

        if current_depth >= depth:
            continue

        for edge in adjacency.get(current_id, []):

            source_id = str(edge.source_node_id)
            target_id = str(edge.target_node_id)

            next_id = (
                target_id
                if source_id == current_id
                else source_id
            )

            edge_id = str(edge.id)

            result.edges[edge_id] = edge

            if next_id in result.paths:
                continue

            parent_path = result.paths[current_id]

            result.paths[next_id] = {
                "node_ids": (
                    parent_path["node_ids"] + [next_id]
                ),
                "edge_ids": (
                    parent_path["edge_ids"] + [edge_id]
                ),
                "depth": current_depth + 1,
            }

            queue.append(
                (next_id, current_depth + 1)
            )

    return result