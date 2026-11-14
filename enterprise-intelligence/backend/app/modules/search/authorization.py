from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.principal import UserPrincipal
from app.models.document import Document
from app.models.document_version import DocumentVersion


class DocumentAuthorizationService(Protocol):
    def get_searchable_document_ids(
        self,
        *,
        db: Session,
        principal: UserPrincipal,
        requested_document_id: UUID | None = None,
    ) -> set[UUID]:
        ...


class DatabaseDocumentAuthorizationService:
    """
    Organization-level document authorization.

    The current project has no document ACL table. This implementation
    allows active organization members to search indexed documents
    belonging to their organization.

    It intentionally does not implement department or per-document ACLs.
    """

    def get_searchable_document_ids(
        self,
        *,
        db: Session,
        principal: UserPrincipal,
        requested_document_id: UUID | None = None,
    ) -> set[UUID]:

        if not principal.is_active:
            return set()

        statement = (
            select(Document.id)
            .join(
                DocumentVersion,
                DocumentVersion.document_id == Document.id,
            )
            .where(
                Document.organization_id == principal.organization_id,
                DocumentVersion.organization_id == principal.organization_id,
                Document.status == "indexed",
                DocumentVersion.status == "indexed",
            )
            .distinct()
        )

        if requested_document_id is not None:
            statement = statement.where(
                Document.id == requested_document_id
            )

        return set(db.execute(statement).scalars().all())