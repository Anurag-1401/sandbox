
from __future__ import annotations

from itertools import combinations

from app.modules.intelligence.prompts import CONTRADICTION_PROMPT


class ContradictionDetector:
    def __init__(
        self,
        llm,
        *,
        max_pairs: int = 80,
    ):
        self.llm = llm
        self.max_pairs = max_pairs

    def run(
        self,
        *,
        claims: list[dict],
        evidence: list[dict],
        existing_comparisons: list[dict] | None = None,
    ) -> tuple[list[dict], list[str]]:

        pairs = list(combinations(claims, 2))

        limitations = []

        if len(pairs) > self.max_pairs:
            pairs = pairs[:self.max_pairs]
            limitations.append(
                "Contradiction analysis was bounded to the first "
                f"{self.max_pairs} claim pairs."
            )

        if not pairs:
            return [], limitations

        valid_evidence_ids = {
            item["evidence_id"]
            for item in evidence
        }

        claim_payload = [
            {
                "claim_a_id": left["claim_id"],
                "claim_a": left["text"],
                "claim_a_entity": left.get("entity"),
                "claim_a_jurisdiction": left.get("jurisdiction"),
                "claim_a_time": left.get("temporal_scope"),
                "claim_b_id": right["claim_id"],
                "claim_b": right["text"],
                "claim_b_entity": right.get("entity"),
                "claim_b_jurisdiction": right.get("jurisdiction"),
                "claim_b_time": right.get("temporal_scope"),
            }
            for left, right in pairs
        ]

        evidence_payload = [
            {
                "evidence_id": item["evidence_id"],
                "document_title": item["document_title"],
                "version_number": item["version_number"],
                "page_start": item["page_start"],
                "page_end": item["page_end"],
                "content": item["content"][:2500],
            }
            for item in evidence[:30]
        ]

        response = self.llm.generate_json(
            system_prompt=CONTRADICTION_PROMPT,
            user_prompt=(
                f"Claim pairs:\n{claim_payload}\n\n"
                f"Evidence:\n{evidence_payload}\n\n"
                f"Existing comparisons:\n"
                f"{(existing_comparisons or [])[:30]}"
            ),
        )

        raw = response.get("contradictions", [])

        if not isinstance(raw, list):
            raw = []

        valid_claim_ids = {
            item["claim_id"]
            for item in claims
        }

        normalized = []
        seen_pairs = set()

        for item in raw[:self.max_pairs]:
            if not isinstance(item, dict):
                continue

            left = str(item.get("claim_a_id", ""))
            right = str(item.get("claim_b_id", ""))

            if (
                left not in valid_claim_ids
                or right not in valid_claim_ids
                or left == right
            ):
                continue

            pair_key = tuple(sorted((left, right)))

            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)

            evidence_ids = item.get("evidence_ids", [])

            if not isinstance(evidence_ids, list):
                evidence_ids = []

            evidence_ids = list(dict.fromkeys(
                str(value)
                for value in evidence_ids
                if str(value) in valid_evidence_ids
            ))

            severity = str(item.get("severity", "medium"))

            if severity not in {"high", "medium", "low"}:
                severity = "medium"

            # Without source evidence, a contradiction is not accepted.
            left_claim = next(
                item for item in claims
                if item["claim_id"] == left
            )
            
            right_claim = next(
                item for item in claims
                if item["claim_id"] == right
            )
            
            left_refs = set(left_claim["evidence_ids"])
            right_refs = set(right_claim["evidence_ids"])
            
            has_left_support = bool(set(evidence_ids) & left_refs)
            has_right_support = bool(set(evidence_ids) & right_refs)
            
            if not has_left_support or not has_right_support:
                limitations.append(
                    f"Potential contradiction between {left} and {right} "
                    "was not accepted because two valid evidence references "
                    "were not returned."
                )
                continue

            normalized.append({
                "contradiction_id": f"X{len(normalized) + 1}",
                "claim_a_id": left,
                "claim_b_id": right,
                "description": str(
                    item.get("description", "")
                )[:4000],
                "severity": severity,
                "evidence_ids": evidence_ids,
                "temporal_conflict": bool(
                    item.get("temporal_conflict", False)
                ),
                "resolution_status": "unresolved",
            })

        return normalized, limitations
