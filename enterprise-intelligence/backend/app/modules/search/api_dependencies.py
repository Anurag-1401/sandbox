from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security.auth import get_current_principal
from app.core.security.principal import UserPrincipal
from app.db.dependencies import get_db

from app.modules.search.authorization import (
    DatabaseDocumentAuthorizationService,
)


def get_document_authorization_service():
    return DatabaseDocumentAuthorizationService()


def get_authorized_search_context(
    principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    authorization = get_document_authorization_service()

    allowed_document_ids = (
        authorization.get_searchable_document_ids(
            db=db,
            principal=principal,
        )
    )

    return {
        "principal": principal,
        "allowed_document_ids": allowed_document_ids,
    }