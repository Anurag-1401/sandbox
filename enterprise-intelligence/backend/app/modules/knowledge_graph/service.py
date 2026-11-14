from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.document_chunk import DocumentChunk

from app.models.knowledge_graph import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeGraphEvidence,
)

from app.modules.knowledge_graph.schemas import (
    NodeCreate,
    EdgeCreate,
    EvidenceCreate,
)


class KnowledgeGraphService:

    def __init__(
        self,
        db: Session,
        organization_id: UUID,
        user_id: UUID,
    ):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id

    # ---------------------------------------------------------
    # NODE OPERATIONS
    # ---------------------------------------------------------

    def create_node(
        self,
        payload: NodeCreate,
    ) -> KnowledgeGraphNode:

        existing = self.db.execute(
            select(KnowledgeGraphNode).where(
                KnowledgeGraphNode.organization_id
                == self.organization_id,
                KnowledgeGraphNode.canonical_key
                == payload.canonical_key,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        node = KnowledgeGraphNode(
            organization_id=self.organization_id,
            node_type=payload.node_type,
            name=payload.name,
            canonical_key=payload.canonical_key,
            external_identifier=payload.external_identifier,
            description=payload.description,
            jurisdiction=payload.jurisdiction,
            aliases=payload.aliases,
            properties=payload.properties,
            confidence=payload.confidence,
            verification_status="unverified",
            created_by=self.user_id,
        )

        self.db.add(node)
        self.db.flush()

        return node

    def get_node(
        self,
        node_id: UUID,
    ) -> KnowledgeGraphNode:

        node = self.db.execute(
            select(KnowledgeGraphNode).where(
                KnowledgeGraphNode.id == node_id,
                KnowledgeGraphNode.organization_id
                == self.organization_id,
            )
        ).scalar_one_or_none()

        if node is None:
            raise HTTPException(
                status_code=404,
                detail="Knowledge graph node not found",
            )

        return node

    def search_nodes(
        self,
        query: str | None = None,
        node_type: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ):

        statement = select(KnowledgeGraphNode).where(
            KnowledgeGraphNode.organization_id
            == self.organization_id
        )

        if node_type:
            statement = statement.where(
                KnowledgeGraphNode.node_type == node_type
            )

        if query:
            search_term = f"%{query.strip()}%"

            statement = statement.where(
                or_(
                    KnowledgeGraphNode.name.ilike(search_term),
                    KnowledgeGraphNode.description.ilike(search_term),
                    KnowledgeGraphNode.canonical_key.ilike(search_term),
                    KnowledgeGraphNode.external_identifier.ilike(
                        search_term
                    ),
                )
            )

        count_statement = select(
            KnowledgeGraphNode.id
        ).where(
            KnowledgeGraphNode.organization_id
            == self.organization_id
        )

        if node_type:
            count_statement = count_statement.where(
                KnowledgeGraphNode.node_type == node_type
            )

        if query:
            search_term = f"%{query.strip()}%"
            count_statement = count_statement.where(
                or_(
                    KnowledgeGraphNode.name.ilike(search_term),
                    KnowledgeGraphNode.description.ilike(search_term),
                    KnowledgeGraphNode.canonical_key.ilike(search_term),
                    KnowledgeGraphNode.external_identifier.ilike(
                        search_term
                    ),
                )
            )

        total = len(
            self.db.execute(count_statement).all()
        )

        items = self.db.execute(
            statement
            .order_by(KnowledgeGraphNode.name.asc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()

        return items, total

    # ---------------------------------------------------------
    # EDGE OPERATIONS
    # ---------------------------------------------------------

    def create_edge(
        self,
        payload: EdgeCreate,
    ) -> KnowledgeGraphEdge:

        source = self.get_node(payload.source_node_id)
        target = self.get_node(payload.target_node_id)

        if source.organization_id != target.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Cross-organization edges are forbidden",
            )

        existing = self.db.execute(
            select(KnowledgeGraphEdge).where(
                KnowledgeGraphEdge.organization_id
                == self.organization_id,
                KnowledgeGraphEdge.source_node_id
                == source.id,
                KnowledgeGraphEdge.target_node_id
                == target.id,
                KnowledgeGraphEdge.relation_type
                == payload.relation_type,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        edge = KnowledgeGraphEdge(
            organization_id=self.organization_id,
            source_node_id=source.id,
            target_node_id=target.id,
            relation_type=payload.relation_type,
            description=payload.description,
            properties=payload.properties,
            confidence=payload.confidence,
            verification_status="unverified",
            created_by=self.user_id,
        )

        self.db.add(edge)
        self.db.flush()

        return edge

    # ---------------------------------------------------------
    # EVIDENCE OPERATIONS
    # ---------------------------------------------------------

    def add_evidence(
        self,
        payload: EvidenceCreate,
    ) -> KnowledgeGraphEvidence:

        # Validate target belongs to the current organization.
        if payload.node_id:
            self.get_node(payload.node_id)

        if payload.edge_id:
            edge = self.db.execute(
                select(KnowledgeGraphEdge).where(
                    KnowledgeGraphEdge.id == payload.edge_id,
                    KnowledgeGraphEdge.organization_id
                    == self.organization_id,
                )
            ).scalar_one_or_none()

            if edge is None:
                raise HTTPException(
                    status_code=404,
                    detail="Knowledge graph edge not found",
                )

        # Validate document ownership.
        document = self.db.execute(
            select(Document).where(
                Document.id == payload.document_id,
                Document.organization_id == self.organization_id,
            )
        ).scalar_one_or_none()

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found in this organization",
            )

        # Validate version belongs to the same document and tenant.
        version = self.db.execute(
            select(DocumentVersion).where(
                DocumentVersion.id == payload.version_id,
                DocumentVersion.document_id == payload.document_id,
                DocumentVersion.organization_id
                == self.organization_id,
            )
        ).scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Document version not found",
            )

        # If a chunk is provided, ensure it belongs to this version.
        if payload.chunk_id:
            chunk = self.db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.id == payload.chunk_id,
                    DocumentChunk.version_id == payload.version_id,
                    DocumentChunk.organization_id
                    == self.organization_id,
                )
            ).scalar_one_or_none()

            if chunk is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "The evidence chunk does not belong "
                        "to the supplied document version"
                    ),
                )

            if payload.page_number is None:
                payload.page_number = chunk.page_start

        evidence = KnowledgeGraphEvidence(
            organization_id=self.organization_id,
            node_id=payload.node_id,
            edge_id=payload.edge_id,
            document_id=payload.document_id,
            version_id=payload.version_id,
            chunk_id=payload.chunk_id,
            page_number=payload.page_number,
            quote=payload.quote,
            evidence_role=payload.evidence_role,
            metadata_json=payload.metadata_json,
            created_by=self.user_id,
        )

        self.db.add(evidence)
        self.db.flush()

        return evidence

    def get_node_evidence(
        self,
        node_id: UUID,
    ):

        self.get_node(node_id)

        return self.db.execute(
            select(KnowledgeGraphEvidence).where(
                KnowledgeGraphEvidence.node_id == node_id,
                KnowledgeGraphEvidence.organization_id
                == self.organization_id,
            ).order_by(
                KnowledgeGraphEvidence.created_at.desc()
            )
        ).scalars().all()

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    def verify_node(
        self,
        node_id: UUID,
        verification_status: str,
    ):

        node = self.get_node(node_id)

        node.verification_status = verification_status

        self.db.flush()

        return node

    def verify_edge(
        self,
        edge_id: UUID,
        verification_status: str,
    ):

        edge = self.db.execute(
            select(KnowledgeGraphEdge).where(
                KnowledgeGraphEdge.id == edge_id,
                KnowledgeGraphEdge.organization_id
                == self.organization_id,
            )
        ).scalar_one_or_none()

        if edge is None:
            raise HTTPException(
                status_code=404,
                detail="Knowledge graph edge not found",
            )

        edge.verification_status = verification_status

        self.db.flush()

        return edge

    # ---------------------------------------------------------
    # GRAPH NEIGHBORHOOD
    # ---------------------------------------------------------

    def get_neighborhood(
        self,
        root_id: UUID,
        depth: int = 1,
        include_unverified: bool = True,
    ):

        if depth < 1 or depth > 3:
            raise HTTPException(
                status_code=400,
                detail="Graph depth must be between 1 and 3",
            )

        root = self.get_node(root_id)

        visited = {root.id}
        frontier = {root.id}

        discovered_edges = {}

        for _ in range(depth):

            if not frontier:
                break

            edge_filters = [
                KnowledgeGraphEdge.organization_id
                == self.organization_id,
                or_(
                    KnowledgeGraphEdge.source_node_id.in_(frontier),
                    KnowledgeGraphEdge.target_node_id.in_(frontier),
                ),
            ]

            if not include_unverified:
                edge_filters.append(
                    KnowledgeGraphEdge.verification_status
                    == "verified"
                )

            edges = self.db.execute(
                select(KnowledgeGraphEdge).where(
                    *edge_filters
                )
            ).scalars().all()

            next_frontier = set()

            for edge in edges:
                discovered_edges[edge.id] = edge

                other_id = (
                    edge.target_node_id
                    if edge.source_node_id in frontier
                    else edge.source_node_id
                )

                if other_id not in visited:
                    visited.add(other_id)
                    next_frontier.add(other_id)

            frontier = next_frontier

        nodes = self.db.execute(
            select(KnowledgeGraphNode).where(
                KnowledgeGraphNode.organization_id
                == self.organization_id,
                KnowledgeGraphNode.id.in_(visited),
            )
        ).scalars().all()

        return {
            "root": root,
            "nodes": nodes,
            "edges": list(discovered_edges.values()),
            "depth": depth,
        }