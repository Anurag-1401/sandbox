
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient, PyJWKClientError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.principal import UserPrincipal
from app.db.session import get_db
from app.models.identity import (
    User,
    Organization,
    OrganizationMembership,
)


def unauthorized() -> HTTPException:
    """Return a standard authentication error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    """
    Create and cache the JWKS client.

    Caching avoids creating a new client for every API request.
    The client also caches signing keys.
    """
    return PyJWKClient(
        settings.oidc_jwks_url,
        cache_keys=True,
    )


def verify_access_token(token: str) -> dict:
    """
    Verify an OIDC access token.

    Validates:
    - Signature
    - Allowed signing algorithm
    - Issuer
    - Audience
    - Expiration
    - Required claims
    """

    if not all(
        [
            settings.oidc_issuer,
            settings.oidc_audience,
            settings.oidc_jwks_url,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured",
        )

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(
            token
        )

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={
                "require": [
                    "exp",
                    "iat",
                    "sub",
                    "iss",
                    "aud",
                ],
            },
        )

        return claims

    except (
        jwt.InvalidTokenError,
        PyJWKClientError,
        ValueError,
    ) as exc:
        raise unauthorized() from exc


def set_transaction_context(
    db: Session,
    *,
    user_id: UUID,
    organization_id: UUID | None = None,
) -> None:
    """
    Set PostgreSQL transaction-local security context.

    The third argument to set_config is TRUE, so values are
    automatically reset when the transaction ends.
    """

    db.execute(
        text(
            """
            SELECT set_config(
                'app.current_user_id',
                :user_id,
                true
            )
            """
        ),
        {
            "user_id": str(user_id),
        },
    )

    if organization_id is not None:
        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_org_id',
                    :organization_id,
                    true
                )
                """
            ),
            {
                "organization_id": str(organization_id),
            },
        )


def get_current_principal(
    authorization: str | None = Header(default=None),
    organization_id: UUID | None = Header(
        default=None,
        alias="X-Organization-ID",
    ),
    db: Session = Depends(get_db),
) -> UserPrincipal:
    """
    Authenticate the user and resolve their organization membership.

    Authentication flow:
    1. Extract Bearer token.
    2. Verify the OIDC JWT.
    3. Resolve the internal user.
    4. Set transaction-local user context.
    5. Resolve active organization memberships.
    6. Validate the selected organization.
    7. Set transaction-local organization context.
    8. Return the authenticated principal.
    """

    # ---------------------------------------------------------
    # 1. Validate Authorization header
    # ---------------------------------------------------------

    if not authorization:
        raise unauthorized()

    scheme, separator, token = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token.strip()
    ):
        raise unauthorized()

    token = token.strip()

    # ---------------------------------------------------------
    # 2. Verify JWT
    # ---------------------------------------------------------

    claims = verify_access_token(token)

    external_subject = claims.get("sub")

    if not isinstance(external_subject, str) or not external_subject:
        raise unauthorized()

    # ---------------------------------------------------------
    # 3. Resolve internal user
    # ---------------------------------------------------------

    try:
        user = db.execute(
            select(User).where(
                User.external_subject == external_subject,
                User.is_active.is_(True),
            )
        ).scalar_one_or_none()

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to resolve authenticated user",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not registered or is inactive",
        )

    # Only accept email data asserted as verified by the OIDC provider.
    verified_email = claims.get("email")
    email_verified = claims.get("email_verified") is True

    if email_verified and isinstance(verified_email, str):
        user.email = verified_email.strip().lower()
        user.email_verified = True
        db.flush()

    # ---------------------------------------------------------
    # 4. Establish user context before membership query
    # ---------------------------------------------------------

    try:
        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_user_id',
                    :user_id,
                    true
                )
                """
            ),
            {
                "user_id": str(user.id),
            },
        )

        # -----------------------------------------------------
        # 5. Resolve active memberships
        # -----------------------------------------------------

        membership_statement = (
            select(
                OrganizationMembership,
                Organization,
            )
            .join(
                Organization,
                Organization.id
                == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == "active",
                Organization.is_active.is_(True),
            )
        )

        # -----------------------------------------------------
        # 6. Apply optional organization selection
        # -----------------------------------------------------

        if organization_id is not None:
            membership_statement = membership_statement.where(
                OrganizationMembership.organization_id
                == organization_id
            )

        memberships = db.execute(
            membership_statement
        ).all()

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to resolve organization membership",
        ) from exc

    # ---------------------------------------------------------
    # 7. Validate membership
    # ---------------------------------------------------------

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active membership found for this organization",
        )

    if len(memberships) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Multiple organization memberships found. "
                "Select an organization using X-Organization-ID."
            ),
        )

    membership, organization = memberships[0]

    # ---------------------------------------------------------
    # 8. Establish organization context
    # ---------------------------------------------------------

    try:
        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_org_id',
                    :organization_id,
                    true
                )
                """
            ),
            {
                "organization_id": str(organization.id),
            },
        )

        db.execute(
            text(
                """
                SELECT set_config(
                    'app.current_org_role',
                    :organization_role,
                    true
                )
                """
            ),
            {
                "organization_role": membership.role,
            },
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to establish organization security context",
        ) from exc

    # ---------------------------------------------------------
    # 9. Return authenticated principal
    # ---------------------------------------------------------

    return UserPrincipal(
        user_id=user.id,
        organization_id=organization.id,
        role=membership.role,
        is_active=True,
    )
