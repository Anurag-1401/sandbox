from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.investigations.graph.workflow import (
    build_investigation_graph,
)
from app.modules.investigations.repository import (
    InvestigationRepository,
)
from app.modules.investigations.llm import (
    get_investigation_llm,
)
from app.modules.search.dependencies import (
    get_retrieval_service,
)
from app.modules.intelligence.service import IntelligenceService
from app.modules.ml_intelligence.service import MLIntelligenceService


class InvestigationService:

    def __init__(
        self,
        repository: InvestigationRepository | None = None,
        intelligence_service: IntelligenceService | None = None,
        ml_service: MLIntelligenceService | None = None,
    ):
        self.repository = (
            repository or InvestigationRepository()
        )
        self.intelligence_service = intelligence_service
        self.ml_service = ml_service or MLIntelligenceService()

    def create(
        self,
        db,
        *,
        organization_id: UUID,
        user_id: UUID,
        title: str,
        question: str,
        scope: dict,
    ):
        return self.repository.create_investigation(
            db,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            question=question,
            scope=scope,
        )

    def _get_intelligence_service(self):
        if self.intelligence_service is None:
            llm = get_investigation_llm()
            self.intelligence_service = IntelligenceService(llm=llm)

        return self.intelligence_service

    def execute(
        self,
        db,
        *,
        investigation,
        run,
        user_id: UUID,
        allowed_document_ids: set[UUID],
    ) -> dict:

        llm = get_investigation_llm()
        retrieval = get_retrieval_service()

        selected_document_ids = set(
            investigation.scope.get("document_ids", [])
        )

        if selected_document_ids:
            selected_document_ids = {
                UUID(str(item))
                for item in selected_document_ids
            }

            if not selected_document_ids.issubset(
                allowed_document_ids
            ):
                raise PermissionError(
                    "Investigation contains inaccessible documents."
                )

        state = {
            "investigation_id": str(investigation.id),
            "run_id": str(run.id),
            "organization_id": str(investigation.organization_id),
            "user_id": str(user_id),
            "title": investigation.title,
            "question": investigation.question,
            "scope": investigation.scope,
            "allowed_document_ids": [
                str(item)
                for item in allowed_document_ids
            ],
            "selected_document_ids": [
                str(item)
                for item in selected_document_ids
            ],
            "status": "queued",
            "tasks": [],
            "evidence": [],
            "findings": [],
            "comparisons": [],
            "verification_issues": [],
            "summary": "",
            "limitations": [],
            "final_report": {},
            "errors": [],
        }

        graph = build_investigation_graph(
            db=db,
            run=run,
            investigation=investigation,
            repository=self.repository,
            llm=llm,
            retrieval_service=retrieval,
        )

        try:
            # M4: controlled LangGraph investigation workflow.
            result = graph.invoke(state)

            final_report = result.get("final_report", {})

            if not final_report:
                raise RuntimeError(
                    "Investigation workflow produced no final report."
                )

            findings = result.get("findings", [])
            evidence = result.get("evidence", [])
            comparisons = result.get("comparisons", [])
            scope = result.get("scope", investigation.scope)

            # M5: evidence-grounded claim intelligence.
            intelligence = self._get_intelligence_service().run(
                question=investigation.question,
                findings=findings,
                evidence=evidence,
                comparisons=comparisons,
                scope=scope,
            )

            final_report["intelligence"] = intelligence

            # M6: ML-derived signals. These do not change M5 verdicts.
            ml_enrichment = self.ml_service.enrich_investigation(
                findings=findings,
                evidence=evidence,
                existing_intelligence=intelligence,
            )

            final_report["model_intelligence"] = ml_enrichment

            # Preserve all original workflow limitations.
            combined_limitations = list(
                final_report.get("limitations", [])
            )
            combined_limitations.extend(
                intelligence.get("limitations", [])
            )
            combined_limitations.extend(
                ml_enrichment.get("limitations", [])
            )

            final_report["limitations"] = list(
                dict.fromkeys(combined_limitations)
            )

            final_report["human_review_required"] = bool(
                final_report.get("human_review_required", False)
                or intelligence.get("human_review_required", False)
                or ml_enrichment.get("human_review_required", False)
            )

            final_report["milestone_versions"] = {
                "investigation_engine": "M4",
                "intelligence": "M5",
                "model_intelligence": "M6",
            }

            # Keep the graph state and complete report in the existing
            # JSON columns. No new database schema is necessary.
            result["final_report"] = final_report
            result["intelligence"] = intelligence
            result["model_intelligence"] = ml_enrichment

            self.repository.update_run(
                db,
                run=run,
                status="review_required",
                state=result,
                result=final_report,
                completed=True,
            )

            investigation.status = "review_required"

            self.repository.add_event(
                db,
                run=run,
                event_type="run_completed",
                description=(
                    "Investigation, intelligence verification, and "
                    "model enrichment completed. Human review is required."
                ),
                payload={
                    "m5_claim_count": len(
                        intelligence.get("claims", [])
                    ),
                    "m6_entity_count": len(
                        ml_enrichment.get("entities", [])
                    ),
                    "m6_obligation_count": len(
                        ml_enrichment.get("obligations", [])
                    ),
                    "m6_clause_signal_count": len(
                        ml_enrichment.get("clause_signals", [])
                    ),
                },
                actor_id=user_id,
            )

            db.commit()
            return final_report

        except Exception as exc:
            db.rollback()

            run = self.repository.get_run(
                db,
                run_id=run.id,
                organization_id=investigation.organization_id,
            )

            investigation = self.repository.get_investigation(
                db,
                investigation_id=investigation.id,
                organization_id=investigation.organization_id,
            )

            if run is not None:
                self.repository.update_run(
                    db,
                    run=run,
                    status="failed",
                    error_message=(
                        "Investigation execution failed. "
                        "Check server logs for diagnostic details."
                    ),
                    completed=True,
                )

                self.repository.add_event(
                    db,
                    run=run,
                    event_type="run_failed",
                    description="Investigation execution failed.",
                    payload={
                        "error_type": type(exc).__name__,
                    },
                    actor_id=user_id,
                )

            if investigation is not None:
                investigation.status = "failed"

            db.commit()
            raise

    def review(
        self,
        db,
        *,
        investigation,
        run,
        reviewer_id: UUID,
        decision: str,
        comments: str,
    ) -> None:

        if run.status != "review_required":
            raise ValueError(
                "Only investigations awaiting review can be reviewed."
            )

        if decision == "approve":
            run.status = "approved"
            investigation.status = "approved"
            event_type = "review_approved"
            description = "Investigation approved by reviewer."

        elif decision == "reject":
            run.status = "rejected"
            investigation.status = "rejected"
            event_type = "review_rejected"
            description = "Investigation rejected by reviewer."

        elif decision == "request_changes":
            investigation.status = "draft"
            event_type = "changes_requested"
            description = "Reviewer requested further investigation."

        else:
            raise ValueError("Unsupported review decision.")

        self.repository.add_event(
            db,
            run=run,
            event_type=event_type,
            description=description,
            payload={
                "comments": comments,
                "decision": decision,
            },
            actor_id=reviewer_id,
        )

        db.commit()