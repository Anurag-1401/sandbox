from __future__ import annotations

from app.modules.investigations.llm import InvestigationLLM
from app.modules.investigations.prompts import COMPARISON_PROMPT


ALLOWED_STATUSES = {
    "consistent",
    "conflict",
    "potential_gap",
    "insufficient_information",
}


class ComparisonAgent:

    def __init__(self, llm: InvestigationLLM):
        self.llm = llm

    def run(
        self,
        *,
        question: str,
        findings: list[dict],
        evidence: list[dict],
    ) -> tuple[list[dict], list[str]]:

        if not findings:
            return [], [
                "Comparison could not be performed because no findings were extracted."
            ]

        valid_evidence_ids = {
            item["evidence_id"]
            for item in evidence
        }

        response = self.llm.generate_json(
            system_prompt=COMPARISON_PROMPT,
            user_prompt=(
                f"Investigation question:\n{question}\n\n"
                f"Findings:\n{findings}\n\n"
                f"Available evidence IDs:\n{sorted(valid_evidence_ids)}"
            ),
        )

        comparisons = response.get("comparisons", [])

        if not isinstance(comparisons, list):
            comparisons = []

        normalized = []

        for item in comparisons[:30]:
            if not isinstance(item, dict):
                continue

            evidence_ids = item.get("evidence_ids", [])

            if not isinstance(evidence_ids, list):
                evidence_ids = []

            evidence_ids = [
                str(evidence_id)
                for evidence_id in evidence_ids
                if str(evidence_id) in valid_evidence_ids
            ]

            status = str(item.get("status", ""))

            if status not in ALLOWED_STATUSES:
                status = "insufficient_information"

            normalized.append(
                {
                    "topic": str(item.get("topic", ""))[:500],
                    "comparison": str(
                        item.get("comparison", "")
                    )[:4000],
                    "status": status,
                    "evidence_ids": evidence_ids,
                    "review_required": (
                        bool(item.get("review_required", False))
                        or status != "consistent"
                        or not evidence_ids
                    ),
                }
            )

        limitations = response.get("limitations", [])

        if not isinstance(limitations, list):
            limitations = []

        return normalized, [
            str(item)[:1000]
            for item in limitations[:20]
        ]