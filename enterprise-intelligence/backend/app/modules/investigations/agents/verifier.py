from __future__ import annotations

from app.modules.investigations.llm import InvestigationLLM
from app.modules.investigations.prompts import VERIFIER_PROMPT


class VerificationAgent:

    def __init__(self, llm: InvestigationLLM):
        self.llm = llm

    def run(
        self,
        *,
        question: str,
        findings: list[dict],
        comparisons: list[dict],
        evidence: list[dict],
    ) -> tuple[list[dict], list[str], list[str]]:

        valid_ids = {
            item["evidence_id"]
            for item in evidence
        }

        issues = []
        approved_finding_ids = []

        for finding in findings:
            valid_refs = [
                evidence_id
                for evidence_id in finding["evidence_ids"]
                if evidence_id in valid_ids
            ]

            finding["evidence_ids"] = valid_refs

            if not valid_refs:
                issues.append(
                    {
                        "issue_type": "unsupported_claim",
                        "description": (
                            "Finding has no valid evidence references."
                        ),
                        "finding_id": finding["finding_id"],
                        "evidence_ids": [],
                    }
                )

                finding["review_required"] = True
            else:
                approved_finding_ids.append(
                    finding["finding_id"]
                )

        for comparison in comparisons:
            comparison["evidence_ids"] = [
                evidence_id
                for evidence_id in comparison["evidence_ids"]
                if evidence_id in valid_ids
            ]

            if not comparison["evidence_ids"]:
                comparison["review_required"] = True

                issues.append(
                    {
                        "issue_type": "unsupported_comparison",
                        "description": (
                            "Comparison has no valid evidence references."
                        ),
                        "finding_id": None,
                        "evidence_ids": [],
                    }
                )

        # Send only a bounded evidence summary to the verification model.
        compact_evidence = [
            {
                "evidence_id": item["evidence_id"],
                "document_title": item["document_title"],
                "page_start": item["page_start"],
                "page_end": item["page_end"],
                "content": item["content"][:2500],
            }
            for item in evidence[:30]
        ]

        response = self.llm.generate_json(
            system_prompt=VERIFIER_PROMPT,
            user_prompt=(
                f"Question:\n{question}\n\n"
                f"Findings:\n{findings}\n\n"
                f"Comparisons:\n{comparisons}\n\n"
                f"Evidence:\n{compact_evidence}"
            ),
        )

        model_issues = response.get(
            "verification_issues",
            [],
        )

        if isinstance(model_issues, list):
            for issue in model_issues[:30]:
                if not isinstance(issue, dict):
                    continue

                refs = issue.get("evidence_ids", [])

                if not isinstance(refs, list):
                    refs = []

                issues.append(
                    {
                        "issue_type": str(
                            issue.get("issue_type", "review_required")
                        )[:100],
                        "description": str(
                            issue.get("description", "")
                        )[:2000],
                        "finding_id": (
                            str(issue["finding_id"])
                            if issue.get("finding_id")
                            else None
                        ),
                        "evidence_ids": [
                            str(ref)
                            for ref in refs
                            if str(ref) in valid_ids
                        ],
                    }
                )

        # Any issue referencing a finding forces human review.
        affected_finding_ids = {
            issue["finding_id"]
            for issue in issues
            if issue["finding_id"]
        }

        for finding in findings:
            if finding["finding_id"] in affected_finding_ids:
                finding["review_required"] = True

        limitations = response.get("limitations", [])

        if not isinstance(limitations, list):
            limitations = []

        return (
            issues,
            approved_finding_ids,
            [str(item)[:1000] for item in limitations[:20]],
        )