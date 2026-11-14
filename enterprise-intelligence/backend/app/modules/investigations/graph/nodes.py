from __future__ import annotations

from datetime import datetime, timezone

from app.modules.investigations.agents.planner import PlannerAgent
from app.modules.investigations.agents.researcher import ResearchAgent
from app.modules.investigations.agents.document_analyst import (
    DocumentAnalystAgent,
)
from app.modules.investigations.agents.comparator import ComparisonAgent
from app.modules.investigations.agents.verifier import VerificationAgent
from app.modules.investigations.repository import InvestigationRepository


class InvestigationNodes:

    def __init__(
        self,
        *,
        db,
        run,
        investigation,
        repository: InvestigationRepository,
        llm,
        retrieval_service,
    ):
        self.db = db
        self.run = run
        self.investigation = investigation
        self.repository = repository

        self.planner = PlannerAgent(llm)
        self.researcher = ResearchAgent(retrieval_service)
        self.analyst = DocumentAnalystAgent(llm)
        self.comparator = ComparisonAgent(llm)
        self.verifier = VerificationAgent(llm)

    def _persist(
        self,
        state: dict,
        *,
        status: str,
        event_type: str,
        description: str,
        updates: dict,
    ) -> dict:

        merged = dict(state)
        merged.update(updates)
        merged["status"] = status

        self.repository.update_run(
            self.db,
            run=self.run,
            status=status,
            state=merged,
        )

        self.investigation.status = status

        self.repository.add_event(
            self.db,
            run=self.run,
            event_type=event_type,
            description=description,
            payload={
                "status": status,
            },
        )

        self.db.commit()

        return updates

    def plan(self, state: dict) -> dict:
        tasks, limitations = self.planner.run(
            question=state["question"],
            scope=state.get("scope", {}),
        )

        return self._persist(
            state,
            status="planning",
            event_type="planning_completed",
            description="Investigation research plan generated.",
            updates={
                "tasks": tasks,
                "limitations": limitations,
            },
        )

    def research(self, state: dict) -> dict:
        evidence = self.researcher.run(
            db=self.db,
            organization_id=state["organization_id"],
            allowed_document_ids={
                __import__("uuid").UUID(item)
                for item in state["allowed_document_ids"]
            },
            selected_document_ids={
                __import__("uuid").UUID(item)
                for item in state.get("selected_document_ids", [])
            },
            tasks=state["tasks"],
        )

        return self._persist(
            state,
            status="researching",
            event_type="research_completed",
            description="Research retrieval completed.",
            updates={
                "evidence": evidence,
            },
        )

    def analyze(self, state: dict) -> dict:
        result = self.analyst.run(
            question=state["question"],
            evidence=state.get("evidence", []),
        )

        return self._persist(
            state,
            status="analyzing",
            event_type="analysis_completed",
            description="Document analysis completed.",
            updates={
                "findings": result["findings"],
                "summary": result["summary"],
                "limitations": (
                    state.get("limitations", [])
                    + result["limitations"]
                ),
            },
        )

    def compare(self, state: dict) -> dict:
        comparisons, limitations = self.comparator.run(
            question=state["question"],
            findings=state.get("findings", []),
            evidence=state.get("evidence", []),
        )

        return self._persist(
            state,
            status="comparing",
            event_type="comparison_completed",
            description="Finding comparison completed.",
            updates={
                "comparisons": comparisons,
                "limitations": (
                    state.get("limitations", [])
                    + limitations
                ),
            },
        )

    def verify(self, state: dict) -> dict:
        issues, approved_ids, limitations = self.verifier.run(
            question=state["question"],
            findings=state.get("findings", []),
            comparisons=state.get("comparisons", []),
            evidence=state.get("evidence", []),
        )

        findings = state.get("findings", [])

        review_required = (
            bool(issues)
            or any(
                finding["review_required"]
                for finding in findings
            )
            or any(
                comparison["review_required"]
                for comparison in state.get("comparisons", [])
            )
        )

        final_status = "review_required"

        report = {
            "title": state["title"],
            "question": state["question"],
            "summary": state.get("summary", ""),
            "findings": findings,
            "comparisons": state.get("comparisons", []),
            "evidence": state.get("evidence", []),
            "verification_issues": issues,
            "approved_finding_ids": approved_ids,
            "limitations": (
                state.get("limitations", []) + limitations
            ),
            "human_review_required": review_required,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return self._persist(
            state,
            status=final_status,
            event_type="verification_completed",
            description=(
                "Verification completed. Human review is required "
                "before the investigation can be approved."
            ),
            updates={
                "verification_issues": issues,
                "final_report": report,
                "limitations": report["limitations"],
            },
        )