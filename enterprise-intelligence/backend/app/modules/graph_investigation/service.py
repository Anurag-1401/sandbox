from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.knowledge_graph import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeGraphEvidence,
)

from app.models.graph_investigation import (
    GraphInvestigationRun,
    GraphInvestigationFinding,
)

from app.modules.graph_investigation.engine import (
    traverse_graph,
    calculate_priority,
    priority_label,
)


class GraphInvestigationService:

    def __init__(
        self,
        db: Session,
        organization_id: UUID,
        user_id: UUID,
    ):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id

    def _get_roots(self, root_ids):

        roots = self.db.execute(
            select(KnowledgeGraphNode).where(
                KnowledgeGraphNode.organization_id
                == self.organization_id,
                KnowledgeGraphNode.id.in_(root_ids),
            )
        ).scalars().all()

        if len(roots) != len(root_ids):
            raise HTTPException(
                status_code=404,
                detail=(
                    "One or more starting nodes were not found "
                    "in this organization"
                ),
            )

        return roots

    def _load_edges(
        self,
        root_ids,
        depth,
        include_unverified,
        relationship_types,
    ):

        # Load only tenant-owned edges.
        # The traversal engine enforces the requested depth.
        statement = select(KnowledgeGraphEdge).where(
            KnowledgeGraphEdge.organization_id
            == self.organization_id
        )

        if not include_unverified:
            statement = statement.where(
                KnowledgeGraphEdge.verification_status
                == "verified"
            )

        if relationship_types:
            statement = statement.where(
                KnowledgeGraphEdge.relation_type.in_(
                    relationship_types
                )
            )

        # Limit the graph data loaded into memory.
        # This is a safety cap, not a substitute for pagination
        # or a graph database for very large deployments.
        edges = self.db.execute(
            statement.limit(10000)
        ).scalars().all()

        return edges

def _load_nodes_for_traversal(
    self,
    roots,
    edges,
    include_unverified,
    node_types=None,
):

    candidate_ids = {
        root.id for root in roots
    }

    for edge in edges:
        candidate_ids.add(edge.source_node_id)
        candidate_ids.add(edge.target_node_id)

    statement = select(KnowledgeGraphNode).where(
        KnowledgeGraphNode.organization_id
        == self.organization_id,
        KnowledgeGraphNode.id.in_(candidate_ids),
    )

    if not include_unverified:
        statement = statement.where(
            or_(
                KnowledgeGraphNode.verification_status == "verified",
                KnowledgeGraphNode.id.in_(
                    [root.id for root in roots]
                ),
            )
        )

    return self.db.execute(statement).scalars().all()

    def _load_evidence(self, node_ids):

        if not node_ids:
            return []

        return self.db.execute(
            select(KnowledgeGraphEvidence).where(
                KnowledgeGraphEvidence.organization_id
                == self.organization_id,
                KnowledgeGraphEvidence.node_id.in_(node_ids),
            ).limit(20000)
        ).scalars().all()

    def _make_finding(
        self,
        run,
        node,
        path,
        finding_type,
        title,
        summary,
        evidence,
        details=None,
    ):

        supporting = [
            item for item in evidence
            if item.evidence_role == "supports"
        ]

        contradicting = [
            item for item in evidence
            if item.evidence_role == "contradicts"
        ]

        evidence_gap = (
            finding_type == "evidence_gap"
        )

        score = calculate_priority(
            node_type=node.node_type,
            path_depth=path["depth"],
            evidence_count=len(supporting),
            contradiction_count=len(contradicting),
            evidence_gap=evidence_gap,
        )

        confidence = (
            float(node.confidence)
            if node.confidence is not None
            else None
        )

        finding = GraphInvestigationFinding(
            organization_id=self.organization_id,
            run_id=run.id,
            node_id=node.id,
            finding_type=finding_type,
            priority=priority_label(score),
            priority_score=score,
            confidence=confidence,
            title=title,
            summary=summary,
            status="open",
            path_node_ids=path["node_ids"],
            path_edge_ids=path["edge_ids"],
            evidence_ids=[
                str(item.id) for item in evidence
            ],
            details=details or {},
        )

        self.db.add(finding)

        return finding

    def create_investigation(
        self,
        payload,
    ):

        roots = self._get_roots(
            payload.root_node_ids
        )

        now = datetime.now(timezone.utc)

        run = GraphInvestigationRun(
            organization_id=self.organization_id,
            title=payload.title,
            description=payload.description,
            status="running",
            root_node_ids=[
                str(item) for item in payload.root_node_ids
            ],
            depth=payload.depth,
            filters={
                "include_unverified": payload.include_unverified,
                "relationship_types": payload.relationship_types,
                "node_types": payload.node_types,
                "include_evidence": payload.include_evidence,
            },
            created_by=self.user_id,
            started_at=now,
        )

        self.db.add(run)
        self.db.flush()

        try:

            edges = self._load_edges(
                root_ids=payload.root_node_ids,
                depth=payload.depth,
                include_unverified=payload.include_unverified,
                relationship_types=payload.relationship_types,
            )

            nodes = self._load_nodes_for_traversal(
                roots=roots,
                edges=edges,
                include_unverified=payload.include_unverified,
                node_types=payload.node_types,
            )

            node_map = {
                str(node.id): node
                for node in nodes
            }

            # Keep only edges whose endpoints are eligible.
            eligible_edges = [
                edge for edge in edges
                if (
                    str(edge.source_node_id) in node_map
                    and str(edge.target_node_id) in node_map
                )
            ]

            traversal = traverse_graph(
                root_nodes=roots,
                edges=eligible_edges,
                depth=payload.depth,
            )

            # Retain only nodes discovered by the traversal.
            reached_nodes = {
                node_id: node_map[node_id]
                for node_id in traversal.paths
                if node_id in node_map
            }

            evidence_by_node = {}

            if payload.include_evidence:

                evidence = self._load_evidence(
                    [
                        node.id
                        for node in reached_nodes.values()
                    ]
                )

                for item in evidence:
                    evidence_by_node.setdefault(
                        str(item.node_id),
                        [],
                    ).append(item)

            findings = []

            for node_id, node in reached_nodes.items():

                if node_id in {
                    str(root.id) for root in roots
                }:
                    continue

                if (
                    payload.node_types
                    and node.node_type not in payload.node_types
                ):
                    continue

                path = traversal.paths[node_id]

                node_evidence = evidence_by_node.get(
                    node_id,
                    [],
                )

                supporting = [
                    item for item in node_evidence
                    if item.evidence_role == "supports"
                ]

                contradicting = [
                    item for item in node_evidence
                    if item.evidence_role == "contradicts"
                ]

                if node.node_type == "obligation":

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="obligation_impact",
                            title=f"Potential obligation impact: {node.name}",
                            summary=(
                                "This obligation is connected to "
                                "one of the investigation's starting "
                                "entities. Review the relationship "
                                "path and supporting evidence before "
                                "making an applicability decision."
                            ),
                            evidence=node_evidence,
                            details={
                                "relationship_path": path,
                                "supporting_evidence_count": len(supporting),
                                "contradicting_evidence_count": len(contradicting),
                                "applicability": "not_assessed",
                            },
                        )
                    )

                elif node.node_type == "product":

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="product_impact",
                            title=f"Potential product impact: {node.name}",
                            summary=(
                                "This product is connected to the "
                                "investigation graph. Confirm the "
                                "relevant obligation and product scope."
                            ),
                            evidence=node_evidence,
                            details={
                                "relationship_path": path,
                                "applicability": "not_assessed",
                            },
                        )
                    )

                elif node.node_type == "organization":

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="organization_impact",
                            title=f"Potential organization impact: {node.name}",
                            summary=(
                                "This organization entity is connected "
                                "to the investigation. Confirm its "
                                "relationship to the affected requirement."
                            ),
                            evidence=node_evidence,
                            details={
                                "relationship_path": path,
                                "applicability": "not_assessed",
                            },
                        )
                    )

                if node.node_type == "obligation" and not supporting:

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="evidence_gap",
                            title=f"Evidence gap: {node.name}",
                            summary=(
                                "No supporting evidence was linked "
                                "to this obligation in the graph. "
                                "This does not establish that evidence "
                                "does not exist elsewhere."
                            ),
                            evidence=node_evidence,
                            details={
                                "gap_type": "no_supporting_graph_evidence",
                                "search_required": True,
                            },
                        )
                    )

                if contradicting:

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="contradiction",
                            title=f"Contradicting evidence: {node.name}",
                            summary=(
                                "One or more evidence records are "
                                "marked as contradicting this entity. "
                                "Review the source passages and their "
                                "context before resolving the conflict."
                            ),
                            evidence=contradicting,
                            details={
                                "contradiction_count": len(contradicting),
                                "resolution_required": True,
                            },
                        )
                    )

                if (
                    node.node_type not in {
                        "obligation",
                        "product",
                        "organization",
                    }
                    and not contradicting
                ):

                    findings.append(
                        self._make_finding(
                            run=run,
                            node=node,
                            path=path,
                            finding_type="related_entity",
                            title=f"Related entity: {node.name}",
                            summary=(
                                "This entity was discovered through "
                                "the graph traversal and may provide "
                                "useful context for the investigation."
                            ),
                            evidence=node_evidence,
                            details={
                                "node_type": node.node_type,
                            },
                        )
                    )

            self.db.flush()

            # Sort the saved findings by priority.
            findings.sort(
                key=lambda item: float(item.priority_score),
                reverse=True,
            )

            counts = {}

            for finding in findings:
                counts[finding.finding_type] = (
                    counts.get(finding.finding_type, 0) + 1
                )

            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

            run.summary = (
                f"Investigation completed. "
                f"{len(reached_nodes)} graph nodes were reached, "
                f"{len(traversal.edges)} relationships were traversed, "
                f"and {len(findings)} findings were generated. "
                "Applicability decisions require human review."
            )

            run.result_metadata = {
                "nodes_reached": len(reached_nodes),
                "edges_traversed": len(traversal.edges),
                "findings_generated": len(findings),
                "finding_counts": counts,
                "evidence_records": sum(
                    len(items)
                    for items in evidence_by_node.values()
                ),
                "algorithm": "bounded_breadth_first_search",
                "scoring_version": "1.0",
            }

            self.db.flush()

            return run, findings

        except Exception as exc:

            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.completed_at = datetime.now(timezone.utc)

            self.db.flush()

            raise

    def get_investigation(self, run_id: UUID):

        run = self.db.execute(
            select(GraphInvestigationRun).where(
                GraphInvestigationRun.id == run_id,
                GraphInvestigationRun.organization_id
                == self.organization_id,
            )
        ).scalar_one_or_none()

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="Investigation not found",
            )

        findings = self.db.execute(
            select(GraphInvestigationFinding).where(
                GraphInvestigationFinding.run_id == run.id,
                GraphInvestigationFinding.organization_id
                == self.organization_id,
            ).order_by(
                GraphInvestigationFinding.priority_score.desc()
            )
        ).scalars().all()

        return run, findings

    def list_investigations(
        self,
        limit=20,
        offset=0,
    ):

        statement = select(GraphInvestigationRun).where(
            GraphInvestigationRun.organization_id
            == self.organization_id
        ).order_by(
            GraphInvestigationRun.created_at.desc()
        )

        runs = self.db.execute(
            statement.offset(offset).limit(limit)
        ).scalars().all()

        return runs

    def review_finding(
        self,
        finding_id: UUID,
        payload,
    ):

        finding = self.db.execute(
            select(GraphInvestigationFinding).where(
                GraphInvestigationFinding.id == finding_id,
                GraphInvestigationFinding.organization_id
                == self.organization_id,
            )
        ).scalar_one_or_none()

        if finding is None:
            raise HTTPException(
                status_code=404,
                detail="Investigation finding not found",
            )

        finding.status = payload.status
        finding.review_decision = payload.review_decision
        finding.review_notes = payload.review_notes
        finding.reviewed_by = self.user_id
        finding.reviewed_at = datetime.now(timezone.utc)

        self.db.flush()

        return finding